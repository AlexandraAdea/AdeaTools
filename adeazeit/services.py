"""
Business-Logik für Arbeitszeitberechnungen in AdeaZeit.
"""
from decimal import Decimal
from datetime import date, timedelta
from functools import lru_cache
from django.db.models import Sum, Q
from calendar import monthrange
from .models import EmployeeInternal, TimeEntry, Absence, Holiday


class WorkingTimeCalculator:
    """
    Erweiterte Berechnungen für Arbeitszeit mit Abwesenheiten und Feiertagen.
    """

    @staticmethod
    @lru_cache(maxsize=256)
    def _holidays_set(year: int, month: int, canton: str):
        """
        Cached holidays for (year, month, canton).

        Hint: Holidays ändern sich selten; durch Caching vermeiden wir N× identische DB-Queries
        (z.B. in EmployeeMonthlyStatsView).
        """
        holidays = (
            Holiday.objects.filter(date__year=year, date__month=month)
            .filter(Q(canton="") | Q(canton=canton))
            .values_list("date", flat=True)
        )
        return frozenset(holidays)

    @staticmethod
    @lru_cache(maxsize=256)
    def _count_workdays_for_canton(year: int, month: int, canton: str) -> int:
        """Cached nominal workdays (Mon–Fri ohne Feiertage) pro Monat und Kanton."""
        holidays_set = WorkingTimeCalculator._holidays_set(year, month, canton)
        workdays = 0
        for day in WorkingTimeCalculator.iter_days(year, month):
            # Monday = 0, Friday = 4
            if day.weekday() < 5 and day not in holidays_set:
                workdays += 1
        return workdays
    
    @staticmethod
    def iter_days(year: int, month: int):
        """Yield all dates of a given month."""
        _, last_day = monthrange(year, month)
        current_date = date(year, month, 1)
        while current_date.month == month:
            yield current_date
            current_date += timedelta(days=1)
    
    @staticmethod
    def count_workdays(employee: EmployeeInternal, year: int, month: int) -> int:
        """
        Count nominal workdays in a month for the employee:
        - Monday–Friday only.
        - Exclude holidays (Holiday) that match employee.work_canton OR canton="".
        """
        employee_canton = employee.work_canton or ""
        return WorkingTimeCalculator._count_workdays_for_canton(year, month, employee_canton)
    
    @staticmethod
    def monthly_soll_hours(employee: EmployeeInternal, year: int, month: int) -> Decimal:
        """
        Base formula:
            nominal_workdays * (employee.weekly_soll_hours / weekly_working_days)
        If weekly_working_days is null, assume 5.0.
        Then apply employment_percent:
            base_hours * (employment_percent / 100)
        Return Decimal rounded to 2 decimals.
        """
        if not employee.weekly_soll_hours or employee.weekly_soll_hours == 0:
            return Decimal('0.00')
        
        workdays = WorkingTimeCalculator.count_workdays(employee, year, month)
        weekly_working_days = employee.weekly_working_days or Decimal('5.0')
        
        # Daily hours = weekly_soll_hours / weekly_working_days
        daily_hours = employee.weekly_soll_hours / weekly_working_days
        
        # Base hours for the month
        base_hours = Decimal(str(workdays)) * daily_hours
        
        # Apply employment_percent
        employment_factor = employee.employment_percent / Decimal('100.00')
        monthly_soll = base_hours * employment_factor
        
        return monthly_soll.quantize(Decimal('0.01'))
    
    @staticmethod
    def monthly_absence_hours(employee: EmployeeInternal, year: int, month: int) -> Decimal:
        """
        Sum up all Absence hours for the month:
        - For full_day absences: convert days to hours = daily_hours * number_of_workdays
          where daily_hours = weekly_soll_hours / weekly_working_days
        - For partial-day absences: use hours directly.
        - Feiertage are NOT captured here (we handle them via Holiday model).
        """
        # Date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        # Get all absences for this month (excluding FEIERTAG)
        absences = Absence.objects.filter(
            employee=employee,
            date_from__lt=end_date,
            date_to__gte=start_date
        ).exclude(absence_type="FEIERTAG")
        
        total_hours = Decimal('0.00')
        weekly_working_days = employee.weekly_working_days or Decimal('5.0')
        daily_hours = employee.weekly_soll_hours / weekly_working_days if employee.weekly_soll_hours and weekly_working_days > 0 else Decimal('0.00')
        
        # Get holidays for this month (to exclude from workday count) – cached per (year, month, canton)
        employee_canton = employee.work_canton or ""
        holidays_set = WorkingTimeCalculator._holidays_set(year, month, employee_canton)
        
        for absence in absences:
            # Calculate overlap with the month
            overlap_start = max(absence.date_from, start_date)
            overlap_end = min(absence.date_to, end_date - timedelta(days=1))
            
            if absence.full_day:
                # Count workdays in the overlap period (excluding weekends and holidays)
                days_count = 0
                current_day = overlap_start
                while current_day <= overlap_end:
                    # Monday = 0, Friday = 4
                    if current_day.weekday() < 5:  # Monday to Friday
                        if current_day not in holidays_set:
                            days_count += 1
                    current_day += timedelta(days=1)
                
                total_hours += Decimal(str(days_count)) * daily_hours
            else:
                # Partial day: use hours directly
                if absence.hours:
                    total_hours += absence.hours
        
        return total_hours.quantize(Decimal('0.01'))
    
    @staticmethod
    def monthly_ist_hours(employee: EmployeeInternal, year: int, month: int) -> Decimal:
        """
        Sum all TimeEntry.dauer (duration) for the employee in that month.
        """
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        total = TimeEntry.objects.filter(
            mitarbeiter=employee,
            datum__gte=start_date,
            datum__lt=end_date
        ).aggregate(total=Sum('dauer'))['total']
        
        if total is None:
            return Decimal('0.00')
        
        return Decimal(str(total)).quantize(Decimal('0.01'))
    
    @staticmethod
    def monthly_effective_soll_hours(employee: EmployeeInternal, year: int, month: int) -> Decimal:
        """
        effective_soll = monthly_soll_hours - (FERIEN + KRANK + UNBEZAHLT + WEITERBILDUNG)
        Feiertage already reduced nominal_workdays in count_workdays().
        Do not allow negative values (min 0).
        """
        soll = WorkingTimeCalculator.monthly_soll_hours(employee, year, month)
        absence = WorkingTimeCalculator.monthly_absence_hours(employee, year, month)
        
        effective = soll - absence
        return max(effective, Decimal('0.00')).quantize(Decimal('0.01'))
    
    @staticmethod
    def monthly_productivity(employee: EmployeeInternal, year: int, month: int) -> Decimal:
        """
        productivity = ist / effective_soll * 100
        If effective_soll == 0, return 0.
        """
        ist = WorkingTimeCalculator.monthly_ist_hours(employee, year, month)
        effective_soll = WorkingTimeCalculator.monthly_effective_soll_hours(employee, year, month)
        
        if effective_soll == 0:
            return Decimal('0.00')
        
        productivity = (ist / effective_soll) * Decimal('100.00')
        return productivity.quantize(Decimal('0.01'))
