"""
PDF-Generator für Rechnungen.
Verwendet ReportLab für professionelle PDF-Erstellung.
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus.flowables import HRFlowable
from decimal import Decimal
from django.http import HttpResponse
from io import BytesIO
import qrcode
from qrbill import QRBill
from adeacore.models import CompanyData
from django.db.models import Sum, Min, Max
from reportlab.lib.utils import simpleSplit


class InvoicePDFGenerator:
    """Generiert professionelle Rechnungs-PDFs."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Richtet benutzerdefinierte Styles ein."""
        # Überschrift
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1d1d1f'),
            spaceAfter=6,
            alignment=1,  # Center
        )
        
        # Unterüberschrift
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1d1d1f'),
            spaceAfter=6,
        )
        
        # Normaler Text
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1d1d1f'),
        )
    
    def generate_pdf(self, invoice):
        """
        Generiert PDF für eine Rechnung.
        
        Args:
            invoice: Invoice-Objekt
        
        Returns:
            HttpResponse mit PDF
        """
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20*mm,
            rightMargin=20*mm,
            topMargin=14*mm,
            bottomMargin=24*mm,
        )
        
        story = []
        
        # Firmendaten
        company_data = CompanyData.get_instance()
        
        # 1. Kopfzeile
        story.extend(self._create_header(company_data, invoice))
        story.append(Spacer(1, 6*mm))
        
        # 2. Rechnungsempfänger
        story.extend(self._create_client_info(invoice.client))
        story.append(Spacer(1, 6*mm))
        
        # 3. Rechnungsinformationen
        story.extend(self._create_invoice_info(invoice))
        story.append(Spacer(1, 6*mm))
        
        # 4. Rechnungspositionen
        story.extend(self._create_invoice_items(invoice))
        story.append(Spacer(1, 6*mm))
        
        # 5. Zusammenfassung
        story.extend(self._create_summary(invoice))
        story.append(Spacer(1, 6*mm))
        
        # 6. Schweizer QR-Zahlteil (A6-ähnlicher Abschnitt unten)
        if company_data.iban:
            story.extend(self._create_qr_payment_slip(invoice, company_data))
        
        # PDF erstellen
        doc.build(story, onFirstPage=self._draw_footer_notice, onLaterPages=self._draw_footer_notice)
        
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Rechnung_{invoice.invoice_number}.pdf"'
        
        return response
    
    def _create_header(self, company_data, invoice):
        """Erstellt Kopfzeile mit Firmendaten."""
        elements = []
        elements.append(Paragraph("Treuhanbüro Ivanova", self.title_style))
        elements.append(Spacer(1, 2 * mm))

        locations = list(company_data.locations.filter(is_active=True).order_by("sort_order", "id"))
        if not locations and (company_data.street or company_data.zipcode or company_data.city):
            fallback = {
                "name": "",
                "street": f"{company_data.street} {company_data.house_number}".strip(),
                "zip_city": f"{company_data.zipcode} {company_data.city}".strip(),
                "country": str(company_data.country or "").strip(),
            }
            locations = [fallback]

        location_cells = []
        for loc in locations:
            street = (
                f"{getattr(loc, 'street', '')} {getattr(loc, 'house_number', '')}".strip()
                if hasattr(loc, "street")
                else loc.get("street", "")
            )
            zip_city = (
                f"{getattr(loc, 'zipcode', '')} {getattr(loc, 'city', '')}".strip()
                if hasattr(loc, "zipcode")
                else loc.get("zip_city", "")
            )
            country = getattr(loc, "country", "") if hasattr(loc, "country") else loc.get("country", "")

            lines = []
            if street:
                lines.append(street)
            if zip_city:
                lines.append(zip_city)
            if country:
                lines.append(str(country))
            location_cells.append(Paragraph("<br/>".join(lines) if lines else "-", self.normal_style))

        right_lines = []
        if company_data.email:
            right_lines.append(f"E-Mail: {company_data.email}")
        if company_data.phone:
            right_lines.append(f"Telefon: {company_data.phone}")
        if company_data.mwst_nr:
            right_lines.append(f"MWST-Nr.: {company_data.mwst_nr}")
        right_text = "<br/>".join(right_lines)

        right_style = ParagraphStyle(
            "HeaderRight",
            parent=self.normal_style,
            alignment=2,
        )
        center_style = ParagraphStyle(
            "HeaderCenter",
            parent=self.normal_style,
            alignment=1,
        )
        # 3 gleichmässige Spalten: Standort links, Standort mitte, Kontakt rechts
        col1 = location_cells[0] if len(location_cells) > 0 else Paragraph("", self.normal_style)
        if len(location_cells) > 1:
            col2_text = location_cells[1].text
            col2 = Paragraph(col2_text, center_style)
        else:
            col2 = Paragraph("", center_style)
        col3 = Paragraph(right_text, right_style)

        header_table = Table(
            [[col1, col2, col3]],
            colWidths=[56.5 * mm, 56.5 * mm, 56.5 * mm],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elements.append(header_table)
        elements.append(Spacer(1, 3 * mm))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e5ea')))
        
        return elements
    
    def _create_client_info(self, client):
        """Erstellt Rechnungsempfänger-Informationen."""
        elements = []
        elements.append(Paragraph("<b>Rechnungsempfänger:</b>", self.heading_style))
        
        # Name
        elements.append(Paragraph(client.name, self.normal_style))
        elements.append(Spacer(1, 2*mm))
        
        # Adresse
        address_lines = []
        if client.street:
            address_lines.append(f"{client.street} {client.house_number}".strip())
        if client.zipcode or client.city:
            address_lines.append(f"{client.zipcode} {client.city}".strip())
        
        for line in address_lines:
            elements.append(Paragraph(line, self.normal_style))
        
        # MWST-Nummer (falls vorhanden)
        if client.mwst_nr:
            elements.append(Spacer(1, 2*mm))
            elements.append(Paragraph(f"MWST-Nr.: {client.mwst_nr}", self.normal_style))
        
        return elements
    
    def _create_invoice_info(self, invoice):
        """Erstellt Rechnungsinformationen."""
        elements = []

        data = [
            ['Rechnungsnummer:', invoice.invoice_number],
            ['Rechnungsdatum:', invoice.invoice_date.strftime('%d.%m.%Y')],
            ['Fälligkeitsdatum:', invoice.due_date.strftime('%d.%m.%Y')],
        ]
        
        table = Table(data, colWidths=[50*mm, 100*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6e6e73')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1d1d1f')),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_invoice_items(self, invoice):
        """Erstellt Tabelle mit Rechnungspositionen."""
        elements = []
        elements.append(Paragraph("<b>Leistungen:</b>", self.heading_style))
        elements.append(Spacer(1, 3*mm))
        
        data = [['Leistung', 'Zeitraum', 'Stunden', 'Stundensatz', 'Betrag']]

        grouped_items = (
            invoice.items.values(
                "time_entry__service_type__name",
                "service_type_code",
                "unit_price",
            )
            .annotate(
                stunden_total=Sum("quantity"),
                betrag_total=Sum("net_amount"),
                datum_von=Min("service_date"),
                datum_bis=Max("service_date"),
            )
            .order_by("time_entry__service_type__name")
        )

        for item in grouped_items:
            leistung = item.get("time_entry__service_type__name") or item.get("service_type_code") or "Leistung"

            if item.get("datum_von") and item.get("datum_bis"):
                zeitraum = f"{item['datum_von'].strftime('%d.%m.%Y')} - {item['datum_bis'].strftime('%d.%m.%Y')}"
            else:
                zeitraum = "–"

            data.append([
                leistung,
                zeitraum,
                f"{item['stunden_total']:.2f}",
                f"{item['unit_price']:.2f} CHF",
                f"{item['betrag_total']:.2f} CHF",
            ])
        
        table = Table(data, colWidths=[70*mm, 45*mm, 18*mm, 25*mm, 26*mm])
        table.setStyle(TableStyle([
            # Kopfzeile
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1d1d1f')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (4, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            # Datenzeilen
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1d1d1f')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e5ea')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_summary(self, invoice):
        """Erstellt Zusammenfassung mit Beträgen."""
        elements = []
        
        data = [
            ['Nettobetrag:', f"{invoice.net_amount:.2f} CHF"],
        ]
        
        data.append([f"MWST ({invoice.vat_rate}%):", f"{invoice.vat_amount:.2f} CHF"])
        data.append(["Gesamtbetrag:", f"{invoice.amount:.2f} CHF"])
        
        table = Table(data, colWidths=[100*mm, 50*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1d1d1f')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('LINEABOVE', (0, -1), (-1, -1), 0.8, colors.HexColor('#c7c7cc')),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_qr_payment_slip(self, invoice, company_data):
        """Erstellt einen Schweizer QR-Zahlteil für den unteren Rechnungsbereich."""
        elements = []

        qr_bill = self._build_qr_bill(invoice, company_data)
        if qr_bill is None:
            return elements

        qr_data = qr_bill.qr_data()
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        qr_image = Image(img_buffer, width=46 * mm, height=46 * mm)
        info_table = Table(
            [
                [Paragraph("<b>Zahlteil (Swiss QR)</b>", self.normal_style)],
                [Paragraph(f"Empfänger: {company_data.company_name}", self.normal_style)],
                [Paragraph(f"IBAN: {company_data.iban}", self.normal_style)],
                [Paragraph(f"Betrag: {invoice.amount:.2f} CHF", self.normal_style)],
                [Paragraph(f"Referenz: {invoice.invoice_number}", self.normal_style)],
            ],
            colWidths=[114 * mm],
        )
        info_table.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )

        slip = Table(
            [[qr_image, info_table]],
            colWidths=[50 * mm, 114 * mm],
            rowHeights=[55 * mm],
        )
        slip.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#bdbdbd")),
                    ("LINEBEFORE", (1, 0), (1, 0), 0.6, colors.HexColor("#d0d0d0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        elements.append(Spacer(1, 4 * mm))
        elements.append(slip)
        return elements

    def _build_qr_bill(self, invoice, company_data):
        """Erstellt ein QRBill-Objekt für CH-Zahlungen."""
        iban = (str(company_data.iban or "").replace(" ", "")).strip()
        if not iban:
            return None

        creditor_name = str(company_data.company_name or "").strip() or "Adea Treuhand"
        creditor_street = str(company_data.street or "").strip() or "Unbekannt"
        creditor_house_num = str(company_data.house_number or "").strip() or ""
        creditor_zip = str(company_data.zipcode or "").strip() or "0000"
        creditor_city = str(company_data.city or "").strip() or "Unbekannt"
        creditor_country = "CH"

        return QRBill(
            account=iban,
            creditor={
                "name": creditor_name,
                "street": creditor_street,
                "house_num": creditor_house_num,
                "pcode": creditor_zip,
                "city": creditor_city,
                "country": creditor_country,
            },
            amount=Decimal(str(invoice.amount)).quantize(Decimal("0.01")),
            currency="CHF",
            additional_information=f"Rechnung {invoice.invoice_number}",
        )

    def _draw_footer_notice(self, canvas, doc):
        """Zeichnet den rechtlichen Hinweis als Footer ohne Seitenumbruch im Story-Flow."""
        text = (
            "Bei Zahlungsverzug behalten wir uns vor, ab dem 30. Tag einen Verzugszins von 5 % p.a. "
            "gemäss Art. 104 OR sowie eine Mahngebühr von CHF 20.– pro Mahnstufe zu erheben."
        )
        canvas.saveState()
        font_name = "Helvetica"
        font_size = 7
        line_height = 3.2 * mm
        canvas.setFont(font_name, font_size)
        canvas.setFillColor(colors.HexColor("#6e6e73"))
        max_width = A4[0] - doc.leftMargin - doc.rightMargin
        lines = simpleSplit(text, font_name, font_size, max_width)[:2]
        text_obj = canvas.beginText()
        text_obj.setTextOrigin(doc.leftMargin, 12 * mm)
        text_obj.setLeading(line_height)
        text_obj.setFont(font_name, font_size)
        for line in lines:
            text_obj.textLine(line)
        canvas.drawText(text_obj)
        canvas.restoreState()
