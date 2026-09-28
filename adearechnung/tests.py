from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase

from adeacore.models import Client, CompanyData, Invoice, InvoiceItem, AkontoPlan
from adeazeit.models import EmployeeInternal, ServiceType, TimeEntry
from adearechnung.services import InvoiceService


class InvoiceFromTimeEntriesRegressionTest(TestCase):
    """
    Regressionstest für die bestehende Rechnungserstellung aus Zeiteinträgen.
    Stellt sicher, dass die Akonto-Erweiterung (neue Felder invoice_type /
    akonto_plan auf Invoice) das bisherige Verhalten nicht verändert hat.
    """

    def setUp(self):
        self.client_obj = Client.objects.create(name="Regressions Client", client_type="FIRMA")
        self.employee = EmployeeInternal.objects.create(
            code="EMP-REG",
            name="Test Mitarbeiterin",
            function_title="Consultant",
            employment_percent=Decimal('100.00'),
            weekly_soll_hours=Decimal('42.00'),
            weekly_working_days=Decimal('5.0'),
            work_canton="ZH",
            eintrittsdatum=date(2020, 1, 1),
            aktiv=True,
        )
        self.service_type = ServiceType.objects.create(
            code="BUCH",
            name="Buchhaltung",
            standard_rate=Decimal('150.00'),
            billable=True,
        )
        company_data = CompanyData.get_instance()
        company_data.mwst_pflichtig = True
        company_data.mwst_satz = Decimal('8.10')
        company_data.save()

        self.time_entry = TimeEntry.objects.create(
            mitarbeiter=self.employee,
            client=self.client_obj,
            datum=date(2026, 1, 10),
            dauer=Decimal('5.00'),
            service_type=self.service_type,
            rate=Decimal('150.00'),
            betrag=Decimal('750.00'),
            billable=True,
        )

    def test_create_invoice_from_time_entries_unchanged(self):
        invoice = InvoiceService.create_invoice_from_time_entries(
            time_entry_ids=[self.time_entry.id],
            client=self.client_obj,
        )

        self.assertEqual(invoice.net_amount, Decimal('750.00'))
        self.assertEqual(invoice.vat_rate, Decimal('8.10'))
        self.assertEqual(invoice.vat_amount, Decimal('60.75'))
        self.assertEqual(invoice.amount, Decimal('810.75'))

        # Neue Felder dürfen das bestehende Verhalten nicht verändern:
        self.assertEqual(invoice.invoice_type, "NORMAL")
        self.assertIsNone(invoice.akonto_plan)

        self.time_entry.refresh_from_db()
        self.assertTrue(self.time_entry.verrechnet)

    def test_invoice_number_format_unchanged(self):
        invoice = InvoiceService.create_invoice_from_time_entries(
            time_entry_ids=[self.time_entry.id],
            client=self.client_obj,
        )
        year = date.today().year
        self.assertTrue(invoice.invoice_number.startswith(f"RE-{year}-"))


class AkontoInvoiceTest(TestCase):
    """Tests für die neue Akonto-Rechnungsfunktion."""

    def setUp(self):
        self.client_obj = Client.objects.create(name="Akonto Client", client_type="FIRMA")
        self.company_data = CompanyData.get_instance()
        self.company_data.mwst_pflichtig = True
        self.company_data.mwst_satz = Decimal('8.10')
        self.company_data.save()

        self.plan = AkontoPlan.objects.create(
            client=self.client_obj,
            amount=Decimal('500.00'),
            interval="QUARTALSWEISE",
            start_date=date(2026, 1, 1),
            active=True,
        )

    def test_create_akonto_invoice_basic(self):
        invoice = InvoiceService.create_akonto_invoice(self.plan)

        self.assertEqual(invoice.invoice_type, "AKONTO")
        self.assertEqual(invoice.akonto_plan, self.plan)
        self.assertEqual(invoice.client, self.client_obj)
        self.assertEqual(invoice.net_amount, Decimal('500.00'))
        self.assertEqual(invoice.vat_amount, Decimal('40.50'))
        self.assertEqual(invoice.amount, Decimal('540.50'))
        self.assertEqual(invoice.items.count(), 1)

        item = invoice.items.first()
        self.assertEqual(item.pricing_type, "FIXED")
        self.assertEqual(item.item_source, "MANUAL")
        self.assertEqual(item.net_amount, Decimal('500.00'))

    def test_create_akonto_invoice_not_vat_liable(self):
        self.company_data.mwst_pflichtig = False
        self.company_data.save()

        invoice = InvoiceService.create_akonto_invoice(self.plan)

        self.assertEqual(invoice.vat_amount, Decimal('0.00'))
        self.assertEqual(invoice.amount, invoice.net_amount)

    def test_create_akonto_invoice_uses_normal_invoice_numbering(self):
        """Akonto-Rechnungen teilen sich die Nummerierung mit normalen Rechnungen."""
        first = InvoiceService.create_akonto_invoice(self.plan)
        second = InvoiceService.create_akonto_invoice(self.plan)
        self.assertNotEqual(first.invoice_number, second.invoice_number)

    def test_existing_invoices_default_to_normal_type(self):
        """Rein additive Migration: bestehende Rechnungen ohne invoice_type-Angabe sind NORMAL."""
        invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="RE-2025-9999",
            invoice_date=date(2025, 1, 1),
            due_date=date(2025, 1, 16),
            amount=Decimal('100.00'),
            net_amount=Decimal('92.51'),
            vat_amount=Decimal('7.49'),
            vat_rate=Decimal('8.10'),
        )
        self.assertEqual(invoice.invoice_type, "NORMAL")
        self.assertIsNone(invoice.akonto_plan)


class AkontoDeductionTest(TestCase):
    """Tests für den Akonto-Abzug auf der Schlussrechnung."""

    def setUp(self):
        self.client_obj = Client.objects.create(name="Schluss Client", client_type="FIRMA")
        self.other_client = Client.objects.create(name="Anderer Client", client_type="FIRMA")
        self.company_data = CompanyData.get_instance()
        self.company_data.mwst_pflichtig = True
        self.company_data.mwst_satz = Decimal('8.10')
        self.company_data.save()

        self.plan = AkontoPlan.objects.create(
            client=self.client_obj,
            amount=Decimal('500.00'),
            interval="JAEHRLICH",
            start_date=date(2026, 1, 1),
            active=True,
        )
        self.akonto_invoice = InvoiceService.create_akonto_invoice(self.plan)

        # Schlussrechnung mit einer manuellen Position über 1200 CHF netto.
        self.final_invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="RE-2026-0100",
            invoice_date=date(2026, 12, 31),
            due_date=date(2027, 1, 15),
            amount=Decimal('0.00'),
            net_amount=Decimal('0.00'),
            vat_amount=Decimal('0.00'),
            vat_rate=Decimal('8.10'),
        )
        InvoiceItem.objects.create(
            invoice=self.final_invoice,
            title="Jahresarbeit",
            description="Jahresarbeit 2026",
            service_date=date(2026, 12, 31),
            item_source="MANUAL",
            pricing_type="FIXED",
            quantity=Decimal('1.00'),
            unit_price=Decimal('1200.00'),
            net_amount=Decimal('1200.00'),
            vat_rate=Decimal('8.10'),
            vat_amount=Decimal('97.20'),
            gross_amount=Decimal('1297.20'),
        )
        self.final_invoice.recalculate_amounts_from_items()
        self.final_invoice.save()

    def test_add_akonto_deduction_reduces_totals(self):
        self.assertEqual(self.final_invoice.net_amount, Decimal('1200.00'))

        InvoiceService.add_akonto_deduction(self.final_invoice, self.akonto_invoice)
        self.final_invoice.refresh_from_db()

        self.assertEqual(self.final_invoice.items.count(), 2)
        self.assertEqual(self.final_invoice.net_amount, Decimal('700.00'))
        self.assertEqual(self.final_invoice.vat_amount, Decimal('56.70'))
        self.assertEqual(self.final_invoice.amount, Decimal('756.70'))

    def test_add_akonto_deduction_rejects_wrong_client(self):
        other_plan = AkontoPlan.objects.create(
            client=self.other_client,
            amount=Decimal('300.00'),
            interval="MONATLICH",
            start_date=date(2026, 1, 1),
            active=True,
        )
        other_akonto_invoice = InvoiceService.create_akonto_invoice(other_plan)

        with self.assertRaises(ValueError):
            InvoiceService.add_akonto_deduction(self.final_invoice, other_akonto_invoice)

    def test_add_akonto_deduction_rejects_non_akonto_invoice(self):
        normal_invoice = Invoice.objects.create(
            client=self.client_obj,
            invoice_number="RE-2026-0200",
            invoice_date=date(2026, 6, 1),
            due_date=date(2026, 6, 16),
            amount=Decimal('100.00'),
            net_amount=Decimal('92.51'),
            vat_amount=Decimal('7.49'),
            vat_rate=Decimal('8.10'),
        )

        with self.assertRaises(ValueError):
            InvoiceService.add_akonto_deduction(self.final_invoice, normal_invoice)
