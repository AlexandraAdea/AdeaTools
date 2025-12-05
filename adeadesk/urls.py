from django.urls import path

from . import views

app_name = "adeadesk"

urlpatterns = [
    path("", views.ClientListView.as_view(), name="client-list"),
    path("new/", views.ClientCreateView.as_view(), name="client-create"),
    path("<int:pk>/", views.ClientDetailView.as_view(), name="client-detail"),
    path("<int:pk>/edit/", views.ClientUpdateView.as_view(), name="client-update"),
    path("<int:pk>/delete/", views.ClientDeleteView.as_view(), name="client-delete"),
    # Events
    path("<int:client_pk>/events/new/", views.EventCreateView.as_view(), name="event-create"),
    path("<int:client_pk>/events/<int:pk>/edit/", views.EventUpdateView.as_view(), name="event-update"),
    path("<int:client_pk>/events/<int:pk>/delete/", views.EventDeleteView.as_view(), name="event-delete"),
    # Documents
    path("<int:client_pk>/documents/new/", views.DocumentCreateView.as_view(), name="document-create"),
    path("<int:client_pk>/documents/<int:pk>/delete/", views.DocumentDeleteView.as_view(), name="document-delete"),
]
