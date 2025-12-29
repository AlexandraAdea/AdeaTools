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
]



