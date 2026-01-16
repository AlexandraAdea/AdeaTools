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


def create_payroll_item_and_recompute(
    *,
    payroll,
    wage_type,
    quantity: Any,
    amount,
    description: str = "",
):
    """
    Erstellt ein PayrollItem, berechnet den PayrollRecord neu und speichert.
    Gibt danach ein Redirect zur Payroll-Detailseite zurück.
    """
    PayrollItem.objects.create(
        payroll=payroll,
        wage_type=wage_type,
        quantity=Decimal(str(quantity)),
        amount=amount,
        description=description,
    )

    payroll.recompute_bases_from_items()
    payroll.save()

    return redirect(reverse("adealohn:payroll-detail", args=[payroll.pk]))

