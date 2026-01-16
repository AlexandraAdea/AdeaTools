"""
Geld-/Rundungs-Helfer für AdeaTools.

Bewusst klein gehalten: nur wiederverwendbare, deterministische Rundungsfunktionen.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


FIVE_RAPPEN = Decimal("0.05")


def round_to_5_rappen(amount: Decimal) -> Decimal:
    """
    Rundet einen Betrag auf 0.05 CHF (5 Rappen) mit ROUND_HALF_UP.

    Entspricht exakt dem bisherigen Pattern:
    (amount / 0.05).quantize(1, ROUND_HALF_UP) * 0.05
    """
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return (amount / FIVE_RAPPEN).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * FIVE_RAPPEN

