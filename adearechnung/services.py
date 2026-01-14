"""
Services für Rechnungserstellung.
"""
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction
from django.utils import timezone
from adeacore.models import Invoice, InvoiceItem, CompanyData, Client
from adeazeit.models import TimeEntry


class InvoiceService:
    """Service für Rechnungserstellung und -verwaltung."""
    
    @staticmethod
    def generate_invoice_number(year: int = None) -> str:
        """
        Generiert eine eindeutige Rechnungsnummer.
        Format: RE-YYYY-NNNN (z.B. RE-2025-0001)
        """
        if year is None:
            year = date.today().year
        
        # Finde die höchste Nummer für dieses Jahr
        prefix = f"RE-{year}-"
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            # Extrahiere die Nummer aus der letzten Rechnung
            try:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f"{prefix}{next_number:04d}"
    
    @staticmethod
    def calculate_vat(net_amount: Decimal, vat_rate: Decimal = Decimal('7.7')) -> Decimal:
        """Berechnet MWST-Betrag."""
        return (net_amount * vat_rate / Decimal('100')).quantize(Decimal('0.01'))
    
    @staticmethod
    @transaction.atomic
    def create_invoice_from_time_entries(
        time_entry_ids: list,
        client: Client,
        invoice_date: date = None,
        created_by=None
    ) -> Invoice:
        """
        Erstellt eine Rechnung aus ausgewählten Zeiteinträgen.
        
        Args:
            time_entry_ids: Liste von TimeEntry-IDs
            client: Client für die Rechnung
            invoice_date: Rechnungsdatum (default: heute)
            created_by: User, der die Rechnung erstellt
        
        Returns:
            Erstellte Invoice
        """
        if invoice_date is None:
            invoice_date = date.today()
        
        # Lade Zeiteinträge
        time_entries = TimeEntry.objects.filter(
            id__in=time_entry_ids,
            client=client,
            verrechnet=False
        ).select_related('service_type', 'mitarbeiter')
        
        if not time_entries.exists():
            raise ValueError("Keine verrechenbaren Zeiteinträge gefunden.")
        
        # Prüfe ob Client MWST-pflichtig ist
        vat_rate = Decimal('7.7') if client.mwst_pflichtig else Decimal('0.00')
        
        # Berechne Gesamtbeträge
        total_net = Decimal('0.00')
        invoice_items_data = []
        
        for entry in time_entries:
            if not entry.billable:
                continue
            
            net_amount = entry.betrag or Decimal('0.00')
            vat_amount = InvoiceService.calculate_vat(net_amount, vat_rate)
            gross_amount = net_amount + vat_amount
            
            total_net += net_amount
            
            invoice_items_data.append({
                'time_entry': entry,
                'description': entry.kommentar or f"{entry.service_type.code} - {entry.service_type.name}",
                'service_type_code': entry.service_type.code,
                'employee_name': entry.mitarbeiter.name if entry.mitarbeiter else '',
                'service_date': entry.datum,
                'quantity': entry.dauer,
                'unit_price': entry.rate or Decimal('0.00'),
                'net_amount': net_amount,
                'vat_rate': vat_rate,
                'vat_amount': vat_amount,
                'gross_amount': gross_amount,
            })
        
        if not invoice_items_data:
            raise ValueError("Keine verrechenbaren Zeiteinträge gefunden.")
        
        # Berechne Gesamt-MWST und Bruttobetrag
        total_vat = InvoiceService.calculate_vat(total_net, vat_rate)
        total_gross = total_net + total_vat
        
        # Berechne Fälligkeitsdatum
        payment_days = client.zahlungsziel_tage or 30
        due_date = invoice_date + timedelta(days=payment_days)
        
        # Erstelle Rechnung
        invoice = Invoice.objects.create(
            client=client,
            invoice_number=InvoiceService.generate_invoice_number(),
            invoice_date=invoice_date,
            due_date=due_date,
            amount=total_gross,
            net_amount=total_net,
            vat_amount=total_vat,
            vat_rate=vat_rate,
            description=f"Zeiterfassung: {len(invoice_items_data)} Positionen",
            created_by=created_by,
        )
        
        # Erstelle Rechnungspositionen
        for item_data in invoice_items_data:
            InvoiceItem.objects.create(
                invoice=invoice,
                time_entry=item_data['time_entry'],
                description=item_data['description'],
                service_type_code=item_data['service_type_code'],
                employee_name=item_data['employee_name'],
                service_date=item_data['service_date'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                net_amount=item_data['net_amount'],
                vat_rate=item_data['vat_rate'],
                vat_amount=item_data['vat_amount'],
                gross_amount=item_data['gross_amount'],
            )
            
            # Markiere Zeiteintrag als verrechnet
            item_data['time_entry'].verrechnet = True
            item_data['time_entry'].save(update_fields=['verrechnet'])
        
        return invoice





