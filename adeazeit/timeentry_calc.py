"""
Kleine, zentrale Berechnungs-Helper für Zeiteinträge (TimeEntry).

Ziel: DRY ohne Business-Logik zu ändern.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional


DECIMAL_2 = Decimal("0.01")


def calculate_timeentry_rate(*, service_type, employee) -> Decimal:
    """
    Berechnet den Stundensatz für einen TimeEntry.

    Bestehendes Verhalten (1:1):
    - base_rate = service_type.standard_rate oder 0.00
    - wenn employee.stundensatz > 0: base_rate * stundensatz, quantized auf 0.01
    - sonst: base_rate (ohne zusätzliche Quantisierung)
    """
    base_rate = getattr(service_type, "standard_rate", None) or Decimal("0.00")
    coeff = getattr(employee, "stundensatz", None) if employee else None
    if coeff and coeff > 0:
        return (base_rate * coeff).quantize(DECIMAL_2)
    return base_rate


def calculate_timeentry_amount(*, rate: Optional[Decimal], dauer: Optional[Decimal]) -> Decimal:
    """
    Berechnet den Betrag (CHF) eines TimeEntry.

    Bestehendes Verhalten (1:1):
    - wenn rate und dauer gesetzt: rate * dauer, quantized auf 0.01
    - sonst: 0.00
    """
    if rate and dauer:
        return (rate * dauer).quantize(DECIMAL_2)
    return Decimal("0.00")

