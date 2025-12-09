from decimal import Decimal
from calendar import month_name
from datetime import datetime, timedelta, date
from django.db.models import Q, Sum
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.http import JsonResponse, HttpResponseForbidden

from adeacore.models import Client
from .models import EmployeeInternal, ServiceType, ZeitProject, TimeEntry, Absence, RunningTimeEntry, Task
from .forms import (
    EmployeeInternalForm,
    ServiceTypeForm,
    ZeitProjectForm,
    TimeEntryForm,
    AbsenceForm,
    TaskForm,
)
from .services import WorkingTimeCalculator
from .mixins import (
    ManagerOrAdminRequiredMixin,
    AdminRequiredMixin,
    TimeEntryFilterMixin,
    EmployeeFilterMixin,
    AbsenceFilterMixin,
    CanEditMixin,
    CanDeleteMixin,
)
from .permissions import (
    can_edit_all_entries,
    can_view_all_entries,
    can_manage_employees,
    can_manage_service_types,
    can_manage_absences,
    can_delete_entries,
    get_accessible_employees,
)


# ============================================================================
# Index View
# ============================================================================

class AdeaZeitIndexView(LoginRequiredMixin, TemplateView):
    """Index-View für AdeaZeit - leitet zur Tagesansicht weiter."""
    template_name = "adeazeit/index.html"
    login_url = '/admin/login/'

    def get(self, request, *args, **kwargs):
        # Weiterleitung zur Tagesansicht
        return redirect('adeazeit:timeentry-day')


# ============================================================================
# EmployeeInternal Views
# ============================================================================

class EmployeeInternalListView(ManagerOrAdminRequiredMixin, EmployeeFilterMixin, ListView):
    model = EmployeeInternal
    template_name = "adeazeit/employeeinternal_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        queryset = super().get_queryset().order_by("name")
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(code__icontains=query) |
                Q(rolle__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["can_manage"] = can_manage_employees(self.request.user)
        return context


class EmployeeInternalCreateView(ManagerOrAdminRequiredMixin, CreateView):
    model = EmployeeInternal
    form_class = EmployeeInternalForm
    template_name = "adeazeit/employeeinternal_form.html"

    def form_valid(self, form):
        """Setze eintrittsdatum automatisch aus employment_start, falls nicht gesetzt."""
        response = super().form_valid(form)
        if not self.object.eintrittsdatum and self.object.employment_start:
            self.object.eintrittsdatum = self.object.employment_start
            self.object.save(update_fields=['eintrittsdatum'])
        elif not self.object.eintrittsdatum:
            # Falls weder eintrittsdatum noch employment_start gesetzt sind, heute setzen
            from datetime import date
            self.object.eintrittsdatum = date.today()
            self.object.save(update_fields=['eintrittsdatum'])
        return response

    def get_success_url(self):
        messages.success(self.request, f'Mitarbeiterin "{self.object.name}" wurde erfolgreich angelegt.')
        return reverse("adeazeit:employee-list")


class EmployeeInternalUpdateView(ManagerOrAdminRequiredMixin, UpdateView):
    model = EmployeeInternal
    form_class = EmployeeInternalForm
    template_name = "adeazeit/employeeinternal_form.html"

    def form_valid(self, form):
        """Synchronisiere eintrittsdatum mit employment_start, falls employment_start gesetzt ist."""
        response = super().form_valid(form)
        if self.object.employment_start and not self.object.eintrittsdatum:
            self.object.eintrittsdatum = self.object.employment_start
            self.object.save(update_fields=['eintrittsdatum'])
        return response

    def get_success_url(self):
        messages.success(self.request, f'Mitarbeiterin "{self.object.name}" wurde erfolgreich aktualisiert.')
        return reverse("adeazeit:employee-list")


class EmployeeInternalDeleteView(AdminRequiredMixin, DeleteView):
    model = EmployeeInternal
    template_name = "adeazeit/employeeinternal_confirm_delete.html"
    success_url = reverse_lazy("adeazeit:employee-list")

    def delete(self, request, *args, **kwargs):
        employee_name = self.get_object().name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Mitarbeiterin "{employee_name}" wurde erfolgreich gelöscht.')
        return response


# ============================================================================
# ServiceType Views
# ============================================================================

class ServiceTypeListView(ManagerOrAdminRequiredMixin, ListView):
    model = ServiceType
    template_name = "adeazeit/servicetype_list.html"
    context_object_name = "service_types"

    def get_queryset(self):
        queryset = ServiceType.objects.all().order_by("code")
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(code__icontains=query) |
                Q(name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class ServiceTypeCreateView(ManagerOrAdminRequiredMixin, CreateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = "adeazeit/servicetype_form.html"

    def get_success_url(self):
        return reverse("adeazeit:servicetype-list")


class ServiceTypeUpdateView(ManagerOrAdminRequiredMixin, UpdateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = "adeazeit/servicetype_form.html"

    def get_success_url(self):
        return reverse("adeazeit:servicetype-list")


class ServiceTypeDeleteView(AdminRequiredMixin, DeleteView):
    model = ServiceType
    template_name = "adeazeit/confirm_delete.html"
    success_url = reverse_lazy("adeazeit:servicetype-list")


# ============================================================================
# ZeitProject Views
# ============================================================================

class ZeitProjectListView(LoginRequiredMixin, ListView):
    model = ZeitProject
    template_name = "adeazeit/zeitproject_list.html"
    context_object_name = "projects"
    login_url = '/admin/login/'

    def get_queryset(self):
        queryset = ZeitProject.objects.select_related("client").order_by("client", "name")
        client_id = self.request.GET.get("client")
        query = self.request.GET.get("q")
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(client__name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["selected_client"] = self.request.GET.get("client", "")
        context["clients"] = Client.objects.all().order_by("name")
        return context


class ZeitProjectCreateView(LoginRequiredMixin, CreateView):
    model = ZeitProject
    form_class = ZeitProjectForm
    template_name = "adeazeit/zeitproject_form.html"
    login_url = '/admin/login/'

    def get_success_url(self):
        return reverse("adeazeit:project-list")


class ZeitProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = ZeitProject
    form_class = ZeitProjectForm
    template_name = "adeazeit/zeitproject_form.html"
    login_url = '/admin/login/'

    def get_success_url(self):
        return reverse("adeazeit:project-list")


class ZeitProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = ZeitProject
    template_name = "adeazeit/confirm_delete.html"
    success_url = reverse_lazy("adeazeit:project-list")
    login_url = '/admin/login/'


# ============================================================================
# TimeEntry Views
# ============================================================================

class TimeEntryDayView(LoginRequiredMixin, TemplateView):
    """Tagesansicht für Zeiteinträge."""
    template_name = "adeazeit/timeentry_day.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Datum aus URL oder heute
        date_str = self.request.GET.get("date")
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                selected_date = date.today()
        else:
            selected_date = date.today()
        
        context["selected_date"] = selected_date
        context["previous_date"] = selected_date - timedelta(days=1)
        context["next_date"] = selected_date + timedelta(days=1)
        
        # Filter nach Rolle
        from .permissions import get_accessible_time_entries
        accessible_entries = get_accessible_time_entries(self.request.user)
        context["time_entries"] = accessible_entries.filter(
            datum=selected_date
        ).select_related("mitarbeiter", "client", "project", "service_type").order_by("start")
        
        # Statistiken (optimiert: DB-Aggregation statt Python-Loop)
        from django.db.models import Sum, Q
        stats = accessible_entries.filter(datum=selected_date).aggregate(
            total_dauer=Sum('dauer'),
            total_betrag=Sum('betrag'),
            billable_dauer=Sum('dauer', filter=Q(billable=True))
        )
        
        context["total_dauer"] = stats["total_dauer"] or Decimal('0.00')
        context["total_betrag"] = stats["total_betrag"] or Decimal('0.00')
        context["billable_dauer"] = stats["billable_dauer"] or Decimal('0.00')
        context["can_edit_all"] = can_view_all_entries(self.request.user)
        
        # Für Template: Liste der zugänglichen Mitarbeiter-IDs für Bearbeitungsprüfung
        accessible_employee_ids = list(get_accessible_employees(self.request.user).values_list('id', flat=True))
        context["accessible_employee_ids"] = accessible_employee_ids
        
        return context


class TimeEntryWeekView(LoginRequiredMixin, TemplateView):
    """Wochenansicht für Zeiteinträge."""
    template_name = "adeazeit/timeentry_week.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Woche aus URL oder aktuelle Woche
        date_str = self.request.GET.get("date")
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                selected_date = date.today()
        else:
            selected_date = date.today()
        
        # Montag der Woche
        days_since_monday = selected_date.weekday()
        monday = selected_date - timedelta(days=days_since_monday)
        sunday = monday + timedelta(days=6)
        
        context["monday"] = monday
        context["sunday"] = sunday
        context["week_dates"] = [monday + timedelta(days=i) for i in range(7)]
        
        # Zeiteinträge für die Woche (gefiltert nach Rolle)
        from .permissions import get_accessible_time_entries
        accessible_entries = get_accessible_time_entries(self.request.user)
        time_entries = accessible_entries.filter(
            datum__range=[monday, sunday]
        ).select_related("mitarbeiter", "client", "project", "service_type").order_by("datum", "start")
        
        # Gruppiere nach Datum
        entries_by_date = {}
        for entry in time_entries:
            if entry.datum not in entries_by_date:
                entries_by_date[entry.datum] = []
            entries_by_date[entry.datum].append(entry)
        
        context["entries_by_date"] = entries_by_date
        
        # Statistiken (optimiert: DB-Aggregation statt Python-Loop)
        stats = accessible_entries.filter(datum__range=[monday, sunday]).aggregate(
            total_dauer=Sum('dauer'),
            total_betrag=Sum('betrag'),
            billable_dauer=Sum('dauer', filter=Q(billable=True))
        )
        
        context["total_dauer"] = stats["total_dauer"] or Decimal('0.00')
        context["total_betrag"] = stats["total_betrag"] or Decimal('0.00')
        context["billable_dauer"] = stats["billable_dauer"] or Decimal('0.00')
        context["can_edit_all"] = can_view_all_entries(self.request.user)
        
        return context


class TimeEntryCreateView(LoginRequiredMixin, CreateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = "adeazeit/timeentry_form.html"
    
    def form_valid(self, form):
        """Stelle sicher, dass alle Felder korrekt gespeichert werden."""
        # Setze Standard-Datum falls nicht gesetzt
        if not form.cleaned_data.get('datum'):
            from datetime import date
            form.instance.datum = date.today()
        
        # Stelle sicher, dass Kommentar gespeichert wird
        if 'kommentar' in form.cleaned_data:
            form.instance.kommentar = form.cleaned_data['kommentar']
        
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        # Default: Heute
        initial["datum"] = date.today()
        return initial

    def get_form(self, form_class=None):
        from django import forms
        form = super().get_form(form_class)
        # Filter Mitarbeiter nach Rolle
        if not can_view_all_entries(self.request.user):
            accessible_employees = get_accessible_employees(self.request.user)
            form.fields["mitarbeiter"].queryset = accessible_employees
            
            # Für normale Mitarbeiter: Automatisch eigenen Mitarbeiter setzen und Feld verstecken
            if accessible_employees.count() == 1:
                employee = accessible_employees.first()
                form.fields["mitarbeiter"].initial = employee
                form.fields["mitarbeiter"].widget = forms.HiddenInput()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mitarbeiter-Info für Sidebar
        employee_id = self.request.GET.get("mitarbeiter")
        if employee_id:
            try:
                accessible_employees = get_accessible_employees(self.request.user)
                employee = accessible_employees.get(pk=employee_id)
                today = date.today()
                context["employee_info"] = {
                    "employee": employee,
                    "employment_percent": employee.employment_percent,
                    "weekly_soll_hours": employee.weekly_soll_hours,
                    "monthly_soll": WorkingTimeCalculator.monthly_soll_hours(employee, today.year, today.month),
                    "monthly_absence": WorkingTimeCalculator.monthly_absence_hours(employee, today.year, today.month),
                    "monthly_effective_soll": WorkingTimeCalculator.monthly_effective_soll_hours(employee, today.year, today.month),
                    "monthly_ist": WorkingTimeCalculator.monthly_ist_hours(employee, today.year, today.month),
                    "productivity": WorkingTimeCalculator.monthly_productivity(employee, today.year, today.month),
                }
            except EmployeeInternal.DoesNotExist:
                pass
        return context

    def get_success_url(self):
        # Redirect zur Tagesansicht
        return reverse("adeazeit:timeentry-day") + f"?date={self.object.datum}"


class TimeEntryUpdateView(LoginRequiredMixin, UpdateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = "adeazeit/timeentry_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        try:
            obj = self.get_object()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Fehler beim Laden des Zeiteintrags: {e}", exc_info=True)
            return HttpResponseForbidden(f"Zeiteintrag konnte nicht geladen werden: {str(e)}")
        
        # Prüfe, ob User alle Einträge bearbeiten kann
        if can_view_all_entries(request.user):
            return super().dispatch(request, *args, **kwargs)
        
        # Prüfe, ob User den eigenen Eintrag bearbeitet
        if not obj.mitarbeiter:
            return HttpResponseForbidden("Zeiteintrag hat keinen zugeordneten Mitarbeiter.")
        
        try:
            accessible_employees = get_accessible_employees(request.user)
            accessible_employee_ids = list(accessible_employees.values_list('id', flat=True))
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Fehler beim Laden der zugänglichen Mitarbeiter: {e}", exc_info=True)
            return HttpResponseForbidden(f"Fehler beim Prüfen der Berechtigungen: {str(e)}")
        
        if not accessible_employee_ids:
            return HttpResponseForbidden("Sie haben keinen zugeordneten Mitarbeiter-Profil. Bitte kontaktieren Sie den Administrator.")
        
        if obj.mitarbeiter.id in accessible_employee_ids:
            return super().dispatch(request, *args, **kwargs)
        
        return HttpResponseForbidden("Sie können nur eigene Zeiteinträge bearbeiten.")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter Mitarbeiter nach Rolle
        if not can_view_all_entries(self.request.user):
            form.fields["mitarbeiter"].queryset = get_accessible_employees(self.request.user)
        return form

    def form_valid(self, form):
        """Stelle sicher, dass alle Felder korrekt gespeichert werden."""
        # Stelle sicher, dass Datum gespeichert wird
        if 'datum' in form.cleaned_data and form.cleaned_data['datum']:
            form.instance.datum = form.cleaned_data['datum']
        
        # Stelle sicher, dass Kommentar gespeichert wird
        if 'kommentar' in form.cleaned_data:
            form.instance.kommentar = form.cleaned_data['kommentar']
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mitarbeiter-Info für Sidebar
        if self.object and self.object.mitarbeiter:
            try:
                today = date.today()
                employee = self.object.mitarbeiter
                context["employee_info"] = {
                    "employee": employee,
                    "employment_percent": employee.employment_percent,
                    "weekly_soll_hours": employee.weekly_soll_hours,
                    "monthly_soll": WorkingTimeCalculator.monthly_soll_hours(employee, today.year, today.month),
                    "monthly_absence": WorkingTimeCalculator.monthly_absence_hours(employee, today.year, today.month),
                    "monthly_effective_soll": WorkingTimeCalculator.monthly_effective_soll_hours(employee, today.year, today.month),
                    "monthly_ist": WorkingTimeCalculator.monthly_ist_hours(employee, today.year, today.month),
                    "productivity": WorkingTimeCalculator.monthly_productivity(employee, today.year, today.month),
                }
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Fehler beim Laden der Mitarbeiter-Info: {e}", exc_info=True)
                # Setze employee_info auf None, damit Template nicht crasht
                context["employee_info"] = None
        return context

    def get_success_url(self):
        return reverse("adeazeit:timeentry-day") + f"?date={self.object.datum}"


class TimeEntryDeleteView(AdminRequiredMixin, DeleteView):
    model = TimeEntry
    template_name = "adeazeit/confirm_delete.html"

    def get_success_url(self):
        # Redirect zur Tagesansicht des gelöschten Eintrags
        datum = self.object.datum
        return reverse("adeazeit:timeentry-day") + f"?date={datum}"


# AJAX View für Projekte
class LoadProjectsView(LoginRequiredMixin, TemplateView):
    """AJAX-View zum Laden von Projekten für einen Client."""
    login_url = '/admin/login/'

    def get(self, request, *args, **kwargs):
        client_id = request.GET.get("client_id")
        if client_id:
            projects = ZeitProject.objects.filter(
                client_id=client_id, aktiv=True
            ).order_by("name")
            projects_data = [{"id": p.id, "name": p.name} for p in projects]
            return JsonResponse({"projects": projects_data})
        return JsonResponse({"projects": []})


# AJAX View für Mitarbeiter-Info
class LoadEmployeeInfoView(LoginRequiredMixin, TemplateView):
    """AJAX-View zum Laden von Mitarbeiter-Informationen."""
    login_url = '/admin/login/'

    def get(self, request, *args, **kwargs):
        employee_id = request.GET.get("employee_id")
        year = request.GET.get("year")
        month = request.GET.get("month")
        
        if not employee_id:
            return JsonResponse({"success": False, "error": "Keine Mitarbeiter-ID angegeben"})
        
        try:
            employee = EmployeeInternal.objects.get(pk=employee_id)
            if not year or not month:
                today = date.today()
                year = today.year
                month = today.month
            else:
                try:
                    year = int(year)
                    month = int(month)
                    if not (1 <= month <= 12):
                        raise ValueError("Monat muss zwischen 1 und 12 sein")
                except (ValueError, TypeError):
                    return JsonResponse({"success": False, "error": "Ungültiges Jahr oder Monat"})
            
            # Use WorkingTimeCalculator for comprehensive info including absences
            info = {
                "name": employee.name,
                "function_title": employee.function_title,
                "internal_full_name": employee.internal_full_name,
                "employment_percent": str(employee.employment_percent),
                "weekly_soll_hours": str(employee.weekly_soll_hours),
                "monthly_soll": str(WorkingTimeCalculator.monthly_soll_hours(employee, year, month)),
                "monthly_absence": str(WorkingTimeCalculator.monthly_absence_hours(employee, year, month)),
                "monthly_effective_soll": str(WorkingTimeCalculator.monthly_effective_soll_hours(employee, year, month)),
                "monthly_ist": str(WorkingTimeCalculator.monthly_ist_hours(employee, year, month)),
                "productivity": str(WorkingTimeCalculator.monthly_productivity(employee, year, month)),
            }
            return JsonResponse({
                "success": True,
                "employee": info
            })
        except EmployeeInternal.DoesNotExist:
            return JsonResponse({"success": False, "error": "Mitarbeiter nicht gefunden"})
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Fehler beim Laden der Mitarbeiter-Info: {e}", exc_info=True)
            return JsonResponse({"success": False, "error": "Ein Fehler ist aufgetreten"})


# AJAX View für Service-Typ Standard-Stundensatz
class LoadServiceTypeRateView(LoginRequiredMixin, TemplateView):
    """AJAX-View zum Laden des Standard-Stundensatzes eines Service-Typs."""
    login_url = '/admin/login/'

    def get(self, request, *args, **kwargs):
        from django.http import JsonResponse
        from .models import ServiceType
        
        service_type_id = request.GET.get("service_type_id")
        
        if not service_type_id:
            return JsonResponse({"success": False, "error": "Keine Service-Typ-ID angegeben"})
        
        try:
            service_type = ServiceType.objects.get(pk=service_type_id)
            return JsonResponse({
                "success": True,
                "standard_rate": str(service_type.standard_rate),
                "billable": service_type.billable
            })
        except ServiceType.DoesNotExist:
            return JsonResponse({"success": False, "error": "Service-Typ nicht gefunden"})
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Fehler beim Laden des Service-Typ-Stundensatzes: {e}")
            return JsonResponse({"success": False, "error": "Ein Fehler ist aufgetreten"})


# ============================================================================
# Absence Views
# ============================================================================

class AbsenceListView(LoginRequiredMixin, AbsenceFilterMixin, ListView):
    model = Absence
    template_name = "adeazeit/absence_list.html"
    context_object_name = "absences"

    def get_queryset(self):
        queryset = super().get_queryset().select_related("employee").order_by("-date_from")
        employee_id = self.request.GET.get("employee")
        absence_type = self.request.GET.get("absence_type")
        month = self.request.GET.get("month")
        year = self.request.GET.get("year")
        
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if absence_type:
            queryset = queryset.filter(absence_type=absence_type)
        
        # Filter by month/year if provided
        if year and month:
            try:
                year = int(year)
                month = int(month)
                start_date = date(year, month, 1)
                if month == 12:
                    end_date = date(year + 1, 1, 1)
                else:
                    end_date = date(year, month + 1, 1)
                queryset = queryset.filter(date_from__lt=end_date, date_to__gte=start_date)
            except (ValueError, TypeError):
                pass
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_employee"] = self.request.GET.get("employee", "")
        context["selected_absence_type"] = self.request.GET.get("absence_type", "")
        context["selected_month"] = self.request.GET.get("month", "")
        context["selected_year"] = self.request.GET.get("year", "")
        
        today = date.today()
        context["selected_month"] = context["selected_month"] or str(today.month)
        context["selected_year"] = context["selected_year"] or str(today.year)
        
        # Filter: Nur aktive Mitarbeitende (nach Rolle)
        today = date.today()
        accessible_employees = get_accessible_employees(self.request.user)
        context["employees"] = accessible_employees.filter(
            aktiv=True
        ).filter(
            Q(employment_end__isnull=True) | Q(employment_end__gte=today)
        ).order_by("name")
        context["absence_types"] = Absence.TYPE_CHOICES
        context["can_manage"] = can_manage_absences(self.request.user)
        return context


class AbsenceCreateView(LoginRequiredMixin, CreateView):
    model = Absence
    form_class = AbsenceForm
    template_name = "adeazeit/absence_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter Mitarbeiter nach Rolle
        if not can_view_all_entries(self.request.user):
            form.fields["employee"].queryset = get_accessible_employees(self.request.user)
        return form

    def get_success_url(self):
        return reverse("adeazeit:absence-list")


class AbsenceUpdateView(LoginRequiredMixin, CanEditMixin, UpdateView):
    model = Absence
    form_class = AbsenceForm
    template_name = "adeazeit/absence_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        obj = self.get_object()
        
        # Prüfe, ob User alle Abwesenheiten bearbeiten kann
        if can_manage_absences(request.user):
            return super().dispatch(request, *args, **kwargs)
        
        # Prüfe, ob User die eigene Abwesenheit bearbeitet
        accessible_employees = get_accessible_employees(request.user)
        if obj.employee in accessible_employees:
            return super().dispatch(request, *args, **kwargs)
        
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Sie können nur eigene Abwesenheiten bearbeiten.")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter Mitarbeiter nach Rolle
        if not can_view_all_entries(self.request.user):
            form.fields["employee"].queryset = get_accessible_employees(self.request.user)
        return form

    def get_success_url(self):
        return reverse("adeazeit:absence-list")


class AbsenceDeleteView(AdminRequiredMixin, DeleteView):
    model = Absence
    template_name = "adeazeit/absence_confirm_delete.html"
    success_url = reverse_lazy("adeazeit:absence-list")


# ============================================================================
# Task Views
# ============================================================================

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "adeazeit/task_list.html"
    context_object_name = "tasks"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Admin/Manager sehen alle Tasks
        if can_view_all_entries(self.request.user) or self.request.user.is_staff:
            # Alle Tasks anzeigen - keine Filterung
            pass
        else:
            # Mitarbeiter sehen nur eigene Tasks
            try:
                from .models import UserProfile
                user_profile = UserProfile.objects.get(user=self.request.user)
                if user_profile.employee:
                    queryset = queryset.filter(mitarbeiter=user_profile.employee)
                else:
                    # User ohne Employee-Profil sehen keine Tasks
                    queryset = queryset.none()
            except UserProfile.DoesNotExist:
                # User ohne UserProfile sehen keine Tasks
                queryset = queryset.none()
        
        # Filter nach Status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter nach Priorität
        prioritaet_filter = self.request.GET.get('prioritaet')
        if prioritaet_filter:
            queryset = queryset.filter(prioritaet=prioritaet_filter)
        
        return queryset.order_by('prioritaet', 'fälligkeitsdatum', '-erstellt_am')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['prioritaet_filter'] = self.request.GET.get('prioritaet', '')
        return context


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "adeazeit/task_form.html"
    
    def get_initial(self):
        initial = super().get_initial()
        # Automatisch Mitarbeiter setzen für normale User
        if not self.request.user.is_staff:
            try:
                from .models import UserProfile
                user_profile = UserProfile.objects.get(user=self.request.user)
                if user_profile.employee:
                    initial["mitarbeiter"] = user_profile.employee
            except UserProfile.DoesNotExist:
                pass
        return initial
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Mitarbeiter-Feld verstecken für normale User
        if not self.request.user.is_staff:
            try:
                from .models import UserProfile
                user_profile = UserProfile.objects.get(user=self.request.user)
                if user_profile.employee:
                    form.fields['mitarbeiter'].widget = forms.HiddenInput()
                    form.fields['mitarbeiter'].initial = user_profile.employee
            except UserProfile.DoesNotExist:
                pass
        return form
    
    def form_valid(self, form):
        # Setze erledigt_am wenn Status auf ERLEDIGT
        if form.cleaned_data['status'] == 'ERLEDIGT' and not self.object.erledigt_am:
            form.instance.erledigt_am = timezone.now()
        elif form.cleaned_data['status'] != 'ERLEDIGT':
            form.instance.erledigt_am = None
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("adeazeit:task-list")


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "adeazeit/task_form.html"
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Mitarbeiter können nur eigene Tasks bearbeiten
        if not can_view_all_entries(self.request.user):
            try:
                from .models import UserProfile
                user_profile = UserProfile.objects.get(user=self.request.user)
                if user_profile.employee:
                    queryset = queryset.filter(mitarbeiter=user_profile.employee)
            except UserProfile.DoesNotExist:
                queryset = queryset.none()
        return queryset
    
    def form_valid(self, form):
        # Setze erledigt_am wenn Status auf ERLEDIGT
        if form.cleaned_data['status'] == 'ERLEDIGT' and not self.object.erledigt_am:
            form.instance.erledigt_am = timezone.now()
        elif form.cleaned_data['status'] != 'ERLEDIGT':
            form.instance.erledigt_am = None
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("adeazeit:task-list")


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy("adeazeit:task-list")
    template_name = "adeazeit/task_confirm_delete.html"
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Mitarbeiter können nur eigene Tasks löschen
        if not can_view_all_entries(self.request.user):
            try:
                from .models import UserProfile
                user_profile = UserProfile.objects.get(user=self.request.user)
                if user_profile.employee:
                    queryset = queryset.filter(mitarbeiter=user_profile.employee)
            except UserProfile.DoesNotExist:
                queryset = queryset.none()
        return queryset


# ============================================================================
# Timer Views (Live-Tracking)
# ============================================================================

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

@login_required
@require_http_methods(["POST"])
def start_timer(request):
    """Startet einen Live-Timer für Zeiterfassung."""
    try:
        data = json.loads(request.body)
        mitarbeiter_id = data.get('mitarbeiter_id')
        client_id = data.get('client_id')
        service_type_id = data.get('service_type_id')
        beschreibung = data.get('beschreibung', '')
        
        if not mitarbeiter_id or not service_type_id:
            return JsonResponse({"success": False, "error": "Mitarbeiter und Service-Typ sind erforderlich"})
        
        # Prüfe ob User Zugriff auf diesen Mitarbeiter hat
        from .permissions import get_accessible_employees
        accessible_employees = get_accessible_employees(request.user)
        mitarbeiter = get_object_or_404(accessible_employees, pk=mitarbeiter_id)
        
        service_type = get_object_or_404(ServiceType, pk=service_type_id)
        
        # Prüfe ob bereits ein Timer läuft
        existing_timer = RunningTimeEntry.objects.filter(mitarbeiter=mitarbeiter).first()
        if existing_timer:
            return JsonResponse({"success": False, "error": "Es läuft bereits ein Timer für diesen Mitarbeiter"})
        
        # Erstelle neuen Timer
        timer = RunningTimeEntry.objects.create(
            mitarbeiter=mitarbeiter,
            client_id=client_id if client_id else None,
            service_type=service_type,
            beschreibung=beschreibung
        )
        
        return JsonResponse({
            "success": True,
            "timer_id": timer.pk,
            "message": "Timer gestartet"
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Fehler beim Starten des Timers: {e}", exc_info=True)
        return JsonResponse({"success": False, "error": str(e)})


@login_required
@require_http_methods(["POST"])
def stop_timer(request):
    """Stoppt den laufenden Timer und erstellt einen Zeiteintrag."""
    try:
        from .permissions import get_accessible_employees
        accessible_employees = get_accessible_employees(request.user)
        
        # Finde Timer für einen der zugänglichen Mitarbeiter
        timer = RunningTimeEntry.objects.filter(mitarbeiter__in=accessible_employees).first()
        
        if not timer:
            return JsonResponse({"success": False, "error": "Kein laufender Timer gefunden"})
        
        # Berechne Dauer
        duration_hours = timer.get_duration_hours()
        
        # Erstelle Zeiteintrag
        rate = timer.service_type.standard_rate if timer.service_type.standard_rate else Decimal('0.00')
        betrag = duration_hours * rate
        
        # Berechne Start- und Endzeit
        start_time_local = timezone.localtime(timer.start_time)
        end_time_local = timezone.now()
        start_time_obj = start_time_local.time()
        
        # Runde Endzeit auf nächste Minute auf, um Konflikte zu vermeiden
        # (z.B. wenn Timer bei 10:30:45 gestoppt wird, wird Endzeit 10:31:00)
        from datetime import datetime, timedelta
        end_datetime_local = datetime.combine(end_time_local.date(), end_time_local.time())
        # Runde auf nächste Minute auf
        seconds = end_datetime_local.second
        if seconds > 0:
            end_datetime_local = end_datetime_local.replace(second=0, microsecond=0) + timedelta(minutes=1)
        else:
            end_datetime_local = end_datetime_local.replace(microsecond=0)
        
        end_time_obj = end_datetime_local.time()
        
        # Wenn Endzeit vor Startzeit (z.B. über Mitternacht), berechne korrekte Endzeit
        if end_time_obj < start_time_obj or (end_time_obj == start_time_obj and end_datetime_local.date() == timer.datum):
            # Timer läuft über Mitternacht oder Endzeit ist gleich Startzeit - berechne korrekte Endzeit basierend auf Dauer
            start_datetime = datetime.combine(timer.datum, start_time_obj)
            end_datetime = start_datetime + timedelta(hours=float(duration_hours))
            end_time_obj = end_datetime.time()
            # Aktualisiere auch das Datum falls nötig
            if end_datetime.date() > timer.datum:
                # Timer läuft über Mitternacht - verwende das Datum vom Start
                # Die Dauer wird korrekt berechnet, auch wenn es über Mitternacht geht
                pass
        
        # Stelle sicher, dass Dauer mindestens 0.01 Stunden ist
        if duration_hours <= 0:
            duration_hours = Decimal('0.01')  # Mindestdauer: 36 Sekunden
        
        # Stelle sicher, dass Kommentar nicht verloren geht
        kommentar = timer.beschreibung if timer.beschreibung else ''
        
        # Erstelle TimeEntry ohne clean() zu rufen (um Validierung zu umgehen)
        time_entry = TimeEntry(
            mitarbeiter=timer.mitarbeiter,
            client=timer.client,
            service_type=timer.service_type,
            project=timer.projekt,  # projekt (RunningTimeEntry) -> project (TimeEntry)
            datum=timer.datum,
            start=start_time_obj,
            ende=end_time_obj,
            dauer=duration_hours,
            rate=rate,
            betrag=betrag,
            billable=timer.service_type.billable,
            kommentar=kommentar
        )
        # Validiere manuell (ohne ende <= start Check wenn über Mitternacht)
        if time_entry.dauer <= 0:
            raise ValueError("Dauer muss größer als 0 sein.")
        time_entry.save()
        
        # Lösche Timer
        timer.delete()
        
        return JsonResponse({
            "success": True,
            "duration_hours": str(duration_hours),
            "time_entry_id": time_entry.pk,
            "message": "Zeiteintrag gespeichert"
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Fehler beim Stoppen des Timers: {e}", exc_info=True)
        return JsonResponse({"success": False, "error": str(e)})
