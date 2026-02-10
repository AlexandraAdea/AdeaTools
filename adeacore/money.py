"""
Geld-/Rundungs-Helfer für AdeaTools.

Delegiert an adea_payroll.rounding.rappen() — Single Source of Truth.
"""

from __future__ import annotations

from decimal import Decimal

from adea_payroll.rounding import rappen  # noqa: E402


FIVE_RAPPEN = Decimal("0.05")  # Beibehalten für Abwärtskompatibilität


def round_to_5_rappen(amount: Decimal) -> Decimal:
    """
    Rundet einen Betrag auf 0.05 CHF (5 Rappen) mit ROUND_HALF_UP.

    Delegiert an adea_payroll.rounding.rappen() für konsistente Rundung.
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return rappen(amount)


