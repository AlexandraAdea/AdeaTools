"""
Zentrale Berechnungsfunktion für Lohnabrechnungen.
Single Source of Truth für UI und Print.
"""

from decimal import Decimal
from adeacore.models import PayrollRecord
from adeacore.money import round_to_5_rappen


def berechne_lohnabrechnung(record: PayrollRecord) -> dict:
    """
    Zentrale Funktion für Lohnabrechnungsberechnung.
    Single Source of Truth für UI und Print.
    
    Formeln:
    - nettolohn = bruttolohn - sozialabzuege_total - qst_abzug
    - auszahlung = nettolohn - privatanteile_total + zulagen_total
    
    Returns:
        {
            'bruttolohn': Decimal,
            'sozialabzuege_total': Decimal,
            'qst_abzug': Decimal,
            'nettolohn': Decimal,
            'privatanteile_total': Decimal,
            'zulagen_total': Decimal,
            'auszahlung': Decimal,
            'rundung': Decimal,
            'aufschluesselung': {
                'ahv': Decimal,
                'alv': Decimal,
                'nbu': Decimal,
                'bvg': Decimal,
                'ktg': Decimal,
            }
        }
    """
    # Bruttolohn
    bruttolohn = record.bruttolohn or Decimal("0")
    
    # Sozialabzüge
    sozialabzuege_total = (
        (record.ahv_employee or Decimal("0")) +
        (record.alv_employee or Decimal("0")) +
        (record.nbu_employee or Decimal("0")) +
        (record.bvg_employee or Decimal("0"))
    )
    
    # QST
    qst_abzug = record.qst_abzug or Decimal("0")
    
    # Nettolohn = Bruttolohn - Sozialabzüge - QST
    nettolohn = bruttolohn - sozialabzuege_total - qst_abzug
    
    # Privatanteile (aus PayrollItems)
    privatanteil_items = record.items.filter(
        wage_type__code__startswith="PRIVATANTEIL_"
    )
    privatanteile_total = sum(item.total for item in privatanteil_items)
    
    # Familienzulagen (Durchlaufender Posten SVA)
    family_allowance_items = record.items.filter(
        wage_type__code__in=['KINDERZULAGE', 'FAMILIENZULAGE']
    )
    zulagen_total = sum(item.total for item in family_allowance_items)
    
    # Auszahlung = Nettolohn - Privatanteile + Zulagen
    auszahlung_raw = nettolohn - privatanteile_total + zulagen_total
    
    # Rundung auf 5 Rappen
    auszahlung_gerundet = round_to_5_rappen(auszahlung_raw)
    rundung = auszahlung_gerundet - auszahlung_raw
    
    return {
        'bruttolohn': bruttolohn,
        'sozialabzuege_total': sozialabzuege_total,
        'qst_abzug': qst_abzug,
        'nettolohn': nettolohn,
        'privatanteile_total': privatanteile_total,
        'zulagen_total': zulagen_total,
        'auszahlung': auszahlung_gerundet,
        'rundung': rundung,
        'aufschluesselung': {
            'ahv': record.ahv_employee or Decimal("0"),
            'alv': record.alv_employee or Decimal("0"),
            'nbu': record.nbu_employee or Decimal("0"),
            'bvg': record.bvg_employee or Decimal("0"),
            'ktg': record.ktg_employee or Decimal("0"),
        }
    }
