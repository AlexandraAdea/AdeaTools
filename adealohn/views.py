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
    EmployeeForm, PayrollRecordForm, FamilyAllowanceNachzahlungForm, 
    PayrollItemSpesenForm, PayrollItemPrivatanteilForm, InsuranceRatesForm
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
        ahv = AHVParameter.objects.filter(year=year).first()
        if ahv:
            initial['ahv_rate_employee'] = ahv.rate_employee * Decimal("100")
            initial['ahv_rate_employer'] = ahv.rate_employer * Decimal("100")
            initial['ahv_rentner_freibetrag'] = ahv.rentner_freibetrag_monat
        else:
            initial['ahv_rate_employee'] = Decimal("5.3")
            initial['ahv_rate_employer'] = Decimal("5.3")
            initial['ahv_rentner_freibetrag'] = Decimal("1400.00")
        
        # ALV Parameter (Umwandlung von Dezimal zu Prozent)
        alv = ALVParameter.objects.filter(year=year).first()
        if alv:
            initial['alv_rate_employee'] = alv.rate_employee * Decimal("100")
            initial['alv_rate_employer'] = alv.rate_employer * Decimal("100")
            initial['alv_max_annual'] = alv.max_annual_insured_salary
        else:
            initial['alv_rate_employee'] = Decimal("1.1")
            initial['alv_rate_employer'] = Decimal("1.1")
            initial['alv_max_annual'] = Decimal("148200.00")
        
        # FAK Parameter (DEFAULT) (Umwandlung von Dezimal zu Prozent)
        current_client = self.get_current_client()
        canton = current_client.work_canton if current_client else None
        fak = FAKParameter.objects.filter(year=year, canton=(canton or "DEFAULT")).first()
        if not fak:
            fak = FAKParameter.objects.filter(year=year, canton="DEFAULT").first()
        if fak:
            initial['fak_canton'] = fak.canton
            initial['fak_rate_employer'] = fak.fak_rate_employer * Decimal("100")
        else:
            initial['fak_canton'] = canton or "DEFAULT"
            initial['fak_rate_employer'] = Decimal("1.0")
        
        # VK Parameter (Umwandlung von Dezimal zu Prozent)
        vk = VKParameter.objects.filter(year=year).first()
        if vk:
            initial['vk_rate_employer'] = vk.rate_employer * Decimal("100")
        else:
            initial['vk_rate_employer'] = Decimal("3.0")
        
        # UVG Parameter (Umwandlung von Dezimal zu Prozent)
        uvg = UVGParameter.objects.filter(year=year).first()
        if uvg:
            initial['bu_rate_employer'] = uvg.bu_rate_employer * Decimal("100")
            initial['nbu_rate_employee'] = uvg.nbu_rate_employee * Decimal("100")
            initial['uvg_max_annual'] = uvg.max_annual_insured_salary
        else:
            initial['bu_rate_employer'] = Decimal("0.644")
            initial['nbu_rate_employee'] = Decimal("2.3")
            initial['uvg_max_annual'] = Decimal("148200.00")
        
        # KTG Parameter (Umwandlung von Dezimal zu Prozent)
        ktg = KTGParameter.objects.filter(year=year).first()
        if ktg:
            initial['ktg_rate_employee'] = ktg.ktg_rate_employee * Decimal("100")
            initial['ktg_rate_employer'] = ktg.ktg_rate_employer * Decimal("100")
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
                'rate_employee': form.cleaned_data['ahv_rate_employee'] / Decimal("100"),
                'rate_employer': form.cleaned_data['ahv_rate_employer'] / Decimal("100"),
                'rentner_freibetrag_monat': form.cleaned_data['ahv_rentner_freibetrag'],
            }
        )
        
        # ALV Parameter (Umwandlung von Prozent zu Dezimal)
        alv, _ = ALVParameter.objects.update_or_create(
            year=year,
            defaults={
                'rate_employee': form.cleaned_data['alv_rate_employee'] / Decimal("100"),
                'rate_employer': form.cleaned_data['alv_rate_employer'] / Decimal("100"),
                'max_annual_insured_salary': form.cleaned_data['alv_max_annual'],
            }
        )
        
        # FAK Parameter (Umwandlung von Prozent zu Dezimal)
        fak_canton = form.cleaned_data.get('fak_canton', 'DEFAULT') or 'DEFAULT'
        fak, _ = FAKParameter.objects.update_or_create(
            year=year,
            canton=fak_canton.upper(),
            defaults={
                'fak_rate_employer': form.cleaned_data['fak_rate_employer'] / Decimal("100"),
            }
        )
        
        # VK Parameter (Umwandlung von Prozent zu Dezimal)
        vk, _ = VKParameter.objects.update_or_create(
            year=year,
            defaults={
                'rate_employer': form.cleaned_data['vk_rate_employer'] / Decimal("100"),
            }
        )
        
        # UVG Parameter (Umwandlung von Prozent zu Dezimal)
        uvg, _ = UVGParameter.objects.update_or_create(
            year=year,
            defaults={
                'bu_rate_employer': form.cleaned_data['bu_rate_employer'] / Decimal("100"),
                'nbu_rate_employee': form.cleaned_data['nbu_rate_employee'] / Decimal("100"),
                'max_annual_insured_salary': form.cleaned_data['uvg_max_annual'],
            }
        )
        
        # KTG Parameter (Umwandlung von Prozent zu Dezimal)
        ktg, _ = KTGParameter.objects.update_or_create(
            year=year,
            defaults={
                'ktg_rate_employee': form.cleaned_data['ktg_rate_employee'] / Decimal("100"),
                'ktg_rate_employer': form.cleaned_data['ktg_rate_employer'] / Decimal("100"),
                'ktg_max_basis': form.cleaned_data.get('ktg_max_basis'),
            }
        )
        
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
        context["clients"] = Client.objects.filter(
            client_type="FIRMA",
            lohn_aktiv=True
        ).order_by("name")
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
            from adealohn.models import WageType
            
            # Grundlohn
            grundlohn_wage_type, _ = WageType.objects.get_or_create(
                code="GRUNDLOHN_STUNDEN",
                defaults={
                    "name": "Grundlohn Stundenlohn",
                    "category": WageTypeCategory.GRUNDLOHN,
                    "is_lohnwirksam": True,
                    "ahv_relevant": True,
                    "alv_relevant": True,
                    "uv_relevant": True,
                    "bvg_relevant": True,
                    "qst_relevant": True,
                }
            )
            
            grundlohn_amount = hours_total * employee.hourly_rate
            PayrollItem.objects.create(
                payroll=payroll_record,
                wage_type=grundlohn_wage_type,
                quantity=hours_total,
                amount=employee.hourly_rate,
                description=f"Grundlohn für {month}/{year}",
            )
            
            # Ferienentschädigung
            ferien_wage_type, _ = WageType.objects.get_or_create(
                code="FERIENENTSCHAEDIGUNG",
                defaults={
                    "name": "Ferienentschädigung",
                    "category": WageTypeCategory.ZULAGE,
                    "is_lohnwirksam": True,
                    "ahv_relevant": True,
                    "alv_relevant": True,
                    "uv_relevant": True,
                    "bvg_relevant": False,  # WICHTIG: Ferienentschädigung ist NICHT BVG-relevant!
                    "qst_relevant": True,
                }
            )
            
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
            grundlohn_wage_type, _ = WageType.objects.get_or_create(
                code="GRUNDLOHN_MONAT",
                defaults={
                    "name": "Grundlohn Monatslohn",
                    "category": WageTypeCategory.GRUNDLOHN,
                    "is_lohnwirksam": True,
                    "ahv_relevant": True,
                    "alv_relevant": True,
                    "uv_relevant": True,
                    "bvg_relevant": True,
                    "qst_relevant": True,
                }
            )
            
            # Verwende monthly_salary vom Employee, falls vorhanden, sonst gross_salary aus Formular
            monatslohn = employee.monthly_salary if employee.monthly_salary > 0 else form.cleaned_data.get('gross_salary', Decimal("0"))
            
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
            grundlohn_wage_type, _ = WageType.objects.get_or_create(
                code="GRUNDLOHN_STUNDEN",
                defaults={
                    "name": "Grundlohn Stundenlohn",
                    "category": WageTypeCategory.GRUNDLOHN,
                    "is_lohnwirksam": True,
                    "ahv_relevant": True,
                    "alv_relevant": True,
                    "uv_relevant": True,
                    "bvg_relevant": True,
                    "qst_relevant": True,
                }
            )
            
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
            ferien_wage_type, _ = WageType.objects.get_or_create(
                code="FERIENENTSCHAEDIGUNG",
                defaults={
                    "name": "Ferienentschädigung",
                    "category": WageTypeCategory.ZULAGE,
                    "is_lohnwirksam": True,
                    "ahv_relevant": True,
                    "alv_relevant": True,
                    "uv_relevant": True,
                    "bvg_relevant": False,  # WICHTIG: Ferienentschädigung ist NICHT BVG-relevant!
                    "qst_relevant": True,
                }
            )
            
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
            from adealohn.models import WageType
            
            grundlohn_wage_type, _ = WageType.objects.get_or_create(
                code="GRUNDLOHN_MONAT",
                defaults={
                    "name": "Grundlohn Monatslohn",
                    "category": WageTypeCategory.GRUNDLOHN,
                    "is_lohnwirksam": True,
                    "ahv_relevant": True,
                    "alv_relevant": True,
                    "uv_relevant": True,
                    "bvg_relevant": True,
                    "qst_relevant": True,
                }
            )
            
            # Verwende monthly_salary vom Employee, falls vorhanden, sonst gross_salary aus Formular
            monatslohn = employee.monthly_salary if employee.monthly_salary > 0 else form.cleaned_data.get('gross_salary', Decimal("0"))
            
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
        bvg_params = BVGParameter.objects.filter(year=self.object.year).first()
        # Jahreslohn für BVG: YTD-Basis + aktuelle Basis
        ytd_basis = self.object.employee.bvg_ytd_basis or Decimal("0")
        annual_salary = ytd_basis + (self.object.bvg_basis or Decimal("0"))
        
        # Familienzulagen: Alle PayrollItems mit KINDERZULAGE oder AUSBILDUNGSZULAGE
        family_allowance_items = self.object.items.filter(
            wage_type__code__in=['KINDERZULAGE', 'AUSBILDUNGSZULAGE']
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
        context["summe_familienzulagen"] = summe_familienzulagen
        
        # Spesen: Alle PayrollItems mit WageTypes, deren code mit "SPESEN_" beginnt
        spesen_items = self.object.items.filter(
            wage_type__code__startswith="SPESEN_"
        ).select_related('wage_type').order_by('wage_type__code', 'id')
        context["spesen_items"] = spesen_items
        context["summe_spesen"] = sum(item.total for item in spesen_items)
        
        # BVG-Sätze in Prozent berechnen (für Template-Anzeige)
        bvg_employee_rate_percent = None
        bvg_employer_rate_percent = None
        if bvg_params:
            bvg_employee_rate_percent = bvg_params.employee_rate * Decimal("100")
            bvg_employer_rate_percent = bvg_params.employer_rate * Decimal("100")
        
        context["bvg_employee_rate_percent"] = bvg_employee_rate_percent
        context["bvg_employer_rate_percent"] = bvg_employer_rate_percent
        
        return context


class PayrollRecordDeleteView(LoginRequiredMixin, TenantObjectMixin, LockedPayrollGuardMixin, DeleteView):
    model = PayrollRecord
    template_name = "adealohn/payroll/confirm_delete.html"
    login_url = '/admin/login/'
    success_url = reverse_lazy("adealohn:payroll-list")


class FamilyAllowanceNachzahlungView(LoginRequiredMixin, TenantObjectMixin, LockedPayrollFormGuardMixin, CreateView):
    model = PayrollItem
    form_class = FamilyAllowanceNachzahlungForm
    template_name = "adealohn/payroll/family_allowance_nachzahlung.html"
    login_url = '/admin/login/'
    
    def get_payroll_record(self):
        payroll_id = self.kwargs.get('pk')
        return PayrollRecord.objects.get(pk=payroll_id)
    
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
        
        return create_payroll_item_and_recompute(payroll_record, payroll_item.wage_type.code, payroll_item.amount, payroll_item.description)


class PayrollItemSpesenCreateView(LoginRequiredMixin, TenantObjectMixin, LockedPayrollFormGuardMixin, CreateView):
    model = PayrollItem
    form_class = PayrollItemSpesenForm
    template_name = "adealohn/payroll/spesen_create.html"
    login_url = '/admin/login/'
    
    def get_payroll_record(self):
        payroll_id = self.kwargs.get('pk')
        return PayrollRecord.objects.get(pk=payroll_id)
    
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
        
        return create_payroll_item_and_recompute(payroll_record, payroll_item.wage_type.code, payroll_item.amount, payroll_item.description)


class PayrollItemPrivatanteilCreateView(LoginRequiredMixin, TenantObjectMixin, LockedPayrollFormGuardMixin, CreateView):
    model = PayrollItem
    form_class = PayrollItemPrivatanteilForm
    template_name = "adealohn/payroll/privatanteil_create.html"
    login_url = '/admin/login/'
    
    def get_payroll_record(self):
        payroll_id = self.kwargs.get('pk')
        return PayrollRecord.objects.get(pk=payroll_id)
    
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
        
        return create_payroll_item_and_recompute(payroll_record, payroll_item.wage_type.code, payroll_item.amount, payroll_item.description)
