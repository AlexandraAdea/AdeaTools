from django.urls import path
from . import views, timer_views

app_name = "adeazeit"

urlpatterns = [
    # Login/Logout
    path("login/", views.employee_login, name="login"),
    path("logout/", views.employee_logout, name="logout"),
    
    # Index
    path("", views.AdeaZeitIndexView.as_view(), name="index"),
    
    # EmployeeInternal
    path("mitarbeitende/", views.EmployeeInternalListView.as_view(), name="employee-list"),
    path("mitarbeitende/neu/", views.EmployeeInternalCreateView.as_view(), name="employee-create"),
    path("mitarbeitende/<int:pk>/bearbeiten/", views.EmployeeInternalUpdateView.as_view(), name="employee-update"),
    path("mitarbeitende/<int:pk>/loeschen/", views.EmployeeInternalDeleteView.as_view(), name="employee-delete"),
    
    # ServiceType
    path("service-typen/", views.ServiceTypeListView.as_view(), name="servicetype-list"),
    path("service-typen/neu/", views.ServiceTypeCreateView.as_view(), name="servicetype-create"),
    path("service-typen/<int:pk>/bearbeiten/", views.ServiceTypeUpdateView.as_view(), name="servicetype-update"),
    path("service-typen/<int:pk>/loeschen/", views.ServiceTypeDeleteView.as_view(), name="servicetype-delete"),
    
    # ZeitProject
    path("projekte/", views.ZeitProjectListView.as_view(), name="project-list"),
    path("projekte/neu/", views.ZeitProjectCreateView.as_view(), name="project-create"),
    path("projekte/<int:pk>/bearbeiten/", views.ZeitProjectUpdateView.as_view(), name="project-update"),
    path("projekte/<int:pk>/loeschen/", views.ZeitProjectDeleteView.as_view(), name="project-delete"),
    
    # TimeEntry
    path("zeit/tag/", views.TimeEntryDayView.as_view(), name="timeentry-day"),
    path("zeit/woche/", views.TimeEntryWeekView.as_view(), name="timeentry-week"),
    path("zeit/neu/", views.TimeEntryCreateView.as_view(), name="timeentry-create"),
    path("zeit/<int:pk>/bearbeiten/", views.TimeEntryUpdateView.as_view(), name="timeentry-update"),
    path("zeit/<int:pk>/loeschen/", views.TimeEntryDeleteView.as_view(), name="timeentry-delete"),
    
    # Timer (Live-Tracking)
    path("timer/start/", timer_views.start_timer, name="timer-start"),
    path("timer/stop/", timer_views.stop_timer, name="timer-stop"),
    path("timer/cancel/", timer_views.cancel_timer, name="timer-cancel"),
    path("timer/status/", timer_views.get_timer_status, name="timer-status"),
    
    # AJAX
    path("ajax/projekte/", views.LoadProjectsView.as_view(), name="load-projects"),
    path("ajax/mitarbeiter-info/", views.LoadEmployeeInfoView.as_view(), name="load-employee-info"),
    path("ajax/service-type-rate/", views.LoadServiceTypeRateView.as_view(), name="load-service-type-rate"),
    
    # Absence
    path("abwesenheiten/", views.AbsenceListView.as_view(), name="absence-list"),
    path("abwesenheiten/neu/", views.AbsenceCreateView.as_view(), name="absence-create"),
    path("abwesenheiten/<int:pk>/bearbeiten/", views.AbsenceUpdateView.as_view(), name="absence-update"),
    path("abwesenheiten/<int:pk>/loeschen/", views.AbsenceDeleteView.as_view(), name="absence-delete"),
    
    # Tasks (To-Do-Liste)
    path("aufgaben/", views.TaskListView.as_view(), name="task-list"),
    path("aufgaben/neu/", views.TaskCreateView.as_view(), name="task-create"),
    path("aufgaben/<int:pk>/bearbeiten/", views.TaskUpdateView.as_view(), name="task-update"),
    path("aufgaben/<int:pk>/loeschen/", views.TaskDeleteView.as_view(), name="task-delete"),
    path("aufgaben/<int:pk>/status/", views.TaskQuickStatusUpdateView.as_view(), name="task-quick-status"),
]
