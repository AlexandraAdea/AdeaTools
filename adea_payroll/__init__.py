"""
adea_payroll — Чистый Python-пакет для швейцарских зарплатных расчётов.

Единый источник истины для бизнес-логики расчёта зарплат.
Не зависит от Django, CustomTkinter или любого другого фреймворка.

Используется как из AdeaLohn (десктоп), так и из AdeaCore (Django).
"""

# ============================================================================
# Public API
# ============================================================================

# Hauptfunktionen
from .calculator import berechne_lohnlauf
from .validation import pruefe_plausibilitaet

# Rundung
from .rounding import rappen, proz

# Bruttolohn
from .gross import (
    berechne_effektiven_monatslohn,
    berechne_anteiligen_lohn,
    berechne_brutto,
)

# Sozialversicherungen
from .social_insurance import (
    berechne_bvg,
    berechne_privatanteil_auto,
    berechne_quellensteuer,
    berechne_bu_ag,
    ist_nbu_pflichtig,
    berechne_nbu_an,
    hole_ktg_satz_for_mitarbeiter,
    split_ktg_an_ag,
    ist_bvg_pflichtig_fuer_warnung,
)

# 13. Monatslohn
from .thirteenth_salary import berechne_dreizehnter

# Überstunden
from .overtime import berechne_basis_stundenlohn, berechne_ueberstunden

# Modelle (re-export)
from .models import (
    Lohnart, LohnBasisTyp, Dreizehnter, Ferienwochen,
    Zivilstand, Konfession, QSTTarif, Branche, GAVStatus,
    LohnlaufStatus, KTGKategorie, KTGVerteilung, FamilienzulageTyp,
    Firmendaten, QSTDaten, Mitarbeitende, Familienzulage,
    Lohnstamm, Sozialabzuege, Lohnkomponenten, Lohnlauf, Lohnabrechnung,
    PDFFirmenkopf, PDFMitarbeiterBlock, PDFLohnzeile, PDFAbzugszeile,
    LohnabrechnungPDF,
    ermittle_gav_status, get_aktueller_lohnstamm,
)

# Konstanten
from .constants import (
    AHV_AN, AHV_AG, AHV_FREIBETRAG_RENTNER,
    ALV_AN, ALV_AG, ALV_CAP_JAHR, ALV_CAP_MONAT,
    BVG_MINDESTLOHN_JAHR, BVG_MINDESTLOHN_MONAT, BVG_MINDESTALTER,
    KOORDINATIONSABZUG_JAHR, KOORDINATIONSABZUG_MONAT,
    BVG_MAX_KOORDINIERTER_LOHN_JAHR,
)

__version__ = "1.0.0"
__all__ = [
    # Hauptfunktionen
    "berechne_lohnlauf",
    "pruefe_plausibilitaet",
    # Rundung
    "rappen",
    "proz",
    # Bruttolohn
    "berechne_effektiven_monatslohn",
    "berechne_anteiligen_lohn",
    "berechne_brutto",
    # Sozialversicherungen
    "berechne_bvg",
    "berechne_privatanteil_auto",
    "berechne_quellensteuer",
    "berechne_bu_ag",
    "ist_nbu_pflichtig",
    "berechne_nbu_an",
    "hole_ktg_satz_for_mitarbeiter",
    "split_ktg_an_ag",
    "ist_bvg_pflichtig_fuer_warnung",
    # 13. Monatslohn
    "berechne_dreizehnter",
    # Überstunden
    "berechne_basis_stundenlohn",
    "berechne_ueberstunden",
]
