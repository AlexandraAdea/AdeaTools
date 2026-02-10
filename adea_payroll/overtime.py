"""
Überstunden-Modul für adea_payroll.
Berechnet Überstunden-Entschädigung gemäß Schweizer Arbeitsrecht.
Extrahiert aus ueberstunden.py (AdeaLohn).

Gesetzliche Grundlage: Art. 321c OR
"""

from decimal import Decimal
from typing import Tuple

from .models import Lohnstamm, Lohnart
from .gross import berechne_effektiven_monatslohn


# ============================================================================
# KONSTANTEN
# ============================================================================

# Durchschnittliche Monatsstunden (Schweizer Standard)
MONATSSTUNDEN = Decimal("174.0")  # 42 Stunden/Woche × 52 Wochen / 12 Monate ≈ 182h
# Alternativ: 21.74 Arbeitstage × 8h = 173.92h ≈ 174h

# Standard-Zuschläge (gemäß OR)
ZUSCHLAG_NORMAL = Decimal("25.0")  # 25% für normale Überstunden
ZUSCHLAG_NACHT = Decimal("50.0")  # 50% für Nacht-/Sonntags-/Feiertagsarbeit


# ============================================================================
# ÜBERSTUNDEN-BERECHNUNG
# ============================================================================

def berechne_basis_stundenlohn(lohnstamm: Lohnstamm) -> Decimal:
    """
    Berechnet den Basis-Stundenlohn für Überstunden-Berechnung.
    
    Bei Monatslohn: Monatslohn / 174 Stunden
    Bei Stundenlohn: Direkter Stundenlohn
    
    Args:
        lohnstamm: Lohnstamm mit Lohnart und Lohn
        
    Returns:
        Basis-Stundenlohn (ohne Zuschläge)
    """
    if lohnstamm.lohnart == Lohnart.MONATSLOHN and lohnstamm.monatslohn:
        # Effektiven Monatslohn berechnen (mit Beschäftigungsgrad)
        effektiver_monatslohn = berechne_effektiven_monatslohn(lohnstamm)
        
        # Basis-Stundenlohn = Monatslohn / Monatsstunden
        basis_stundenlohn = effektiver_monatslohn / MONATSSTUNDEN
        return basis_stundenlohn
    
    elif lohnstamm.lohnart == Lohnart.STUNDENLOHN and lohnstamm.stundenlohn:
        # Bei Stundenlohn: Direkter Stundenlohn ist Basis
        return lohnstamm.stundenlohn
    
    return Decimal("0.0")


def berechne_ueberstunden(
    lohnstamm: Lohnstamm,
    ueberstunden_normal: Decimal,
    ueberstunden_nacht: Decimal,
    zuschlag_normal: Decimal = None,
    zuschlag_nacht: Decimal = None
) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
    """
    Berechnet Überstunden-Entschädigung mit Zuschlägen.
    
    Berechnung:
    1. Basis-Stundenlohn ermitteln (aus Monatslohn oder Stundenlohn)
    2. Normale Überstunden: Basis × (1 + Zuschlag%) × Anzahl Stunden
    3. Nacht-Überstunden: Basis × (1 + Zuschlag%) × Anzahl Stunden
    4. Total: Summe normal + Nacht
    
    Args:
        lohnstamm: Lohnstamm mit Lohnart und Lohn
        ueberstunden_normal: Anzahl normale Überstunden
        ueberstunden_nacht: Anzahl Nacht-/Sonntags-/Feiertagsüberstunden
        zuschlag_normal: Zuschlag % für normale Überstunden (Standard: aus Lohnstamm)
        zuschlag_nacht: Zuschlag % für Nacht-Überstunden (Standard: aus Lohnstamm)
        
    Returns:
        Tuple (Basis-Stundenlohn, Normal-Betrag, Nacht-Betrag, Total-Betrag)
    """
    # Basis-Stundenlohn ermitteln
    basis_stundenlohn = berechne_basis_stundenlohn(lohnstamm)
    
    if basis_stundenlohn == 0:
        return Decimal("0.0"), Decimal("0.0"), Decimal("0.0"), Decimal("0.0")
    
    # Zuschläge (Standard aus Lohnstamm, falls nicht überschrieben)
    if zuschlag_normal is None:
        zuschlag_normal = lohnstamm.ueberstunden_zuschlag_normal
    
    if zuschlag_nacht is None:
        zuschlag_nacht = lohnstamm.ueberstunden_zuschlag_nacht
    
    # Normale Überstunden berechnen
    if ueberstunden_normal > 0:
        # Ansatz = Basis × (1 + Zuschlag%)
        ansatz_normal = basis_stundenlohn * (Decimal("1.0") + zuschlag_normal / Decimal("100.0"))
        ueberstunden_normal_betrag = ueberstunden_normal * ansatz_normal
    else:
        ueberstunden_normal_betrag = Decimal("0.0")
    
    # Nacht-/Sonntags-/Feiertagsüberstunden berechnen
    if ueberstunden_nacht > 0:
        # Ansatz = Basis × (1 + Zuschlag%)
        ansatz_nacht = basis_stundenlohn * (Decimal("1.0") + zuschlag_nacht / Decimal("100.0"))
        ueberstunden_nacht_betrag = ueberstunden_nacht * ansatz_nacht
    else:
        ueberstunden_nacht_betrag = Decimal("0.0")
    
    # Total Überstunden-Entschädigung
    ueberstunden_betrag_total = ueberstunden_normal_betrag + ueberstunden_nacht_betrag
    
    return basis_stundenlohn, ueberstunden_normal_betrag, ueberstunden_nacht_betrag, ueberstunden_betrag_total
