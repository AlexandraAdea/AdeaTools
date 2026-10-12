from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from adeacore.models import Client, CompanyData, Invoice
from adearechnung import mahn_service, mahnlogik
from adearechnung.mahn_pdf import MahnungPDFGenerator
from adearechnung.mahnlogik import Rechnung, pruefe, schreiben
from adearechnung.models import Mahnung

TEST_IBAN = "CH93 0076 2011 6238 5295 7"  # Standard-Beispiel-IBAN, nicht die der Praxis


def re0099(**kw):
    basis = dict(nummer="RE-2026-0099", kunde="Beispiel Kunde",
                 rechnungsdatum=date(2026, 9, 10), faelligkeit=date(2026, 9, 25),
                 brutto=Decimal("324.30"))
    basis.update(kw)
    return Rechnung(**basis)


class MahnlogikTest(SimpleTestCase):
    def test_re_0099_am_12_10_ist_stufe_1(self):
        e = pruefe(re0099(), date(2026, 10, 12))
        self.assertEqual(e.aktion, "mahnen")
        self.assertEqual(e.stufe.nr, 1)
        self.assertEqual(e.tage_ueberfaellig, 17)
        self.assertEqual(e.zins_tage, 2)  # Zins ab 10.10.2026 (Rechnungsdatum + 30)
        self.assertEqual(e.zins, Decimal("0.09"))  # 324.30 * 5% * 2/365 = 0.0888
        self.assertEqual(e.gebuehren, Decimal("20.00"))
        self.assertEqual(e.total, Decimal("344.40"))  # 344.39 auf 5 Rappen
        self.assertEqual(e.zahlungsfrist, date(2026, 10, 22))

    def test_zins_ab_faelligkeit_konfigurierbar(self):
        cfg = mahnlogik.Config(zins_beginn="faelligkeit", zins_nach_tage=0)
        e = pruefe(re0099(), date(2026, 10, 12), cfg)
        self.assertEqual(e.zins_tage, 17)
        self.assertEqual(e.zins, Decimal("0.76"))  # 324.30 * 5% * 17/365 = 0.7552

    def test_mwst_auf_gebuehren_nicht_auf_zins(self):
        e = pruefe(re0099(), date(2026, 10, 12))
        self.assertEqual((e.gebuehren_netto, e.gebuehren_mwst), (Decimal("18.50"), Decimal("1.50")))
        self.assertEqual(e.offen + e.zins + e.gebuehren, Decimal("344.39"))
        e2 = pruefe(re0099(mahnungen=[(1, date(2026, 10, 12))]), date(2026, 10, 22))
        self.assertEqual((e2.gebuehren_netto, e2.gebuehren_mwst), (Decimal("37.00"), Decimal("3.00")))

    def test_ohne_mwst_pflicht_keine_mwst(self):
        cfg = mahnlogik.Config(mwst_satz=Decimal("0"))
        e = pruefe(re0099(), date(2026, 10, 12), cfg)
        self.assertEqual((e.gebuehren_netto, e.gebuehren_mwst), (Decimal("20.00"), Decimal("0.00")))
        self.assertNotIn("MWST", schreiben(e, cfg))

    def test_karenz_vor_stufe_1(self):
        self.assertIsNone(pruefe(re0099(), date(2026, 9, 29)))
        self.assertIsNotNone(pruefe(re0099(), date(2026, 9, 30)))

    def test_nicht_faellig_bezahlt_gesperrt(self):
        self.assertIsNone(pruefe(re0099(), date(2026, 9, 25)))
        self.assertIsNone(pruefe(re0099(bezahlt=Decimal("324.30")), date(2026, 10, 12)))
        self.assertIsNone(pruefe(re0099(mahnsperre=True), date(2026, 10, 12)))

    def test_teilzahlung_reduziert_basis(self):
        e = pruefe(re0099(bezahlt=Decimal("124.30")), date(2026, 10, 12))
        self.assertEqual(e.offen, Decimal("200.00"))

    def test_stufen_folge_und_betreibung(self):
        r = re0099(mahnungen=[(1, date(2026, 10, 12))])
        self.assertIsNone(pruefe(r, date(2026, 10, 21)))
        e = pruefe(r, date(2026, 10, 22))
        self.assertEqual((e.stufe.nr, e.gebuehren), (2, Decimal("40.00")))
        r3 = re0099(mahnungen=[(1, date(2026, 10, 12)), (2, date(2026, 10, 22)), (3, date(2026, 11, 1))])
        self.assertIsNone(pruefe(r3, date(2026, 11, 11)))
        e3 = pruefe(r3, date(2026, 11, 12))
        self.assertEqual((e3.aktion, e3.gebuehren), ("betreibung_pruefen", Decimal("60.00")))
        with self.assertRaises(ValueError):
            schreiben(e3)

    def test_text(self):
        t = schreiben(pruefe(re0099(), date(2026, 10, 12)))
        for erwartet in ("Zahlungserinnerung", "RE-2026-0099", "22.10.2026", "CHF 344.40", "MWST 8.1 %: CHF 1.50"):
            self.assertIn(erwartet, t)


class MahnwesenDatenbankTest(TestCase):
    def setUp(self):
        cd = CompanyData.get_instance()
        cd.mwst_pflichtig = True
        cd.mwst_satz = Decimal("8.10")
        cd.iban = TEST_IBAN
        cd.save()
        self.kunde = Client.objects.create(name="Testkunde AG", client_type="FIRMA")
        self.heute = date.today()
        self.inv = self._rechnung("RE-T-1", tage_alt=32, faellig_vor=17)

    def _rechnung(self, nummer, tage_alt, faellig_vor, **kw):
        return Invoice.objects.create(
            client=self.kunde, invoice_number=nummer,
            invoice_date=self.heute - timedelta(days=tage_alt),
            due_date=self.heute - timedelta(days=faellig_vor),
            amount=Decimal("324.30"), **kw)

    def test_vorschau_findet_nur_faellige_offene_rechnungen(self):
        self._rechnung("RE-T-bezahlt", 32, 17, paid_amount=Decimal("324.30"))
        # Invoice.save() berechnet den Status immer neu; STORNIERT wird daher per update() gesetzt.
        storno = self._rechnung("RE-T-storno", 32, 17)
        Invoice.objects.filter(pk=storno.pk).update(payment_status="STORNIERT")
        self._rechnung("RE-T-sperre", 32, 17, mahnsperre=True, mahnsperre_grund="Raten")
        self._rechnung("RE-T-nicht-faellig", 10, -5)
        self._rechnung("RE-T-karenz", 30, 3)  # erst 3 Tage überfällig
        e = mahn_service.vorschau(self.heute)
        self.assertEqual([x.rechnung.nummer for x in e], ["RE-T-1"])
        self.assertEqual(e[0].stufe.nr, 1)
        self.assertEqual(e[0].gebuehren_mwst, Decimal("1.50"))

    def test_lauf_speichert_und_ist_idempotent(self):
        erzeugt, _ = mahn_service.mahnlauf_ausfuehren(self.heute)
        self.assertEqual(len(erzeugt), 1)
        m = Mahnung.objects.get()
        self.assertEqual((m.invoice, m.stufe, m.datum), (self.inv, 1, self.heute))
        self.assertEqual(m.zahlungsfrist, self.heute + timedelta(days=10))
        self.assertEqual(m.gebuehren, Decimal("20.00"))
        self.assertEqual(m.gebuehren_mwst, Decimal("1.50"))
        erzeugt2, _ = mahn_service.mahnlauf_ausfuehren(self.heute)
        self.assertEqual(erzeugt2, [])
        self.assertEqual(Mahnung.objects.count(), 1)

    def test_stufe_2_nach_wartezeit(self):
        mahn_service.mahnlauf_ausfuehren(self.heute - timedelta(days=0))
        spaeter = self.heute + timedelta(days=10)
        e = mahn_service.vorschau(spaeter)
        self.assertEqual(e[0].stufe.nr, 2)

    def test_auswahl_begrenzt_lauf(self):
        zweite = self._rechnung("RE-T-2", 32, 17)
        erzeugt, _ = mahn_service.mahnlauf_ausfuehren(self.heute, nur_rechnungen=[zweite.pk])
        self.assertEqual([m.invoice for m in erzeugt], [zweite])

    def test_pdf_und_qr_mit_gesamtbetrag(self):
        mahn_service.mahnlauf_ausfuehren(self.heute)
        m = Mahnung.objects.get()
        gen = MahnungPDFGenerator()
        response = gen.generate_mahnung_pdf(m)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertIn("Stufe1", response["Content-Disposition"])
        from types import SimpleNamespace
        bill = gen._build_qr_bill(SimpleNamespace(amount=m.total, invoice_number="RE-T-1"), CompanyData.get_instance())
        self.assertEqual(bill.amount, str(m.total))
        self.assertEqual(bill.additional_information, "Mahnung RE-T-1")

    def test_mahnung_nutzt_kopf_und_fusszeile_der_rechnung(self):
        # Kopfzeile (_create_header) und Fusszeilenhinweis (_draw_footer_notice) werden
        # unverändert von InvoicePDFGenerator geerbt.
        from adearechnung.pdf_generator import InvoicePDFGenerator
        self.assertIs(MahnungPDFGenerator._draw_footer_notice, InvoicePDFGenerator._draw_footer_notice)
        self.assertIs(MahnungPDFGenerator._create_header, InvoicePDFGenerator._create_header)

    def test_befehl_trockenlauf_und_ausfuehren(self):
        out = StringIO()
        call_command("mahnlauf", "--stichtag", self.heute.isoformat(), stdout=out)
        self.assertIn("RE-T-1", out.getvalue())
        self.assertIn("Trockenlauf", out.getvalue())
        self.assertEqual(Mahnung.objects.count(), 0)
        call_command("mahnlauf", "--stichtag", self.heute.isoformat(), "--ausfuehren", stdout=StringIO())
        self.assertEqual(Mahnung.objects.count(), 1)


class MahnwesenViewsTest(TestCase):
    def setUp(self):
        cd = CompanyData.get_instance()
        cd.mwst_pflichtig, cd.mwst_satz, cd.iban = True, Decimal("8.10"), TEST_IBAN
        cd.save()
        kunde = Client.objects.create(name="Testkunde AG", client_type="FIRMA")
        self.heute = date.today()
        self.inv = Invoice.objects.create(
            client=kunde, invoice_number="RE-V-1", amount=Decimal("324.30"),
            invoice_date=self.heute - timedelta(days=32), due_date=self.heute - timedelta(days=17))
        User = get_user_model()
        self.user = User.objects.create_user(username="chefin", password="x", is_staff=True, is_superuser=True)
        self.client.force_login(self.user)
        self.url = reverse("adearechnung:mahnlauf")

    def test_login_erforderlich(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_vorschau_zeigt_faellige_rechnung(self):
        r = self.client.get(self.url, {"stichtag": self.heute.isoformat()})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "RE-V-1")
        self.assertContains(r, "Zahlungserinnerung")
        self.assertEqual(Mahnung.objects.count(), 0)

    def test_ungueltiger_stichtag_faellt_auf_heute_zurueck(self):
        self.assertEqual(self.client.get(self.url, {"stichtag": "kaputt"}).status_code, 200)

    def test_post_erzeugt_mahnung_und_pdf_ist_abrufbar(self):
        r = self.client.post(self.url, {"stichtag": self.heute.isoformat(), "rechnung": [self.inv.pk]})
        self.assertEqual(r.status_code, 302)
        m = Mahnung.objects.get()
        self.assertEqual(m.erstellt_von, self.user)
        pdf = self.client.get(reverse("adearechnung:mahnung-pdf", args=[m.pk]))
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_post_ohne_auswahl_oder_in_der_zukunft_erzeugt_nichts(self):
        self.client.post(self.url, {"stichtag": self.heute.isoformat()})
        zukunft = (self.heute + timedelta(days=1)).isoformat()
        self.client.post(self.url, {"stichtag": zukunft, "rechnung": [self.inv.pk]})
        self.assertEqual(Mahnung.objects.count(), 0)

    def test_mahnsperre_setzen_und_aufheben(self):
        url = reverse("adearechnung:invoice-mahnsperre", args=[self.inv.pk])
        self.client.post(url, {"grund": "Ratenzahlung vereinbart"})
        self.inv.refresh_from_db()
        self.assertTrue(self.inv.mahnsperre)
        self.assertEqual(self.inv.mahnsperre_grund, "Ratenzahlung vereinbart")
        self.assertEqual(mahn_service.vorschau(self.heute), [])
        self.client.post(url)
        self.inv.refresh_from_db()
        self.assertFalse(self.inv.mahnsperre)

    def test_als_versendet_markieren(self):
        mahn_service.mahnlauf_ausfuehren(self.heute)
        m = Mahnung.objects.get()
        self.client.post(reverse("adearechnung:mahnung-versendet", args=[m.pk]))
        m.refresh_from_db()
        self.assertEqual(m.versendet_am, date.today())

    def test_get_aendert_nichts(self):
        # Zustandsändernde Views akzeptieren nur POST
        url = reverse("adearechnung:invoice-mahnsperre", args=[self.inv.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
