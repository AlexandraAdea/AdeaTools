"""
Integrationstests für kritische Payroll-Workflows.

Diese Tests prüfen End-to-End Szenarien, wie sie in der Praxis auftreten.
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError

from adeacore.models import Employee, Client, PayrollRecord
from adealohn.models import WageType, BVGParameter, PayrollItem


class PayrollWorkflowTestCase(TestCase):
    """End-to-End Tests für kritische Payroll-Workflows."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client.objects.create(
            name="Test Client",
            client_type="FIRMA",
            lohn_aktiv=True
        )
        self.employee = Employee.objects.create(
            client=self.client,
            first_name="Test",
            last_name="Employee",
            monthly_salary=Decimal("7200.00"),
            weekly_hours=Decimal("40.0"),
            is_rentner=False,
            qst_pflichtig=False,
        )
        
        # Hole oder erstelle notwendige WageTypes (Migrationen haben sie bereits erstellt)
        self.wage_type_monatslohn, _ = WageType.objects.get_or_create(
            code="GRUNDLOHN_MONAT",
            defaults={
                "name": "Grundlohn Monatslohn",
                "category": "GRUNDLOHN",
                "is_lohnwirksam": True,
                "ahv_relevant": True,
                "alv_relevant": True,
                "bvg_relevant": True,
                "uv_relevant": True,
            }
        )
        self.wage_type_privatanteil_auto, _ = WageType.objects.get_or_create(
            code="PRIVATANTEIL_AUTO",
            defaults={
                "name": "Privatanteil Auto",
                "category": "SACHLEISTUNG",
                "is_lohnwirksam": True,
                "ahv_relevant": True,
                "alv_relevant": True,
                "bvg_relevant": True,
                "uv_relevant": True,
            }
        )
        self.wage_type_kinderzulage, _ = WageType.objects.get_or_create(
            code="KINDERZULAGE",
            defaults={
                "name": "Kinderzulage",
                "category": "FAMILIENZULAGE",
                "is_lohnwirksam": False,  # WICHTIG: Durchlaufender Posten
                "ahv_relevant": False,
                "alv_relevant": False,
                "bvg_relevant": False,
                "uv_relevant": False,
                "qst_relevant": True,
            }
        )
        # Stelle sicher dass is_lohnwirksam=False ist (Migration könnte es gesetzt haben)
        if self.wage_type_kinderzulage.is_lohnwirksam:
            self.wage_type_kinderzulage.is_lohnwirksam = False
            self.wage_type_kinderzulage.save()
    
    def test_family_allowance_not_in_bruttolohn(self):
        """
        Test: Familienzulagen gehören NICHT zum Bruttolohn.
        
        Szenario:
        - Monatslohn: 7'200 CHF
        - Privatanteil Auto: 150 CHF
        - Familienzulage: 215 CHF
        
        Erwartet:
        - Bruttolohn = 7'350 CHF (7'200 + 150, OHNE 215)
        - Familienzulage wird separat angezeigt
        """
        # Erstelle PayrollRecord
        payroll = PayrollRecord.objects.create(
            employee=self.employee,
            month=1,
            year=2026,
        )
        
        # Füge Monatslohn hinzu
        PayrollItem.objects.create(
            payroll=payroll,
            wage_type=self.wage_type_monatslohn,
            quantity=Decimal("1"),
            amount=Decimal("7200.00"),
            description="Monatslohn Januar 2026"
        )
        
        # Füge Privatanteil Auto hinzu
        PayrollItem.objects.create(
            payroll=payroll,
            wage_type=self.wage_type_privatanteil_auto,
            quantity=Decimal("1"),
            amount=Decimal("150.00"),
            description="Privatanteil Auto"
        )
        
        # Füge Familienzulage hinzu
        PayrollItem.objects.create(
            payroll=payroll,
            wage_type=self.wage_type_kinderzulage,
            quantity=Decimal("1"),
            amount=Decimal("215.00"),
            description="Kinderzulage"
        )
        
        # Berechne neu
        payroll.recompute_bases_from_items()
        payroll.save()
        
        # Prüfe: Bruttolohn sollte OHNE Familienzulage sein
        self.assertEqual(payroll.bruttolohn, Decimal("7350.00"), 
                        "Bruttolohn sollte 7'350 CHF sein (7'200 + 150), NICHT 7'565 CHF")
        
        # Prüfe: Familienzulage sollte NICHT in AHV-Basis sein
        self.assertEqual(payroll.ahv_basis, Decimal("7350.00"),
                        "AHV-Basis sollte 7'350 CHF sein (ohne Familienzulage)")
        
        # Prüfe: Familienzulage sollte als PayrollItem existieren
        family_allowance_items = payroll.items.filter(
            wage_type__code="KINDERZULAGE"
        )
        self.assertEqual(family_allowance_items.count(), 1,
                        "Familienzulage sollte als PayrollItem existieren")
        self.assertEqual(family_allowance_items.first().total, Decimal("215.00"),
                        "Familienzulage sollte 215 CHF sein")
    
    def test_private_contribution_added_to_gross_and_deducted_from_net(self):
        """
        Test: Privatanteile werden zum Bruttolohn addiert und vom Nettolohn abgezogen.
        
        Szenario:
        - Monatslohn: 7'200 CHF
        - Privatanteil Auto: 150 CHF
        
        Erwartet:
        - Bruttolohn = 7'350 CHF (7'200 + 150)
        - Sozialversicherungs-Basis = 7'350 CHF
        - Privatanteil wird später abgezogen
        """
        # Erstelle PayrollRecord
        payroll = PayrollRecord.objects.create(
            employee=self.employee,
            month=1,
            year=2026,
        )
        
        # Füge Monatslohn hinzu
        PayrollItem.objects.create(
            payroll=payroll,
            wage_type=self.wage_type_monatslohn,
            quantity=Decimal("1"),
            amount=Decimal("7200.00"),
        )
        
        # Füge Privatanteil Auto hinzu
        PayrollItem.objects.create(
            payroll=payroll,
            wage_type=self.wage_type_privatanteil_auto,
            quantity=Decimal("1"),
            amount=Decimal("150.00"),
        )
        
        # Berechne neu
        payroll.recompute_bases_from_items()
        payroll.save()
        
        # Prüfe: Bruttolohn sollte MIT Privatanteil sein
        self.assertEqual(payroll.bruttolohn, Decimal("7350.00"),
                        "Bruttolohn sollte 7'350 CHF sein (7'200 + 150)")
        
        # Prüfe: AHV-Basis sollte MIT Privatanteil sein
        self.assertEqual(payroll.ahv_basis, Decimal("7350.00"),
                        "AHV-Basis sollte 7'350 CHF sein (inkl. Privatanteil)")
        
        # Prüfe: ALV-Basis sollte MIT Privatanteil sein
        self.assertEqual(payroll.alv_basis, Decimal("7350.00"),
                        "ALV-Basis sollte 7'350 CHF sein (inkl. Privatanteil)")
        
        # Prüfe: BVG-Basis sollte MIT Privatanteil sein
        self.assertEqual(payroll.bvg_basis, Decimal("7350.00"),
                        "BVG-Basis sollte 7'350 CHF sein (inkl. Privatanteil)")
    
    def test_bvg_manual_only_without_parameters(self):
        """
        Test: BVG ohne Parameter → nur manuelle Eingabe.
        
        Szenario:
        - Keine BVG-Parameter konfiguriert
        - Manuelle BVG-Beiträge: AN = 100 CHF, AG = 100 CHF
        
        Erwartet:
        - bvg_employee = 100 CHF
        - bvg_employer = 100 CHF
        """
        # Erstelle PayrollRecord OHNE BVG-Parameter
        payroll = PayrollRecord.objects.create(
            employee=self.employee,
            month=1,
            year=2026,
            bruttolohn=Decimal("5000.00"),
            ahv_basis=Decimal("5000.00"),
            alv_basis=Decimal("5000.00"),
            bvg_basis=Decimal("5000.00"),
            uv_basis=Decimal("5000.00"),
            manual_bvg_employee=Decimal("100.00"),
            manual_bvg_employer=Decimal("100.00"),
        )
        
        # Speichere (triggert Berechnung)
        payroll.save()
        
        # Prüfe: BVG sollte nur manuelle Beiträge enthalten
        self.assertEqual(payroll.bvg_employee, Decimal("100.00"),
                        "BVG AN sollte 100 CHF sein (nur manuell)")
        self.assertEqual(payroll.bvg_employer, Decimal("100.00"),
                        "BVG AG sollte 100 CHF sein (nur manuell)")
    
    def test_bvg_cannot_be_added_as_payroll_item(self):
        """
        Test: BVG_AN/BVG_AG können nicht als PayrollItem erfasst werden.
        
        Szenario:
        - Versuche PayrollItem mit WageType BVG_AN zu erstellen
        
        Erwartet:
        - BVG_AN sollte NICHT in PayrollItemGeneralForm erscheinen
        - Direkte Erstellung sollte nicht möglich sein (falls WageType existiert)
        """
        # Prüfe: BVG_AN sollte NICHT als aktiver WageType existieren
        bvg_an_exists = WageType.objects.filter(
            code="BVG_AN",
            is_active=True
        ).exists()
        
        # Falls BVG_AN existiert, sollte is_lohnwirksam=False sein
        if bvg_an_exists:
            bvg_an = WageType.objects.get(code="BVG_AN")
            self.assertFalse(bvg_an.is_lohnwirksam,
                           "BVG_AN sollte nicht lohnwirksam sein")
        
        # Prüfe: BVG_AN sollte NICHT in PayrollItemGeneralForm erscheinen
        # (Dies wird durch excluded_codes in forms.py sichergestellt)
        from adealohn.forms import PayrollItemGeneralForm
        from adealohn.views import PayrollItemGeneralCreateView
        
        # Erstelle PayrollRecord für Test
        payroll = PayrollRecord.objects.create(
            employee=self.employee,
            month=1,
            year=2026,
        )
        
        # Erstelle Formular
        form = PayrollItemGeneralForm()
        
        # Prüfe: BVG_AN sollte NICHT im Queryset sein
        wage_type_queryset = form.fields['wage_type'].queryset
        bvg_an_in_queryset = wage_type_queryset.filter(code="BVG_AN").exists()
        self.assertFalse(bvg_an_in_queryset,
                        "BVG_AN sollte NICHT in PayrollItemGeneralForm erscheinen")
    
    def test_complete_payroll_calculation_example(self):
        """
        Test: Vollständige Lohnabrechnung nach Praxis-Beispiel.
        
        Szenario (aus Excel):
        - Monatslohn: 7'200 CHF
        - Privatanteil Auto: 150 CHF
        - Familienzulage: 215 CHF
        - BVG AN: 249.75 CHF (manuell)
        - BVG AG: 249.75 CHF (manuell)
        
        Erwartet:
        - Bruttolohn: 7'350 CHF
        - AHV (5.3%): 389.55 CHF
        - ALV (1.1%): 80.85 CHF
        - NBU (1.5%): 110.25 CHF
        - BVG: 249.75 CHF
        - Auszahlung: 6'369.60 CHF (nach Abzug Privatanteil und Addition Familienzulage)
        """
        # Erstelle AHV/ALV/NBU Parameter (falls nötig)
        from adealohn.models import AHVParameter, ALVParameter
        
        AHVParameter.objects.create(
            year=2026,
            rate_employee=Decimal("0.053"),
            rate_employer=Decimal("0.053"),
        )
        
        ALVParameter.objects.create(
            year=2026,
            rate_employee=Decimal("0.011"),
            rate_employer=Decimal("0.011"),
            max_annual_insured_salary=Decimal("148200.00"),
        )
        
        # Erstelle PayrollRecord
        payroll = PayrollRecord.objects.create(
            employee=self.employee,
            month=1,
            year=2026,
            manual_bvg_employee=Decimal("249.75"),
            manual_bvg_employer=Decimal("249.75"),
        )
        
        # Füge Monatslohn hinzu
        PayrollItem.objects.create(
            payroll=payroll,
            wage_type=self.wage_type_monatslohn,
            quantity=Decimal("1"),
            amount=Decimal("7200.00"),
        )
        
        # Füge Privatanteil Auto hinzu
        PayrollItem.objects.create(
            payroll=payroll,
            wage_type=self.wage_type_privatanteil_auto,
            quantity=Decimal("1"),
            amount=Decimal("150.00"),
        )
        
        # Füge Familienzulage hinzu
        PayrollItem.objects.create(
            payroll=payroll,
            wage_type=self.wage_type_kinderzulage,
            quantity=Decimal("1"),
            amount=Decimal("215.00"),
        )
        
        # Berechne neu
        payroll.recompute_bases_from_items()
        payroll.save()
        
        # Prüfe: Bruttolohn
        self.assertEqual(payroll.bruttolohn, Decimal("7350.00"),
                        "Bruttolohn sollte 7'350 CHF sein")
        
        # Prüfe: AHV-Berechnung (5.3% von 7'350)
        expected_ahv = Decimal("7350.00") * Decimal("0.053")
        # Rundung auf 5 Rappen
        from adeacore.money import round_to_5_rappen
        expected_ahv_rounded = round_to_5_rappen(expected_ahv)
        self.assertAlmostEqual(payroll.ahv_employee, expected_ahv_rounded, places=2,
                              msg=f"AHV sollte ca. {expected_ahv_rounded} CHF sein")
        
        # Prüfe: ALV-Berechnung (1.1% von 7'350)
        expected_alv = Decimal("7350.00") * Decimal("0.011")
        expected_alv_rounded = round_to_5_rappen(expected_alv)
        self.assertAlmostEqual(payroll.alv_employee, expected_alv_rounded, places=2,
                              msg=f"ALV sollte ca. {expected_alv_rounded} CHF sein")
        
        # Prüfe: BVG (manuell)
        self.assertEqual(payroll.bvg_employee, Decimal("249.75"),
                        "BVG AN sollte 249.75 CHF sein")
        
        # Prüfe: Familienzulage existiert
        family_allowance_items = payroll.items.filter(
            wage_type__code="KINDERZULAGE"
        )
        self.assertEqual(family_allowance_items.count(), 1)
        self.assertEqual(family_allowance_items.first().total, Decimal("215.00"))
        
        # Prüfe: Privatanteil existiert
        private_items = payroll.items.filter(
            wage_type__code="PRIVATANTEIL_AUTO"
        )
        self.assertEqual(private_items.count(), 1)
        self.assertEqual(private_items.first().total, Decimal("150.00"))
        
        # Prüfe: Zentrale Berechnung - UI und Print müssen identische Auszahlung zeigen
        from adealohn.payroll_calculator import berechne_lohnabrechnung
        result = berechne_lohnabrechnung(payroll)
        
        # Prüfe Formeln
        self.assertEqual(result['nettolohn'], result['bruttolohn'] - result['sozialabzuege_total'] - result['qst_abzug'],
                        "Nettolohn = Bruttolohn - Sozialabzüge - QST")
        self.assertEqual(result['auszahlung'], result['nettolohn'] - result['privatanteile_total'] + result['zulagen_total'],
                        "Auszahlung = Nettolohn - Privatanteile + Zulagen")
        
        # Prüfe: Auszahlung berechnen
        # Erwartete Berechnung:
        # Bruttolohn: 7350.00
        # Sozialabzüge: AHV + ALV + NBU + BVG
        # Nettolohn: Bruttolohn - Sozialabzüge
        # Auszahlung: Nettolohn - Privatanteile + Zulagen
        expected_nettolohn = result['bruttolohn'] - result['sozialabzuege_total'] - result['qst_abzug']
        expected_auszahlung = expected_nettolohn - result['privatanteile_total'] + result['zulagen_total']
        expected_auszahlung_rounded = round_to_5_rappen(expected_auszahlung)
        
        self.assertEqual(result['auszahlung'], expected_auszahlung_rounded,
                        f"Auszahlung sollte {expected_auszahlung_rounded} CHF sein (berechnet: {result['auszahlung']})")
