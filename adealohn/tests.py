from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError

from adeacore.models import Employee, Client, PayrollRecord
from adealohn.models import WageType, BVGParameter, QSTParameter
from adealohn.ahv_calculator import AHVCalculator
from adealohn.alv_calculator import ALVCalculator
from adealohn.uvg_calculator import UVGCalculator
from adealohn.bvg_calculator import BVGCalculator
from adealohn.qst_calculator import QSTCalculator


class CalculatorTestCase(TestCase):
    """Basis-Tests für alle Calculator."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client.objects.create(name="Test Client", client_type="FIRMA")
        self.employee = Employee.objects.create(
            client=self.client,
            first_name="Test",
            last_name="Employee",
            hourly_rate=Decimal("50.00"),
            weekly_hours=Decimal("40.0"),
            is_rentner=False,
            qst_pflichtig=False,
        )
        self.payroll = PayrollRecord.objects.create(
            employee=self.employee,
            month=1,
            year=2025,
            bruttolohn=Decimal("5000.00"),
            ahv_basis=Decimal("5000.00"),
            alv_basis=Decimal("5000.00"),
            uv_basis=Decimal("5000.00"),
            bvg_basis=Decimal("5000.00"),
            qst_basis=Decimal("5000.00"),
        )

    def test_ahv_calculator_basic(self):
        """Test AHV Calculator mit normalem Mitarbeiter."""
        result = AHVCalculator.calculate_for_payroll(self.payroll)
        self.assertIn("ahv_effective_basis", result)
        self.assertIn("ahv_employee", result)
        self.assertIn("ahv_employer", result)
        self.assertGreaterEqual(result["ahv_effective_basis"], Decimal("0.00"))
        self.assertGreaterEqual(result["ahv_employee"], Decimal("0.00"))
        self.assertGreaterEqual(result["ahv_employer"], Decimal("0.00"))

    def test_ahv_calculator_rentner(self):
        """Test AHV Calculator mit Rentner."""
        self.employee.is_rentner = True
        self.employee.ahv_freibetrag_aktiv = True
        self.employee.save()
        
        result = AHVCalculator.calculate_for_payroll(self.payroll)
        # Rentner sollten Freibetrag haben
        self.assertLessEqual(result["ahv_effective_basis"], self.payroll.ahv_basis)

    def test_alv_calculator_basic(self):
        """Test ALV Calculator."""
        calc = ALVCalculator()
        result = calc.calculate_for_payroll(self.payroll)
        self.assertIn("alv_effective_basis", result)
        self.assertIn("alv_employee", result)
        self.assertIn("alv_employer", result)
        self.assertGreaterEqual(result["alv_effective_basis"], Decimal("0.00"))

    def test_alv_calculator_rentner(self):
        """Test ALV Calculator mit Rentner (sollte 0 sein)."""
        self.employee.is_rentner = True
        self.employee.save()
        
        calc = ALVCalculator()
        result = calc.calculate_for_payroll(self.payroll)
        self.assertEqual(result["alv_effective_basis"], Decimal("0.00"))
        self.assertEqual(result["alv_employee"], Decimal("0.00"))
        self.assertEqual(result["alv_employer"], Decimal("0.00"))

    def test_alv_calculator_ytd_capping(self):
        """Test ALV YTD-Kappung bei 148'200 CHF."""
        # Setze YTD-Basis auf Maximum
        self.employee.alv_ytd_basis = Decimal("148200.00")
        self.employee.save()
        
        calc = ALVCalculator()
        result = calc.calculate_for_payroll(self.payroll)
        # Sollte gekappt sein
        self.assertEqual(result["alv_effective_basis"], Decimal("0.00"))

    def test_uvg_calculator_basic(self):
        """Test UVG Calculator."""
        calc = UVGCalculator()
        result = calc.calculate_for_payroll(self.payroll)
        self.assertIn("uvg_effective_basis", result)
        self.assertIn("bu_employer", result)
        self.assertIn("nbu_employee", result)

    def test_uvg_calculator_ytd_capping(self):
        """Test UVG YTD-Kappung bei 148'200 CHF."""
        self.employee.uvg_ytd_basis = Decimal("148200.00")
        self.employee.save()
        
        calc = UVGCalculator()
        result = calc.calculate_for_payroll(self.payroll)
        self.assertEqual(result["uvg_effective_basis"], Decimal("0.00"))

    def test_bvg_calculator_basic(self):
        """Test BVG Calculator."""
        # Erstelle BVG-Parameter
        BVGParameter.objects.create(
            year=2025,
            entry_threshold=Decimal("22032.00"),
            coordination_deduction=Decimal("22032.00"),
            min_insured_salary=Decimal("0.00"),
            max_insured_salary=Decimal("880800.00"),
            employee_rate=Decimal("0.05"),
            employer_rate=Decimal("0.05"),
        )
        
        calc = BVGCalculator()
        result = calc.calculate_for_payroll(self.payroll)
        self.assertIn("bvg_insured_salary", result)
        self.assertIn("bvg_employee", result)
        self.assertIn("bvg_employer", result)

    def test_bvg_calculator_below_threshold(self):
        """Test BVG Calculator unter Eintrittsschwelle."""
        BVGParameter.objects.create(
            year=2025,
            entry_threshold=Decimal("22032.00"),
            coordination_deduction=Decimal("22032.00"),
            min_insured_salary=Decimal("0.00"),
            max_insured_salary=Decimal("880800.00"),
            employee_rate=Decimal("0.05"),
            employer_rate=Decimal("0.05"),
        )
        
        # Setze niedrige Basis
        self.payroll.bvg_basis = Decimal("1000.00")
        self.payroll.save()
        self.employee.bvg_ytd_basis = Decimal("10000.00")  # Jahreslohn = 22'000 < 22'032
        self.employee.save()
        
        calc = BVGCalculator()
        result = calc.calculate_for_payroll(self.payroll)
        self.assertEqual(result["bvg_insured_salary"], Decimal("0.00"))
        self.assertEqual(result["bvg_employee"], Decimal("0.00"))

    def test_qst_calculator_not_liable(self):
        """Test QST Calculator wenn nicht QST-pflichtig."""
        self.employee.qst_pflichtig = False
        self.employee.save()
        
        calc = QSTCalculator()
        calc.calculate_for_payroll(self.payroll)
        self.assertEqual(self.payroll.qst_abzug, Decimal("0.00"))

    def test_qst_calculator_fixbetrag(self):
        """Test QST Calculator mit Fixbetrag."""
        self.employee.qst_pflichtig = True
        self.employee.qst_fixbetrag = Decimal("100.00")
        self.employee.save()
        
        calc = QSTCalculator()
        calc.calculate_for_payroll(self.payroll)
        self.assertEqual(self.payroll.qst_abzug, Decimal("100.00"))


class PayrollRecordTestCase(TestCase):
    """Tests für PayrollRecord Model."""
    
    def setUp(self):
        self.client = Client.objects.create(name="Test Client", client_type="FIRMA")
        self.employee = Employee.objects.create(
            client=self.client,
            first_name="Test",
            last_name="Employee",
            hourly_rate=Decimal("50.00"),
        )

    def test_unique_together_constraint(self):
        """Test dass unique_together Constraint funktioniert."""
        PayrollRecord.objects.create(
            employee=self.employee,
            month=1,
            year=2025,
        )
        
        # Zweiter Record mit gleichem Employee/Month/Year sollte fehlschlagen
        with self.assertRaises(ValidationError):
            payroll2 = PayrollRecord(
                employee=self.employee,
                month=1,
                year=2025,
            )
            payroll2.full_clean()

    def test_january_ytd_reset(self):
        """Test dass YTD-Basen im Januar zurückgesetzt werden."""
        self.employee.alv_ytd_basis = Decimal("1000.00")
        self.employee.uvg_ytd_basis = Decimal("2000.00")
        self.employee.save()
        
        payroll = PayrollRecord.objects.create(
            employee=self.employee,
            month=1,
            year=2025,
        )
        payroll.save()
        
        # YTD sollte zurückgesetzt sein
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.alv_ytd_basis, Decimal("0.00"))
        self.assertEqual(self.employee.uvg_ytd_basis, Decimal("0.00"))

    def test_status_locked(self):
        """Test is_locked() Methode."""
        payroll = PayrollRecord.objects.create(
            employee=self.employee,
            month=1,
            year=2025,
            status="ENTWURF",
        )
        self.assertFalse(payroll.is_locked())
        
        payroll.status = "ABGERECHNET"
        payroll.save()
        self.assertTrue(payroll.is_locked())
        
        payroll.status = "GESPERRT"
        payroll.save()
        self.assertTrue(payroll.is_locked())


class TenantTestCase(TestCase):
    """Tests für Multi-Mandanten-Funktionalität."""
    
    def setUp(self):
        """Set up test data mit mehreren Clients (nur FIRMA-Typ mit aktiviertem Lohnmodul)."""
        self.client_a = Client.objects.create(name="Client A", client_type="FIRMA", lohn_aktiv=True)
        self.client_b = Client.objects.create(name="Client B", client_type="FIRMA", lohn_aktiv=True)
        # Privat-Client für Tests (sollte nicht in AdeaLohn erscheinen)
        self.client_privat = Client.objects.create(name="Privatperson", client_type="PRIVAT", lohn_aktiv=False)
        # FIRMA ohne aktiviertes Lohnmodul (sollte nicht in AdeaLohn erscheinen)
        self.client_firma_ohne_lohn = Client.objects.create(name="Firma ohne Lohn", client_type="FIRMA", lohn_aktiv=False)
        
        self.employee_a = Employee.objects.create(
            client=self.client_a,
            first_name="Employee",
            last_name="A",
            hourly_rate=Decimal("50.00"),
        )
        self.employee_b = Employee.objects.create(
            client=self.client_b,
            first_name="Employee",
            last_name="B",
            hourly_rate=Decimal("60.00"),
        )
        
        self.payroll_a = PayrollRecord.objects.create(
            employee=self.employee_a,
            month=1,
            year=2025,
        )
        self.payroll_b = PayrollRecord.objects.create(
            employee=self.employee_b,
            month=1,
            year=2025,
        )
    
    def test_client_switch_view(self):
        """Test dass ClientSwitchView Client-ID in Session speichert."""
        from django.test import Client as TestClient
        from django.contrib.auth.models import User
        
        # Erstelle Test-User
        user = User.objects.create_user(username='testuser', password='testpass')
        
        client = TestClient()
        client.force_login(user)
        
        # POST auf Client-Switch
        response = client.post('/lohn/mandant/wechsel/', {'client_id': self.client_a.pk})
        
        # Prüfe Session
        self.assertEqual(client.session.get('active_client_id'), self.client_a.pk)
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_payroll_list_filtered_by_client(self):
        """Test dass PayrollRecordListView nur Records des aktuellen Clients zeigt."""
        from django.test import Client as TestClient
        from django.contrib.auth.models import User
        
        user = User.objects.create_user(username='testuser', password='testpass')
        test_client = TestClient()
        test_client.force_login(user)
        
        # Setze Client A in Session
        session = test_client.session
        session['active_client_id'] = self.client_a.pk
        session.save()
        
        # Rufe Payroll-Liste auf
        response = test_client.get('/lohn/payroll/')
        
        self.assertEqual(response.status_code, 200)
        # Prüfe dass nur PayrollRecord von Client A in der Liste ist
        records = response.context['records']
        self.assertEqual(records.count(), 1)
        self.assertEqual(records.first(), self.payroll_a)
        self.assertNotIn(self.payroll_b, records)
    
    def test_payroll_detail_forbidden_for_other_client(self):
        """Test dass Detail-View für anderen Client 404 wirft."""
        from django.test import Client as TestClient
        from django.contrib.auth.models import User
        
        user = User.objects.create_user(username='testuser', password='testpass')
        test_client = TestClient()
        test_client.force_login(user)
        
        # Setze Client A in Session
        session = test_client.session
        session['active_client_id'] = self.client_a.pk
        session.save()
        
        # Versuche PayrollRecord von Client B aufzurufen
        response = test_client.get(f'/lohn/payroll/{self.payroll_b.pk}/')
        
        # Sollte 404 sein (TenantObjectMixin wirft Http404)
        self.assertEqual(response.status_code, 404)
    
    def test_employee_form_filters_by_client(self):
        """Test dass PayrollCreate-Form nur Employees des aktuellen Clients zeigt."""
        from django.test import Client as TestClient
        from django.contrib.auth.models import User
        
        user = User.objects.create_user(username='testuser', password='testpass')
        test_client = TestClient()
        test_client.force_login(user)
        
        # Setze Client A in Session
        session = test_client.session
        session['active_client_id'] = self.client_a.pk
        session.save()
        
        # Rufe Payroll-Create-Form auf
        response = test_client.get('/lohn/payroll/new/')
        
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        # Prüfe dass nur Employee A im Queryset ist
        employee_queryset = form.fields['employee'].queryset
        self.assertEqual(employee_queryset.count(), 1)
        self.assertEqual(employee_queryset.first(), self.employee_a)
        self.assertNotIn(self.employee_b, employee_queryset)
    
    def test_employee_list_filtered_by_client(self):
        """Test dass EmployeeListView nur Employees des aktuellen Clients zeigt."""
        from django.test import Client as TestClient
        from django.contrib.auth.models import User
        
        user = User.objects.create_user(username='testuser', password='testpass')
        test_client = TestClient()
        test_client.force_login(user)
        
        # Setze Client A in Session
        session = test_client.session
        session['active_client_id'] = self.client_a.pk
        session.save()
        
        # Rufe Employee-Liste auf
        response = test_client.get('/lohn/')
        
        self.assertEqual(response.status_code, 200)
        employees = response.context['employees']
        self.assertEqual(employees.count(), 1)
        self.assertEqual(employees.first(), self.employee_a)
        self.assertNotIn(self.employee_b, employees)
    
    def test_payroll_create_with_wrong_client_employee(self):
        """Test dass PayrollRecord nicht mit Employee eines anderen Clients erstellt werden kann."""
        from django.test import Client as TestClient
        from django.contrib.auth.models import User
        
        user = User.objects.create_user(username='testuser', password='testpass')
        test_client = TestClient()
        test_client.force_login(user)
        
        # Setze Client A in Session
        session = test_client.session
        session['active_client_id'] = self.client_a.pk
        session.save()
        
        # Versuche PayrollRecord mit Employee von Client B zu erstellen
        response = test_client.post('/lohn/payroll/new/', {
            'employee': self.employee_b.pk,
            'month': 2,
            'year': 2025,
            'status': 'ENTWURF',
        })
        
        # Form sollte Fehler haben
        self.assertEqual(response.status_code, 200)  # Form wird erneut angezeigt
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('employee', form.errors)
    
    def test_client_switch_only_shows_firma_clients_with_lohn_aktiv(self):
        """Test dass ClientSwitchView nur FIRMA-Clients mit aktiviertem Lohnmodul anzeigt."""
        from django.test import Client as TestClient
        from django.contrib.auth.models import User
        
        user = User.objects.create_user(username='testuser', password='testpass')
        test_client = TestClient()
        test_client.force_login(user)
        
        # Rufe Client-Switch-Seite auf
        response = test_client.get('/lohn/mandant/wechsel/')
        
        self.assertEqual(response.status_code, 200)
        clients = response.context['clients']
        # Nur FIRMA-Clients mit aktiviertem Lohnmodul sollten angezeigt werden
        self.assertEqual(clients.count(), 2)  # client_a und client_b
        self.assertIn(self.client_a, clients)
        self.assertIn(self.client_b, clients)
        self.assertNotIn(self.client_privat, clients)  # Privat-Client sollte NICHT erscheinen
        self.assertNotIn(self.client_firma_ohne_lohn, clients)  # FIRMA ohne Lohnmodul sollte NICHT erscheinen
    
    def test_privat_client_not_allowed_in_payroll(self):
        """Test dass Privat-Clients nicht in AdeaLohn verwendet werden können."""
        from django.test import Client as TestClient
        from django.contrib.auth.models import User
        
        user = User.objects.create_user(username='testuser', password='testpass')
        test_client = TestClient()
        test_client.force_login(user)
        
        # Versuche Privat-Client in Session zu setzen
        session = test_client.session
        session['active_client_id'] = self.client_privat.pk
        session.save()
        
        # Rufe Payroll-Liste auf (TenantMixin sollte Privat-Client entfernen)
        response = test_client.get('/lohn/payroll/')
        
        # Session sollte geleert sein (Privat-Client wurde entfernt)
        self.assertIsNone(test_client.session.get('active_client_id'))
        # current_client sollte None sein
        self.assertIsNone(response.context.get('current_client'))
    
    def test_firma_without_lohn_aktiv_not_allowed_in_payroll(self):
        """Test dass FIRMA-Clients ohne aktiviertes Lohnmodul nicht in AdeaLohn verwendet werden können."""
        from django.test import Client as TestClient
        from django.contrib.auth.models import User
        
        user = User.objects.create_user(username='testuser', password='testpass')
        test_client = TestClient()
        test_client.force_login(user)
        
        # Versuche FIRMA-Client ohne aktiviertes Lohnmodul in Session zu setzen
        session = test_client.session
        session['active_client_id'] = self.client_firma_ohne_lohn.pk
        session.save()
        
        # Rufe Payroll-Liste auf (TenantMixin sollte Client entfernen)
        response = test_client.get('/lohn/payroll/')
        
        # Session sollte geleert sein (Client ohne Lohnmodul wurde entfernt)
        self.assertIsNone(test_client.session.get('active_client_id'))
        # current_client sollte None sein
        self.assertIsNone(response.context.get('current_client'))


class DataIntegrityTestCase(TestCase):
    """Tests für Datenintegrität: PRIVAT-Clients dürfen keine Employees haben."""
    
    def setUp(self):
        self.client_firma = Client.objects.create(name="Firma", client_type="FIRMA", lohn_aktiv=True)
        self.client_privat = Client.objects.create(name="Privatperson", client_type="PRIVAT", lohn_aktiv=False)
        self.client_firma_ohne_lohn = Client.objects.create(name="Firma ohne Lohn", client_type="FIRMA", lohn_aktiv=False)
    
    def test_employee_cannot_be_created_with_privat_client(self):
        """Test dass Employee nicht mit PRIVAT-Client erstellt werden kann."""
        with self.assertRaises(ValidationError) as cm:
            employee = Employee(
                client=self.client_privat,
                first_name="Test",
                last_name="Employee",
            )
            employee.full_clean()
        
        # Prüfe Fehlermeldung
        self.assertIn('client', cm.exception.error_dict)
        error_msg = str(cm.exception.error_dict['client'][0])
        self.assertIn('Firmen-Mandanten', error_msg)
        self.assertIn('Privatperson', error_msg)
    
    def test_employee_can_be_created_with_firma_client_with_lohn_aktiv(self):
        """Test dass Employee mit FIRMA-Client mit aktiviertem Lohnmodul erstellt werden kann."""
        employee = Employee(
            client=self.client_firma,
            first_name="Test",
            last_name="Employee",
        )
        # Sollte keine ValidationError werfen
        employee.full_clean()
        employee.save()
        self.assertIsNotNone(employee.pk)
    
    def test_employee_cannot_be_created_with_firma_client_without_lohn_aktiv(self):
        """Test dass Employee nicht mit FIRMA-Client ohne aktiviertes Lohnmodul erstellt werden kann."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as cm:
            employee = Employee(
                client=self.client_firma_ohne_lohn,
                first_name="Test",
                last_name="Employee",
            )
            employee.full_clean()
        
        # Prüfe Fehlermeldung
        self.assertIn('client', cm.exception.error_dict)
        error_msg = str(cm.exception.error_dict['client'][0])
        self.assertIn('Lohnmodul', error_msg)
        self.assertIn('aktiviert', error_msg)
    
    def test_payroll_cannot_be_created_with_privat_employee(self):
        """Test dass PayrollRecord nicht mit Employee von PRIVAT-Client erstellt werden kann."""
        # Da Employee.clean() bereits verhindert, dass ein Employee mit PRIVAT-Client erstellt wird,
        # testen wir hier nur die PayrollRecord.clean() Validierung.
        # In der Praxis würde dieser Fall nicht auftreten, da Employee.clean() bereits greift.
        
        # Erstelle einen Employee mit FIRMA-Client (normaler Weg)
        employee_firma = Employee.objects.create(
            client=self.client_firma,
            first_name="Test",
            last_name="Firma",
        )
        
        # Ändere Client zu PRIVAT über direkten DB-Zugriff (simuliert Edge-Case)
        # In Realität würde Employee.clean() dies verhindern
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE adeacore_employee SET client_id = ? WHERE id = ?",
                [self.client_privat.pk, employee_firma.pk]
            )
        
        # Lade Employee neu
        employee_privat = Employee.objects.get(pk=employee_firma.pk)
        
        # Versuche PayrollRecord zu erstellen - sollte ValidationError werfen
        with self.assertRaises(ValidationError) as cm:
            payroll = PayrollRecord(
                employee=employee_privat,
                month=1,
                year=2025,
            )
            payroll.full_clean()
        
        # Prüfe Fehlermeldung
        self.assertIn('employee', cm.exception.error_dict)
        error_msg = str(cm.exception.error_dict['employee'][0])
        self.assertIn('Firmen', error_msg)
        self.assertIn('Privatperson', error_msg)
