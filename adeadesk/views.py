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
