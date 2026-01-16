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


def calculate_employee_monthly_stats_bulk(*, employees, year: int, month: int) -> Dict[int, Dict[str, Any]]:
    """
    Bulk-Variante für Monatsstatistiken.

    Ziel: identische Business-Logik wie `calculate_employee_monthly_stats`, aber mit
    deutlich weniger DB-Queries (TimeEntry/Absence aggregiert pro Monat).
    """
    from collections import defaultdict
    from datetime import date, timedelta
    from decimal import Decimal

    from django.db.models import Sum

    from .models import Absence, TimeEntry
    from .services import WorkingTimeCalculator

    employees_list = list(employees)
    if not employees_list:
        return {}

    employee_by_id = {e.id: e for e in employees_list}
    employee_ids = list(employee_by_id.keys())

    start_date = date(year, month, 1)
    end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    # IST: 1 Query (Sum dauer) gruppiert nach employee_id
    ist_rows = (
        TimeEntry.objects.filter(
            mitarbeiter_id__in=employee_ids,
            datum__gte=start_date,
            datum__lt=end_date,
        )
        .values("mitarbeiter_id")
        .annotate(total=Sum("dauer"))
    )
    ist_by_employee_id: Dict[int, Decimal] = {
        row["mitarbeiter_id"]: (Decimal(str(row["total"])) if row["total"] is not None else Decimal("0.00"))
        for row in ist_rows
    }

    # Abwesenheiten: 1 Query für den Monat (ohne FEIERTAG), Rechnung in Python wie bisher
    absences = (
        Absence.objects.filter(
            employee_id__in=employee_ids,
            date_from__lt=end_date,
            date_to__gte=start_date,
        )
        .exclude(absence_type="FEIERTAG")
        .only("employee_id", "date_from", "date_to", "full_day", "hours")
    )

    absence_by_employee_id: Dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))

    for absence in absences:
        employee = employee_by_id.get(absence.employee_id)
        if employee is None:
            continue

        weekly_working_days = employee.weekly_working_days or Decimal("5.0")
        daily_hours = (
            employee.weekly_soll_hours / weekly_working_days
            if employee.weekly_soll_hours and weekly_working_days > 0
            else Decimal("0.00")
        )

        # Overlap mit dem Monat (end_date ist exklusive Grenze)
        overlap_start = max(absence.date_from, start_date)
        overlap_end = min(absence.date_to, end_date - timedelta(days=1))

        if absence.full_day:
            # Count workdays in overlap period (excluding weekends and holidays)
            employee_canton = employee.work_canton or ""
            holidays_set = WorkingTimeCalculator._holidays_set(year, month, employee_canton)

            days_count = 0
            current_day = overlap_start
            while current_day <= overlap_end:
                if current_day.weekday() < 5 and current_day not in holidays_set:
                    days_count += 1
                current_day += timedelta(days=1)

            absence_by_employee_id[employee.id] += Decimal(str(days_count)) * daily_hours
        else:
            if absence.hours:
                absence_by_employee_id[employee.id] += absence.hours

    # Final: identische Rundung/Derivate wie WorkingTimeCalculator
    result: Dict[int, Dict[str, Any]] = {}
    for employee in employees_list:
        monthly_soll = WorkingTimeCalculator.monthly_soll_hours(employee, year, month)
        monthly_absence = absence_by_employee_id.get(employee.id, Decimal("0.00")).quantize(Decimal("0.01"))
        monthly_ist = ist_by_employee_id.get(employee.id, Decimal("0.00")).quantize(Decimal("0.01"))

        monthly_effective_soll = max(monthly_soll - monthly_absence, Decimal("0.00")).quantize(Decimal("0.01"))
        if monthly_effective_soll == 0:
            productivity = Decimal("0.00")
        else:
            productivity = ((monthly_ist / monthly_effective_soll) * Decimal("100.00")).quantize(Decimal("0.01"))

        result[employee.id] = {
            "monthly_soll": monthly_soll,
            "monthly_absence": monthly_absence,
            "monthly_effective_soll": monthly_effective_soll,
            "monthly_ist": monthly_ist,
            "productivity": productivity,
        }

    return result


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

