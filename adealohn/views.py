from decimal import Decimal
from calendar import month_name
from datetime import datetime, timedelta
import logging

from django.db.models import Q, Sum
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    TemplateView,
    FormView,
)
from django import forms
from django.contrib import messages

from adeacore.models import Employee, Client, TimeRecord, PayrollRecord
from adealohn.models import (
    WageType, WageTypeCategory, BVGParameter, PayrollItem, FamilyAllowanceParameter,
    AHVParameter, ALVParameter, VKParameter, KTGParameter, UVGParameter, FAKParameter
)
from .forms import (
    EmployeeForm, PayrollRecordForm, FamilyAllowanceNachzahlungForm, FamilyAllowanceLaufendForm, 
    PayrollItemSpesenForm, PayrollItemPrivatanteilForm, PayrollItemGeneralForm, InsuranceRatesForm
)
from .mixins import (
    TenantMixin,
    TenantFilterMixin,
    TenantObjectMixin,
    LockedPayrollGuardMixin,
    LockedPayrollFormGuardMixin,
)
from .payroll_flow import create_payroll_item_and_recompute
from adeacore.tenancy import resolve_current_client
from .helpers import (
    percent_to_decimal, decimal_to_percent,
    get_parameter_for_year, get_firma_clients_with_lohn_aktiv,
    ensure_grundlohn_wage_type, ensure_ferien_wage_type,
)

logger = logging.getLogger(__name__)


class ClientSwitchView(LoginRequiredMixin, TemplateView):
    """View zum Wechseln des aktiven Mandanten (Client)."""
    template_name = "adealohn/client_switch.html"
    login_url = '/admin/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Nur Firmen-Mandanten mit aktiviertem Lohnmodul anzeigen
        context['clients'] = Client.objects.filter(
            client_type="FIRMA",
            lohn_aktiv=True
        ).order_by("name")
        
        current_client = resolve_current_client(self.request)
        context['current_client'] = current_client
        
        return context
    
    def post(self, request, *args, **kwargs):
        client_id = request.POST.get('client_id')
        if client_id:
            try:
                client = Client.objects.get(pk=client_id)
                if client.client_type == "FIRMA" and client.lohn_aktiv:
                    request.session['active_client_id'] = client_id
                    messages.success(request, f"Mandant '{client.name}' wurde ausgewählt.")
                    return redirect('adealohn:employee-list')
                else:
                    messages.error(request, "Ungültiger Mandant ausgewählt.")
            except Client.DoesNotExist:
                messages.error(request, "Mandant nicht gefunden.")
        
        return redirect('adealohn:client_switch')


class InsuranceRatesView(LoginRequiredMixin, TenantMixin, FormView):
    """
    View zum Eingeben aller Versicherungsansätze (Arbeitgeber-Ebene) pro Jahr.
    Entspricht der Excel-Vorlage "VERSICHERUNGSANSÄTZE".
    """
    template_name = "adealohn/insurance_rates.html"
    form_class = InsuranceRatesForm
    login_url = '/admin/login/'
    
    def get_initial(self):
        """Lade vorhandene Parameter für das aktuelle Jahr (oder Standardwerte)."""
        current_year = datetime.now().year
        year = int(self.request.GET.get('year', current_year))
        
        initial = {'year': year}
        
        # AHV Parameter (Umwandlung von Dezimal zu Prozent)
        ahv = get_parameter_for_year(AHVParameter, year)
        if ahv:
            initial['ahv_rate_employee'] = decimal_to_percent(ahv.rate_employee)
            initial['ahv_rate_employer'] = decimal_to_percent(ahv.rate_employer)
            initial['ahv_rentner_freibetrag'] = ahv.rentner_freibetrag_monat
        else:
            initial['ahv_rate_employee'] = Decimal("5.3")
            initial['ahv_rate_employer'] = Decimal("5.3")
            initial['ahv_rentner_freibetrag'] = Decimal("1400.00")
        
        # ALV Parameter (Umwandlung von Dezimal zu Prozent)
        alv = get_parameter_for_year(ALVParameter, year)
        if alv:
            initial['alv_rate_employee'] = decimal_to_percent(alv.rate_employee)
            initial['alv_rate_employer'] = decimal_to_percent(alv.rate_employer)
            initial['alv_max_annual'] = alv.max_annual_insured_salary
        else:
            initial['alv_rate_employee'] = Decimal("1.1")
            initial['alv_rate_employer'] = Decimal("1.1")
            initial['alv_max_annual'] = Decimal("148200.00")
        
        # FAK Parameter (DEFAULT) (Umwandlung von Dezimal zu Prozent)
        current_client = self.get_current_client()
        canton = current_client.work_canton if current_client else None
        fak = get_parameter_for_year(FAKParameter, year, canton=(canton or "DEFAULT"))
        if not fak:
            fak = get_parameter_for_year(FAKParameter, year, canton="DEFAULT")
        if fak:
            initial['fak_canton'] = fak.canton
            initial['fak_rate_employer'] = decimal_to_percent(fak.fak_rate_employer)
        else:
            initial['fak_canton'] = canton or "DEFAULT"
            initial['fak_rate_employer'] = Decimal("1.0")
        
        # VK Parameter (Umwandlung von Dezimal zu Prozent)
        vk = get_parameter_for_year(VKParameter, year)
        if vk:
            initial['vk_rate_employer'] = decimal_to_percent(vk.rate_employer)
        else:
            initial['vk_rate_employer'] = Decimal("3.0")
        
        # UVG Parameter (Umwandlung von Dezimal zu Prozent)
        uvg = get_parameter_for_year(UVGParameter, year)
        if uvg:
            initial['bu_rate_employer'] = decimal_to_percent(uvg.bu_rate_employer)
            initial['nbu_rate_employee'] = decimal_to_percent(uvg.nbu_rate_employee)
            initial['uvg_max_annual'] = uvg.max_annual_insured_salary
        else:
            initial['bu_rate_employer'] = Decimal("0.644")
            initial['nbu_rate_employee'] = Decimal("2.3")
            initial['uvg_max_annual'] = Decimal("148200.00")
        
        # KTG Parameter (Umwandlung von Dezimal zu Prozent)
        ktg = get_parameter_for_year(KTGParameter, year)
        if ktg:
            initial['ktg_rate_employee'] = decimal_to_percent(ktg.ktg_rate_employee)
            initial['ktg_rate_employer'] = decimal_to_percent(ktg.ktg_rate_employer)
            initial['ktg_max_basis'] = ktg.ktg_max_basis
        else:
            initial['ktg_rate_employee'] = Decimal("0.5")
            initial['ktg_rate_employer'] = Decimal("0.5")
            initial['ktg_max_basis'] = Decimal("300000.00")
        
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_client = self.get_current_client()
        context['current_client'] = current_client
        context['current_year'] = datetime.now().year
        context['available_years'] = list(range(2020, 2030))  # Jahre 2020-2029
        return context
    
    def form_valid(self, form):
        """Speichere alle Parameter-Models."""
        year = form.cleaned_data['year']
        
        # AHV Parameter (Umwandlung von Prozent zu Dezimal)
        ahv, _ = AHVParameter.objects.update_or_create(
            year=year,
            defaults={
                'rate_employee': percent_to_decimal(form.cleaned_data['ahv_rate_employee']),
                'rate_employer': percent_to_decimal(form.cleaned_data['ahv_rate_employer']),
                'rentner_freibetrag_monat': form.cleaned_data['ahv_rentner_freibetrag'],
            }
        )
        
        # ALV Parameter (Umwandlung von Prozent zu Dezimal)
        alv, _ = ALVParameter.objects.update_or_create(
            year=year,
            defaults={
                'rate_employee': percent_to_decimal(form.cleaned_data['alv_rate_employee']),
                'rate_employer': percent_to_decimal(form.cleaned_data['alv_rate_employer']),
                'max_annual_insured_salary': form.cleaned_data['alv_max_annual'],
            }
        )
        
        # FAK Parameter (Umwandlung von Prozent zu Dezimal)
        fak_canton = form.cleaned_data.get('fak_canton', 'DEFAULT') or 'DEFAULT'
        fak, _ = FAKParameter.objects.update_or_create(
            year=year,
            canton=fak_canton.upper(),
            defaults={
                'fak_rate_employer': percent_to_decimal(form.cleaned_data['fak_rate_employer']),
            }
        )
        
        # VK Parameter (Umwandlung von Prozent zu Dezimal)
        vk, _ = VKParameter.objects.update_or_create(
            year=year,
            defaults={
                'rate_employer': percent_to_decimal(form.cleaned_data['vk_rate_employer']),
            }
        )
        
        # UVG Parameter (Umwandlung von Prozent zu Dezimal)
        uvg, _ = UVGParameter.objects.update_or_create(
            year=year,
            defaults={
                'bu_rate_employer': percent_to_decimal(form.cleaned_data['bu_rate_employer']),
                'nbu_rate_employee': percent_to_decimal(form.cleaned_data['nbu_rate_employee']),
                'max_annual_insured_salary': form.cleaned_data['uvg_max_annual'],
            }
        )
        
        # KTG Parameter (Umwandlung von Prozent zu Dezimal)
        ktg, _ = KTGParameter.objects.update_or_create(
            year=year,
            defaults={
                'ktg_rate_employee': percent_to_decimal(form.cleaned_data['ktg_rate_employee']),
                'ktg_rate_employer': percent_to_decimal(form.cleaned_data['ktg_rate_employer']),
                'ktg_max_basis': form.cleaned_data.get('ktg_max_basis'),
            }
        )
        
        # Cache leeren nach Änderungen
        from .helpers import clear_parameter_cache
        clear_parameter_cache()
        
        messages.success(self.request, f"Versicherungsansätze für {year} wurden gespeichert.")
        return redirect('adealohn:insurance-rates')


class EmployeeListView(LoginRequiredMixin, TenantFilterMixin, ListView):
    model = Employee
    template_name = "adealohn/list.html"
    context_object_name = "employees"
    login_url = '/admin/login/'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        current_client = self.get_current_client()
        
        if current_client:
            queryset = queryset.filter(client=current_client)
        
        # Suche
        query = self.request.GET.get("q", "")
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(role__icontains=query)
                | Q(client__name__icontains=query)
            )
        
        return queryset.order_by("last_name", "first_name")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Nur FIRMA-Clients mit aktiviertem Lohnmodul im Filter anzeigen
        context["clients"] = get_firma_clients_with_lohn_aktiv()
        context["selected_client"] = self.request.GET.get("client", "")
        context["query"] = self.request.GET.get("q", "")
        return context


class EmployeeCreateView(LoginRequiredMixin, TenantMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "adealohn/form.html"
    login_url = '/admin/login/'
    
    def get_form(self, form_class=None):
        """Filtere Client-Feld nach current_client."""
        form = super().get_form(form_class)
        current_client = self.get_current_client()
        
        if current_client:
            # Setze current_client als Default (nur wenn es eine Firma ist)
            if current_client.client_type == "FIRMA":
                form.fields["client"].queryset = Client.objects.filter(pk=current_client.pk)
                form.initial["client"] = current_client.pk
            else:
                form.fields["client"].queryset = Client.objects.none()
        else:
            # Kein Mandant ausgewählt - zeige alle FIRMA-Clients
            form.fields["client"].queryset = Client.objects.filter(
                client_type="FIRMA",
                lohn_aktiv=True
            )
        
        return form
    
    def get_success_url(self):
        return reverse("adealohn:employee-detail", args=[self.object.pk])


class EmployeeDetailView(LoginRequiredMixin, TenantObjectMixin, DetailView):
    model = Employee
    template_name = "adealohn/detail.html"
    login_url = '/admin/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.object
        
        # Zeiteinträge für diesen Mitarbeiter
        time_records = TimeRecord.objects.filter(employee=employee).order_by("-date")[:10]
        hours_sum = time_records.aggregate(total=Sum("hours"))["total"] or Decimal("0")
        
        context["time_records"] = time_records
        context["hours_sum"] = hours_sum
        
        return context


class EmployeeUpdateView(LoginRequiredMixin, TenantObjectMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "adealohn/form.html"
    login_url = '/admin/login/'
    
    def get_form(self, form_class=None):
        """Filtere Client-Feld nach current_client."""
        form = super().get_form(form_class)
        current_client = self.get_current_client()
        
        if current_client and current_client.client_type == "FIRMA":
            form.fields["client"].queryset = Client.objects.filter(pk=current_client.pk)
        else:
            form.fields["client"].queryset = Client.objects.filter(
                client_type="FIRMA",
                lohn_aktiv=True
            )
        
        return form
    
    def get_success_url(self):
        return reverse("adealohn:employee-detail", args=[self.object.pk])


class EmployeeDeleteView(LoginRequiredMixin, TenantObjectMixin, DeleteView):
    model = Employee
    template_name = "adealohn/confirm_delete.html"
    login_url = '/admin/login/'
    success_url = reverse_lazy("adealohn:employee-list")


class PayrollRecordListView(LoginRequiredMixin, TenantFilterMixin, ListView):
    model = PayrollRecord
    template_name = "adealohn/payroll/list.html"
    context_object_name = "records"
    login_url = '/admin/login/'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        current_client = self.get_current_client()
        
        if current_client:
            queryset = queryset.filter(employee__client=current_client)
        
        # Filter nach Mitarbeiter
        employee_id = self.request.GET.get("employee")
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter nach Monat
        month = self.request.GET.get("month")
        if month:
            queryset = queryset.filter(month=month)
        
        # Filter nach Jahr
        year = self.request.GET.get("year")
        if year:
            queryset = queryset.filter(year=year)
        
        # Suche
        query = self.request.GET.get("q", "")
        if query:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=query)
                | Q(employee__last_name__icontains=query)
                | Q(employee__client__name__icontains=query)
            )
        
        return queryset.select_related("employee", "employee__client").order_by("-year", "-month", "employee__last_name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_client = self.get_current_client()
        
        # Mitarbeiter für Filter
        if current_client:
            employees = Employee.objects.filter(client=current_client).order_by("last_name", "first_name")
        else:
            employees = Employee.objects.none()
        
        # Jahre für Filter (aus vorhandenen PayrollRecords)
        years = PayrollRecord.objects.filter(employee__client=current_client).values_list('year', flat=True).distinct().order_by('-year') if current_client else []
        
        # Monate für Filter
        from calendar import month_name
        months = [(i, month_name[i]) for i in range(1, 13)]
        
        context["employees"] = employees
        context["years"] = years
        context["months"] = months
        context["selected_employee"] = self.request.GET.get("employee", "")
        context["selected_month"] = self.request.GET.get("month", "")
        context["selected_year"] = self.request.GET.get("year", "")
        context["query"] = self.request.GET.get("q", "")
        
        return context


class PayrollRecordMixin:
    """Mixin für PayrollRecord Views mit gemeinsamer Logik."""
    
    def get_hours_total(self, employee, month, year):
        """Berechnet Gesamtstunden aus TimeRecords für Monat/Jahr."""
        time_records = TimeRecord.objects.filter(
            employee=employee,
            date__month=month,
            date__year=year,
        )
        total = time_records.aggregate(total=Sum("hours"))["total"]
        return total or Decimal("0")

    def ensure_wage_type(self, code, name):
        wage_type, _ = WageType.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "category": WageTypeCategory.BASIS,
                "is_lohnwirksam": True,
                "ahv_relevant": True,
                "alv_relevant": True,
                "uv_relevant": True,
                "bvg_relevant": True,
                "qst_relevant": True,
                "taxable": True,
            },
        )
        return wage_type

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hours_total"] = getattr(self, "hours_total", None)
        return context


class PayrollRecordCreateView(LoginRequiredMixin, TenantMixin, PayrollRecordMixin, CreateView):
    model = PayrollRecord
    form_class = PayrollRecordForm
    template_name = "adealohn/payroll/form.html"
    login_url = '/admin/login/'
    
    def get_initial(self):
        """Setze Initialwerte für Jahr und Monat auf aktuelle Werte."""
        initial = super().get_initial()
        today = datetime.now()
        initial['year'] = today.year
        initial['month'] = today.month
        return initial
    
    def get_form(self, form_class=None):
        """Filtere Employee-Feld nach current_client."""
        form = super().get_form(form_class)
        current_client = self.get_current_client()
        
        if current_client and current_client.client_type == "FIRMA":
            form.fields["employee"].queryset = Employee.objects.filter(client=current_client)
        else:
            form.fields["employee"].queryset = Employee.objects.none()
        
        # Wenn employee_id in GET-Parameter, setze als Initial-Wert
        employee_id = self.request.GET.get('employee')
        if employee_id:
            try:
                employee = Employee.objects.get(pk=employee_id, client=current_client)
                form.initial['employee'] = employee.pk
            except Employee.DoesNotExist:
                pass
        
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_client = self.get_current_client()
        
        # Prüfe ob Mitarbeiter vorhanden sind
        if current_client:
            has_employees = Employee.objects.filter(client=current_client).exists()
            context['has_employees'] = has_employees
        
        return context
    
    @transaction.atomic
    def form_valid(self, form):
        employee = form.cleaned_data['employee']
        month = form.cleaned_data['month']
        year = form.cleaned_data['year']
        
        # Stunden berechnen
        hours_from_records = self.get_hours_total(employee, month, year)
        hours_manual = form.cleaned_data.get('hours_manual') or Decimal("0")
        hours_total = hours_from_records if hours_from_records > 0 else hours_manual
        
        # PayrollRecord speichern
        payroll_record = form.save(commit=False)
        payroll_record.save()
        
        # Bei Stundenlohn: Grundlohn und Ferienentschädigung automatisch erstellen
        if employee.hourly_rate > 0 and hours_total > 0:
            from adealohn.vacation_calculator import VacationCalculator
            
            # Grundlohn
            grundlohn_wage_type = ensure_grundlohn_wage_type("STUNDEN")
            
            grundlohn_amount = hours_total * employee.hourly_rate
            PayrollItem.objects.create(
                payroll=payroll_record,
                wage_type=grundlohn_wage_type,
                quantity=hours_total,
                amount=employee.hourly_rate,
                description=f"Grundlohn für {month}/{year}",
            )
            
            # Ferienentschädigung
            ferien_wage_type = ensure_ferien_wage_type()
            
            vacation_allowance = VacationCalculator.calculate_vacation_allowance(
                grundlohn_amount,
                employee.vacation_weeks
            )
            
            PayrollItem.objects.create(
                payroll=payroll_record,
                wage_type=ferien_wage_type,
                quantity=Decimal("1"),
                amount=vacation_allowance,
                description=f"Ferienentschädigung ({employee.vacation_weeks} Wochen)",
            )
        
        # Bei Monatslohn: Grundlohn erstellen
        elif employee.monthly_salary > 0:
            grundlohn_wage_type = ensure_grundlohn_wage_type("MONAT")
            
            # Verwende monthly_salary vom Employee, falls vorhanden, sonst gross_salary aus Formular
            monatslohn = employee.monthly_salary if employee.monthly_salary > 0 else form.cleaned_data.get('bruttolohn', Decimal("0"))
            
            PayrollItem.objects.create(
                payroll=payroll_record,
                wage_type=grundlohn_wage_type,
                quantity=Decimal("1"),
                amount=monatslohn,
                description=f"Grundlohn für {month}/{year}",
            )
        
        # PayrollRecord neu berechnen
        payroll_record.recompute_bases_from_items()
        payroll_record.save()
        
        messages.success(self.request, f"Payroll-Eintrag für {month}/{year} wurde erstellt.")
        return redirect('adealohn:payroll-detail', pk=payroll_record.pk)


class PayrollRecordUpdateView(LoginRequiredMixin, TenantObjectMixin, LockedPayrollFormGuardMixin, PayrollRecordMixin, UpdateView):
    model = PayrollRecord
    form_class = PayrollRecordForm
    template_name = "adealohn/payroll/form.html"
    login_url = '/admin/login/'
    
    def get_form(self, form_class=None):
        """Filtere Employee-Feld nach current_client."""
        form = super().get_form(form_class)
        current_client = self.get_current_client()
        
        if current_client and current_client.client_type == "FIRMA":
            form.fields["employee"].queryset = Employee.objects.filter(client=current_client)
        else:
            form.fields["employee"].queryset = Employee.objects.none()
        
        # Stunden berechnen für Kontext
        if self.object and self.object.employee:
            self.hours_total = self.get_hours_total(
                self.object.employee,
                self.object.month,
                self.object.year
            )
        
        return form
    
    @transaction.atomic
    def form_valid(self, form):
        employee = form.cleaned_data['employee']
        month = form.cleaned_data['month']
        year = form.cleaned_data['year']
        
        # Stunden berechnen
        hours_from_records = self.get_hours_total(employee, month, year)
        hours_manual = form.cleaned_data.get('hours_manual') or Decimal("0")
        hours_total = hours_from_records if hours_from_records > 0 else hours_manual
        
        # PayrollRecord speichern
        payroll_record = form.save()
        
        # Bei Stundenlohn: Grundlohn und Ferienentschädigung aktualisieren/erstellen
        if employee.hourly_rate > 0 and hours_total > 0:
            from adealohn.vacation_calculator import VacationCalculator
            from adealohn.models import WageType
            
            # Grundlohn aktualisieren/erstellen
            grundlohn_wage_type = ensure_grundlohn_wage_type("STUNDEN")
            
            grundlohn_item, _ = PayrollItem.objects.get_or_create(
                payroll=payroll_record,
                wage_type=grundlohn_wage_type,
                defaults={
                    "quantity": hours_total,
                    "amount": employee.hourly_rate,
                    "description": f"Grundlohn für {month}/{year}",
                }
            )
            if grundlohn_item.quantity != hours_total:
                grundlohn_item.quantity = hours_total
                grundlohn_item.save()
            
            grundlohn_amount = hours_total * employee.hourly_rate
            
            # Ferienentschädigung aktualisieren/erstellen
            ferien_wage_type = ensure_ferien_wage_type()
            
            vacation_allowance = VacationCalculator.calculate_vacation_allowance(
                grundlohn_amount,
                employee.vacation_weeks
            )
            
            ferien_item, _ = PayrollItem.objects.get_or_create(
                payroll=payroll_record,
                wage_type=ferien_wage_type,
                defaults={
                    "quantity": Decimal("1"),
                    "amount": vacation_allowance,
                    "description": f"Ferienentschädigung ({employee.vacation_weeks} Wochen)",
                }
            )
            if ferien_item.amount != vacation_allowance:
                ferien_item.amount = vacation_allowance
                ferien_item.save()
        
        # Bei Monatslohn: Grundlohn aktualisieren/erstellen
        elif employee.monthly_salary > 0:
            grundlohn_wage_type = ensure_grundlohn_wage_type("MONAT")
            
            # Verwende monthly_salary vom Employee, falls vorhanden, sonst gross_salary aus Formular
            monatslohn = employee.monthly_salary if employee.monthly_salary > 0 else form.cleaned_data.get('bruttolohn', Decimal("0"))
            
            grundlohn_item, _ = PayrollItem.objects.get_or_create(
                payroll=payroll_record,
                wage_type=grundlohn_wage_type,
                defaults={
                    "quantity": Decimal("1"),
                    "amount": monatslohn,
                    "description": f"Grundlohn für {month}/{year}",
                }
            )
            if grundlohn_item.amount != monatslohn:
                grundlohn_item.amount = monatslohn
                grundlohn_item.save()
        
        # PayrollRecord neu berechnen
        payroll_record.recompute_bases_from_items()
        payroll_record.save()
        
        messages.success(self.request, f"Payroll-Eintrag für {month}/{year} wurde aktualisiert.")
        return redirect('adealohn:payroll-detail', pk=payroll_record.pk)


class PayrollRecordDetailView(LoginRequiredMixin, TenantObjectMixin, DetailView):
    model = PayrollRecord
    template_name = "adealohn/payroll/detail.html"
    login_url = '/admin/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Setze 'record' als Alias für 'object' (für Template-Kompatibilität)
        context["record"] = self.object
        
        time_records = (
            TimeRecord.objects.filter(
                employee=self.object.employee,
                date__month=self.object.month,
                date__year=self.object.year,
            )
            .select_related("client", "project")
            .order_by("-date")
        )
        hours_total = time_records.aggregate(total=Sum("hours"))["total"] or Decimal("0")
        from .helpers import get_parameter_for_year
        bvg_params = get_parameter_for_year(BVGParameter, self.object.year)
        # Jahreslohn für BVG: YTD-Basis + aktuelle Basis
        ytd_basis = self.object.employee.bvg_ytd_basis or Decimal("0")
        annual_salary = ytd_basis + (self.object.bvg_basis or Decimal("0"))
        
        # Familienzulagen: Alle PayrollItems mit KINDERZULAGE oder FAMILIENZULAGE (vereinfacht)
        family_allowance_items = self.object.items.filter(
            wage_type__code__in=['KINDERZULAGE', 'FAMILIENZULAGE']
        ).select_related('wage_type').order_by('wage_type__code', 'id')
        
        # Trennung zwischen laufenden Zulagen und Nachzahlungen (basierend auf Beschreibung)
        laufende_zulagen = []
        nachzahlungen = []
        for item in family_allowance_items:
            if 'Nachzahlung' in item.description or 'nachzahlung' in item.description.lower():
                nachzahlungen.append(item)
            else:
                laufende_zulagen.append(item)
        
        # Summe der Familienzulagen
        summe_familienzulagen = sum(item.total for item in family_allowance_items)
        
        context["time_records"] = time_records
        context["hours_total"] = hours_total
        context["month_name"] = month_name[self.object.month]
        context["bvg_params"] = bvg_params
        context["annual_salary"] = annual_salary
        context["family_allowance_items"] = family_allowance_items
        context["laufende_zulagen"] = laufende_zulagen
        context["nachzahlungen"] = nachzahlungen
        context["zulagen_total"] = summe_familienzulagen
        
        # Spesen: Alle PayrollItems mit WageTypes, deren code mit "SPESEN_" beginnt
        spesen_items = self.object.items.filter(
            wage_type__code__startswith="SPESEN_"
        ).select_related('wage_type').order_by('wage_type__code', 'id')
        context["spesen_items"] = spesen_items
        context["summe_spesen"] = sum(item.total for item in spesen_items)
        
        # Privatanteile: Alle PayrollItems mit WageTypes, deren code mit "PRIVATANTEIL_" beginnt
        privatanteil_items = self.object.items.filter(
            wage_type__code__startswith="PRIVATANTEIL_"
        ).select_related('wage_type').order_by('wage_type__code', 'id')
        context["privatanteil_items"] = privatanteil_items
        context["privatanteile_total"] = sum(item.total for item in privatanteil_items)
        
        # Zentrale Berechnung verwenden
        from adealohn.payroll_calculator import berechne_lohnabrechnung
        lohnabrechnung = berechne_lohnabrechnung(self.object)
        context["auszahlung"] = lohnabrechnung["auszahlung"]
        context["aufschluesselung"] = lohnabrechnung["aufschluesselung"]
        
        # BVG-Sätze in Prozent berechnen (für Template-Anzeige)
        bvg_employee_rate_percent = None
        bvg_employer_rate_percent = None
        if bvg_params:
            bvg_employee_rate_percent = decimal_to_percent(bvg_params.employee_rate)
            bvg_employer_rate_percent = decimal_to_percent(bvg_params.employer_rate)
        
        context["bvg_employee_rate_percent"] = bvg_employee_rate_percent
        context["bvg_employer_rate_percent"] = bvg_employer_rate_percent
        
        # Lohnabrechnung: Alle lohnwirksamen PayrollItems für Bruttolohn-Aufschlüsselung
        lohnwirksame_items = self.object.items.filter(
            wage_type__is_lohnwirksam=True
        ).select_related('wage_type').order_by('wage_type__category', 'wage_type__code', 'id')
        context["lohnwirksame_items"] = lohnwirksame_items
        
        # Summe der lohnwirksamen Items (sollte gleich bruttolohn sein)
        summe_lohnwirksam = sum(item.total for item in lohnwirksame_items)
        context["summe_lohnwirksam"] = summe_lohnwirksam
        
        # Alle anderen Items (nicht lohnwirksam, z.B. BVG_AN, BVG_AG als Abzüge)
        # AUSSER Familienzulagen (KINDERZULAGE, FAMILIENZULAGE) - die werden separat angezeigt
        nicht_lohnwirksame_items = self.object.items.filter(
            wage_type__is_lohnwirksam=False
        ).exclude(
            wage_type__code__in=['KINDERZULAGE', 'FAMILIENZULAGE']
        ).select_related('wage_type').order_by('wage_type__code', 'id')
        context["nicht_lohnwirksame_items"] = nicht_lohnwirksame_items
        
        return context


class PayrollRecordPrintView(LoginRequiredMixin, TenantObjectMixin, DetailView):
    """
    Druckansicht für Lohnabrechnung (kann als PDF gedruckt werden).
    """
    model = PayrollRecord
    template_name = "adealohn/payroll/print.html"
    login_url = '/admin/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = self.object
        
        # Monatsname
        from calendar import month_name
        from datetime import datetime
        import calendar
        
        context["month_name_de"] = month_name[record.month]
        context["record"] = record
        
        # Abrechnungsperiode berechnen (erster und letzter Tag des Monats)
        first_day = datetime(record.year, record.month, 1).date()
        last_day = datetime(record.year, record.month, calendar.monthrange(record.year, record.month)[1]).date()
        context["abrechnungsperiode_start"] = first_day.strftime("%d.%m.%Y")
        context["abrechnungsperiode_ende"] = last_day.strftime("%d.%m.%Y")
        
        # Abrechnungsdatum (aktuelles Datum oder created_at)
        context["abrechnungsdatum"] = record.created_at.date().strftime("%d.%m.%Y")
        
        # Pensum
        pensum = record.employee.pensum or Decimal("100")
        context["pensum"] = pensum
        context["pensum_display"] = f"{int(pensum)}%"
        
        # IBAN
        context["iban"] = record.employee.iban or ""
        
        # Stunden berechnen
        time_records = (
            TimeRecord.objects.filter(
                employee=record.employee,
                date__month=record.month,
                date__year=record.year,
            )
            .select_related("client", "project")
            .order_by("-date")
        )
        hours_total = time_records.aggregate(total=Sum("hours"))["total"] or Decimal("0")
        context["hours_total"] = hours_total
        
        # BVG Parameter und Berechnung
        from .helpers import get_parameter_for_year, decimal_to_percent
        from adealohn.bvg_calculator import BVGCalculator
        bvg_params = get_parameter_for_year(BVGParameter, record.year)
        bvg_employee_rate_percent = None
        bvg_insured_month = Decimal("0.00")
        bvg_is_manual = False
        
        # Prüfe ob BVG komplett manuell ist (manual_bvg_employee/employer vorhanden, aber keine berechnete BVG)
        has_manual_bvg = (record.manual_bvg_employee > 0) or (record.manual_bvg_employer > 0)
        
        if bvg_params:
            bvg_employee_rate_percent = decimal_to_percent(bvg_params.employee_rate)
            # BVG-Berechnung für versicherten Lohn des Monats
            bvg_calc = BVGCalculator()
            bvg_result = bvg_calc.calculate_for_payroll(record)
            calculated_bvg = bvg_result.get("bvg_employee", Decimal("0.00"))
            
            # Wenn manuelle BVG vorhanden und berechnete BVG = 0, dann ist es komplett manuell
            if has_manual_bvg and calculated_bvg == Decimal("0.00"):
                bvg_is_manual = True
                bvg_insured_month = None  # Keine Basis bei komplett manueller BVG
            else:
                bvg_insured_month = bvg_result.get("bvg_insured_month", Decimal("0.00"))
        elif has_manual_bvg:
            # Keine BVG-Parameter, aber manuelle BVG vorhanden
            bvg_is_manual = True
            bvg_insured_month = None
        
        context["bvg_employee_rate_percent"] = bvg_employee_rate_percent
        context["bvg_insured_month"] = bvg_insured_month
        context["bvg_is_manual"] = bvg_is_manual
        
        # Familienzulagen (vereinfacht - nur KINDERZULAGE)
        family_allowance_items = record.items.filter(
            wage_type__code__in=['KINDERZULAGE', 'FAMILIENZULAGE']
        ).select_related('wage_type').order_by('wage_type__code', 'id')
        context["family_allowance_items"] = family_allowance_items
        
        # Privatanteile
        privatanteil_items = record.items.filter(
            wage_type__code__startswith="PRIVATANTEIL_"
        ).select_related('wage_type').order_by('wage_type__code', 'id')
        context["privatanteil_items"] = privatanteil_items
        
        # Spesen: Alle PayrollItems mit WageTypes, deren code mit "SPESEN_" beginnt
        spesen_items = record.items.filter(
            wage_type__code__startswith="SPESEN_"
        ).select_related('wage_type').order_by('wage_type__code', 'id')
        context["spesen_items"] = spesen_items
        context["summe_spesen"] = sum(item.total for item in spesen_items)
        
        # Monatslohn-Berechnung: Monatslohn + Privatanteile
        # Monatslohn wird mit Pensum angezeigt
        monatslohn = Decimal("0")
        if record.employee.monthly_salary > 0:
            monatslohn = record.employee.monthly_salary
        elif record.employee.hourly_rate > 0 and hours_total > 0:
            monatslohn = record.employee.hourly_rate * hours_total
        
        context["monatslohn"] = monatslohn
        
        # Monatslohn mit Pensum anzeigen (ohne Datumsbereich - das ist interne Info)
        monatslohn_mit_datum = f"Monatslohn ({context['pensum_display']})"
        
        context["monatslohn_mit_pensum"] = monatslohn_mit_datum
        
        # Zentrale Berechnung verwenden
        from adealohn.payroll_calculator import berechne_lohnabrechnung
        lohnabrechnung = berechne_lohnabrechnung(record)
        
        context["auszahlung"] = lohnabrechnung["auszahlung"]
        context["rundung"] = lohnabrechnung["rundung"]
        context["abzuege_sozialversicherungen"] = lohnabrechnung["sozialabzuege_total"]
        context["privatanteile_total"] = lohnabrechnung["privatanteile_total"]
        context["zulagen_total"] = lohnabrechnung["zulagen_total"]
        context["qst_abzug"] = lohnabrechnung["qst_abzug"]
        
        return context


class PayrollRecordDeleteView(LoginRequiredMixin, TenantObjectMixin, LockedPayrollGuardMixin, DeleteView):
    model = PayrollRecord
    template_name = "adealohn/payroll/confirm_delete.html"
    login_url = '/admin/login/'
    success_url = reverse_lazy("adealohn:payroll-list")
    
    def get_context_data(self, **kwargs):
        """Setze 'record' als Alias für 'object' (für Template-Kompatibilität)."""
        context = super().get_context_data(**kwargs)
        context["record"] = self.object
        return context


class FamilyAllowanceNachzahlungView(LoginRequiredMixin, TenantMixin, LockedPayrollFormGuardMixin, CreateView):
    model = PayrollItem
    form_class = FamilyAllowanceNachzahlungForm
    template_name = "adealohn/payroll/family_allowance_nachzahlung.html"
    login_url = '/admin/login/'
    
    def get_payroll_record(self):
        """Lädt PayrollRecord und prüft Tenant-Zugriff."""
        payroll_id = self.kwargs.get('pk')
        payroll_record = PayrollRecord.objects.select_related('employee__client').get(pk=payroll_id)
        
        # Tenant-Prüfung
        current_client = self.get_current_client()
        if current_client and payroll_record.employee.client != current_client:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Kein Zugriff auf diesen PayrollRecord.")
        
        return payroll_record
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payroll_record'] = self.get_payroll_record()
        return context
    
    def form_valid(self, form):
        payroll_record = self.get_payroll_record()
        payroll_item = form.save(commit=False)
        payroll_item.payroll = payroll_record
        payroll_item.quantity = Decimal("1")
        payroll_item.save()
        
        return create_payroll_item_and_recompute(payroll_record, payroll_item=payroll_item)


class FamilyAllowanceLaufendView(LoginRequiredMixin, TenantMixin, LockedPayrollFormGuardMixin, CreateView):
    """View zum Hinzufügen von laufenden Familienzulagen (nicht Nachzahlungen)."""
    model = PayrollItem
    form_class = FamilyAllowanceLaufendForm
    template_name = "adealohn/payroll/family_allowance_laufend.html"
    login_url = '/admin/login/'
    
    def get_payroll_record(self):
        """Lädt PayrollRecord und prüft Tenant-Zugriff."""
        payroll_id = self.kwargs.get('pk')
        payroll_record = PayrollRecord.objects.select_related('employee__client').get(pk=payroll_id)
        
        # Tenant-Prüfung
        current_client = self.get_current_client()
        if current_client and payroll_record.employee.client != current_client:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Kein Zugriff auf diesen PayrollRecord.")
        
        return payroll_record
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payroll_record = self.get_payroll_record()
        context['payroll_record'] = payroll_record
        from calendar import month_name
        context['month_name'] = month_name[payroll_record.month]
        return context
    
    def form_valid(self, form):
        payroll_record = self.get_payroll_record()
        payroll_item = form.save(commit=False)
        payroll_item.payroll = payroll_record
        payroll_item.quantity = Decimal("1")  # Laufende Zulagen: immer 1 Monat
        payroll_item.save()
        
        return create_payroll_item_and_recompute(payroll_record, payroll_item=payroll_item)


class PayrollItemSpesenCreateView(LoginRequiredMixin, TenantMixin, LockedPayrollFormGuardMixin, CreateView):
    model = PayrollItem
    form_class = PayrollItemSpesenForm
    template_name = "adealohn/payroll/spesen_create.html"
    login_url = '/admin/login/'
    
    def get_payroll_record(self):
        """Lädt PayrollRecord und prüft Tenant-Zugriff."""
        payroll_id = self.kwargs.get('pk')
        payroll_record = PayrollRecord.objects.select_related('employee__client').get(pk=payroll_id)
        
        # Tenant-Prüfung
        current_client = self.get_current_client()
        if current_client and payroll_record.employee.client != current_client:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Kein Zugriff auf diesen PayrollRecord.")
        
        return payroll_record
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payroll_record'] = self.get_payroll_record()
        return context
    
    def form_valid(self, form):
        payroll_record = self.get_payroll_record()
        payroll_item = form.save(commit=False)
        payroll_item.payroll = payroll_record
        payroll_item.quantity = Decimal("1")
        payroll_item.save()
        
        return create_payroll_item_and_recompute(payroll_record, payroll_item=payroll_item)


class PayrollItemPrivatanteilCreateView(LoginRequiredMixin, TenantMixin, LockedPayrollFormGuardMixin, CreateView):
    model = PayrollItem
    form_class = PayrollItemPrivatanteilForm
    template_name = "adealohn/payroll/privatanteil_create.html"
    login_url = '/admin/login/'
    
    def get_payroll_record(self):
        """Lädt PayrollRecord und prüft Tenant-Zugriff."""
        payroll_id = self.kwargs.get('pk')
        payroll_record = PayrollRecord.objects.select_related('employee__client').get(pk=payroll_id)
        
        # Tenant-Prüfung
        current_client = self.get_current_client()
        if current_client and payroll_record.employee.client != current_client:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Kein Zugriff auf diesen PayrollRecord.")
        
        return payroll_record
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payroll_record'] = self.get_payroll_record()
        return context
    
    def form_valid(self, form):
        payroll_record = self.get_payroll_record()
        payroll_item = form.save(commit=False)
        payroll_item.payroll = payroll_record
        payroll_item.quantity = Decimal("1")
        payroll_item.save()
        
        return create_payroll_item_and_recompute(payroll_record, payroll_item=payroll_item)


class PayrollItemGeneralCreateView(LoginRequiredMixin, TenantMixin, LockedPayrollFormGuardMixin, CreateView):
    """Allgemeine View zum Hinzufügen von PayrollItems (Prämien, Trinkgeld, BVG-Zusatzbeiträge, etc.)"""
    model = PayrollItem
    form_class = PayrollItemGeneralForm
    template_name = "adealohn/payroll/item_create.html"
    login_url = '/admin/login/'
    
    def get_payroll_record(self):
        """Lädt PayrollRecord und prüft Tenant-Zugriff."""
        payroll_id = self.kwargs.get('pk')
        payroll_record = PayrollRecord.objects.select_related('employee__client').get(pk=payroll_id)
        
        # Tenant-Prüfung
        current_client = self.get_current_client()
        if current_client and payroll_record.employee.client != current_client:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Kein Zugriff auf diesen PayrollRecord.")
        
        return payroll_record
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payroll_record'] = self.get_payroll_record()
        return context
    
    def form_valid(self, form):
        from adealohn.payroll_flow import create_payroll_item_and_recompute
        payroll_record = self.get_payroll_record()
        payroll_item = form.save(commit=False)
        payroll_item.payroll = payroll_record
        payroll_item.save()
        
        return create_payroll_item_and_recompute(payroll_record, payroll_item=payroll_item)


class PayrollItemDeleteView(LoginRequiredMixin, TenantObjectMixin, LockedPayrollFormGuardMixin, DeleteView):
    """
    Löscht ein einzelnes PayrollItem und berechnet den PayrollRecord neu.
    """
    model = PayrollItem
    template_name = "adealohn/payroll/item_confirm_delete.html"
    login_url = '/admin/login/'
    locked_reason = "gelöscht werden"
    
    def get_object(self, queryset=None):
        """Lädt PayrollItem und prüft Tenant-Zugriff."""
        obj = super().get_object(queryset)
        # Tenant-Prüfung erfolgt bereits durch TenantObjectMixin
        # Zusätzlich prüfen wir, ob das PayrollRecord gesperrt ist
        if obj.payroll.is_locked():
            raise HttpResponseForbidden(
                f"Dieser Lohnlauf ist gesperrt (Status: {obj.payroll.get_status_display()}) "
                f"und kann nicht mehr bearbeitet werden."
            )
        return obj
    
    def get_success_url(self):
        """Nach dem Löschen zurück zur Payroll-Detail-Seite."""
        payroll_id = self.object.payroll.pk
        return reverse("adealohn:payroll-detail", args=[payroll_id])
    
    def delete(self, request, *args, **kwargs):
        """Löscht das Item und berechnet den PayrollRecord neu."""
        self.object = self.get_object()
        payroll_record = self.object.payroll
        
        # Item löschen
        result = super().delete(request, *args, **kwargs)
        
        # PayrollRecord neu berechnen
        payroll_record.recompute_bases_from_items()
        payroll_record.save()
        
        messages.success(request, f"Lohnart '{self.object.wage_type.name}' wurde gelöscht.")
        return result
    
    def get_context_data(self, **kwargs):
        """Setze zusätzliche Context-Daten für das Template."""
        context = super().get_context_data(**kwargs)
        context["payroll_record"] = self.object.payroll
        context["item"] = self.object
        return context
