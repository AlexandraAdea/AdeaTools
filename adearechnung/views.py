"""
Views für AdeaRechnung - Fakturierung und Rechnungserstellung.

Diese Views nutzen die Funktionalität aus AdeaZeit, um Code-Duplikation zu vermeiden.
Die Kundenübersicht wird hier als eigenständiges Modul präsentiert (Vertec-Stil).
"""
from django.views.generic import TemplateView
from adeazeit.mixins import ManagerOrAdminRequiredMixin
from adeazeit.views import mark_as_invoiced
from datetime import datetime, date
from decimal import Decimal
from django.db.models import Sum, Q


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
        
        entries = entries_query.select_related("client", "mitarbeiter", "service_type").order_by("client__name", "datum")
        
        # Gruppiere nach Kunde
        from collections import defaultdict
        
        client_summary = defaultdict(lambda: {
            'client': None,
            'entries': [],
            'total_dauer': Decimal('0.00'),
            'total_betrag': Decimal('0.00'),
            'verrechnet_dauer': Decimal('0.00'),
            'verrechnet_betrag': Decimal('0.00'),
            'nicht_verrechnet_dauer': Decimal('0.00'),
            'nicht_verrechnet_betrag': Decimal('0.00'),
        })
        
        for entry in entries:
            # Stelle sicher, dass client nicht None ist
            if not entry.client:
                continue
                
            client_id = entry.client.id
            if client_id not in client_summary:
                client_summary[client_id]['client'] = entry.client
            
            client_summary[client_id]['entries'].append(entry)
            client_summary[client_id]['total_dauer'] += entry.dauer
            client_summary[client_id]['total_betrag'] += entry.betrag
            
            if entry.verrechnet:
                client_summary[client_id]['verrechnet_dauer'] += entry.dauer
                client_summary[client_id]['verrechnet_betrag'] += entry.betrag
            else:
                client_summary[client_id]['nicht_verrechnet_dauer'] += entry.dauer
                client_summary[client_id]['nicht_verrechnet_betrag'] += entry.betrag
        
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

