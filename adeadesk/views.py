from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from adeacore.models import Client
from .forms import ClientForm
from .mixins import AdminOrManagerRequiredMixin, AdeaDeskAccessMixin


class ClientListView(AdeaDeskAccessMixin, ListView):
    model = Client
    template_name = "adeadesk/list.html"
    context_object_name = "clients"
    paginate_by = 10
    login_url = '/admin/login/'

    def get_queryset(self):
        queryset = super().get_queryset().order_by("name")
        query = self.request.GET.get("q")
        client_type_filter = self.request.GET.get("client_type")
        status_filter = self.request.GET.get("status")
        
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(city__icontains=query)
                | Q(email__icontains=query)
            )
        
        if client_type_filter:
            queryset = queryset.filter(client_type=client_type_filter)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["client_type_filter"] = self.request.GET.get("client_type", "")
        context["status_filter"] = self.request.GET.get("status", "")
        return context


class ClientCreateView(AdminOrManagerRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "adeadesk/form.html"
    login_url = '/admin/login/'
    
    def form_valid(self, form):
        """Speichert mit aktuellen Benutzer für Audit-Log."""
        # Setze aktuellen Benutzer für Audit-Logging
        form.instance._current_user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.object.pk])


class ClientDetailView(AdeaDeskAccessMixin, DetailView):
    model = Client
    template_name = "adeadesk/detail.html"
    context_object_name = "client"
    login_url = '/admin/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        
        # CRM-Daten für Timeline
        from adeacore.models import Communication, Event, Invoice, Document
        
        # Kommunikationen (letzte 10)
        context['communications'] = Communication.objects.filter(client=client).order_by('-date')[:10]
        
        # Termine (kommende und überfällige)
        from django.utils import timezone
        context['upcoming_events'] = Event.objects.filter(
            client=client,
            start_date__gte=timezone.now()
        ).order_by('start_date')[:10]
        context['overdue_events'] = Event.objects.filter(
            client=client,
            start_date__lt=timezone.now(),
            end_date__isnull=True
        ).order_by('start_date')[:5]
        
        # Rechnungen (offene und überfällige)
        context['open_invoices'] = Invoice.objects.filter(
            client=client,
            payment_status__in=['OFFEN', 'TEILWEISE', 'UEBERFAELLIG']
        ).order_by('-invoice_date')[:10]
        context['total_open_amount'] = sum(inv.remaining_amount for inv in context['open_invoices'])
        
        # Dokumente (letzte 10)
        context['documents'] = Document.objects.filter(client=client).order_by('-created_at')[:10]
        
        # Timeline (kombiniert aus allen Aktivitäten)
        timeline_items = []
        for comm in Communication.objects.filter(client=client).order_by('-date')[:5]:
            timeline_items.append({
                'type': 'communication',
                'date': comm.date,
                'title': f"{comm.get_communication_type_display()}: {comm.subject or 'Kein Betreff'}",
                'object': comm,
            })
        for event in Event.objects.filter(client=client).order_by('-start_date')[:5]:
            timeline_items.append({
                'type': 'event',
                'date': event.start_date,
                'title': f"Termin: {event.title}",
                'object': event,
            })
        for invoice in Invoice.objects.filter(client=client).order_by('-invoice_date')[:5]:
            timeline_items.append({
                'type': 'invoice',
                'date': invoice.invoice_date,
                'title': f"Rechnung: {invoice.invoice_number}",
                'object': invoice,
            })
        
        timeline_items.sort(key=lambda x: x['date'], reverse=True)
        context['timeline'] = timeline_items[:10]
        
        return context


class ClientUpdateView(AdminOrManagerRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "adeadesk/form.html"
    login_url = '/admin/login/'
    
    def form_valid(self, form):
        """Speichert mit aktuellen Benutzer für Audit-Log."""
        # Setze aktuellen Benutzer für Audit-Logging
        form.instance._current_user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.object.pk])


class ClientDeleteView(AdminOrManagerRequiredMixin, DeleteView):
    model = Client
    template_name = "adeadesk/confirm_delete.html"
    context_object_name = "client"
    success_url = reverse_lazy("adeadesk:client-list")
    login_url = '/admin/login/'
