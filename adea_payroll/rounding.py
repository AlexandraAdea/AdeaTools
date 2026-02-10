"""
Rundungsfunktionen für Schweizer Lohnberechnungen.
Extrahiert aus lohnlauf.py (AdeaLohn).
"""

from decimal import Decimal, ROUND_HALF_UP


def rappen(betrag: Decimal) -> Decimal:
    """
    Rundet einen Betrag auf 5 Rappen (0.05 CHF) gemäss Schweizer Standard.

    Verwendet ROUND_HALF_UP (kaufmännisches Runden):
    - 10.02  → 10.00
    - 10.03  → 10.05
    - 10.024 → 10.00
    - 10.025 → 10.05
    - 10.074 → 10.05
    - 10.075 → 10.10

    Args:
        betrag: Zu rundender Betrag

    Returns:
        Auf 0.05 CHF gerundeter Betrag
    """
    return (betrag / Decimal("0.05")).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * Decimal("0.05")


def proz(betrag: Decimal, prozentsatz: Decimal) -> Decimal:
    """
    Berechnet Prozentsatz von einem Betrag und rundet auf 5 Rappen.

    Args:
        betrag: Ausgangsbetrag
        prozentsatz: Prozentsatz (z.B. 5.3 für 5.3%)

    Returns:
        Berechneter und gerundeter Betrag
    """
    return rappen(betrag * prozentsatz / Decimal("100"))
