"""
Plausibilitätsprüfung für Lohnabrechnungen.
Extrahiert aus lohnlauf.py (AdeaLohn).
"""

from decimal import Decimal
from datetime import date, timedelta

from .models import (
    Mitarbeitende, Lohnstamm, Lohnabrechnung, Firmendaten,
    Lohnart,
)
from .constants import AHV_FREIBETRAG_RENTNER
from .social_insurance import (
    ist_nbu_pflichtig,
    hole_ktg_satz_for_mitarbeiter,
)
from .thirteenth_salary import berechne_dreizehnter


def pruefe_plausibilitaet(
    mitarbeiter: Mitarbeitende,
    lohnstamm: Lohnstamm,
    abrechnung: Lohnabrechnung,
    firmendaten: Firmendaten,
    monat: int,
    jahr: int
) -> list:
    """
    Prüft eine Lohnabrechnung auf Plausibilität und mögliche Probleme.

    Rückgabe: Liste von Dictionaries mit:
    - "typ": "ok" | "warn" | "error"
    - "msg": Beschreibung der Prüfung/des Problems

    Args:
        mitarbeiter: Mitarbeiter-Objekt
        lohnstamm: Lohnstamm des Mitarbeiters
        abrechnung: Berechnete Lohnabrechnung
        firmendaten: Firmendaten mit Versicherungssätzen
        monat: Abrechnungsmonat
        jahr: Abrechnungsjahr

    Returns:
        Liste von Prüfungsergebnissen
    """
    ergebnisse = []

    # ========================================================================
    # FEHLER (❌) - Abrechnung kann nicht durchgeführt werden
    # ========================================================================

    # Fehler: QST-pflichtig aber QST-Satz fehlt
    if mitarbeiter.qst_daten.qst_pflichtig and not mitarbeiter.qst_daten.qst_prozentsatz:
        ergebnisse.append({
            "typ": "error",
            "msg": "QST-pflichtig, aber QST-Satz fehlt in den Mitarbeiterdaten"
        })

    # Fehler: Lohnstamm ungültig (gültig_bis liegt vor Berechnungsmonat)
    stichtag = date(jahr, monat, 1)
    if lohnstamm.gueltig_bis and lohnstamm.gueltig_bis < stichtag:
        ergebnisse.append({
            "typ": "error",
            "msg": f"Lohnstamm ist nicht gültig für {monat}/{jahr} (gültig bis {lohnstamm.gueltig_bis})"
        })

    # Fehler: Netto < 0 (sollte nicht vorkommen, aber sicherheitshalber prüfen)
    if abrechnung.netto < 0:
        ergebnisse.append({
            "typ": "error",
            "msg": f"Nettolohn ist negativ: CHF {abrechnung.netto}"
        })

    # Fehler: Stundenlohn ohne Stunden (für v2 vorbereitet)
    if lohnstamm.lohnart == Lohnart.STUNDENLOHN and abrechnung.grundlohn == 0:
        ergebnisse.append({
            "typ": "error",
            "msg": "Stundenlohn gewählt, aber keine Stunden erfasst"
        })

    # ========================================================================
    # WARNUNGEN (⚠️) - Auffälligkeiten, die geprüft werden sollten
    # ========================================================================

    # Warnung: Grundlohn = 0 bei Monatslohn
    if lohnstamm.lohnart == Lohnart.MONATSLOHN and abrechnung.grundlohn == 0:
        ergebnisse.append({
            "typ": "warn",
            "msg": "Grundlohn ist 0 CHF (Monatslohn)"
        })

    # ========================================================================
    # PRIVATANTEIL AUTO - PRÜFUNGEN
    # ========================================================================
    
    # Warnung: Privatanteil aktiv aber Betrag = 0
    if lohnstamm.privatanteil_auto_aktiv and abrechnung.privatanteil_auto == 0:
        if abrechnung.privatanteil_auto_brutto > 0:
            # Privatanteil Brutto vorhanden, aber Netto = 0 (vollständig vom MA bezahlt)
            ergebnisse.append({
                "typ": "ok",
                "msg": f"Privatanteil Auto: CHF {abrechnung.privatanteil_auto_brutto}/Monat wird vollständig vom Mitarbeiter bezahlt - "
                       f"Hinweis im Lohnausweis erforderlich (Ziffer 15)"
            })
        else:
            ergebnisse.append({
                "typ": "warn",
                "msg": "Privatanteil Auto aktiviert, aber kein Fahrzeugpreis hinterlegt"
            })
    
    # Warnung: Mitarbeiterbeitrag > Privatanteil Brutto (Überbezahlung)
    if lohnstamm.privatanteil_auto_aktiv and lohnstamm.auto_preis:
        privatanteil_brutto = lohnstamm.auto_preis * Decimal("0.009")
        mitarbeiter_beitrag = lohnstamm.auto_mitarbeiter_beitrag_monat or Decimal("0.0")
        
        if mitarbeiter_beitrag > privatanteil_brutto:
            ergebnisse.append({
                "typ": "warn",
                "msg": f"Mitarbeiterbeitrag (CHF {mitarbeiter_beitrag}/Monat) > Privatanteil Brutto (CHF {privatanteil_brutto}/Monat) - "
                       f"Überbezahlung! Mietverhältnis prüfen oder Beitrag korrigieren."
            })
    
    # Info: Privatanteil mit Mitarbeiterbeitrag
    if (lohnstamm.privatanteil_auto_aktiv and 
        abrechnung.privatanteil_auto_brutto > 0 and 
        abrechnung.privatanteil_auto_mitarbeiter_beitrag > 0 and
        abrechnung.privatanteil_auto > 0):
        ergebnisse.append({
            "typ": "ok",
            "msg": f"Privatanteil Auto: Brutto CHF {abrechnung.privatanteil_auto_brutto}/Monat - "
                   f"MA-Beitrag CHF {abrechnung.privatanteil_auto_mitarbeiter_beitrag}/Monat = "
                   f"Netto CHF {abrechnung.privatanteil_auto}/Monat"
        })

    # ========================================================================
    # ALTERSRENTNER-PRÜFUNGEN
    # ========================================================================
    
    # Warnung: ALV für Altersrentner (sollte 0 sein)
    if mitarbeiter.ist_altersrentner:
        if abrechnung.alv1_an > 0 or abrechnung.alv1_ag > 0 or abrechnung.alv2_an > 0 or abrechnung.alv2_ag > 0:
            ergebnisse.append({
                "typ": "error",
                "msg": "Altersrentner sind von ALV-Beiträgen befreit - ALV-Beiträge sollten 0 sein"
            })
        
        # Warnung: BVG für Altersrentner (normalerweise nicht mehr pflichtig)
        if abrechnung.bvg_an > 0 or abrechnung.bvg_ag > 0:
            ergebnisse.append({
                "typ": "warn",
                "msg": "Altersrentner mit BVG-Beiträgen (freiwillige Weiterversicherung?)"
            })
        
        # Info: AHV-Freibetrag angewendet
        if not mitarbeiter.verzicht_ahv_freibetrag and abrechnung.ahv_an == 0 and abrechnung.ahv_ag == 0:
            ergebnisse.append({
                "typ": "ok",
                "msg": f"AHV-Freibetrag (CHF {AHV_FREIBETRAG_RENTNER}/Jahr) angewendet - keine AHV-Beiträge diesen Monat"
            })
        elif mitarbeiter.verzicht_ahv_freibetrag:
            ergebnisse.append({
                "typ": "ok",
                "msg": "Altersrentner mit Verzicht auf AHV-Freibetrag - volle AHV-Beiträge"
            })
    
    # ========================================================================
    # NBU-PRÜFUNGEN
    # ========================================================================
    
    # Warnung: NBU = 0 obwohl Firma einen Satz definiert hat (nur wenn NBU-pflichtig)
    STANDARD_WOCHENSTUNDEN = Decimal("42.0")
    MIN_NBU_STUNDEN = Decimal("8.0")
    wochenstunden = STANDARD_WOCHENSTUNDEN * (lohnstamm.beschaeftigungsgrad / Decimal("100.0"))
    
    if ist_nbu_pflichtig(lohnstamm) and firmendaten.nbu_satz_an > 0 and abrechnung.nbu_an == 0:
        ergebnisse.append({
            "typ": "warn",
            "msg": f"Mitarbeiter arbeitet {wochenstunden:.1f} Stunden/Woche (≥ 8 Stunden). "
                   f"NBU-Satz in Firmendaten ({firmendaten.nbu_satz_an}%), aber NBU-Beitrag ist 0 CHF"
        })
    
    # Warnung: NBU sollte nicht berechnet werden (weniger als 8 Stunden/Woche)
    if wochenstunden < MIN_NBU_STUNDEN and abrechnung.nbu_an > 0:
        ergebnisse.append({
            "typ": "warn",
            "msg": f"Mitarbeiter arbeitet {wochenstunden:.1f} Stunden/Woche (< 8 Stunden). "
                   "NBU ist NICHT pflichtig. Mitarbeiter muss sich selbst versichern. "
                   "Bitte NBU-Beitrag prüfen (sollte 0 CHF sein)."
        })
    
    # ========================================================================
    # VALIDIERUNG: SPESEN
    # ========================================================================
    # Validierung: Effektive Spesen >= 0
    if abrechnung.effektive_spesen_betrag < 0:
        ergebnisse.append({
            "typ": "error",
            "msg": f"Effektive Spesen dürfen nicht negativ sein (aktuell: CHF {abrechnung.effektive_spesen_betrag:.2f})"
        })
    
    # Validierung: Arbeitstage Pauschalspesen >= 0
    if abrechnung.arbeitstage_pauschalspesen < 0:
        ergebnisse.append({
            "typ": "error",
            "msg": f"Arbeitstage für Pauschalspesen dürfen nicht negativ sein (aktuell: {abrechnung.arbeitstage_pauschalspesen})"
        })
    
    # Validierung: Wenn pauschalspesen_pro_tag > 0, dann müssen Arbeitstage > 0 sein
    if lohnstamm.pauschalspesen_pro_tag and lohnstamm.pauschalspesen_pro_tag > 0:
        if abrechnung.arbeitstage_pauschalspesen == 0:
            ergebnisse.append({
                "typ": "warn",
                "msg": f"Pauschalspesen pro Tag ist {lohnstamm.pauschalspesen_pro_tag} CHF, aber Arbeitstage ist 0. "
                       "Bitte Anzahl Arbeitstage für Pauschalspesen eingeben."
            })
        elif abrechnung.pauschalspesen_total == 0:
            ergebnisse.append({
                "typ": "warn",
                "msg": f"Pauschalspesen pro Tag ist {lohnstamm.pauschalspesen_pro_tag} CHF und {abrechnung.arbeitstage_pauschalspesen} Tage, "
                       f"aber Pauschalspesen Total ist 0 CHF. Bitte prüfen."
            })
    
    # Info: Spesen werden korrekt zum Netto addiert (steuer- und sozialversicherungsfrei)
    if abrechnung.effektive_spesen_betrag > 0 or abrechnung.pauschalspesen_total > 0:
        ergebnisse.append({
            "typ": "ok",
            "msg": f"Spesen korrekt berücksichtigt: Effektive Spesen CHF {abrechnung.effektive_spesen_betrag:.2f}, "
                   f"Pauschalspesen CHF {abrechnung.pauschalspesen_total:.2f} (steuer- und sozialversicherungsfrei)"
        })

    # Warnung: BU = 0 obwohl Firma einen Satz definiert hat
    if firmendaten.bu_satz_ag > 0 and abrechnung.bu_ag == 0:
        ergebnisse.append({
            "typ": "warn",
            "msg": f"BU-Satz in Firmendaten ({firmendaten.bu_satz_ag}%), aber BU-Beitrag ist 0 CHF"
        })

    # Warnung: KTG = 0 obwohl Firma Sätze definiert hat
    ktg_satz = hole_ktg_satz_for_mitarbeiter(mitarbeiter, firmendaten)
    if ktg_satz > 0 and abrechnung.ktg_an == 0 and abrechnung.ktg_ag == 0:
        ergebnisse.append({
            "typ": "warn",
            "msg": f"KTG-Satz definiert ({ktg_satz}%), aber KTG-Beitrag ist 0 CHF"
        })

    # Warnung: BVG-pflichtig aber BVG-Beitrag = 0
    if lohnstamm.bvg_pflichtig and abrechnung.bvg_an == 0 and abrechnung.bvg_ag == 0:
        ergebnisse.append({
            "typ": "warn",
            "msg": "Mitarbeiter ist BVG-pflichtig, aber BVG-Beiträge sind 0 CHF"
        })
    
    # Warnung: Nicht mehr BVG-pflichtig aber BVG-Beiträge vorhanden
    if not lohnstamm.bvg_pflichtig and (abrechnung.bvg_an > 0 or abrechnung.bvg_ag > 0):
        ergebnisse.append({
            "typ": "warn",
            "msg": "Mitarbeiter ist NICHT mehr BVG-pflichtig, aber BVG-Beiträge sind vorhanden. Bitte prüfen und ggf. entfernen."
        })
    
    # ========================================================================
    # WARNHINWEISE: FAMILIENZULAGEN
    # ========================================================================
    
    # Warnung: Familienzulage existiert, aber im Monat kein Betrag gezogen wurde
    abrechnungsmonat_start = date(jahr, monat, 1)
    if monat == 12:
        abrechnungsmonat_ende = date(jahr + 1, 1, 1)
    else:
        abrechnungsmonat_ende = date(jahr, monat + 1, 1)
    abrechnungsmonat_ende = abrechnungsmonat_ende - timedelta(days=1)
    
    for zulage in mitarbeiter.familienzulagen:
        zulage_ende = zulage.gueltig_bis if zulage.gueltig_bis else date.max
        # Prüfe ob Zulage im Abrechnungsmonat gültig sein sollte
        if zulage.gueltig_ab <= abrechnungsmonat_ende and zulage_ende >= abrechnungsmonat_start:
            # Zulage sollte aktiv sein, prüfe ob sie in der Berechnung enthalten ist
            if abrechnung.familienzulagen == 0:
                ergebnisse.append({
                    "typ": "warn",
                    "msg": f"Familienzulage {zulage.typ.value} (CHF {zulage.betrag}) sollte im Monat {monat}/{jahr} aktiv sein, aber kein Betrag in Berechnung"
                })
    
    # Warnung: Zwei Zulagen überlappen sich im Zeitraum
    for i, zulage1 in enumerate(mitarbeiter.familienzulagen):
        for j, zulage2 in enumerate(mitarbeiter.familienzulagen):
            if i >= j:
                continue
            zulage1_ende = zulage1.gueltig_bis if zulage1.gueltig_bis else date.max
            zulage2_ende = zulage2.gueltig_bis if zulage2.gueltig_bis else date.max
            # Prüfe ob sich die Zeiträume überlappen
            if (zulage1.gueltig_ab <= zulage2_ende and zulage2.gueltig_ab <= zulage1_ende):
                ergebnisse.append({
                    "typ": "warn",
                    "msg": f"Familienzulagen überlappen sich: {zulage1.typ.value} ({zulage1.gueltig_ab} - {zulage1.gueltig_bis or 'offen'}) und {zulage2.typ.value} ({zulage2.gueltig_ab} - {zulage2.gueltig_bis or 'offen'})"
                })
    
    # Warnung: Beschäftigungsgrad != 100% (Hinweis)
    if lohnstamm.beschaeftigungsgrad != Decimal("100.0"):
        ergebnisse.append({
            "typ": "ok",
            "msg": f"Beschäftigungsgrad: {lohnstamm.beschaeftigungsgrad}% (Lohn wurde entsprechend angepasst)"
        })
    
    # Warnung: 13. Monatslohn-Modell definiert aber nicht in diesem Monat fällig
    if lohnstamm.dreizehnter_modell.value != "Kein 13. Monatslohn":
        dreizehnter_betrag = berechne_dreizehnter(lohnstamm, monat)
        if dreizehnter_betrag == 0:
            ergebnisse.append({
                "typ": "ok",
                "msg": f"13. Monatslohn-Modell: {lohnstamm.dreizehnter_modell.value} (nicht fällig in Monat {monat})"
            })
    
    # Warnung: Geburtsdatum fehlt (für BVG-Pflicht-Prüfung nötig)
    if not mitarbeiter.geburtsdatum:
        ergebnisse.append({
            "typ": "warn",
            "msg": "Geburtsdatum fehlt - BVG-Pflicht kann nicht automatisch geprüft werden"
        })

    # Info: Anteilige Berechnung bei Eintritt/Austritt
    if abrechnung.anteiliger_lohn:
        abrechnungsmonat_start = date(jahr, monat, 1)
        if monat == 12:
            abrechnungsmonat_ende = date(jahr + 1, 1, 1) - timedelta(days=1)
        else:
            abrechnungsmonat_ende = date(jahr, monat + 1, 1) - timedelta(days=1)
        
        eintritt_im_monat = False
        if mitarbeiter.eintrittsdatum and abrechnungsmonat_start <= mitarbeiter.eintrittsdatum <= abrechnungsmonat_ende:
            eintritt_im_monat = True
        
        austritt_im_monat = False
        if mitarbeiter.austrittsdatum and abrechnungsmonat_start <= mitarbeiter.austrittsdatum <= abrechnungsmonat_ende:
            austritt_im_monat = True
        
        ergebnisse.append({
            "typ": "ok",
            "msg": f"{'Eintritt' if eintritt_im_monat else 'Austritt'} im Monat ({mitarbeiter.eintrittsdatum if eintritt_im_monat else mitarbeiter.austrittsdatum}) - Lohn wurde anteilig berechnet (gemäss Arbeitsrecht)"
        })

    # ========================================================================
    # OK (✅) - Wenn keine Fehler oder Warnungen
    # ========================================================================
    if not ergebnisse:
        ergebnisse.append({
            "typ": "ok",
            "msg": "Keine Auffälligkeiten"
        })

    return ergebnisse
