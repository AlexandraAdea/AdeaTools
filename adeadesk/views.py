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
from django.shortcuts import get_object_or_404

from adeacore.models import Client, Event, Document, ClientNote
from .forms import ClientForm, EventForm, DocumentForm, ClientNoteForm


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = "adeadesk/index.html"
    context_object_name = "clients"
    paginate_by = 10
    login_url = '/login/'

    def get_queryset(self):
        queryset = super().get_queryset().order_by("name")
        query = self.request.GET.get("q")
        client_type_filter = self.request.GET.get("client_type")
        
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(city__icontains=query)
                | Q(email__icontains=query)
            )
        
        if client_type_filter:
            queryset = queryset.filter(client_type=client_type_filter)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["client_type_filter"] = self.request.GET.get("client_type", "")
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "adeadesk/form.html"
    login_url = '/login/'

    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.object.pk])


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = "adeadesk/detail.html"
    context_object_name = "client"
    login_url = '/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.object
        
        # Lade Events und Documents für diesen Client
        from adeacore.models import Event, Document
        context['events'] = Event.objects.filter(client=client).order_by('start_date')[:10]
        context['documents'] = Document.objects.filter(client=client).order_by('-created_at')[:10]
        
        # NEU: Lade Tasks aus AdeaZeit für diesen Client
        from adeazeit.models import Task
        context['tasks'] = Task.objects.filter(client=client, archiviert=False).order_by('-erstellt_am')[:10]
        
        # NEU: Lade Notizen für diesen Client
        note_filter = self.request.GET.get('note_filter', 'all')
        notes_queryset = ClientNote.objects.filter(client=client)
        
        if note_filter == 'offen':
            notes_queryset = notes_queryset.filter(status='OFFEN', archiviert=False)
        elif note_filter == 'erledigt':
            notes_queryset = notes_queryset.filter(status='ERLEDIGT', archiviert=False)
        elif note_filter == 'archiviert':
            notes_queryset = notes_queryset.filter(archiviert=True)
        else:
            notes_queryset = notes_queryset.filter(archiviert=False)
        
        context['notes'] = notes_queryset.order_by('-note_date', '-created_at')[:10]
        context['note_filter'] = note_filter
        
        return context


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "adeadesk/form.html"
    login_url = '/login/'

    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.object.pk])


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = "adeadesk/confirm_delete.html"
    context_object_name = "client"
    success_url = reverse_lazy("adeadesk:client-list")
    login_url = '/login/'


# Event Views
class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "adeadesk/event_form.html"
    login_url = '/login/'
    
    def get_client(self):
        return get_object_or_404(Client, pk=self.kwargs['client_pk'])
    
    def form_valid(self, form):
        form.instance.client = self.get_client()
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        return context


class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "adeadesk/event_form.html"
    login_url = '/login/'
    
    def get_object(self):
        return get_object_or_404(Event, pk=self.kwargs['pk'], client__pk=self.kwargs['client_pk'])
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = get_object_or_404(Client, pk=self.kwargs['client_pk'])
        return context


class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = "adeadesk/confirm_delete.html"
    login_url = '/login/'
    
    def get_object(self):
        return get_object_or_404(Event, pk=self.kwargs['pk'], client__pk=self.kwargs['client_pk'])
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])


# Document Views
class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "adeadesk/document_form.html"
    login_url = '/login/'
    
    def get_client(self):
        return get_object_or_404(Client, pk=self.kwargs['client_pk'])
    
    def form_valid(self, form):
        form.instance.client = self.get_client()
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        return context


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = Document
    template_name = "adeadesk/confirm_delete.html"
    login_url = '/login/'
    
    def get_object(self):
        return get_object_or_404(Document, pk=self.kwargs['pk'], client__pk=self.kwargs['client_pk'])
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])


# ClientNote Views
class ClientNoteCreateView(LoginRequiredMixin, CreateView):
    model = ClientNote
    form_class = ClientNoteForm
    template_name = "adeadesk/note_form.html"
    login_url = '/login/'
    
    def get_client(self):
        return get_object_or_404(Client, pk=self.kwargs['client_pk'])
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['client'] = self.get_client()
        return kwargs
    
    def form_valid(self, form):
        form.instance.client = self.get_client()
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        # Behalte Filter bei, falls gesetzt
        note_filter = self.request.GET.get('note_filter', '')
        url = reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])
        if note_filter:
            url += f"?note_filter={note_filter}"
        return url
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        return context


class ClientNoteUpdateView(LoginRequiredMixin, UpdateView):
    model = ClientNote
    form_class = ClientNoteForm
    template_name = "adeadesk/note_form.html"
    login_url = '/login/'
    
    def get_object(self):
        return get_object_or_404(ClientNote, pk=self.kwargs['pk'], client__pk=self.kwargs['client_pk'])
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['client'] = self.get_object().client
        return kwargs
    
    def get_success_url(self):
        # Behalte Filter bei, falls gesetzt
        note_filter = self.request.GET.get('note_filter', '')
        url = reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])
        if note_filter:
            url += f"?note_filter={note_filter}"
        return url
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_object().client
        return context


class ClientNoteDeleteView(LoginRequiredMixin, DeleteView):
    model = ClientNote
    template_name = "adeadesk/confirm_delete.html"
    login_url = '/login/'
    
    def get_object(self):
        return get_object_or_404(ClientNote, pk=self.kwargs['pk'], client__pk=self.kwargs['client_pk'])
    
    def get_success_url(self):
        # Behalte Filter bei, falls gesetzt
        note_filter = self.request.GET.get('note_filter', '')
        url = reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])
        if note_filter:
            url += f"?note_filter={note_filter}"
        return url
