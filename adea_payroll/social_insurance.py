"""
Sozialversicherungs-Berechnungen.
Extrahiert aus lohn.py (AdeaLohn).
"""

from decimal import Decimal
from typing import Tuple
from datetime import date, timedelta

from .models import (
    Firmendaten, Mitarbeitende, Lohnstamm,
    KTGVerteilung, KTGKategorie, Lohnart,
)
from .constants import BVG_MINDESTLOHN_JAHR, BVG_MINDESTALTER


def ist_bvg_pflichtig_fuer_warnung(mitarbeiter: Mitarbeitende, lohnstamm: Lohnstamm, stichtag: date = None) -> bool:
    """
    Prüft, ob ein Mitarbeiter BVG-pflichtig sein KÖNNTE (nur für Warnungen).
    
    BVG-Pflicht besteht wenn:
    - Alter ≥ 17 Jahre (bei Eintritt)
    - Jahreslohn ≥ 22'680 CHF (2025)
    
    WICHTIG: Diese Funktion wird NUR für Warnungen verwendet.
    BVG-Beiträge werden MANUELL eingegeben (wie bei Abacus/Sage).
    
    Args:
        mitarbeiter: Mitarbeiter-Objekt mit Geburtsdatum
        lohnstamm: Lohnstamm mit Lohninformationen
        stichtag: Datum für Altersberechnung (default: heute)
    
    Returns:
        True wenn BVG-pflichtig sein könnte, sonst False
    """
    # Prüfe Alter
    if not mitarbeiter.geburtsdatum:
        return False
    
    # Berechne Alter am Stichtag
    if stichtag is None:
        stichtag = date.today()
    
    geburtsjahr = mitarbeiter.geburtsdatum.year
    alter = stichtag.year - geburtsjahr
    
    # Korrigiere Alter falls Geburtstag noch nicht war
    if (stichtag.month, stichtag.day) < (mitarbeiter.geburtsdatum.month, mitarbeiter.geburtsdatum.day):
        alter -= 1
    
    if alter < BVG_MINDESTALTER:
        return False
    
    # Prüfe Jahreslohn (verwende effektiven Monatslohn)
    if lohnstamm.lohnart.value == "Monatslohn" and lohnstamm.monatslohn:
        # Berechne effektiven Monatslohn
        from .gross import berechne_effektiven_monatslohn
        effektiver_monatslohn = berechne_effektiven_monatslohn(lohnstamm)
        jahreslohn = effektiver_monatslohn * Decimal("12.0")
        return jahreslohn >= BVG_MINDESTLOHN_JAHR
    
    # Bei Stundenlohn: kann nicht automatisch geprüft werden
    return False


def berechne_bvg(lohnstamm: Lohnstamm, abrechnungsmonat: int, abrechnungsjahr: int) -> Tuple[Decimal, Decimal]:
    """
    Gibt Tuple (AG, AN) zurück.
    Wenn kein BVG hinterlegt ist → (Decimal(0), Decimal(0))
    
    Prüft BVG-Gültigkeitsdatum (bvg_gueltig_ab).
    
    BVG-Beiträge gelten normalerweise für das ganze Jahr (01.01. - 31.12.).
    Ausnahmen nur bei Eintritt/Austritt im Jahr.

    Args:
        lohnstamm: Lohnstamm des Mitarbeiters mit BVG-Beiträgen
        abrechnungsmonat: Abrechnungsmonat (1-12)
        abrechnungsjahr: Abrechnungsjahr (z.B. 2025)

    Returns:
        Tuple (Arbeitgeber-Beitrag, Arbeitnehmer-Beitrag)
    """
    # Prüfe Gültigkeitsdatum
    if lohnstamm.bvg_gueltig_ab:
        # Berechne Monatsende des Abrechnungsmonats
        if abrechnungsmonat == 12:
            monats_ende = date(abrechnungsjahr + 1, 1, 1) - timedelta(days=1)
        else:
            monats_ende = date(abrechnungsjahr, abrechnungsmonat + 1, 1) - timedelta(days=1)
        
        # BVG-Beiträge sind nur gültig, wenn bvg_gueltig_ab <= Monatsende
        # Normalerweise: bvg_gueltig_ab = 01.01. des Jahres (gilt für ganzes Jahr)
        # Ausnahme: Bei Eintritt im Jahr = Eintrittsdatum
        if lohnstamm.bvg_gueltig_ab > monats_ende:
            return (Decimal("0"), Decimal("0"))
    
    if lohnstamm.bvg_ag_beitrag and lohnstamm.bvg_an_beitrag:
        return (lohnstamm.bvg_ag_beitrag, lohnstamm.bvg_an_beitrag)
    return (Decimal("0"), Decimal("0"))


def berechne_privatanteil_auto(lohnstamm: Lohnstamm) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Berechnet den Privatanteil Fahrzeug gemäss ESTV (0.9% vom Kaufpreis pro Monat für 2025).
    Zieht den Mitarbeiterbeitrag ab (NETTO-Privatanteil).
    
    Wenn kein Privatanteil aktiv ist → (0, 0, 0)
    
    Args:
        lohnstamm: Lohnstamm des Mitarbeiters mit Auto-Daten
    
    Returns:
        Tuple (Privatanteil Brutto, Mitarbeiterbeitrag, Privatanteil Netto)
        - Brutto: 0.9% vom Kaufpreis
        - Mitarbeiterbeitrag: Was MA pro Monat zahlt
        - Netto: Brutto - Mitarbeiterbeitrag (min. 0) → wird zum Bruttolohn addiert
    """
    if not lohnstamm.privatanteil_auto_aktiv or not lohnstamm.auto_preis:
        return Decimal("0.0"), Decimal("0.0"), Decimal("0.0")
    
    # Brutto: 0.9% vom Kaufpreis pro Monat (ESTV 2025)
    privatanteil_brutto = lohnstamm.auto_preis * Decimal("0.009")
    
    # Mitarbeiterbeitrag (falls vorhanden)
    mitarbeiter_beitrag = lohnstamm.auto_mitarbeiter_beitrag_monat or Decimal("0.0")
    
    # Netto: Brutto - Mitarbeiterbeitrag (max = 0 bei Überbezahlung)
    privatanteil_netto = max(Decimal("0.0"), privatanteil_brutto - mitarbeiter_beitrag)
    
    return privatanteil_brutto, mitarbeiter_beitrag, privatanteil_netto


def berechne_quellensteuer(brutto: Decimal, sozialabzuege: Decimal, mitarbeiter: Mitarbeitende) -> Decimal:
    """
    Berechnet die Quellensteuer nach manuellem Prozentsatz.

    Berechnung:
    basis = brutto - sozialabzuege
    qst = basis * (qst_prozentsatz / 100)

    Args:
        brutto: Bruttolohn
        sozialabzuege: Summe aller Sozialversicherungsabzüge
        mitarbeiter: Mitarbeitende-Objekt mit QST-Daten

    Returns:
        Quellensteuerbetrag
    """
    if not mitarbeiter.qst_daten.qst_pflichtig or not mitarbeiter.qst_daten.qst_prozentsatz:
        return Decimal("0")

    basis = brutto - sozialabzuege
    return basis * (mitarbeiter.qst_daten.qst_prozentsatz / Decimal("100"))


def berechne_bu_ag(monatslohn: Decimal, firmendaten: Firmendaten) -> Decimal:
    """
    Berechnet den BU-Beitrag (Berufsunfall), trägt Arbeitgeber

    Args:
        monatslohn: Monatslohn des Mitarbeiters
        firmendaten: Firmendaten mit BU-Satz

    Returns:
        BU-Betrag (Arbeitgeber)
    """
    return monatslohn * firmendaten.bu_satz_ag / Decimal("100.0")


def ist_nbu_pflichtig(lohnstamm: Lohnstamm) -> bool:
    """
    Prüft, ob Mitarbeiter NBU-pflichtig ist.
    
    NBU-Pflicht besteht wenn:
    - Mindestens 8 Stunden pro Woche beim gleichen Arbeitgeber
    
    Standard-Vollzeit: 42 Stunden/Woche
    Grenze: 8 Stunden/Woche = 19.05% Pensum
    
    Args:
        lohnstamm: Lohnstamm mit Beschäftigungsgrad
    
    Returns:
        True wenn NBU-pflichtig (≥8 Stunden/Woche), sonst False
    """
    STANDARD_WOCHENSTUNDEN = Decimal("42.0")  # Standard-Vollzeit Schweiz
    MIN_NBU_STUNDEN = Decimal("8.0")  # Mindeststunden für NBU
    
    # Berechne Wochenstunden aus Beschäftigungsgrad
    wochenstunden = STANDARD_WOCHENSTUNDEN * (lohnstamm.beschaeftigungsgrad / Decimal("100.0"))
    
    return wochenstunden >= MIN_NBU_STUNDEN


def berechne_nbu_an(monatslohn: Decimal, firmendaten: Firmendaten, lohnstamm: Lohnstamm) -> Decimal:
    """
    Berechnet den NBU-Beitrag (Nichtberufsunfall), trägt Arbeitnehmer.
    
    NBU ist nur pflichtig bei mindestens 8 Stunden pro Woche.
    Bei weniger als 8 Stunden/Woche: Mitarbeiter muss sich selbst versichern.
    
    Args:
        monatslohn: Monatslohn des Mitarbeiters
        firmendaten: Firmendaten mit NBU-Satz
        lohnstamm: Lohnstamm mit Beschäftigungsgrad (für 8-Stunden-Prüfung)

    Returns:
        NBU-Betrag (Arbeitnehmer), 0.0 wenn nicht NBU-pflichtig
    """
    # Prüfe 8-Stunden-Regel
    if not ist_nbu_pflichtig(lohnstamm):
        return Decimal("0.0")
    
    return monatslohn * firmendaten.nbu_satz_an / Decimal("100.0")


def hole_ktg_satz_for_mitarbeiter(mitarbeiter: Mitarbeitende, firmendaten: Firmendaten) -> Decimal:
    """
    Ermittelt den KTG-Satz für einen Mitarbeiter basierend auf seiner Kategorie

    Args:
        mitarbeiter: Mitarbeiter mit KTG-Kategorie
        firmendaten: Firmendaten mit KTG-Sätzen pro Kategorie

    Returns:
        KTG-Satz in Prozent
    """
    kategorie_key = mitarbeiter.ktg_kategorie.name  # z.B. "MITARBEITENDE"
    return firmendaten.ktg_saetze_pro_kategorie.get(kategorie_key, Decimal("0.0"))


def split_ktg_an_ag(betrag: Decimal, firmendaten: Firmendaten) -> Tuple[Decimal, Decimal]:
    """
    Teilt den KTG-Beitrag zwischen AN und AG auf gemäß Verteilungsschlüssel

    Args:
        betrag: Gesamt-KTG-Betrag
        firmendaten: Firmendaten mit KTG-Verteilung

    Returns:
        Tuple (AN_Anteil, AG_Anteil)
    """
    if betrag < 0:
        return (Decimal("0.0"), Decimal("0.0"))
    
    if firmendaten.ktg_verteilung == KTGVerteilung.AN_100:
        return (betrag, Decimal("0.0"))
    elif firmendaten.ktg_verteilung == KTGVerteilung.AG_100:
        return (Decimal("0.0"), betrag)
    else:  # HALB_HALB
        haelfte = betrag / Decimal("2.0")
        return (haelfte, haelfte)
