"""
Kleine Helper für wiederkehrende PayrollRecord-Workflows.

Ziel: DRY ohne Business-Logik zu ändern.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.shortcuts import redirect
from django.urls import reverse

from adealohn.models import PayrollItem


def create_payroll_item_and_recompute(payroll_record, payroll_item=None, wage_type_code=None, amount=None, description=None):
    """
    Berechnet den PayrollRecord neu nach Erstellung/Änderung eines PayrollItems.
    Gibt danach ein Redirect zur Payroll-Detailseite zurück.
    
    Args:
        payroll_record: PayrollRecord-Instanz
        payroll_item: PayrollItem-Instanz (falls bereits erstellt)
        wage_type_code: Code des WageType (falls payroll_item None)
        amount: Betrag (falls payroll_item None)
        description: Beschreibung (falls payroll_item None)
    
    Returns:
        HttpResponseRedirect zur Payroll-Detailseite
    """
    # Wenn payroll_item bereits vorhanden ist, verwende es
    # Sonst wurde es bereits in der View erstellt
    if payroll_item:
        # Item wurde bereits gespeichert, nur neu berechnen
        pass
    elif wage_type_code:
        # Legacy-Aufruf: Item wurde noch nicht erstellt
        # Das sollte eigentlich nicht mehr vorkommen, aber für Kompatibilität
        from adealohn.models import WageType
        wage_type = WageType.objects.get(code=wage_type_code)
        PayrollItem.objects.create(
            payroll=payroll_record,
            wage_type=wage_type,
            quantity=Decimal("1"),
            amount=amount,
            description=description or "",
        )
    
    # PayrollRecord neu berechnen
    payroll_record.recompute_bases_from_items()
    payroll_record.save()

    return redirect(reverse("adealohn:payroll-detail", args=[payroll_record.pk]))

