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
from reportlab.pdfgen import canvas
from decimal import Decimal
from datetime import date
from django.http import HttpResponse
from io import BytesIO
import qrcode
from adeacore.models import CompanyData


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
            spaceAfter=12,
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
            topMargin=20*mm,
            bottomMargin=20*mm,
        )
        
        story = []
        
        # Firmendaten
        company_data = CompanyData.get_instance()
        
        # 1. Kopfzeile
        story.extend(self._create_header(company_data, invoice))
        story.append(Spacer(1, 10*mm))
        
        # 2. Rechnungsempfänger
        story.extend(self._create_client_info(invoice.client))
        story.append(Spacer(1, 10*mm))
        
        # 3. Rechnungsinformationen
        story.extend(self._create_invoice_info(invoice))
        story.append(Spacer(1, 10*mm))
        
        # 4. Rechnungspositionen
        story.extend(self._create_invoice_items(invoice))
        story.append(Spacer(1, 10*mm))
        
        # 5. Zusammenfassung
        story.extend(self._create_summary(invoice))
        story.append(Spacer(1, 10*mm))
        
        # 6. QR-Code (falls IBAN vorhanden)
        if company_data.iban:
            story.extend(self._create_qr_code(invoice, company_data))
        
        # PDF erstellen
        doc.build(story)
        
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Rechnung_{invoice.invoice_number}.pdf"'
        
        return response
    
    def _create_header(self, company_data, invoice):
        """Erstellt Kopfzeile mit Firmendaten."""
        elements = []
        
        # Firmenname
        elements.append(Paragraph(company_data.company_name, self.title_style))
        elements.append(Spacer(1, 3*mm))
        
        # Adresse
        address_lines = []
        if company_data.street:
            address_lines.append(f"{company_data.street} {company_data.house_number}".strip())
        if company_data.zipcode or company_data.city:
            address_lines.append(f"{company_data.zipcode} {company_data.city}".strip())
        if company_data.country:
            address_lines.append(company_data.country)
        
        for line in address_lines:
            elements.append(Paragraph(line, self.normal_style))
        
        elements.append(Spacer(1, 3*mm))
        
        # Kontakt
        if company_data.email:
            elements.append(Paragraph(f"E-Mail: {company_data.email}", self.normal_style))
        if company_data.phone:
            elements.append(Paragraph(f"Telefon: {company_data.phone}", self.normal_style))
        if company_data.mwst_nr:
            elements.append(Paragraph(f"MWST-Nr.: {company_data.mwst_nr}", self.normal_style))
        
        elements.append(HRFlowable(width="100%", thickness=1, lineColor=colors.HexColor('#e5e5ea')))
        
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
        
        # Tabellenkopf
        data = [['Datum', 'Service', 'Beschreibung', 'Stunden', 'Stundensatz', 'Betrag']]
        
        # Positionen
        for item in invoice.items.all():
            data.append([
                item.service_date.strftime('%d.%m.%Y'),
                item.service_type_code,
                item.description[:50] + '...' if len(item.description) > 50 else item.description,
                f"{item.quantity:.2f}",
                f"{item.unit_price:.2f} CHF",
                f"{item.gross_amount:.2f} CHF",
            ])
        
        table = Table(data, colWidths=[25*mm, 20*mm, 60*mm, 20*mm, 25*mm, 25*mm])
        table.setStyle(TableStyle([
            # Kopfzeile
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1d1d1f')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (5, -1), 'RIGHT'),
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
        
        if invoice.vat_rate > 0:
            data.append([f'MWST ({invoice.vat_rate}%):', f"{invoice.vat_amount:.2f} CHF"])
        
        data.append(['<b>Gesamtbetrag:</b>', f"<b>{invoice.amount:.2f} CHF</b>"])
        
        table = Table(data, colWidths=[100*mm, 50*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1d1d1f')),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_qr_code(self, invoice, company_data):
        """Erstellt QR-Code für Zahlung (vereinfachte Version)."""
        elements = []
        
        # Einfacher QR-Code mit IBAN, Betrag und Referenz
        qr_data = f"{company_data.iban}\n{invoice.amount:.2f} CHF\n{invoice.invoice_number}"
        
        # QR-Code generieren
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # QR-Code als Bild speichern
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # QR-Code-Bild in PDF einfügen
        qr_image = Image(img_buffer, width=50*mm, height=50*mm)
        elements.append(Paragraph("<b>Zahlungsinformationen:</b>", self.heading_style))
        elements.append(Spacer(1, 3*mm))
        elements.append(qr_image)
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(f"IBAN: {company_data.iban}", self.normal_style))
        elements.append(Paragraph(f"Betrag: {invoice.amount:.2f} CHF", self.normal_style))
        elements.append(Paragraph(f"Referenz: {invoice.invoice_number}", self.normal_style))
        
        return elements
