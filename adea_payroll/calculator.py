"""
Hauptmodul: Lohnlauf-Berechnung.
Berechnet monatliche Lohnabrechnungen mit allen Sozialabzügen und AG-Kosten.
Extrahiert aus lohnlauf.py (AdeaLohn).
"""

from decimal import Decimal
from typing import Optional
from uuid import uuid4
from datetime import date, timedelta

from .models import (
    Mitarbeitende, Lohnstamm, Firmendaten, Lohnabrechnung,
    Lohnart, LohnlaufStatus, Dreizehnter,
)
from .constants import (
    AHV_AN, AHV_AG, AHV_FREIBETRAG_RENTNER,
    ALV_AN, ALV_AG, ALV_CAP_JAHR,
)
from .rounding import rappen, proz
from .gross import berechne_effektiven_monatslohn, berechne_anteiligen_lohn, berechne_brutto
from .social_insurance import (
    berechne_privatanteil_auto,
    berechne_quellensteuer,
    berechne_bvg,
    berechne_bu_ag,
    berechne_nbu_an,
    hole_ktg_satz_for_mitarbeiter,
    split_ktg_an_ag,
    ist_bvg_pflichtig_fuer_warnung,
)
from .thirteenth_salary import berechne_dreizehnter
from .overtime import berechne_ueberstunden


# ============================================================================
# HAUPTFUNKTION: LOHNABRECHNUNG BERECHNEN
# ============================================================================

def berechne_lohnlauf(
    mitarbeiter: Mitarbeitende,
    lohnstamm: Lohnstamm,
    firmendaten: Firmendaten,
    monat: int,
    jahr: int,
    data_manager=None
) -> Lohnabrechnung:
    """
    Berechnet eine vollständige Lohnabrechnung für einen Mitarbeiter.

    Berechnung:
    1. Grundlohn (Monatslohn)
    2. + Privatanteil Auto (0.9% vom Kaufpreis)
    3. = Basis
    4. - Sozialabzüge AN (AHV, ALV, NBU, KTG, BVG, QST)
    5. = Netto
    6. + Kosten AG (AHV, ALV, BU, KTG, BVG)

    Args:
        mitarbeiter: Mitarbeiter-Objekt mit Stammdaten
        lohnstamm: Lohnstamm mit Lohn und Versicherungsdaten
        firmendaten: Firmendaten mit Versicherungssätzen
        monat: Abrechnungsmonat (1-12)
        jahr: Abrechnungsjahr (z.B. 2025)
        data_manager: Optional - SecureDataManager für Jahresakkumulation (AHV-Freibetrag, ALV-Cap)

    Returns:
        Lohnabrechnung-Objekt mit allen berechneten Werten
    """
    # Neue Lohnabrechnung initialisieren
    abrechnung = Lohnabrechnung(
        id=uuid4(),
        mitarbeiter_id=mitarbeiter.id,
        monat=monat,
        jahr=jahr,
        erstellt_am=date.today(),
        status=LohnlaufStatus.ENTWURF  # Neuer Lohnlauf ist immer Entwurf
    )

    # ========================================================================
    # 1. GRUNDLOHN (mit Beschäftigungsgrad)
    # ========================================================================
    # Bei Stundenlohn: stunden_gearbeitet wird manuell pro Abrechnung eingegeben (initial 0.0)
    stunden_gearbeitet = abrechnung.stunden_gearbeitet if hasattr(abrechnung, 'stunden_gearbeitet') else Decimal("0.0")
    effektiver_monatslohn = berechne_brutto(lohnstamm, stunden_gearbeitet)
    
    # Bei Stundenlohn: Zuschläge separat berechnen und speichern
    if lohnstamm.lohnart == Lohnart.STUNDENLOHN and stunden_gearbeitet > 0 and lohnstamm.stundenlohn:
        grundlohn_ohne_zuschlaege = stunden_gearbeitet * lohnstamm.stundenlohn
        
        # Ferienzuschlag
        ferienzuschlag_prozent = lohnstamm.ferien_zuschlag
        abrechnung.ferienzuschlag_betrag = grundlohn_ohne_zuschlaege * (ferienzuschlag_prozent / Decimal("100.0"))
        
        # Feiertagszuschlag
        feiertagszuschlag_prozent = lohnstamm.feiertag_zuschlag
        abrechnung.feiertagszuschlag_betrag = grundlohn_ohne_zuschlaege * (feiertagszuschlag_prozent / Decimal("100.0"))
        
        # 13. Monatslohn (wenn vereinbart)
        abrechnung.dreizehnter_betrag = Decimal("0.0")
        if lohnstamm.dreizehnter_modell != Dreizehnter.KEIN_13:
            dreizehnter_prozent = Decimal("8.33")  # Standard
            abrechnung.dreizehnter_betrag = grundlohn_ohne_zuschlaege * (dreizehnter_prozent / Decimal("100.0"))
        
        abrechnung.stunden_gearbeitet = stunden_gearbeitet
        abrechnung.grundlohn = effektiver_monatslohn  # Enthält bereits alle Zuschläge
    else:
        # Monatslohn: 13. Monatslohn separat berechnen
        abrechnung.ferienzuschlag_betrag = Decimal("0.0")
        abrechnung.feiertagszuschlag_betrag = Decimal("0.0")
        abrechnung.stunden_gearbeitet = Decimal("0.0")
        
        # Anteilige Berechnung bei Eintritt/Austritt im Monat
        vollstaendiger_lohn = effektiver_monatslohn
        if lohnstamm.lohnart == Lohnart.MONATSLOHN and lohnstamm.monatslohn:
            effektiver_monatslohn = berechne_anteiligen_lohn(
                monatslohn=effektiver_monatslohn,
                eintrittsdatum=mitarbeiter.eintrittsdatum,
                austrittsdatum=mitarbeiter.austrittsdatum,
                monat=monat,
                jahr=jahr
            )
            # Markiere als anteilig wenn unterschiedlich
            if abs(effektiver_monatslohn - vollstaendiger_lohn) > Decimal("0.01"):
                abrechnung.anteiliger_lohn = True
        
        abrechnung.grundlohn = effektiver_monatslohn
        
        # 13. Monatslohn wird NUR bei vollständigem Monat ausbezahlt
        # (Bei anteiliger Berechnung wird 13. Monatslohn nicht anteilig berechnet)
        dreizehnter_betrag = berechne_dreizehnter(lohnstamm, monat)
        abrechnung.dreizehnter_betrag = dreizehnter_betrag
        # 13. Monatslohn wird zum Grundlohn hinzugezählt
        abrechnung.grundlohn = abrechnung.grundlohn + dreizehnter_betrag

    # ========================================================================
    # 2. PRIVATANTEIL AUTO (Brutto - Mitarbeiterbeitrag = Netto)
    # ========================================================================
    # Berechnet: Brutto, Mitarbeiterbeitrag, Netto
    privatanteil_auto_brutto, privatanteil_auto_beitrag, privatanteil_auto_netto = berechne_privatanteil_auto(lohnstamm)
    
    # Privatanteil Auto ebenfalls anteilig berechnen bei Eintritt/Austritt
    if abrechnung.anteiliger_lohn and vollstaendiger_lohn > 0:
        anteil_faktor = effektiver_monatslohn / vollstaendiger_lohn
        privatanteil_auto_brutto = privatanteil_auto_brutto * anteil_faktor
        privatanteil_auto_beitrag = privatanteil_auto_beitrag * anteil_faktor
        privatanteil_auto_netto = privatanteil_auto_netto * anteil_faktor
    
    # Privatanteil in Abrechnung speichern
    abrechnung.privatanteil_auto_brutto = privatanteil_auto_brutto
    abrechnung.privatanteil_auto_mitarbeiter_beitrag = privatanteil_auto_beitrag
    abrechnung.privatanteil_auto = privatanteil_auto_netto  # Nur Netto wird zur Basis addiert!

    # ========================================================================
    # 2b. ÜBERSTUNDEN (sozialversicherungspflichtig)
    # ========================================================================
    # Überstunden werden manuell pro Abrechnung eingegeben (initial 0.0)
    # Zuschläge werden aus Lohnstamm übernommen (können pro Abrechnung überschrieben werden)
    
    # Überstunden berechnen
    basis_stundenlohn, ueberstunden_normal_betrag, ueberstunden_nacht_betrag, ueberstunden_total = berechne_ueberstunden(
        lohnstamm=lohnstamm,
        ueberstunden_normal=abrechnung.ueberstunden_normal,
        ueberstunden_nacht=abrechnung.ueberstunden_nacht,
        zuschlag_normal=abrechnung.ueberstunden_normal_zuschlag,
        zuschlag_nacht=abrechnung.ueberstunden_nacht_zuschlag
    )
    
    # Überstunden-Entschädigung speichern
    abrechnung.ueberstunden_betrag_total = ueberstunden_total
    
    # Überstunden zur Basis addieren (sozialversicherungspflichtig!)
    # WICHTIG: Überstunden werden zum Grundlohn addiert (für AHV/ALV/NBU/KTG-Basis)

    # ========================================================================
    # 3. BASIS (Grundlage für Sozialabzüge)
    # ========================================================================
    # Familienzulagen berechnen: Summe aller Zulagen, deren Zeitraum den Abrechnungsmonat deckt
    abrechnungsmonat_start = date(jahr, monat, 1)
    # Letzter Tag des Monats berechnen
    if monat == 12:
        abrechnungsmonat_ende = date(jahr + 1, 1, 1)
    else:
        abrechnungsmonat_ende = date(jahr, monat + 1, 1)
    abrechnungsmonat_ende = abrechnungsmonat_ende - timedelta(days=1)
    
    familienzulagen = Decimal("0.0")
    for zulage in mitarbeiter.familienzulagen:
        # Prüfe ob Zulage im Abrechnungsmonat gültig ist
        zulage_ende = zulage.gueltig_bis if zulage.gueltig_bis else date.max
        if zulage.gueltig_ab <= abrechnungsmonat_ende and zulage_ende >= abrechnungsmonat_start:
            familienzulagen += zulage.betrag
    
    # Familienzulagen ebenfalls anteilig berechnen bei Eintritt/Austritt
    if abrechnung.anteiliger_lohn and vollstaendiger_lohn > 0:
        anteil_faktor = effektiver_monatslohn / vollstaendiger_lohn
        familienzulagen = familienzulagen * anteil_faktor
    
    # Bemessungsgrundlagen berechnen:
    # - AHV/NBU/KTG-Basis = Grundlohn + Bonus + Privatanteil + Familienzulagen
    # - ALV-Basis = Grundlohn + Bonus + Privatanteil (Familienzulagen NICHT ALV-pflichtig)
    # - QST-Basis = ALV-Basis - AN-Sozialabzüge auf ALV-Basis
    # Bonus wird zur Basis hinzugezählt (sozialversicherungspflichtig)
    # Bonus wird initial auf 0.0 gesetzt (wird manuell pro Abrechnung eingegeben)
    abrechnung.bonus = Decimal("0.0")
    
    # Speichere Bemessungsgrundlagen in Abrechnung
    abrechnung.familienzulagen = familienzulagen
    # Nachzahlung/Rückforderung wird manuell eingegeben (initial 0.0, ohne Periode)
    abrechnung.familienzulagen_nachzahlung = Decimal("0.0")
    abrechnung.familienzulagen_nachzahlung_von_monat = None
    abrechnung.familienzulagen_nachzahlung_von_jahr = None
    abrechnung.familienzulagen_nachzahlung_bis_monat = None
    abrechnung.familienzulagen_nachzahlung_bis_jahr = None
    
    # Gesamte Familienzulagen = normale + Nachzahlung/Rückforderung
    familienzulagen_total = familienzulagen + abrechnung.familienzulagen_nachzahlung
    
    # Bemessungsgrundlage mit Gesamt-Familienzulagen, Bonus und Überstunden
    # WICHTIG: Überstunden sind sozialversicherungspflichtig!
    ahv_nbu_ktg_basis = (
        abrechnung.grundlohn + 
        abrechnung.bonus + 
        abrechnung.ueberstunden_betrag_total +  # Überstunden zur Basis!
        abrechnung.privatanteil_auto + 
        familienzulagen_total
    )
    alv_basis = (
        abrechnung.grundlohn + 
        abrechnung.bonus + 
        abrechnung.ueberstunden_betrag_total +  # Überstunden zur ALV-Basis!
        abrechnung.privatanteil_auto
    )
    abrechnung.basis = ahv_nbu_ktg_basis  # Hauptbasis (für AHV/NBU/KTG)
    abrechnung.alv_basis = alv_basis  # ALV-Basis (ohne Familienzulagen, mit Bonus)
    
    # ========================================================================
    # 3b. BVG-PFLICHT FÜR WARNHINWEIS (nicht für Berechnung)
    # ========================================================================
    # BVG-Pflicht nur für Warnung prüfen (BVG-Beiträge werden manuell eingegeben)
    stichtag = date(jahr, monat, 1)
    lohnstamm.bvg_pflichtig = ist_bvg_pflichtig_fuer_warnung(mitarbeiter, lohnstamm, stichtag)

    # ========================================================================
    # 4. ARBEITNEHMER-ABZÜGE (AN)
    # ========================================================================

    # 4a) AHV/IV/EO - Arbeitnehmer (5.3%)
    # Basis: Grundlohn + Privatanteil + Familienzulagen
    # SONDERREGELUNG: Altersrentner haben Freibetrag von CHF 16'800/Jahr (seit AHV 21)
    
    if mitarbeiter.ist_altersrentner and not mitarbeiter.verzicht_ahv_freibetrag:
        # Jahresakkumulation für AHV-Freibetrag (analog zu ALV)
        ahv_basis_jahr_bisher = Decimal("0.0")
        if data_manager:
            try:
                abrechnungen_jahr = data_manager.load_abrechnungen()
                for abr in abrechnungen_jahr:
                    if (abr.mitarbeiter_id == mitarbeiter.id and 
                        abr.jahr == jahr and 
                        abr.monat < monat and
                        abr.status.value in ["abgeschlossen", "ausgezahlt"]):
                        # Für Altersrentner: AHV-Basis (ahv_nbu_ktg_basis) akkumulieren
                        # Verwende gespeicherte Basis (aus Abrechnung)
                        ahv_basis_jahr_bisher += abr.basis
            except Exception as e:
                # Falls Abrechnungen nicht geladen werden können, verwende 0.0 (erster Monat)
                import logging
                logging.getLogger("adea_payroll").warning(f"Abrechnungen konnten nicht geladen werden: {e}")
        
        # Gesamte Basis inkl. diesem Monat
        ahv_basis_gesamt = ahv_basis_jahr_bisher + ahv_nbu_ktg_basis
        
        # Freibetrag anwenden: Nur Betrag ÜBER Freibetrag ist beitragspflichtig
        ahv_basis_nach_freibetrag = max(Decimal("0.0"), ahv_basis_gesamt - AHV_FREIBETRAG_RENTNER)
        
        # AHV nur auf Betrag über Freibetrag
        if ahv_basis_jahr_bisher < AHV_FREIBETRAG_RENTNER:
            # Noch nicht über Freibetrag
            abrechnung.ahv_an = rappen(proz(ahv_basis_nach_freibetrag, AHV_AN))
        else:
            # Bereits über Freibetrag - normale Berechnung auf diesen Monat
            abrechnung.ahv_an = rappen(proz(ahv_nbu_ktg_basis, AHV_AN))
    else:
        # Normale Berechnung (kein Altersrentner ODER Verzicht auf Freibetrag)
        abrechnung.ahv_an = proz(ahv_nbu_ktg_basis, AHV_AN)

    # 4b) ALV - Arbeitnehmer (mit Jahresakkumulation und Cap)
    # Basis: Grundlohn + Bonus + Privatanteil (KEINE Familienzulagen)
    # ALV: 1.1% AN + 1.1% AG = 2.2% gesamt bis Cap (148'200 CHF/Jahr = 12'350 CHF/Monat)
    # WICHTIG: Seit 1. Januar 2023 sind auf Lohnanteile, die diesen Betrag übersteigen,
    #          KEINE ALV-Beiträge mehr zu entrichten
    # SONDERREGELUNG: Altersrentner sind von ALV-Beiträgen BEFREIT (keine ALV nach Referenzalter)
    
    if mitarbeiter.ist_altersrentner:
        # Altersrentner: KEINE ALV-Beiträge mehr
        abrechnung.alv1_an = Decimal("0.0")
        abrechnung.alv2_an = Decimal("0.0")
    else:
        # Jahresakkumulation erforderlich für korrekte Cap-Berechnung
        
        # Berechne ALV-Basis bisher im Jahr (Jahresakkumulation)
        alv_basis_jahr_bisher = Decimal("0.0")
        if data_manager:
            try:
                abrechnungen_jahr = data_manager.load_abrechnungen()
                for abr in abrechnungen_jahr:
                    if (abr.mitarbeiter_id == mitarbeiter.id and 
                        abr.jahr == jahr and 
                        abr.monat < monat and
                        abr.status.value in ["abgeschlossen", "ausgezahlt"]):  # Nur abgeschlossene Abrechnungen
                        alv_basis_jahr_bisher += abr.alv_basis
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Fehler beim Laden der Abrechnungen für ALV-Basis: {e}")
        
        # ALV-Basis für diesen Monat
        alv_basis_monat = alv_basis
        
        # Berechne maximale Jahres-Basis bis einschließlich diesem Monat
        # Vereinfachte Berechnung: Jahres-Cap (148'200 CHF)
        max_basis_jahr = ALV_CAP_JAHR
        
        # ALV-Basis für Berechnung: Nur bis Cap (seit 2023 keine Beiträge mehr über Cap)
        gesamt_basis = alv_basis_jahr_bisher + alv_basis_monat
        
        if gesamt_basis <= max_basis_jahr:
            # Noch nicht bei Cap - volle Monatsbasis
            alv_basis_fuer_berechnung = alv_basis_monat
        elif alv_basis_jahr_bisher < max_basis_jahr:
            # Überschreitet Cap in diesem Monat - nur Teil bis Cap
            alv_basis_fuer_berechnung = max_basis_jahr - alv_basis_jahr_bisher
        else:
            # Bereits über Cap - keine ALV-Beiträge mehr (seit 2023)
            alv_basis_fuer_berechnung = Decimal("0.0")
        
        # ALV-Beitrag: 1.1% AN (nur bis Cap, seit 2023 keine Beiträge mehr über Cap)
        abrechnung.alv1_an = rappen(proz(alv_basis_fuer_berechnung, ALV_AN))
        abrechnung.alv2_an = Decimal("0.0")  # Seit 2023: Keine ALV-Beiträge mehr über Cap

    # 4c) NBU - Arbeitnehmer (aus Firmendaten)
    # Basis: Grundlohn + Privatanteil + Familienzulagen
    # NBU ist nur pflichtig bei mindestens 8 Stunden pro Woche
    abrechnung.nbu_an = berechne_nbu_an(ahv_nbu_ktg_basis, firmendaten, lohnstamm)
    abrechnung.nbu_an = rappen(abrechnung.nbu_an)

    # 4d) KTG - Arbeitnehmer (aus Firmendaten, abhängig von Kategorie und Verteilung)
    # Basis: Grundlohn + Privatanteil + Familienzulagen
    ktg_satz = hole_ktg_satz_for_mitarbeiter(mitarbeiter, firmendaten)
    ktg_total = proz(ahv_nbu_ktg_basis, ktg_satz)
    ktg_an, ktg_ag = split_ktg_an_ag(ktg_total, firmendaten)
    abrechnung.ktg_an = rappen(ktg_an)

    # 4e) BVG - Arbeitnehmer (aus Lohnstamm)
    # BVG-Beiträge gelten normalerweise für das ganze Jahr (01.01. - 31.12.)
    # Ausnahmen nur bei Eintritt/Austritt im Jahr
    bvg_ag, bvg_an = berechne_bvg(lohnstamm, monat, jahr)
    abrechnung.bvg_an = rappen(bvg_an)

    # 4f) Quellensteuer (manuell eingegeben - Prozentsatz)
    # QST-Basis = ALV-Basis - AN-Sozialabzüge auf ALV-Basis
    # AN-Sozialabzüge auf ALV-Basis: AHV + ALV + NBU + KTG + BVG
    # (AHV/NBU/KTG werden auf ahv_nbu_ktg_basis berechnet, aber für QST verwenden wir ALV-Basis)
    ahv_auf_alv_basis = proz(alv_basis, AHV_AN)
    nbu_auf_alv_basis = berechne_nbu_an(alv_basis, firmendaten, lohnstamm)
    ktg_total_auf_alv_basis = proz(alv_basis, ktg_satz)
    ktg_an_auf_alv_basis, _ = split_ktg_an_ag(ktg_total_auf_alv_basis, firmendaten)
    
    sozialabzuege_auf_alv_basis = (
        ahv_auf_alv_basis +
        abrechnung.alv1_an +  # ALV (bereits auf ALV-Basis)
        nbu_auf_alv_basis +
        ktg_an_auf_alv_basis +
        abrechnung.bvg_an  # BVG (unabhängig von Basis)
    )
    abrechnung.qst_basis = alv_basis - sozialabzuege_auf_alv_basis
    abrechnung.qst = berechne_quellensteuer(alv_basis, sozialabzuege_auf_alv_basis, mitarbeiter)
    abrechnung.qst = rappen(abrechnung.qst)

    # ========================================================================
    # 5. SOZIALABZÜGE TOTAL + NETTO
    # ========================================================================
    abrechnung.sozialabzuege_total = (
        abrechnung.ahv_an +
        abrechnung.alv1_an +
        abrechnung.alv2_an +  # ALV2 (seit 2023: immer 0.0, keine Beiträge mehr über Cap)
        abrechnung.nbu_an +
        abrechnung.ktg_an +
        abrechnung.bvg_an +
        abrechnung.qst
    )

    # ========================================================================
    # 5a. SPESEN (AHV/ALV/NBU/BU/BVG/QST-frei, werden zum Netto addiert)
    # ========================================================================
    # Effektive Spesen: werden manuell pro Abrechnung eingegeben (initial 0.0)
    # Pauschalspesen: aus Lohnstamm und Arbeitstagen
    if lohnstamm.pauschalspesen_pro_tag and abrechnung.arbeitstage_pauschalspesen > 0:
        abrechnung.pauschalspesen_pro_tag = lohnstamm.pauschalspesen_pro_tag
        abrechnung.pauschalspesen_total = lohnstamm.pauschalspesen_pro_tag * Decimal(str(abrechnung.arbeitstage_pauschalspesen))
    else:
        abrechnung.pauschalspesen_pro_tag = Decimal("0.0")
        abrechnung.pauschalspesen_total = Decimal("0.0")
    
    # Spesen werden NICHT zur Basis hinzugezählt (AHV/NBU/KTG/ALV-Basis bleibt unverändert)
    # Spesen werden direkt zum Netto addiert (steuer- und sozialversicherungsfrei)

    # ========================================================================
    # 5b. NETTO-BERECHNUNG (mit Spesen)
    # ========================================================================
    # Netto = Basis - Sozialabzüge + Effektive Spesen + Pauschalspesen
    abrechnung.netto = (
        abrechnung.basis - 
        abrechnung.sozialabzuege_total + 
        abrechnung.effektive_spesen_betrag + 
        abrechnung.pauschalspesen_total
    )
    abrechnung.netto = rappen(abrechnung.netto)

    # ========================================================================
    # 6. ARBEITGEBER-KOSTEN (AG)
    # ========================================================================

    # 6a) AHV/IV/EO - Arbeitgeber (5.3%)
    # Basis: Grundlohn + Privatanteil + Familienzulagen
    # SONDERREGELUNG: Altersrentner haben Freibetrag von CHF 16'800/Jahr (seit AHV 21)
    
    if mitarbeiter.ist_altersrentner and not mitarbeiter.verzicht_ahv_freibetrag:
        # Gleiche Logik wie bei AN: AHV nur auf Betrag über Freibetrag
        ahv_basis_jahr_bisher = Decimal("0.0")
        if data_manager:
            try:
                abrechnungen_jahr = data_manager.load_abrechnungen()
                for abr in abrechnungen_jahr:
                    if (abr.mitarbeiter_id == mitarbeiter.id and 
                        abr.jahr == jahr and 
                        abr.monat < monat and
                        abr.status.value in ["abgeschlossen", "ausgezahlt"]):
                        ahv_basis_jahr_bisher += abr.basis
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Fehler beim Laden der Abrechnungen für AHV-Basis: {e}")
        
        ahv_basis_gesamt = ahv_basis_jahr_bisher + ahv_nbu_ktg_basis
        ahv_basis_nach_freibetrag = max(Decimal("0.0"), ahv_basis_gesamt - AHV_FREIBETRAG_RENTNER)
        
        if ahv_basis_jahr_bisher < AHV_FREIBETRAG_RENTNER:
            abrechnung.ahv_ag = rappen(proz(ahv_basis_nach_freibetrag, AHV_AG))
        else:
            abrechnung.ahv_ag = rappen(proz(ahv_nbu_ktg_basis, AHV_AG))
    else:
        # Normale Berechnung
        abrechnung.ahv_ag = proz(ahv_nbu_ktg_basis, AHV_AG)

    # 6b) ALV - Arbeitgeber (mit Jahresakkumulation und Cap)
    # Basis: Grundlohn + Bonus + Privatanteil (KEINE Familienzulagen)
    # SONDERREGELUNG: Altersrentner sind von ALV-Beiträgen BEFREIT (keine ALV nach Referenzalter)
    
    if mitarbeiter.ist_altersrentner:
        # Altersrentner: KEINE ALV-Beiträge mehr (auch AG)
        abrechnung.alv1_ag = Decimal("0.0")
        abrechnung.alv2_ag = Decimal("0.0")
    else:
        # Verwendet gleiche Logik wie AN (alv_basis_fuer_berechnung)
        # ALV: 1.1% AG (nur bis Cap, seit 2023 keine Beiträge mehr über Cap)
        abrechnung.alv1_ag = rappen(proz(alv_basis_fuer_berechnung, ALV_AG))
        abrechnung.alv2_ag = Decimal("0.0")  # Seit 2023: Keine ALV-Beiträge mehr über Cap

    # 6c) BU - Arbeitgeber (aus Firmendaten)
    # Basis: Grundlohn + Privatanteil + Familienzulagen (wie AHV/NBU/KTG)
    abrechnung.bu_ag = berechne_bu_ag(ahv_nbu_ktg_basis, firmendaten)
    abrechnung.bu_ag = rappen(abrechnung.bu_ag)

    # 6d) KTG - Arbeitgeber (bereits oben berechnet)
    abrechnung.ktg_ag = rappen(ktg_ag)

    # 6e) BVG - Arbeitgeber (aus Lohnstamm, bereits oben berechnet)
    abrechnung.bvg_ag = rappen(bvg_ag)

    # ========================================================================
    # 7. ARBEITGEBER-KOSTEN TOTAL
    # ========================================================================
    # Wenn manuelle AG-Kosten eingegeben wurden, diese verwenden
    # Ansonsten automatisch berechnen
    if abrechnung.ag_kosten_manuell is not None:
        abrechnung.ag_kosten_total = rappen(abrechnung.ag_kosten_manuell)
    else:
        abrechnung.ag_kosten_total = (
            abrechnung.ahv_ag +
            abrechnung.alv1_ag +
            abrechnung.alv2_ag +  # ALV2 (seit 2023: immer 0.0, keine Beiträge mehr über Cap)
            abrechnung.bu_ag +
            abrechnung.ktg_ag +
            abrechnung.bvg_ag
        )

    return abrechnung
