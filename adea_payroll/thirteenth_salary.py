"""
Berechnung des 13. Monatslohns.
Extrahiert aus lohn.py (AdeaLohn).
"""

from decimal import Decimal

from .models import Lohnstamm, Dreizehnter
from .gross import berechne_effektiven_monatslohn


def berechne_dreizehnter(lohnstamm: Lohnstamm, monat: int) -> Decimal:
    """
    Berechnet den 13. Monatslohn für einen bestimmten Monat.
    
    Modelle:
    - NOVEMBER_100: 100% im November
    - DEZEMBER_100: 100% im Dezember
    - JUNI_NOVEMBER_50_50: 50% im Juni, 50% im November
    - KEIN_13: Kein 13. Monatslohn
    
    Args:
        lohnstamm: Lohnstamm mit 13. Monatslohn-Modell
        monat: Abrechnungsmonat (1-12)
    
    Returns:
        13. Monatslohn-Betrag für diesen Monat (0.0 wenn nicht fällig)
    """
    if lohnstamm.lohnart.value != "Monatslohn":
        return Decimal("0.0")
    
    if lohnstamm.dreizehnter_modell.value == "Kein 13. Monatslohn":
        return Decimal("0.0")
    
    if not lohnstamm.monatslohn:
        return Decimal("0.0")
    
    # Verwende effektiven Monatslohn (bereits korrekt berechnet)
    monatslohn = berechne_effektiven_monatslohn(lohnstamm)
    
    modell = lohnstamm.dreizehnter_modell.value
    
    if modell == "100% im November" and monat == 11:
        return monatslohn
    elif modell == "100% im Dezember" and monat == 12:
        return monatslohn
    elif modell == "50% Juni / 50% November":
        if monat == 6:
            return monatslohn * Decimal("0.5")
        elif monat == 11:
            return monatslohn * Decimal("0.5")
    
    return Decimal("0.0")
