"""
Bruttolohn-Berechnungen.
Extrahiert aus lohnlauf.py (AdeaLohn).
"""

from decimal import Decimal
from typing import Optional
from datetime import date, timedelta

from .models import Lohnstamm, Lohnart, LohnBasisTyp, Ferienwochen, Dreizehnter


def berechne_effektiven_monatslohn(lohnstamm: Lohnstamm) -> Decimal:
    """
    Berechnet den effektiven Monatslohn basierend auf lohn_basis_typ.
    
    Regeln:
    - 100_PROZENT: monatslohn * (pensum / 100)
    - EFF_EFFEKTIV: monatslohn (bereits effektiv)
    
    Args:
        lohnstamm: Lohnstamm des Mitarbeiters
    
    Returns:
        Effektiver Monatslohn
    """
    if lohnstamm.lohnart != Lohnart.MONATSLOHN or not lohnstamm.monatslohn:
        return Decimal("0.0")
    
    # Default: 100_PROZENT wenn nicht gesetzt
    basis_typ = lohnstamm.lohn_basis_typ
    if basis_typ is None:
        basis_typ = LohnBasisTyp.HUNDERT_PROZENT
    
    if basis_typ == LohnBasisTyp.HUNDERT_PROZENT:
        # Vertragslohn ist 100%-Lohn → mit Pensum multiplizieren
        pensum = lohnstamm.beschaeftigungsgrad / Decimal("100.0")
        return lohnstamm.monatslohn * pensum
    else:  # EFF_EFFEKTIV
        # Vertragslohn ist bereits effektiver Lohn
        return lohnstamm.monatslohn


def berechne_anteiligen_lohn(
    monatslohn: Decimal,
    eintrittsdatum: Optional[date],
    austrittsdatum: Optional[date],
    monat: int,
    jahr: int
) -> Decimal:
    """
    Berechnet anteiligen Monatslohn bei Eintritt/Austritt im Monat.
    
    Berechnung gemäss Schweizer Arbeitsrecht:
    - Bei Eintritt/Austritt im Monat wird der Lohn anteilig berechnet
    - Formel: (Monatslohn / 21.74) * Anzahl Arbeitstage im Zeitraum
    - 21.74 = Durchschnittliche Arbeitstage pro Monat (Schweizer Standard)
    - Arbeitstage = Kalendertage ohne Samstag/Sonntag
    
    Args:
        monatslohn: Vollständiger Monatslohn
        eintrittsdatum: Eintrittsdatum des Mitarbeiters
        austrittsdatum: Austrittsdatum des Mitarbeiters (None = aktiv)
        monat: Abrechnungsmonat (1-12)
        jahr: Abrechnungsjahr
    
    Returns:
        Anteiliger Monatslohn (oder vollständiger Lohn wenn kein Eintritt/Austritt)
    """
    # Durchschnittliche Arbeitstage pro Monat (Schweizer Standard)
    DURCHSCHNITTLICHE_ARBEITSTAGE_PRO_MONAT = Decimal("21.74")
    
    # Prüfe ob Eintritt oder Austritt im Abrechnungsmonat liegt
    abrechnungsmonat_start = date(jahr, monat, 1)
    if monat == 12:
        abrechnungsmonat_ende = date(jahr + 1, 1, 1) - timedelta(days=1)
    else:
        abrechnungsmonat_ende = date(jahr, monat + 1, 1) - timedelta(days=1)
    
    # Prüfe ob Eintritt im Monat
    eintritt_im_monat = False
    if eintrittsdatum and abrechnungsmonat_start <= eintrittsdatum <= abrechnungsmonat_ende:
        eintritt_im_monat = True
    
    # Prüfe ob Austritt im Monat
    austritt_im_monat = False
    if austrittsdatum and abrechnungsmonat_start <= austrittsdatum <= abrechnungsmonat_ende:
        austritt_im_monat = True
    
    # Wenn weder Eintritt noch Austritt im Monat → vollständiger Lohn
    if not eintritt_im_monat and not austritt_im_monat:
        return monatslohn
    
    # Berechne Anzahl Arbeitstage (ohne Samstag/Sonntag)
    # 0 = Montag, 6 = Sonntag
    def ist_arbeitstag(datum: date) -> bool:
        wochentag = datum.weekday()  # 0=Montag, 6=Sonntag
        return wochentag < 5  # Montag-Freitag
    
    # Bestimme Start- und Enddatum für Berechnung
    if eintritt_im_monat:
        start_datum = eintrittsdatum
    else:
        start_datum = abrechnungsmonat_start
    
    if austritt_im_monat:
        end_datum = austrittsdatum
    else:
        end_datum = abrechnungsmonat_ende
    
    # Zähle Arbeitstage im relevanten Zeitraum
    arbeitstage = 0
    aktuelles_datum = start_datum
    while aktuelles_datum <= end_datum:
        if ist_arbeitstag(aktuelles_datum):
            arbeitstage += 1
        aktuelles_datum += timedelta(days=1)
    
    # Anteiliger Lohn = (Monatslohn / 21.74) * Arbeitstage im Zeitraum
    anteiliger_lohn = (monatslohn / DURCHSCHNITTLICHE_ARBEITSTAGE_PRO_MONAT) * Decimal(str(arbeitstage))
    return anteiliger_lohn


def berechne_brutto(lohnstamm: Lohnstamm, stunden_gearbeitet: Decimal = Decimal("0.0")) -> Decimal:
    """
    Berechnet den Brutto-Grundlohn (ohne Privatanteil Auto).
    
    Für Monatslohn: Effektiver Monatslohn basierend auf lohn_basis_typ
    Für Stundenlohn: Stunden × Stundenlohn + Ferienzuschlag + Feiertagszuschlag + 13. Monatslohn

    Args:
        lohnstamm: Lohnstamm des Mitarbeiters
        stunden_gearbeitet: Gearbeitete Stunden (nur bei Stundenlohn)

    Returns:
        Effektiver Grundlohn (Brutto, inkl. Zuschläge bei Stundenlohn)
    """
    if lohnstamm.lohnart == Lohnart.MONATSLOHN:
        return berechne_effektiven_monatslohn(lohnstamm)
    
    elif lohnstamm.lohnart == Lohnart.STUNDENLOHN:
        # Validierung
        if not lohnstamm.stundenlohn or lohnstamm.stundenlohn <= 0:
            return Decimal("0.0")
        
        if stunden_gearbeitet <= 0:
            return Decimal("0.0")
        
        # Grundlohn = Stunden × Stundenlohn
        grundlohn = stunden_gearbeitet * lohnstamm.stundenlohn
        
        # Ferienzuschlag gesetzlich korrekt berechnen
        # Automatisch aus ferienwochen berechnen, falls ferien_zuschlag nicht gesetzt
        if lohnstamm.ferien_zuschlag > 0:
            # Manuell eingegebener Wert hat Priorität
            ferienzuschlag_prozent = lohnstamm.ferien_zuschlag
        else:
            # Automatisch aus ferienwochen berechnen
            if lohnstamm.ferienwochen == Ferienwochen.VIER_WOCHEN:
                ferienzuschlag_prozent = Decimal("8.33")  # 4 Wochen = 8.33%
            elif lohnstamm.ferienwochen == Ferienwochen.FUENF_WOCHEN:
                ferienzuschlag_prozent = Decimal("10.64")  # 5 Wochen = 10.64% (Standard)
            elif lohnstamm.ferienwochen == Ferienwochen.SECHS_WOCHEN:
                ferienzuschlag_prozent = Decimal("13.04")  # 6 Wochen = 13.04%
            else:
                ferienzuschlag_prozent = Decimal("10.64")  # Fallback: 5 Wochen
        ferienzuschlag = grundlohn * (ferienzuschlag_prozent / Decimal("100.0"))
        
        # Feiertagszuschlag berechnen (wenn vorhanden)
        feiertagszuschlag_prozent = lohnstamm.feiertag_zuschlag  # z.B. 3.59 oder 2.27
        feiertagszuschlag = grundlohn * (feiertagszuschlag_prozent / Decimal("100.0"))
        
        # 13. Monatslohn berechnen (wenn vereinbart)
        dreizehnter_betrag = Decimal("0.0")
        if lohnstamm.dreizehnter_modell != Dreizehnter.KEIN_13:
            # 13. Monatslohn als Zuschlag (typisch: 8.33%)
            dreizehnter_prozent = Decimal("8.33")  # Standard, kann variieren
            dreizehnter_betrag = grundlohn * (dreizehnter_prozent / Decimal("100.0"))
        
        # Gesamtlohn = Grundlohn + alle Zuschläge
        return grundlohn + ferienzuschlag + feiertagszuschlag + dreizehnter_betrag
    
    return Decimal("0.0")
