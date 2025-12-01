from django.urls import path

from . import views

app_name = "adealohn"

urlpatterns = [
    path("mandant/wechsel/", views.ClientSwitchView.as_view(), name="client_switch"),
    path("", views.EmployeeListView.as_view(), name="employee-list"),
    path("new/", views.EmployeeCreateView.as_view(), name="employee-create"),
    path("<int:pk>/", views.EmployeeDetailView.as_view(), name="employee-detail"),
    path("<int:pk>/edit/", views.EmployeeUpdateView.as_view(), name="employee-update"),
    path("<int:pk>/delete/", views.EmployeeDeleteView.as_view(), name="employee-delete"),
    path("payroll/", views.PayrollRecordListView.as_view(), name="payroll-list"),
    path("payroll/new/", views.PayrollRecordCreateView.as_view(), name="payroll-create"),
    path("payroll/<int:pk>/", views.PayrollRecordDetailView.as_view(), name="payroll-detail"),
    path("payroll/<int:pk>/edit/", views.PayrollRecordUpdateView.as_view(), name="payroll-update"),
    path("payroll/<int:pk>/delete/", views.PayrollRecordDeleteView.as_view(), name="payroll-delete"),
    path("payroll/<int:pk>/family-allowance-nachzahlung/", views.FamilyAllowanceNachzahlungView.as_view(), name="payroll-family-allowance-nachzahlung"),
    path("payroll/<int:pk>/spesen/new/", views.PayrollItemSpesenCreateView.as_view(), name="payroll_spesen_create"),
    path("payroll/<int:pk>/privatanteil/new/", views.PayrollItemPrivatanteilCreateView.as_view(), name="payroll_privatanteil_create"),
]


