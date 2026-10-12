"""PDF der Mahnung (gleicher Briefkopf, gleiche QR-Rechnung wie die Rechnung)."""
from dataclasses import replace
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from adeacore.models import CompanyData

from . import mahnlogik
from .mahn_service import config_aus_firmendaten
from .pdf_generator import InvoicePDFGenerator


class MahnungPDFGenerator(InvoicePDFGenerator):
    """Erzeugt das Mahnschreiben aus den gespeicherten Beträgen einer ``Mahnung``."""

    def _build_qr_bill(self, invoice, company_data):
        bill = super()._build_qr_bill(invoice, company_data)
        if bill is not None:
            bill.additional_information = f"Mahnung {invoice.invoice_number}"
        return bill

    def generate_mahnung_pdf(self, mahnung):
        inv = mahnung.invoice
        cd = CompanyData.get_instance()
        cfg = config_aus_firmendaten()
        if mahnung.gebuehren_mwst <= 0:
            cfg = replace(cfg, mwst_satz=Decimal("0"))

        stufe = next((s for s in cfg.stufen if s.nr == mahnung.stufe), None)
        if stufe is None:
            raise ValueError(f"Unbekannte Mahnstufe {mahnung.stufe}")

        einleitung, schluss = mahnlogik.stufentexte(
            stufe, inv.invoice_number, inv.invoice_date, inv.due_date, mahnung.zahlungsfrist)
        zeilen = mahnlogik.betragszeilen(
            nummer=inv.invoice_number, rechnungsdatum=inv.invoice_date, faelligkeit=inv.due_date,
            offen=mahnung.offener_betrag, zins=mahnung.verzugszins, zins_tage=mahnung.zins_tage,
            zins_ab=mahnlogik.zins_beginn_datum(inv.invoice_date, inv.due_date, cfg),
            gebuehren=mahnung.gebuehren, gebuehren_mwst=mahnung.gebuehren_mwst,
            total=mahnung.total, stufe_nr=stufe.nr, cfg=cfg)

        right = ParagraphStyle("MahnRight", parent=self.normal_style, alignment=2)
        titel = ParagraphStyle("MahnTitel", parent=self.heading_style, fontSize=14, spaceAfter=4)

        story = []
        story.extend(self._create_header(cd, inv))
        story.extend(self._create_client_info(inv.client))
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph(f"Datum: {mahnlogik.d(mahnung.datum)}", right))
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(f"{stufe.name}: Rechnung {inv.invoice_number}", titel))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("Guten Tag", self.normal_style))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(einleitung, self.normal_style))
        story.append(Spacer(1, 5 * mm))

        letzte = len(zeilen) - 1
        zellen = []
        for i, (label, betrag) in enumerate(zeilen):
            if i == letzte:  # Total fett (Paragraph-Zellen ignorieren FONTNAME der Tabelle)
                label, betrag = f"<b>{label}</b>", f"<b>{betrag}</b>"
            zellen.append([Paragraph(label, self.normal_style), Paragraph(betrag, right)])
        tabelle = Table(zellen, colWidths=[126 * mm, 40 * mm])
        tabelle.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LINEABOVE", (0, letzte), (-1, letzte), 0.8, colors.HexColor("#1d1d1f")),
        ]))
        story.append(tabelle)
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph(schluss, self.normal_style))
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph(f"Freundliche Grüsse<br/>{cfg.firma}", self.normal_style))

        if cd.iban:
            # QR-Zahlteil mit dem Gesamtbetrag der Mahnung
            zahlung = SimpleNamespace(amount=mahnung.total, invoice_number=inv.invoice_number)
            story.extend(self._create_qr_payment_slip(zahlung, cd))

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                                topMargin=14 * mm, bottomMargin=24 * mm)
        doc.build(story, onFirstPage=self._draw_footer_notice, onLaterPages=self._draw_footer_notice)

        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="Mahnung_{inv.invoice_number}_Stufe{mahnung.stufe}.pdf"')
        return response
