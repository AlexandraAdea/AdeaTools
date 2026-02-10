"""
Konstanten für Schweizer Lohnberechnungen.
Zusammengeführt aus lohnlauf.py und lohn.py (AdeaLohn).
"""

from decimal import Decimal


# ============================================================================
# AHV/IV/EO (2025)
# ============================================================================

AHV_AN = Decimal("5.3")  # Arbeitnehmer-Beitrag in %
AHV_AG = Decimal("5.3")  # Arbeitgeber-Beitrag in %
AHV_FREIBETRAG_RENTNER = Decimal("16800.0")  # Freibetrag für erwerbstätige Altersrentner (pro Jahr)


# ============================================================================
# ALV – Arbeitslosenversicherung (2025)
# ============================================================================
# Seit 1. Januar 2023: KEINE ALV-Beiträge mehr auf Lohnanteile über dem Cap
# Gesamtsatz: 2.2% (1.1% AN + 1.1% AG) bis Cap

ALV_AN = Decimal("1.1")  # ALV-Beitrag AN (1.1% bis Cap)
ALV_AG = Decimal("1.1")  # ALV-Beitrag AG (1.1% bis Cap)
ALV_CAP_JAHR = Decimal("148200.0")  # ALV-Cap pro Jahr (2025)
ALV_CAP_MONAT = Decimal("12350.0")  # ALV-Cap pro Monat (148200 / 12)


# ============================================================================
# BVG – Berufliche Vorsorge (2025) – NUR FÜR WARNHINWEISE
# ============================================================================

BVG_MINDESTLOHN_JAHR = Decimal("22680.0")  # CHF pro Jahr (2025)
BVG_MINDESTLOHN_MONAT = Decimal("1890.0")  # CHF pro Monat (22680 / 12)
BVG_MINDESTALTER = 17  # Jahre
KOORDINATIONSABZUG_JAHR = Decimal("26460.0")  # CHF pro Jahr (2025)
KOORDINATIONSABZUG_MONAT = Decimal("2205.0")  # CHF pro Monat (26460 / 12)
BVG_MAX_KOORDINIERTER_LOHN_JAHR = Decimal("64260.0")  # CHF pro Jahr (2025)
