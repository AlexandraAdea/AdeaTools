"""
Views für AdeaRechnung - Fakturierung und Rechnungserstellung.

Diese Views nutzen die Funktionalität aus AdeaZeit, um Code-Duplikation zu vermeiden.
Die Kundenübersicht wird hier als eigenständiges Modul präsentiert (Vertec-Stil).
"""
from django.views.generic import TemplateView, ListView, DetailView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from adeazeit.mixins import ManagerOrAdminRequiredMixin
from adeazeit.views import mark_as_invoiced
from adeacore.models import Invoice, Client
from adearechnung.services import InvoiceService
from adeazeit.models import TimeEntry
from datetime import datetime, date
from decimal import Decimal
from django.db.models import Sum, Q, Min, Max
import json


class ClientTimeSummaryView(ManagerOrAdminRequiredMixin, TemplateView):
    """Übersicht der Zeiteinträge nach Kunde gruppiert - für Fakturierung."""
    template_name = "adearechnung/client_summary.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Datum-Filter aus URL
        date_from_str = self.request.GET.get("date_from")
        date_to_str = self.request.GET.get("date_to")
        
        # Filter nach Verrechnungsstatus
        verrechnet_filter = self.request.GET.get("verrechnet", "")  # "offen", "verrechnet", oder "" (alle)
        
        # Suche nach Kundenname
        client_search = self.request.GET.get("client_search", "").strip()
        
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
            except ValueError:
                # Standard: Letztes Jahr
                date_from = date.today().replace(month=1, day=1)
                if date.today().month == 1:
                    date_from = date_from.replace(year=date.today().year - 1)
        else:
            # Standard: Anfang des aktuellen Jahres
            date_from = date.today().replace(month=1, day=1)
        
        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date()
            except ValueError:
                date_to = date.today()
        else:
            date_to = date.today()
        
        context["date_from"] = date_from
        context["date_to"] = date_to
        context["date_from_str"] = date_from_str or ""
        context["date_to_str"] = date_to_str or ""
        context["verrechnet_filter"] = verrechnet_filter
        context["client_search"] = client_search
        
        # Filter nach Rolle
        from adeazeit.permissions import get_accessible_time_entries
        accessible_entries = get_accessible_time_entries(self.request.user)
        
        # Filter nach Datum und nur Einträge mit Kunde
        # Wenn date_from_str leer ist, zeige alle Einträge (kein Datum-Filter)
        entries_query = accessible_entries.filter(client__isnull=False)
        if date_from_str:  # Nur filtern wenn explizit gesetzt
            entries_query = entries_query.filter(datum__gte=date_from)
        if date_to_str:  # Nur filtern wenn explizit gesetzt
            entries_query = entries_query.filter(datum__lte=date_to)
        
        # Filter nach Verrechnungsstatus
        if verrechnet_filter == "offen":
            entries_query = entries_query.filter(verrechnet=False)
        elif verrechnet_filter == "verrechnet":
            entries_query = entries_query.filter(verrechnet=True)
        # Wenn leer, zeige alle
        
        # Suche nach Kundenname
        if client_search:
            entries_query = entries_query.filter(client__name__icontains=client_search)
        
        # Performance: nur Felder laden, die im Template/Grouping verwendet werden
        entries = (
            entries_query.select_related("client", "mitarbeiter", "service_type")
            .only(
                "id",
                "datum",
                "kommentar",
                "dauer",
                "betrag",
                "verrechnet",
                "client_id",
                "client__name",
                "mitarbeiter_id",
                "mitarbeiter__name",
                "service_type_id",
                "service_type__code",
                "service_type__name",
            )
            .order_by("client__name", "datum")
        )
        
        # Gruppiere nach Kunde und dann nach Service-Typ
        from collections import defaultdict
        
        client_summary = defaultdict(lambda: {
            'client': None,
            'service_groups': defaultdict(lambda: {
                'service_type': None,
                'entries': [],
                'total_dauer': Decimal('0.00'),
                'total_betrag': Decimal('0.00'),
            }),
            'total_dauer': Decimal('0.00'),
            'total_betrag': Decimal('0.00'),
            'verrechnet_dauer': Decimal('0.00'),
            'verrechnet_betrag': Decimal('0.00'),
            'nicht_verrechnet_dauer': Decimal('0.00'),
            'nicht_verrechnet_betrag': Decimal('0.00'),
        })
        
        for entry in entries:
            client_id = entry.client.id
            if client_id not in client_summary:
                client_summary[client_id]['client'] = entry.client
            
            # Gruppiere nach Service-Typ
            service_type_id = entry.service_type.id if entry.service_type else None
            if service_type_id:
                if client_summary[client_id]['service_groups'][service_type_id]['service_type'] is None:
                    client_summary[client_id]['service_groups'][service_type_id]['service_type'] = entry.service_type
                
                client_summary[client_id]['service_groups'][service_type_id]['entries'].append(entry)
                client_summary[client_id]['service_groups'][service_type_id]['total_dauer'] += entry.dauer
                client_summary[client_id]['service_groups'][service_type_id]['total_betrag'] += entry.betrag
            
            client_summary[client_id]['total_dauer'] += entry.dauer
            client_summary[client_id]['total_betrag'] += entry.betrag
            
            if entry.verrechnet:
                client_summary[client_id]['verrechnet_dauer'] += entry.dauer
                client_summary[client_id]['verrechnet_betrag'] += entry.betrag
            else:
                client_summary[client_id]['nicht_verrechnet_dauer'] += entry.dauer
                client_summary[client_id]['nicht_verrechnet_betrag'] += entry.betrag
        
        # Konvertiere service_groups von defaultdict zu dict und sortiere nach Service-Typ Code
        for client_id, summary in client_summary.items():
            summary['service_groups'] = dict(summary['service_groups'])
            # Sortiere Service-Gruppen nach Code
            summary['service_groups'] = dict(sorted(
                summary['service_groups'].items(),
                key=lambda x: x[1]['service_type'].code if x[1]['service_type'] else ''
            ))
        
        # Sortiere nach Kundenname und filtere None-Clients raus
        context["client_summaries"] = sorted(
            [s for s in client_summary.values() if s['client'] is not None],
            key=lambda x: x['client'].name if x['client'] else ''
        )
        
        # Gesamtstatistiken (gleiche Filter wie entries)
        stats_query = accessible_entries.filter(client__isnull=False)
        if date_from_str:  # Nur filtern wenn explizit gesetzt
            stats_query = stats_query.filter(datum__gte=date_from)
        if date_to_str:  # Nur filtern wenn explizit gesetzt
            stats_query = stats_query.filter(datum__lte=date_to)
        
        # Filter nach Verrechnungsstatus für Statistiken
        if verrechnet_filter == "offen":
            stats_query = stats_query.filter(verrechnet=False)
        elif verrechnet_filter == "verrechnet":
            stats_query = stats_query.filter(verrechnet=True)
        
        # Suche nach Kundenname für Statistiken
        if client_search:
            stats_query = stats_query.filter(client__name__icontains=client_search)
        
        total_stats = stats_query.aggregate(
            total_dauer=Sum('dauer'),
            total_betrag=Sum('betrag'),
            verrechnet_dauer=Sum('dauer', filter=Q(verrechnet=True)),
            verrechnet_betrag=Sum('betrag', filter=Q(verrechnet=True))
        )
        
        context["total_dauer"] = total_stats["total_dauer"] or Decimal('0.00')
        context["total_betrag"] = total_stats["total_betrag"] or Decimal('0.00')
        context["verrechnet_dauer"] = total_stats["verrechnet_dauer"] or Decimal('0.00')
        context["verrechnet_betrag"] = total_stats["verrechnet_betrag"] or Decimal('0.00')
        context["nicht_verrechnet_dauer"] = context["total_dauer"] - context["verrechnet_dauer"]
        context["nicht_verrechnet_betrag"] = context["total_betrag"] - context["verrechnet_betrag"]
        
        return context


class CreateInvoiceView(ManagerOrAdminRequiredMixin, View):
    """Erstellt eine Rechnung aus ausgewählten Zeiteinträgen."""
    
    def post(self, request):
        from django.contrib import messages
        from django.shortcuts import redirect
        
        try:
            # Unterstütze sowohl JSON als auch Form-Daten
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                time_entry_ids = data.get('entry_ids', [])
                client_id = data.get('client_id')
                custom_invoice_number = (data.get('invoice_number') or '').strip()
            else:
                # Form-Daten
                selected_entries_str = request.POST.get('selected_entries', '')
                time_entry_ids = [int(eid) for eid in selected_entries_str.split(',') if eid.isdigit()]
                client_id = request.POST.get('client_id')
                custom_invoice_number = (request.POST.get('invoice_number') or '').strip()
            
            if not time_entry_ids:
                if request.content_type == 'application/json':
                    from adeacore.http import json_error

                    return json_error('Keine Zeiteinträge ausgewählt.')
                else:
                    messages.error(request, 'Keine Zeiteinträge ausgewählt.')
                    return redirect('adearechnung:client-summary')
            
            if not client_id:
                if request.content_type == 'application/json':
                    from adeacore.http import json_error

                    return json_error('Kein Kunde angegeben.')
                else:
                    messages.error(request, 'Kein Kunde angegeben.')
                    return redirect('adearechnung:client-summary')
            
            client = get_object_or_404(Client, pk=client_id)
            
            # Erstelle Rechnung
            invoice = InvoiceService.create_invoice_from_time_entries(
                time_entry_ids=time_entry_ids,
                client=client,
                created_by=request.user,
                custom_invoice_number=custom_invoice_number,
            )
            
            if request.content_type == 'application/json':
                from adeacore.http import json_ok

                return json_ok(
                    {
                        'message': f'Rechnung {invoice.invoice_number} erfolgreich erstellt.',
                        'invoice_id': invoice.id,
                        'invoice_number': invoice.invoice_number,
                        'invoice_url': reverse('adearechnung:invoice-detail', args=[invoice.id]),
                    }
                )
            else:
                messages.success(request, f'Rechnung {invoice.invoice_number} erfolgreich erstellt.')
                return redirect('adearechnung:invoice-detail', pk=invoice.id)
            
        except ValueError as e:
            if request.content_type == 'application/json':
                from adeacore.http import json_error

                return json_error(str(e))
            else:
                messages.error(request, f'Fehler: {str(e)}')
                return redirect('adearechnung:client-summary')
        except Exception as e:
            if request.content_type == 'application/json':
                from adeacore.http import json_error

                return json_error(f'Fehler: {str(e)}')
            else:
                messages.error(request, f'Ein unerwarteter Fehler ist aufgetreten: {str(e)}')
                return redirect('adearechnung:client-summary')


class InvoiceListView(ManagerOrAdminRequiredMixin, ListView):
    """Liste aller Rechnungen."""
    model = Invoice
    template_name = "adearechnung/invoice_list.html"
    context_object_name = "invoices"
    paginate_by = 50
    
    def get_queryset(self):
        # List-Template nutzt nur invoice.* + invoice.client.*. `items` wird hier nicht benötigt.
        queryset = Invoice.objects.select_related('client', 'created_by')
        
        # Filter nach Client
        client_id = self.request.GET.get('client_id')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter nach Status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(payment_status=status)
        
        return queryset.order_by('-invoice_date', '-created_at')


class InvoiceDetailView(ManagerOrAdminRequiredMixin, DetailView):
    """Detail-Ansicht einer Rechnung."""
    model = Invoice
    template_name = "adearechnung/invoice_detail.html"
    context_object_name = "invoice"
    
    def get_queryset(self):
        return Invoice.objects.select_related('client', 'created_by').prefetch_related('items__time_entry')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from adeacore.models import CompanyData
        invoice = self.object
        company_data = CompanyData.get_instance()

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

        context["grouped_items"] = grouped_items
        context["company_data"] = company_data
        context["warn_qr_iban_missing"] = not bool((company_data.iban or "").strip())
        return context


class InvoicePDFView(ManagerOrAdminRequiredMixin, DetailView):
    """PDF-Export einer Rechnung."""
    model = Invoice
    
    def get(self, request, *args, **kwargs):
        invoice = self.get_object()
        from adearechnung.pdf_generator import InvoicePDFGenerator
        
        pdf_generator = InvoicePDFGenerator()
        pdf_response = pdf_generator.generate_pdf(invoice)
        pdf_response["Content-Disposition"] = f'inline; filename="RE-{invoice.invoice_number}.pdf"'
        
        return pdf_response


class InvoiceResetBillingView(ManagerOrAdminRequiredMixin, View):
    """
    Nimmt eine Verrechnung zurück:
    - setzt zugeordnete Zeiteinträge auf verrechnet=False
    - entfernt die fehlerhafte Rechnung inkl. Positionen
    """

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice.objects.prefetch_related("items"), pk=pk)

        if invoice.payment_status in ("BEZAHLT", "TEILWEISE"):
            messages.error(
                request,
                f"Rechnung {invoice.invoice_number} ist bereits (teilweise) bezahlt und kann nicht zurückgenommen werden.",
            )
            return redirect("adearechnung:invoice-detail", pk=invoice.pk)

        invoice_number = invoice.invoice_number
        with transaction.atomic():
            time_entry_ids = list(
                invoice.items.exclude(time_entry__isnull=True).values_list("time_entry_id", flat=True)
            )
            if time_entry_ids:
                TimeEntry.objects.filter(pk__in=time_entry_ids).update(verrechnet=False)

            # InvoiceItems werden via CASCADE mitgelöscht.
            invoice.delete()

        messages.success(
            request,
            f"Verrechnung {invoice_number} wurde zurückgenommen. Die Zeiteinträge sind wieder offen und können neu verrechnet werden.",
        )
        return redirect("adearechnung:client-summary")


class InvoiceDeleteView(ManagerOrAdminRequiredMixin, View):
    """
    Löscht eine Rechnung ohne Rücksetzung der Zeiteinträge.
    Schutz: Bereits (teilweise) bezahlte Rechnungen können nicht gelöscht werden.
    """

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)

        if invoice.payment_status in ("BEZAHLT", "TEILWEISE"):
            messages.error(
                request,
                f"Rechnung {invoice.invoice_number} ist bereits (teilweise) bezahlt und kann nicht gelöscht werden.",
            )
            return redirect("adearechnung:invoice-list")

        invoice_number = invoice.invoice_number
        invoice.delete()
        messages.success(request, f"Rechnung {invoice_number} wurde gelöscht.")
        return redirect("adearechnung:invoice-list")


class InvoiceUpdatePaymentView(ManagerOrAdminRequiredMixin, View):
    """
    Aktualisiert Zahlungsdaten einer Rechnung direkt in AdeaRechnung.
    Status wird über Invoice.save() automatisch aus paid_amount/due_date berechnet.
    """

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)

        paid_amount_raw = (request.POST.get("paid_amount") or "0").strip().replace(",", ".")
        payment_date_raw = (request.POST.get("payment_date") or "").strip()

        try:
            paid_amount = Decimal(paid_amount_raw)
        except Exception:
            messages.error(request, "Ungültiger bezahlter Betrag.")
            return redirect("adearechnung:invoice-detail", pk=invoice.pk)

        if paid_amount < Decimal("0"):
            messages.error(request, "Bezahlter Betrag darf nicht negativ sein.")
            return redirect("adearechnung:invoice-detail", pk=invoice.pk)

        if paid_amount > invoice.amount:
            messages.error(
                request,
                f"Bezahlter Betrag darf den Rechnungsbetrag ({invoice.amount:.2f} CHF) nicht überschreiten.",
            )
            return redirect("adearechnung:invoice-detail", pk=invoice.pk)

        parsed_payment_date = None
        if payment_date_raw:
            try:
                parsed_payment_date = datetime.strptime(payment_date_raw, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Ungültiges Zahlungsdatum.")
                return redirect("adearechnung:invoice-detail", pk=invoice.pk)

        # Komfort: bei Zahlung ohne Datum automatisch auf heute setzen.
        if paid_amount > Decimal("0") and not parsed_payment_date:
            parsed_payment_date = date.today()

        if paid_amount == Decimal("0"):
            parsed_payment_date = None

        invoice.paid_amount = paid_amount
        invoice.payment_date = parsed_payment_date
        invoice.save()

        messages.success(
            request,
            f"Zahlung aktualisiert. Neuer Status: {invoice.get_payment_status_display()}.",
        )
        return redirect("adearechnung:invoice-detail", pk=invoice.pk)

