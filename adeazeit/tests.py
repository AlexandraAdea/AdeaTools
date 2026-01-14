from decimal import Decimal
from datetime import date, timedelta, time
from django.test import TestCase
from django.core.exceptions import ValidationError

from adeacore.models import Client
from .models import EmployeeInternal, ServiceType, ZeitProject, TimeEntry, Absence, Holiday
from .forms import EmployeeInternalForm, TimeEntryForm, AbsenceForm
from .services import WorkingTimeService, WorkingTimeCalculator


class EmployeeInternalModelTest(TestCase):
    """Tests für das EmployeeInternal-Modell."""
    
    def setUp(self):
        """Erstelle Test-Daten."""
        self.employee = EmployeeInternal.objects.create(
            code="EMP001",
            name="Max Mustermann",
            function_title="Senior Consultant",
            employment_percent=Decimal('100.00'),
            weekly_soll_hours=Decimal('42.00'),
            eintrittsdatum=date(2020, 1, 1),
            aktiv=True
        )
    
    def test_employee_creation(self):
        """Test: Mitarbeiter kann mit allen Feldern erstellt werden."""
        employee = EmployeeInternal.objects.create(
            code="EMP002",
            name="Anna Muster",
            function_title="Junior Consultant",
            employment_percent=Decimal('60.00'),
            weekly_soll_hours=Decimal('25.20'),
            weekly_working_days=Decimal('3.0'),
            vacation_days_per_year=Decimal('20.00'),
            work_canton="ZH",
            holiday_model="Standard",
            employment_start=date(2024, 1, 1),
            employment_end=None,
            eintrittsdatum=date(2024, 1, 1),
            stundensatz=Decimal('150.00'),
            notes="Test-Notizen",
            aktiv=True
        )
        
        self.assertEqual(employee.code, "EMP002")
        self.assertEqual(employee.name, "Anna Muster")
        self.assertEqual(employee.function_title, "Junior Consultant")
        self.assertEqual(employee.employment_percent, Decimal('60.00'))
        self.assertEqual(employee.weekly_soll_hours, Decimal('25.20'))
        self.assertEqual(employee.weekly_working_days, Decimal('3.0'))
        self.assertEqual(employee.vacation_days_per_year, Decimal('20.00'))
        self.assertEqual(employee.work_canton, "ZH")
        self.assertEqual(employee.holiday_model, "Standard")
        self.assertEqual(employee.notes, "Test-Notizen")
    
    def test_internal_full_name_property(self):
        """Test: internal_full_name Property funktioniert."""
        self.assertEqual(
            self.employee.internal_full_name,
            "Max Mustermann – Senior Consultant"
        )
    
    def test_employment_end_validation(self):
        """Test: employment_end darf nicht vor employment_start liegen."""
        employee = EmployeeInternal(
            code="EMP003",
            name="Test",
            function_title="Test",
            employment_percent=Decimal('100.00'),
            weekly_soll_hours=Decimal('42.00'),
            employment_start=date(2024, 6, 1),
            employment_end=date(2024, 5, 1),  # Vor Start!
            eintrittsdatum=date(2024, 1, 1),
            aktiv=True
        )
        
        with self.assertRaises(ValidationError):
            employee.full_clean()
    
    def test_is_active_method(self):
        """Test: is_active() Methode funktioniert korrekt."""
        # Aktiver Mitarbeiter ohne employment_end
        self.assertTrue(self.employee.is_active())
        
        # Inaktiver Mitarbeiter
        self.employee.aktiv = False
        self.employee.save()
        self.assertFalse(self.employee.is_active())
        
        # Mitarbeiter mit zukünftigem employment_end
        self.employee.aktiv = True
        self.employee.employment_end = date.today() + timedelta(days=30)
        self.employee.save()
        self.assertTrue(self.employee.is_active())
        
        # Mitarbeiter mit vergangenem employment_end
        self.employee.employment_end = date.today() - timedelta(days=1)
        self.employee.save()
        self.assertFalse(self.employee.is_active())


class EmployeeInternalFormTest(TestCase):
    """Tests für EmployeeInternalForm."""
    
    def test_form_validation_employment_percent_positive(self):
        """Test: employment_percent muss > 0 sein."""
        form = EmployeeInternalForm(data={
            "code": "EMP001",
            "name": "Test",
            "function_title": "Test",
            "employment_percent": Decimal('0.00'),  # Ungültig!
            "weekly_soll_hours": Decimal('42.00'),
            "eintrittsdatum": date.today(),
            "aktiv": True,
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn("employment_percent", form.errors)
    
    def test_form_validation_weekly_soll_hours_positive(self):
        """Test: weekly_soll_hours muss > 0 sein."""
        form = EmployeeInternalForm(data={
            "code": "EMP001",
            "name": "Test",
            "function_title": "Test",
            "employment_percent": Decimal('100.00'),
            "weekly_soll_hours": Decimal('0.00'),  # Ungültig!
            "eintrittsdatum": date.today(),
            "aktiv": True,
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn("weekly_soll_hours", form.errors)
    
    def test_form_validation_employment_end_before_start(self):
        """Test: employment_end darf nicht vor employment_start liegen."""
        form = EmployeeInternalForm(data={
            "code": "EMP001",
            "name": "Test",
            "function_title": "Test",
            "employment_percent": Decimal('100.00'),
            "weekly_soll_hours": Decimal('42.00'),
            "employment_start": date(2024, 6, 1),
            "employment_end": date(2024, 5, 1),  # Vor Start!
            "eintrittsdatum": date.today(),
            "aktiv": True,
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn("employment_end", form.errors)


class WorkingTimeServiceTest(TestCase):
    """Tests für WorkingTimeService."""
    
    def setUp(self):
        """Erstelle Test-Daten."""
        self.employee = EmployeeInternal.objects.create(
            code="EMP001",
            name="Max Mustermann",
            function_title="Senior Consultant",
            employment_percent=Decimal('100.00'),
            weekly_soll_hours=Decimal('42.00'),
            eintrittsdatum=date(2020, 1, 1),
            aktiv=True
        )
        
        self.client = Client.objects.create(
            name="Test Client",
            client_type="FIRMA"
        )
        
        self.service_type = ServiceType.objects.create(
            code="STEU",
            name="Steuerberatung",
            standard_rate=Decimal('150.00'),
            billable=True
        )
    
    def test_calculate_monthly_soll(self):
        """Test: Monatliche Sollzeit-Berechnung mit 42h/Woche."""
        soll = WorkingTimeService.calculate_monthly_soll(self.employee, 2025, 1)
        # 42 * 4.333 = 181.986
        expected = Decimal('42.00') * Decimal('4.333')
        self.assertEqual(soll, expected.quantize(Decimal('0.01')))
    
    def test_calculate_monthly_ist_empty(self):
        """Test: Ist-Zeit ist 0 wenn keine Zeiteinträge vorhanden."""
        ist = WorkingTimeService.calculate_monthly_ist(self.employee, 2025, 1)
        self.assertEqual(ist, Decimal('0.00'))
    
    def test_calculate_monthly_ist_with_entries(self):
        """Test: Ist-Zeit wird korrekt aus TimeEntries summiert."""
        # Erstelle Zeiteinträge
        TimeEntry.objects.create(
            mitarbeiter=self.employee,
            client=self.client,
            datum=date(2025, 1, 15),
            dauer=Decimal('8.00'),
            service_type=self.service_type,
            rate=Decimal('150.00'),
            betrag=Decimal('1200.00').quantize(Decimal('0.01')),
            billable=True
        )
        TimeEntry.objects.create(
            mitarbeiter=self.employee,
            client=self.client,
            datum=date(2025, 1, 16),
            dauer=Decimal('6.50'),
            service_type=self.service_type,
            rate=Decimal('150.00'),
            betrag=Decimal('975.00').quantize(Decimal('0.01')),
            billable=True
        )
        
        ist = WorkingTimeService.calculate_monthly_ist(self.employee, 2025, 1)
        self.assertEqual(ist, Decimal('14.50'))
    
    def test_calculate_productivity(self):
        """Test: Produktivität wird korrekt berechnet."""
        # Erstelle Zeiteinträge (14.5h)
        TimeEntry.objects.create(
            mitarbeiter=self.employee,
            client=self.client,
            datum=date(2025, 1, 15),
            dauer=Decimal('8.00'),
            service_type=self.service_type,
            rate=Decimal('150.00'),
            betrag=Decimal('1200.00').quantize(Decimal('0.01')),
            billable=True
        )
        TimeEntry.objects.create(
            mitarbeiter=self.employee,
            client=self.client,
            datum=date(2025, 1, 16),
            dauer=Decimal('6.50'),
            service_type=self.service_type,
            rate=Decimal('150.00'),
            betrag=Decimal('975.00').quantize(Decimal('0.01')),
            billable=True
        )
        
        productivity = WorkingTimeService.calculate_productivity(self.employee, 2025, 1)
        soll = WorkingTimeService.calculate_monthly_soll(self.employee, 2025, 1)
        expected = (Decimal('14.50') / soll) * Decimal('100.00')
        self.assertEqual(productivity, expected.quantize(Decimal('0.01')))
    
    def test_calculate_productivity_zero_soll(self):
        """Test: Produktivität ist 0 wenn Soll-Zeit 0 ist."""
        self.employee.weekly_soll_hours = Decimal('0.00')
        self.employee.save()
        
        productivity = WorkingTimeService.calculate_productivity(self.employee, 2025, 1)
        self.assertEqual(productivity, Decimal('0.00'))
    
    def test_get_employee_info(self):
        """Test: get_employee_info gibt korrekte Informationen zurück."""
        info = WorkingTimeService.get_employee_info(self.employee, 2025, 1)
        
        self.assertEqual(info["employee"], self.employee)
        self.assertEqual(info["employment_percent"], Decimal('100.00'))
        self.assertEqual(info["weekly_soll_hours"], Decimal('42.00'))
        self.assertIn("monthly_soll", info)
        self.assertIn("monthly_ist", info)
        self.assertIn("productivity", info)


class TimeEntryFormTest(TestCase):
    """Tests für TimeEntryForm."""
    
    def setUp(self):
        """Erstelle Test-Daten."""
        self.client = Client.objects.create(
            name="Test Client",
            client_type="FIRMA"
        )
        
        self.service_type = ServiceType.objects.create(
            code="STEU",
            name="Steuerberatung",
            standard_rate=Decimal('150.00'),
            billable=True
        )
        
        # Aktiver Mitarbeiter
        self.active_employee = EmployeeInternal.objects.create(
            code="EMP001",
            name="Aktiver Mitarbeiter",
            function_title="Consultant",
            employment_percent=Decimal('100.00'),
            weekly_soll_hours=Decimal('42.00'),
            eintrittsdatum=date(2020, 1, 1),
            aktiv=True
        )
        
        # Inaktiver Mitarbeiter (employment_end in der Vergangenheit)
        self.inactive_employee = EmployeeInternal.objects.create(
            code="EMP002",
            name="Inaktiver Mitarbeiter",
            function_title="Consultant",
            employment_percent=Decimal('100.00'),
            weekly_soll_hours=Decimal('42.00'),
            eintrittsdatum=date(2020, 1, 1),
            employment_end=date.today() - timedelta(days=1),
            aktiv=True
        )
    
    def test_form_filters_active_employees(self):
        """Test: Form zeigt nur aktive Mitarbeitende."""
        form = TimeEntryForm()
        queryset = form.fields["mitarbeiter"].queryset
        
        # Aktiver Mitarbeiter sollte enthalten sein
        self.assertIn(self.active_employee, queryset)
        
        # Inaktiver Mitarbeiter sollte NICHT enthalten sein
        self.assertNotIn(self.inactive_employee, queryset)
    
    def test_form_filters_employees_with_future_employment_end(self):
        """Test: Mitarbeiter mit zukünftigem employment_end werden angezeigt."""
        future_employee = EmployeeInternal.objects.create(
            code="EMP003",
            name="Zukünftiger Mitarbeiter",
            function_title="Consultant",
            employment_percent=Decimal('100.00'),
            weekly_soll_hours=Decimal('42.00'),
            eintrittsdatum=date(2020, 1, 1),
            employment_end=date.today() + timedelta(days=30),
            aktiv=True
        )
        
        form = TimeEntryForm()
        queryset = form.fields["mitarbeiter"].queryset
        
        self.assertIn(future_employee, queryset)


class AbsenceModelTest(TestCase):
    """Tests für das Absence-Modell."""
    
    def setUp(self):
        """Erstelle Test-Daten."""
        self.employee = EmployeeInternal.objects.create(
            code="EMP001",
            name="Max Mustermann",
            function_title="Senior Consultant",
            employment_percent=Decimal('100.00'),
            weekly_soll_hours=Decimal('42.00'),
            weekly_working_days=Decimal('5.0'),
            eintrittsdatum=date(2020, 1, 1),
            aktiv=True
        )
    
    def test_absence_creation_full_day(self):
        """Test: Ganztägige Abwesenheit kann erstellt werden."""
        absence = Absence.objects.create(
            employee=self.employee,
            absence_type="FERIEN",
            date_from=date(2025, 1, 15),
            date_to=date(2025, 1, 17),
            full_day=True,
            comment="Ferien"
        )
        
        self.assertEqual(absence.employee, self.employee)
        self.assertEqual(absence.absence_type, "FERIEN")
        self.assertEqual(absence.date_from, date(2025, 1, 15))
        self.assertEqual(absence.date_to, date(2025, 1, 17))
        self.assertTrue(absence.full_day)
        self.assertIsNone(absence.hours)
    
    def test_absence_creation_partial_day(self):
        """Test: Teilzeit-Abwesenheit kann erstellt werden."""
        absence = Absence.objects.create(
            employee=self.employee,
            absence_type="KRANK",
            date_from=date(2025, 1, 15),
            date_to=date(2025, 1, 15),
            full_day=False,
            hours=Decimal('4.00'),
            comment="Krank"
        )
        
        self.assertFalse(absence.full_day)
        self.assertEqual(absence.hours, Decimal('4.00'))
    
    def test_absence_validation_date_to_before_date_from(self):
        """Test: date_to darf nicht vor date_from liegen."""
        absence = Absence(
            employee=self.employee,
            absence_type="FERIEN",
            date_from=date(2025, 1, 17),
            date_to=date(2025, 1, 15),  # Vor date_from!
            full_day=True
        )
        
        with self.assertRaises(ValidationError):
            absence.full_clean()
    
    def test_absence_validation_full_day_with_hours(self):
        """Test: Ganztägige Abwesenheit darf keine Stunden haben."""
        absence = Absence(
            employee=self.employee,
            absence_type="FERIEN",
            date_from=date(2025, 1, 15),
            date_to=date(2025, 1, 17),
            full_day=True,
            hours=Decimal('8.00')  # Sollte nicht erlaubt sein!
        )
        
        with self.assertRaises(ValidationError):
            absence.full_clean()
    
    def test_absence_validation_partial_day_without_hours(self):
        """Test: Teilzeit-Abwesenheit muss Stunden haben."""
        absence = Absence(
            employee=self.employee,
            absence_type="KRANK",
            date_from=date(2025, 1, 15),
            date_to=date(2025, 1, 15),
            full_day=False,
            hours=None  # Sollte nicht erlaubt sein!
        )
        
        with self.assertRaises(ValidationError):
            absence.full_clean()
    
    def test_absence_is_aktiv(self):
        """Test: is_aktiv() Methode funktioniert korrekt."""
        # Aktive Abwesenheit (heute)
        today = date.today()
        active_absence = Absence.objects.create(
            employee=self.employee,
            absence_type="FERIEN",
            date_from=today - timedelta(days=1),
            date_to=today + timedelta(days=1),
            full_day=True
        )
        self.assertTrue(active_absence.is_aktiv)
        
        # Vergangene Abwesenheit
        past_absence = Absence.objects.create(
            employee=self.employee,
            absence_type="FERIEN",
            date_from=today - timedelta(days=10),
            date_to=today - timedelta(days=5),
            full_day=True
        )
        self.assertFalse(past_absence.is_aktiv)


class AbsenceFormTest(TestCase):
    """Tests für AbsenceForm."""
    
    def setUp(self):
        """Erstelle Test-Daten."""
        self.employee = EmployeeInternal.objects.create(
            code="EMP001",
            name="Max Mustermann",
            function_title="Senior Consultant",
            employment_percent=Decimal('100.00'),
            weekly_soll_hours=Decimal('42.00'),
            eintrittsdatum=date(2020, 1, 1),
            aktiv=True
        )
    
    def test_form_validation_full_day_with_hours(self):
        """Test: Form validiert, dass ganztägige Abwesenheit keine Stunden hat."""
        form = AbsenceForm(data={
            "employee": self.employee.pk,
            "absence_type": "FERIEN",
            "date_from": "2025-01-15",
            "date_to": "2025-01-17",
            "full_day": True,
            "hours": "8.00",  # Sollte nicht erlaubt sein!
            "comment": ""
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn("hours", form.errors)
    
    def test_form_validation_partial_day_without_hours(self):
        """Test: Form validiert, dass Teilzeit-Abwesenheit Stunden haben muss."""
        form = AbsenceForm(data={
            "employee": self.employee.pk,
            "absence_type": "KRANK",
            "date_from": "2025-01-15",
            "date_to": "2025-01-15",
            "full_day": False,
            "hours": "",  # Sollte nicht erlaubt sein!
            "comment": ""
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn("hours", form.errors)


class WorkingTimeCalculatorTest(TestCase):
    """Tests für WorkingTimeCalculator mit Abwesenheiten und Feiertagen."""
    
    def setUp(self):
        """Erstelle Test-Daten."""
        self.employee = EmployeeInternal.objects.create(
            code="EMP001",
            name="Max Mustermann",
            function_title="Senior Consultant",
            employment_percent=Decimal('100.00'),
            weekly_soll_hours=Decimal('42.00'),
            weekly_working_days=Decimal('5.0'),
            work_canton="ZH",
            eintrittsdatum=date(2020, 1, 1),
            aktiv=True
        )
        
        self.client = Client.objects.create(
            name="Test Client",
            client_type="FIRMA"
        )
        
        self.service_type = ServiceType.objects.create(
            code="STEU",
            name="Steuerberatung",
            standard_rate=Decimal('150.00'),
            billable=True
        )
    
    def test_monthly_soll_hours_with_holidays(self):
        """Test: Monatliche Sollzeit berücksichtigt Feiertage."""
        # Erstelle Feiertag im Januar 2025
        Holiday.objects.create(
            name="Neujahr",
            date=date(2025, 1, 1),
            canton="",  # CH-weit
            is_official=True
        )
        
        soll = WorkingTimeCalculator.monthly_soll_hours(self.employee, 2025, 1)
        
        # Januar 2025 hat 23 Arbeitstage (31 Tage - 8 Wochenenden - 1 Feiertag)
        # 23 * (42 / 5) = 23 * 8.4 = 193.2
        expected_workdays = 23  # 31 Tage - 8 Wochenenden - 1 Feiertag
        expected_hours = Decimal(str(expected_workdays)) * (Decimal('42.00') / Decimal('5.0'))
        
        self.assertEqual(soll, expected_hours.quantize(Decimal('0.01')))
    
    def test_monthly_absence_hours_full_day(self):
        """Test: Monatliche Abwesenheitsstunden für ganztägige Abwesenheit."""
        # Erstelle ganztägige Ferien (3 Arbeitstage)
        Absence.objects.create(
            employee=self.employee,
            absence_type="FERIEN",
            date_from=date(2025, 1, 15),  # Mittwoch
            date_to=date(2025, 1, 17),    # Freitag
            full_day=True,
            comment="Ferien"
        )
        
        absence_hours = WorkingTimeCalculator.monthly_absence_hours(self.employee, 2025, 1)
        
        # 3 Arbeitstage * (42 / 5) = 3 * 8.4 = 25.2
        expected = Decimal('3.00') * (Decimal('42.00') / Decimal('5.0'))
        
        self.assertEqual(absence_hours, expected.quantize(Decimal('0.01')))
    
    def test_monthly_absence_hours_partial_day(self):
        """Test: Monatliche Abwesenheitsstunden für Teilzeit-Abwesenheit."""
        # Erstelle Teilzeit-Krankheit
        Absence.objects.create(
            employee=self.employee,
            absence_type="KRANK",
            date_from=date(2025, 1, 15),
            date_to=date(2025, 1, 15),
            full_day=False,
            hours=Decimal('4.00'),
            comment="Krank"
        )
        
        absence_hours = WorkingTimeCalculator.monthly_absence_hours(self.employee, 2025, 1)
        
        self.assertEqual(absence_hours, Decimal('4.00'))
    
    def test_monthly_effective_soll_hours(self):
        """Test: Effektive Sollzeit berücksichtigt Abwesenheiten."""
        # Erstelle Ferien (3 Arbeitstage)
        Absence.objects.create(
            employee=self.employee,
            absence_type="FERIEN",
            date_from=date(2025, 1, 15),
            date_to=date(2025, 1, 17),
            full_day=True,
            comment="Ferien"
        )
        
        soll = WorkingTimeCalculator.monthly_soll_hours(self.employee, 2025, 1)
        absence = WorkingTimeCalculator.monthly_absence_hours(self.employee, 2025, 1)
        effective_soll = WorkingTimeCalculator.monthly_effective_soll_hours(self.employee, 2025, 1)
        
        expected = soll - absence
        self.assertEqual(effective_soll, expected.quantize(Decimal('0.01')))
    
    def test_monthly_productivity_with_absences(self):
        """Test: Produktivität berücksichtigt Abwesenheiten."""
        # Erstelle Zeiteinträge (10h)
        TimeEntry.objects.create(
            mitarbeiter=self.employee,
            client=self.client,
            datum=date(2025, 1, 10),
            dauer=Decimal('10.00'),
            service_type=self.service_type,
            rate=Decimal('150.00'),
            betrag=Decimal('1500.00'),
            billable=True
        )
        
        # Erstelle Ferien (3 Arbeitstage = 25.2h)
        Absence.objects.create(
            employee=self.employee,
            absence_type="FERIEN",
            date_from=date(2025, 1, 15),
            date_to=date(2025, 1, 17),
            full_day=True,
            comment="Ferien"
        )
        
        ist = WorkingTimeCalculator.monthly_ist_hours(self.employee, 2025, 1)
        effective_soll = WorkingTimeCalculator.monthly_effective_soll_hours(self.employee, 2025, 1)
        productivity = WorkingTimeCalculator.monthly_productivity(self.employee, 2025, 1)
        
        expected_productivity = (ist / effective_soll) * Decimal('100.00') if effective_soll > 0 else Decimal('0.00')
        
        self.assertEqual(productivity, expected_productivity.quantize(Decimal('0.01')))


class HolidayModelTest(TestCase):
    """Tests für das Holiday-Modell."""
    
    def test_holiday_creation(self):
        """Test: Feiertag kann erstellt werden."""
        holiday = Holiday.objects.create(
            name="Neujahr",
            date=date(2025, 1, 1),
            canton="",
            is_official=True
        )
        
        self.assertEqual(holiday.name, "Neujahr")
        self.assertEqual(holiday.date, date(2025, 1, 1))
        self.assertEqual(holiday.canton, "")
        self.assertTrue(holiday.is_official)
    
    def test_holiday_unique_together(self):
        """Test: Unique-Together Constraint für date und canton."""
        Holiday.objects.create(
            name="Neujahr",
            date=date(2025, 1, 1),
            canton="",
            is_official=True
        )
        
        # Versuche, denselben Feiertag nochmals zu erstellen
        with self.assertRaises(Exception):  # IntegrityError
            Holiday.objects.create(
                name="Neujahr (Duplikat)",
                date=date(2025, 1, 1),
                canton="",
                is_official=True
            )
    
    def test_holiday_canton_specific(self):
        """Test: Kantonsspezifische Feiertage können erstellt werden."""
        # CH-weiter Feiertag
        ch_holiday = Holiday.objects.create(
            name="Neujahr",
            date=date(2025, 1, 1),
            canton="",
            is_official=True
        )
        
        # ZH-spezifischer Feiertag
        zh_holiday = Holiday.objects.create(
            name="Sechseläuten",
            date=date(2025, 4, 21),
            canton="ZH",
            is_official=True
        )
        
        self.assertEqual(ch_holiday.canton, "")
        self.assertEqual(zh_holiday.canton, "ZH")


class TimeDurationCalculationTest(TestCase):
    """Tests für die Zeit-Dauer-Berechnung (Helper-Methode)."""
    
    def test_normal_duration(self):
        """Test: Normale Dauer-Berechnung (09:00-17:00 => 480 Minuten)."""
        start = time(9, 0)  # 09:00
        ende = time(17, 0)  # 17:00
        diff_minutes = TimeEntry._calculate_duration_minutes(start, ende)
        self.assertEqual(diff_minutes, 480)  # 8 Stunden = 480 Minuten
    
    def test_midnight_crossing(self):
        """Test: Dauer über Mitternacht (23:00-01:00 => 120 Minuten)."""
        start = time(23, 0)  # 23:00
        ende = time(1, 0)    # 01:00
        diff_minutes = TimeEntry._calculate_duration_minutes(start, ende)
        self.assertEqual(diff_minutes, 120)  # 2 Stunden = 120 Minuten
    
    def test_edge_case_same_time(self):
        """Test: Gleiche Zeit (00:00-00:00 => 1440 Minuten über Mitternacht)."""
        start = time(0, 0)   # 00:00
        ende = time(0, 0)    # 00:00
        diff_minutes = TimeEntry._calculate_duration_minutes(start, ende)
        # Bei gleicher Zeit wird über Mitternacht gerechnet: 24 Stunden = 1440 Minuten
        self.assertEqual(diff_minutes, 1440)
    
    def test_one_minute_difference(self):
        """Test: Ein-Minuten-Unterschied (09:00-09:01 => 1 Minute)."""
        start = time(9, 0)   # 09:00
        ende = time(9, 1)   # 09:01
        diff_minutes = TimeEntry._calculate_duration_minutes(start, ende)
        self.assertEqual(diff_minutes, 1)
    
    def test_partial_hours(self):
        """Test: Teilstunden (09:30-17:45 => 495 Minuten)."""
        start = time(9, 30)  # 09:30
        ende = time(17, 45)  # 17:45
        diff_minutes = TimeEntry._calculate_duration_minutes(start, ende)
        # 8 Stunden 15 Minuten = 495 Minuten
        self.assertEqual(diff_minutes, 495)
    
    def test_midnight_crossing_with_minutes(self):
        """Test: Mitternacht-Übergang mit Minuten (23:30-01:15 => 105 Minuten)."""
        start = time(23, 30)  # 23:30
        ende = time(1, 15)    # 01:15
        diff_minutes = TimeEntry._calculate_duration_minutes(start, ende)
        # 1 Stunde 45 Minuten = 105 Minuten
        self.assertEqual(diff_minutes, 105)
