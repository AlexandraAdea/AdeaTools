from django.urls import path

from . import views
from . import crm_views

app_name = "adeadesk"

urlpatterns = [
    # Client URLs
    path("", views.ClientListView.as_view(), name="client-list"),
    path("new/", views.ClientCreateView.as_view(), name="client-create"),
    path("<int:pk>/", views.ClientDetailView.as_view(), name="client-detail"),
    path("<int:pk>/edit/", views.ClientUpdateView.as_view(), name="client-update"),
    path("<int:pk>/delete/", views.ClientDeleteView.as_view(), name="client-delete"),
    
    # Communication URLs
    path("<int:client_pk>/communication/new/", crm_views.CommunicationCreateView.as_view(), name="communication-create"),
    path("communication/<int:pk>/edit/", crm_views.CommunicationUpdateView.as_view(), name="communication-update"),
    path("communication/<int:pk>/delete/", crm_views.CommunicationDeleteView.as_view(), name="communication-delete"),
    
    # Event URLs
    path("<int:client_pk>/event/new/", crm_views.EventCreateView.as_view(), name="event-create"),
    path("event/<int:pk>/edit/", crm_views.EventUpdateView.as_view(), name="event-update"),
    path("event/<int:pk>/delete/", crm_views.EventDeleteView.as_view(), name="event-delete"),
    
    # Invoice URLs
    path("<int:client_pk>/invoice/new/", crm_views.InvoiceCreateView.as_view(), name="invoice-create"),
    path("invoice/<int:pk>/edit/", crm_views.InvoiceUpdateView.as_view(), name="invoice-update"),
    path("invoice/<int:pk>/delete/", crm_views.InvoiceDeleteView.as_view(), name="invoice-delete"),
    
    # Document URLs
    path("<int:client_pk>/document/new/", crm_views.DocumentCreateView.as_view(), name="document-create"),
    path("document/<int:pk>/edit/", crm_views.DocumentUpdateView.as_view(), name="document-update"),
    path("document/<int:pk>/delete/", crm_views.DocumentDeleteView.as_view(), name="document-delete"),
]
