from decimal import Decimal
from calendar import month_name
from datetime import datetime, timedelta, date
from django.db.models import Q, Sum
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from .login_view import employee_login, employee_logout
from django.contrib import messages
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
)
from django.http import JsonResponse
from django import forms

from adeacore.models import Client
from .models import EmployeeInternal, ServiceType, ZeitProject, TimeEntry, Absence, Task, Task
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
    can_view_all_entries,
    can_edit_all_entries,
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
    login_url = '/zeit/login/'

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

    def get(self, request, *args, **kwargs):
        # Entferne Passwort aus Session wenn gewünscht
        if request.GET.get('clear_password'):
            request.session.pop('created_password', None)
            request.session.pop('created_username', None)
            request.session.pop('created_employee', None)
            request.session.save()  # Wichtig: Session explizit speichern
        return super().get(request, *args, **kwargs)

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
        
        # Erstelle Login-Zugang falls gewünscht
        self.create_user_access(form)
        
        return response
    
    def create_user_access(self, form):
        """Erstellt einen Benutzer-Zugang für den Mitarbeiter, falls gewünscht."""
        create_login = form.cleaned_data.get('create_login')
        if not create_login:
            return
        
        from django.contrib.auth.models import User, Group
        from django.db import transaction
        from .models import UserProfile
        from .permissions import ROLE_ADMIN, ROLE_MANAGER, ROLE_MITARBEITER
        
        login_username = form.cleaned_data.get('login_username', '').strip()
        login_password = form.cleaned_data.get('login_password', '').strip()
        login_email = form.cleaned_data.get('login_email', '').strip()
        login_role = form.cleaned_data.get('login_role', 'mitarbeiter')
        
        # Generiere Username aus Code falls leer
        if not login_username:
            login_username = self.object.code.lower()
        
        # Generiere Passwort falls leer (Format: Code123)
        if not login_password:
            login_password = f"{self.object.code}123"
        
        # Rolle-Mapping
        role_map = {
            'admin': ROLE_ADMIN,
            'manager': ROLE_MANAGER,
            'mitarbeiter': ROLE_MITARBEITER,
        }
        role_name = role_map.get(login_role, ROLE_MITARBEITER)
        
        try:
            with transaction.atomic():
                # Prüfe ob User bereits existiert
                user, created = User.objects.get_or_create(username=login_username)
                
                if created:
                    # Neuer User: Setze Passwort
                    user.set_password(login_password)
                    if login_email:
                        user.email = login_email
                    # Name aus EmployeeInternal
                    name_parts = self.object.name.split()
                    if name_parts:
                        user.first_name = name_parts[0]
                        if len(name_parts) > 1:
                            user.last_name = ' '.join(name_parts[1:])
                    user.save()
                else:
                    # Bestehender User: Passwort nur ändern wenn angegeben
                    if login_password:
                        user.set_password(login_password)
                    if login_email:
                        user.email = login_email
                    user.save()
                
                # Weise Rolle zu
                group, _ = Group.objects.get_or_create(name=role_name)
                user.groups.clear()
                user.groups.add(group)
                
                # Erstelle/Update UserProfile
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.employee = self.object
                profile.save()
                
                # Speichere Passwort in Session für Anzeige nach Redirect
                if created or login_password:
                    self.request.session['created_password'] = login_password
                    self.request.session['created_username'] = login_username
                    self.request.session['created_employee'] = self.object.name
                
                # Versende E-Mail falls angegeben
                if login_email:
                    self.send_password_email(user, login_password, login_username)
                
                if created:
                    messages.success(self.request, f'Login-Zugang erstellt! Benutzername und Passwort werden unten angezeigt.')
                else:
                    messages.info(self.request, f'Login-Zugang aktualisiert für Benutzername "{login_username}"')
                    
        except Exception as e:
            messages.error(self.request, f'Fehler beim Erstellen des Login-Zugangs: {e}')
    
    def send_password_email(self, user, password, username):
        """Versendet Passwort per E-Mail (optional)."""
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            # Prüfe ob E-Mail konfiguriert ist
            if not hasattr(settings, 'EMAIL_HOST') or not settings.EMAIL_HOST:
                return False
            
            subject = f'AdeaZeit - Ihr Login-Zugang für {self.object.name}'
            message = f"""
Hallo {self.object.name},

Ihr Login-Zugang für AdeaZeit wurde erstellt:

Benutzername: {username}
Passwort: {password}

Sie können sich hier einloggen: http://127.0.0.1:8000/admin/

Bitte ändern Sie Ihr Passwort nach dem ersten Login.

Mit freundlichen Grüssen
AdeaTools Team
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL or 'noreply@adea-tools.ch',
                [user.email],
                fail_silently=True,
            )
            return True
        except Exception:
            # E-Mail-Versand fehlgeschlagen, aber nicht kritisch
            return False

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
        
        # Erstelle/Update Login-Zugang falls gewünscht
        self.create_user_access(form)
        
        return response
    
    def create_user_access(self, form):
        """Erstellt oder aktualisiert einen Benutzer-Zugang für den Mitarbeiter, falls gewünscht."""
        create_login = form.cleaned_data.get('create_login')
        if not create_login:
            return
        
        from django.contrib.auth.models import User, Group
        from django.db import transaction
        from .models import UserProfile
        from .permissions import ROLE_ADMIN, ROLE_MANAGER, ROLE_MITARBEITER
        
        login_username = form.cleaned_data.get('login_username', '').strip()
        login_password = form.cleaned_data.get('login_password', '').strip()
        login_email = form.cleaned_data.get('login_email', '').strip()
        login_role = form.cleaned_data.get('login_role', 'mitarbeiter')
        
        if not login_username:
            login_username = self.object.code.lower()
        
        # Rolle-Mapping
        role_map = {
            'admin': ROLE_ADMIN,
            'manager': ROLE_MANAGER,
            'mitarbeiter': ROLE_MITARBEITER,
        }
        role_name = role_map.get(login_role, ROLE_MITARBEITER)
        
        try:
            with transaction.atomic():
                # Prüfe ob User bereits existiert (über UserProfile)
                try:
                    existing_profile = UserProfile.objects.get(employee=self.object)
                    user = existing_profile.user
                    user_created = False
                except UserProfile.DoesNotExist:
                    # Neuer Zugang
                    user, user_created = User.objects.get_or_create(username=login_username)
                
                # Setze/Update Passwort nur wenn angegeben oder neuer User
                if login_password or user_created:
                    if not login_password:
                        login_password = f"{self.object.code}123"
                    user.set_password(login_password)
                
                if login_email:
                    user.email = login_email
                
                # Name aus EmployeeInternal
                name_parts = self.object.name.split()
                if name_parts:
                    user.first_name = name_parts[0]
                    if len(name_parts) > 1:
                        user.last_name = ' '.join(name_parts[1:])
                
                user.save()
                
                # Weise Rolle zu
                group, _ = Group.objects.get_or_create(name=role_name)
                user.groups.clear()
                user.groups.add(group)
                
                # Erstelle/Update UserProfile
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.employee = self.object
                profile.save()
                
                # Speichere Passwort in Session für Anzeige nach Redirect
                if user_created or login_password:
                    self.request.session['created_password'] = login_password
                    self.request.session['created_username'] = login_username
                    self.request.session['created_employee'] = self.object.name
                
                # Versende E-Mail falls angegeben
                if login_email:
                    self.send_password_email(user, login_password, login_username)
                
                if user_created:
                    messages.success(self.request, f'Login-Zugang erstellt! Benutzername und Passwort werden unten angezeigt.')
                else:
                    messages.info(self.request, f'Login-Zugang aktualisiert für Benutzername "{login_username}"')
                    
        except Exception as e:
            messages.error(self.request, f'Fehler beim Erstellen des Login-Zugangs: {e}')
    
    def send_password_email(self, user, password, username):
        """Versendet Passwort per E-Mail (optional)."""
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            # Prüfe ob E-Mail konfiguriert ist
            if not hasattr(settings, 'EMAIL_HOST') or not settings.EMAIL_HOST:
                return False
            
            subject = f'AdeaZeit - Ihr Login-Zugang für {self.object.name}'
            message = f"""
Hallo {self.object.name},

Ihr Login-Zugang für AdeaZeit wurde erstellt:

Benutzername: {username}
Passwort: {password}

Sie können sich hier einloggen: http://127.0.0.1:8000/admin/

Bitte ändern Sie Ihr Passwort nach dem ersten Login.

Mit freundlichen Grüssen
AdeaTools Team
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL or 'noreply@adea-tools.ch',
                [user.email],
                fail_silently=True,
            )
            return True
        except Exception:
            # E-Mail-Versand fehlgeschlagen, aber nicht kritisch
            return False

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
        
        # Berechne vorheriges und nächstes Datum für Navigation
        from datetime import timedelta
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
        # Zugängliche Mitarbeiter-IDs für Template-Prüfung
        accessible_employees = get_accessible_employees(self.request.user)
        context["accessible_employee_ids"] = list(accessible_employees.values_list('pk', flat=True))
        
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
        # Berechne vorherige und nächste Woche für Navigation
        context["previous_monday"] = monday - timedelta(days=7)
        context["next_monday"] = monday + timedelta(days=7)
        
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
        # Zugängliche Mitarbeiter-IDs für Template-Prüfung
        accessible_employees = get_accessible_employees(self.request.user)
        context["accessible_employee_ids"] = list(accessible_employees.values_list('pk', flat=True))
        
        return context


class TimeEntryCreateView(LoginRequiredMixin, CreateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = "adeazeit/timeentry_form.html"

    def get_initial(self):
        initial = super().get_initial()
        # Default: Heute
        initial["datum"] = date.today()
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter Mitarbeiter nach Rolle
        if not can_view_all_entries(self.request.user):
            form.fields["mitarbeiter"].queryset = get_accessible_employees(self.request.user)
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


class TimeEntryUpdateView(LoginRequiredMixin, CanEditMixin, UpdateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = "adeazeit/timeentry_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        obj = self.get_object()
        
        # Prüfe, ob User alle Einträge bearbeiten kann
        if can_edit_all_entries(request.user):
            return super().dispatch(request, *args, **kwargs)
        
        # Prüfe, ob User den eigenen Eintrag bearbeitet
        accessible_employees = get_accessible_employees(request.user)
        # Konvertiere QuerySet zu Liste von IDs für zuverlässige Prüfung
        accessible_employee_ids = list(accessible_employees.values_list('pk', flat=True))
        if obj.mitarbeiter.pk not in accessible_employee_ids:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Sie können nur eigene Zeiteinträge bearbeiten.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Übergib User an Form für Rollenprüfung
        form.user = self.request.user
        # Filter Mitarbeiter nach Rolle
        if not can_view_all_entries(self.request.user):
            accessible_employees = get_accessible_employees(self.request.user)
            form.fields["mitarbeiter"].queryset = accessible_employees
            # Feld auf readonly setzen für Mitarbeiter
            form.fields["mitarbeiter"].widget.attrs['readonly'] = True
            form.fields["mitarbeiter"].widget.attrs['style'] = 'background: #f5f5f7; cursor: not-allowed;'
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mitarbeiter-Info für Sidebar
        if self.object and self.object.mitarbeiter:
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
        # Übergib User an Form für Rollenprüfung
        form.user = self.request.user
        # Filter Mitarbeiter nach Rolle
        if not can_view_all_entries(self.request.user):
            accessible_employees = get_accessible_employees(self.request.user)
            form.fields["employee"].queryset = accessible_employees
            # Setze automatisch auf eigenen Mitarbeiter
            if accessible_employees.exists():
                form.fields["employee"].initial = accessible_employees.first()
                form.fields["employee"].widget.attrs['readonly'] = True
                form.fields["employee"].widget.attrs['style'] = 'background: #f5f5f7; cursor: not-allowed;'
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
        # Übergib User an Form für Rollenprüfung
        form.user = self.request.user
        # Filter Mitarbeiter nach Rolle
        if not can_view_all_entries(self.request.user):
            accessible_employees = get_accessible_employees(self.request.user)
            form.fields["employee"].queryset = accessible_employees
            # Feld auf readonly setzen für Mitarbeiter
            form.fields["employee"].widget.attrs['readonly'] = True
            form.fields["employee"].widget.attrs['style'] = 'background: #f5f5f7; cursor: not-allowed;'
        return form

    def get_success_url(self):
        return reverse("adeazeit:absence-list")


class AbsenceDeleteView(AdminRequiredMixin, DeleteView):
    model = Absence
    template_name = "adeazeit/absence_confirm_delete.html"
    success_url = reverse_lazy("adeazeit:absence-list")


# ============================================================================
# Task Views (To-Do-Liste)
# ============================================================================

class TaskListView(LoginRequiredMixin, ListView):
    """Liste aller Aufgaben für den eingeloggten Mitarbeiter."""
    model = Task
    template_name = "adeazeit/task_list.html"
    context_object_name = "tasks"

    def get_queryset(self):
        # Filter nach Rolle
        from .permissions import get_accessible_employees, can_view_all_entries
        
        if can_view_all_entries(self.request.user):
            queryset = Task.objects.all()
        else:
            # Mitarbeiter: Nur eigene Aufgaben
            accessible_employees = get_accessible_employees(self.request.user)
            queryset = Task.objects.filter(mitarbeiter__in=accessible_employees)
        
        # Filter nach Status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter nach Mandant
        client_filter = self.request.GET.get('client')
        if client_filter:
            queryset = queryset.filter(client_id=client_filter)
        
        # Filter nach Priorität
        prioritaet_filter = self.request.GET.get('prioritaet')
        if prioritaet_filter:
            queryset = queryset.filter(prioritaet=prioritaet_filter)
        
        # Suche
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(titel__icontains=search_query) |
                Q(beschreibung__icontains=search_query) |
                Q(notizen__icontains=search_query)
            )
        
        return queryset.select_related('mitarbeiter', 'client').order_by(
            'prioritaet', 'fälligkeitsdatum', '-erstellt_am'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_filter"] = self.request.GET.get('status', '')
        context["client_filter"] = self.request.GET.get('client', '')
        context["prioritaet_filter"] = self.request.GET.get('prioritaet', '')
        context["search_query"] = self.request.GET.get('q', '')
        
        # Verfügbare Mandanten für Filter
        from .permissions import get_accessible_employees, can_view_all_entries
        if can_view_all_entries(self.request.user):
            context["clients"] = Client.objects.all().order_by("name")
        else:
            # Nur Mandanten mit eigenen Aufgaben
            accessible_employees = get_accessible_employees(self.request.user)
            task_clients = Task.objects.filter(mitarbeiter__in=accessible_employees).values_list('client_id', flat=True).distinct()
            context["clients"] = Client.objects.filter(id__in=task_clients).order_by("name")
        
        # Statistiken
        queryset = self.get_queryset()
        context["stats"] = {
            "total": queryset.count(),
            "offen": queryset.filter(status='OFFEN').count(),
            "in_arbeit": queryset.filter(status='IN_ARBEIT').count(),
            "erledigt": queryset.filter(status='ERLEDIGT').count(),
            "ueberfaellig": queryset.filter(fälligkeitsdatum__lt=date.today()).exclude(status='ERLEDIGT').count(),
        }
        
        return context


class TaskCreateView(LoginRequiredMixin, CreateView):
    """Neue Aufgabe erstellen."""
    model = Task
    form_class = TaskForm
    template_name = "adeazeit/task_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Übergib User an Form
        form.user = self.request.user
        return form

    def form_valid(self, form):
        # Setze Mitarbeiter automatisch basierend auf Rolle
        if can_view_all_entries(self.request.user):
            # Admin/Manager: Kann Mitarbeiter auswählen (wird im Form gemacht)
            if 'mitarbeiter' not in form.cleaned_data or not form.cleaned_data.get('mitarbeiter'):
                # Fallback: Erster aktiver Mitarbeiter
                from .models import EmployeeInternal
                employee = EmployeeInternal.objects.filter(aktiv=True).first()
                if not employee:
                    form.add_error('mitarbeiter', 'Kein aktiver Mitarbeiter gefunden. Bitte erstellen Sie zuerst einen Mitarbeiter.')
                    return self.form_invalid(form)
                form.instance.mitarbeiter = employee
        else:
            # Mitarbeiter: Automatisch auf sich selbst setzen
            accessible_employees = get_accessible_employees(self.request.user)
            if accessible_employees.exists():
                form.instance.mitarbeiter = accessible_employees.first()
            else:
                form.add_error(None, 'Kein Mitarbeiter-Profil gefunden. Bitte kontaktieren Sie den Administrator.')
                return self.form_invalid(form)
        
        # Prüfe, ob Mitarbeiter gesetzt wurde
        if not form.instance.mitarbeiter:
            form.add_error('mitarbeiter', 'Bitte wählen Sie einen Mitarbeiter aus.')
            return self.form_invalid(form)
        
        response = super().form_valid(form)
        messages.success(self.request, f'Aufgabe "{self.object.titel}" wurde erfolgreich erstellt.')
        return response

    def get_success_url(self):
        return reverse("adeazeit:task-list")


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    """Aufgabe bearbeiten."""
    model = Task
    form_class = TaskForm
    template_name = "adeazeit/task_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        obj = self.get_object()
        
        # Prüfe, ob User alle Aufgaben bearbeiten kann
        if can_view_all_entries(request.user):
            return super().dispatch(request, *args, **kwargs)
        
        # Prüfe, ob User die eigene Aufgabe bearbeitet
        accessible_employees = get_accessible_employees(request.user)
        if obj.mitarbeiter not in accessible_employees:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Sie können nur eigene Aufgaben bearbeiten.")
        
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Übergib User an Form
        form.user = self.request.user
        
        # Mitarbeiter-Feld readonly für Mitarbeiter
        if not can_view_all_entries(self.request.user):
            form.fields["mitarbeiter"] = forms.ModelChoiceField(
                queryset=get_accessible_employees(self.request.user),
                widget=forms.Select(attrs={"class": "adea-select", "readonly": True, "style": "background: #f5f5f7; cursor: not-allowed;"}),
                required=False
            )
            form.fields["mitarbeiter"].initial = self.object.mitarbeiter
        
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Aufgabe "{self.object.titel}" wurde erfolgreich aktualisiert.')
        return response

    def get_success_url(self):
        return reverse("adeazeit:task-list")


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    """Aufgabe löschen."""
    model = Task
    template_name = "adeazeit/task_confirm_delete.html"
    success_url = reverse_lazy("adeazeit:task-list")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        obj = self.get_object()
        
        # Prüfe, ob User alle Aufgaben löschen kann
        if can_delete_entries(request.user):
            return super().dispatch(request, *args, **kwargs)
        
        # Prüfe, ob User die eigene Aufgabe löscht
        accessible_employees = get_accessible_employees(request.user)
        if obj.mitarbeiter not in accessible_employees:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Sie können nur eigene Aufgaben löschen.")
        
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        task_title = self.get_object().titel
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Aufgabe "{task_title}" wurde erfolgreich gelöscht.')
        return response


class TaskQuickStatusUpdateView(LoginRequiredMixin, TemplateView):
    """Schnelle Status-Änderung per AJAX."""
    
    def post(self, request, *args, **kwargs):
        task_id = request.POST.get('task_id')
        new_status = request.POST.get('status')
        
        if not task_id or not new_status:
            return JsonResponse({"success": False, "error": "Fehlende Parameter"})
        
        try:
            task = Task.objects.get(pk=task_id)
            
            # Berechtigung prüfen
            if not can_view_all_entries(request.user):
                accessible_employees = get_accessible_employees(request.user)
                if task.mitarbeiter not in accessible_employees:
                    return JsonResponse({"success": False, "error": "Keine Berechtigung"})
            
            # Status ändern
            if new_status in ['OFFEN', 'IN_ARBEIT', 'ERLEDIGT']:
                task.status = new_status
                task.save()
                return JsonResponse({"success": True, "status": new_status})
            else:
                return JsonResponse({"success": False, "error": "Ungültiger Status"})
                
        except Task.DoesNotExist:
            return JsonResponse({"success": False, "error": "Aufgabe nicht gefunden"})
