"""
URL-Konfiguration für AdeaRechnung - Fakturierung und Rechnungserstellung.
"""
from django.urls import path
from . import views
from adeazeit.views import mark_as_invoiced

app_name = "adearechnung"

urlpatterns = [
    # Kundenübersicht / Fakturierung
    path("", views.ClientTimeSummaryView.as_view(), name="client-summary"),
    
    # Verrechnung markieren
    path("mark-invoiced/", mark_as_invoiced, name="mark-invoiced"),
    
    # Rechnungserstellung
    path("create-invoice/", views.CreateInvoiceView.as_view(), name="create-invoice"),
    
    # Rechnungsliste
    path("invoices/", views.InvoiceListView.as_view(), name="invoice-list"),
    
    # Rechnungsdetail
    path("invoices/<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice-detail"),
    path("invoices/<int:pk>/update-payment/", views.InvoiceUpdatePaymentView.as_view(), name="invoice-update-payment"),
    path("invoices/<int:pk>/reset-billing/", views.InvoiceResetBillingView.as_view(), name="invoice-reset-billing"),
    path("invoices/<int:pk>/delete/", views.InvoiceDeleteView.as_view(), name="invoice-delete"),
    
    # PDF-Export
    path("invoices/<int:pk>/pdf/", views.InvoicePDFView.as_view(), name="invoice-pdf"),
]



