"""
Helper für wiederkehrende Employee-Monats-Infos (DRY).

Wichtig: keine Business-Logik-Änderung – nur Zentralisierung der bestehenden Berechnungen.
"""

from __future__ import annotations

from typing import Any, Dict


def calculate_employee_monthly_stats(*, employee, year: int, month: int) -> Dict[str, Any]:
    """
    Liefert die 5 Kernwerte als Decimal (wie bisher in den Views berechnet).
    """
    from .services import WorkingTimeCalculator

    return {
        "monthly_soll": WorkingTimeCalculator.monthly_soll_hours(employee, year, month),
        "monthly_absence": WorkingTimeCalculator.monthly_absence_hours(employee, year, month),
        "monthly_effective_soll": WorkingTimeCalculator.monthly_effective_soll_hours(employee, year, month),
        "monthly_ist": WorkingTimeCalculator.monthly_ist_hours(employee, year, month),
        "productivity": WorkingTimeCalculator.monthly_productivity(employee, year, month),
    }


def build_employee_sidebar_info(*, employee, year: int, month: int) -> Dict[str, Any]:
    """
    Baut das `context["employee_info"]` Dict für Templates (inkl. employee + Stammdaten),
    exakt wie bisher an mehreren Stellen in `views.py`.
    """
    info = {
        "employee": employee,
        "employment_percent": employee.employment_percent,
        "weekly_soll_hours": employee.weekly_soll_hours,
    }
    info.update(calculate_employee_monthly_stats(employee=employee, year=year, month=month))
    return info


def build_employee_ajax_info(*, employee, year: int, month: int) -> Dict[str, Any]:
    """
    Baut das Payload-Dict für `LoadEmployeeInfoView` (Strings wie bisher).
    """
    stats = calculate_employee_monthly_stats(employee=employee, year=year, month=month)
    return {
        "name": employee.name,
        "function_title": employee.function_title,
        "internal_full_name": employee.internal_full_name,
        "employment_percent": str(employee.employment_percent),
        "weekly_soll_hours": str(employee.weekly_soll_hours),
        "monthly_soll": str(stats["monthly_soll"]),
        "monthly_absence": str(stats["monthly_absence"]),
        "monthly_effective_soll": str(stats["monthly_effective_soll"]),
        "monthly_ist": str(stats["monthly_ist"]),
        "productivity": str(stats["productivity"]),
    }

