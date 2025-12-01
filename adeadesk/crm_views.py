"""
CRM-Views für Kommunikation, Termine, Rechnungen und Dokumente.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
)
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from adeacore.models import Client, Communication, Event, Invoice, Document
from .crm_forms import CommunicationForm, EventForm, InvoiceForm, DocumentForm
from .mixins import AdeaDeskAccessMixin


# ============================================================================
# COMMUNICATION VIEWS
# ============================================================================

class CommunicationCreateView(AdeaDeskAccessMixin, CreateView):
    model = Communication
    form_class = CommunicationForm
    template_name = "adeadesk/crm_form.html"
    
    def get_client(self):
        return get_object_or_404(Client, pk=self.kwargs['client_pk'])
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['client'] = self.get_client()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        context['title'] = 'Neue Kommunikation'
        return context
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])


class CommunicationUpdateView(AdeaDeskAccessMixin, UpdateView):
    model = Communication
    form_class = CommunicationForm
    template_name = "adeadesk/crm_form.html"
    
    def get_client(self):
        return self.get_object().client
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['client'] = self.get_client()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        context['title'] = 'Kommunikation bearbeiten'
        return context
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.get_client().pk])


class CommunicationDeleteView(AdeaDeskAccessMixin, DeleteView):
    model = Communication
    template_name = "adeadesk/crm_confirm_delete.html"
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.get_object().client.pk])


# ============================================================================
# EVENT VIEWS
# ============================================================================

class EventCreateView(AdeaDeskAccessMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "adeadesk/crm_form.html"
    
    def get_client(self):
        return get_object_or_404(Client, pk=self.kwargs['client_pk'])
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['client'] = self.get_client()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        context['title'] = 'Neuer Termin'
        return context
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])


class EventUpdateView(AdeaDeskAccessMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "adeadesk/crm_form.html"
    
    def get_client(self):
        return self.get_object().client
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['client'] = self.get_client()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        context['title'] = 'Termin bearbeiten'
        return context
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.get_client().pk])


class EventDeleteView(AdeaDeskAccessMixin, DeleteView):
    model = Event
    template_name = "adeadesk/crm_confirm_delete.html"
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.get_object().client.pk])


# ============================================================================
# INVOICE VIEWS
# ============================================================================

class InvoiceCreateView(AdeaDeskAccessMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "adeadesk/crm_form.html"
    
    def get_client(self):
        return get_object_or_404(Client, pk=self.kwargs['client_pk'])
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['client'] = self.get_client()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        context['title'] = 'Neue Rechnung'
        return context
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])


class InvoiceUpdateView(AdeaDeskAccessMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = "adeadesk/crm_form.html"
    
    def get_client(self):
        return self.get_object().client
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['client'] = self.get_client()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        context['title'] = 'Rechnung bearbeiten'
        return context
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.get_client().pk])


class InvoiceDeleteView(AdeaDeskAccessMixin, DeleteView):
    model = Invoice
    template_name = "adeadesk/crm_confirm_delete.html"
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.get_object().client.pk])


# ============================================================================
# DOCUMENT VIEWS
# ============================================================================

class DocumentCreateView(AdeaDeskAccessMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "adeadesk/crm_form.html"
    
    def get_client(self):
        return get_object_or_404(Client, pk=self.kwargs['client_pk'])
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['client'] = self.get_client()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        context['title'] = 'Neues Dokument'
        return context
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.kwargs['client_pk']])


class DocumentUpdateView(AdeaDeskAccessMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "adeadesk/crm_form.html"
    
    def get_client(self):
        return self.get_object().client
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['client'] = self.get_client()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_client()
        context['title'] = 'Dokument bearbeiten'
        return context
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.get_client().pk])


class DocumentDeleteView(AdeaDeskAccessMixin, DeleteView):
    model = Document
    template_name = "adeadesk/crm_confirm_delete.html"
    
    def get_success_url(self):
        return reverse("adeadesk:client-detail", args=[self.get_object().client.pk])

