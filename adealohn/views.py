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

from adeacore.models import Employee, Client, TimeRecord, PayrollRecord
from adealohn.models import WageType, WageTypeCategory, BVGParameter, PayrollItem, FamilyAllowanceParameter
from .forms import EmployeeForm, PayrollRecordForm, FamilyAllowanceNachzahlungForm, PayrollItemSpesenForm, PayrollItemPrivatanteilForm
from .mixins import (
    TenantMixin,
    TenantFilterMixin,
    TenantObjectMixin,
    LockedPayrollGuardMixin,
    LockedPayrollFormGuardMixin,
)
from .payroll_flow import create_payroll_item_and_recompute

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
        # Wichtig: im Template wird ein Client-Objekt erwartet (name/pk).
        from adeacore.tenancy import resolve_current_client

        context['current_client'] = resolve_current_client(self.request)
        return context
    
    def post(self, request, *args, **kwargs):
        """Speichere gewählten Client in Session (nur FIRMA-Clients)."""
        client_id = request.POST.get("client_id")
        
        if client_id:
            try:
                client = Client.objects.get(pk=client_id)
                # Sicherheitsprüfung: Nur FIRMA-Clients mit aktiviertem Lohnmodul erlauben
                if client.client_type != "FIRMA" or not client.lohn_aktiv:
                    logger.warning(f"Versuch, Client {client.name} (ID: {client_id}, Typ: {client.client_type}, Lohn aktiv: {client.lohn_aktiv}) in AdeaLohn zu verwenden - abgelehnt")
                    return redirect("adealohn:client-switch")
                
                request.session["active_client_id"] = int(client_id)
                request.session.modified = True
                logger.info(f"Mandant gewechselt zu: {client.name} (ID: {client_id})")
                return redirect("adealohn:payroll-list")
            except Client.DoesNotExist:
                pass
        
        return redirect("adealohn:client-switch")


class EmployeeListView(LoginRequiredMixin, TenantFilterMixin, ListView):
    model = Employee
    template_name = "adealohn/list.html"
    context_object_name = "employees"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related("client").order_by("last_name")
        client_id = self.request.GET.get("client")
        query = self.request.GET.get("q")
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(role__icontains=query)
            )
        return queryset

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
                form.fields["client"].initial = current_client.pk
                form.fields["client"].queryset = Client.objects.filter(client_type="FIRMA", pk=current_client.pk)
            else:
                form.fields["client"].queryset = Client.objects.filter(client_type="FIRMA")
        
        return form

    def get_success_url(self):
        return reverse("adealohn:employee-detail", args=[self.object.pk])


class EmployeeDetailView(LoginRequiredMixin, TenantObjectMixin, DetailView):
    model = Employee
    template_name = "adealohn/detail.html"
    context_object_name = "employee"
    login_url = '/admin/login/'


class EmployeeUpdateView(LoginRequiredMixin, TenantObjectMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "adealohn/form.html"
    login_url = '/admin/login/'


class EmployeeDeleteView(LoginRequiredMixin, TenantObjectMixin, DeleteView):
    model = Employee
    template_name = "adealohn/confirm_delete.html"
    context_object_name = "employee"
    success_url = reverse_lazy("adealohn:employee-list")
    login_url = '/admin/login/'


class PayrollRecordListView(LoginRequiredMixin, TenantFilterMixin, ListView):
    model = PayrollRecord
    template_name = "adealohn/payroll/list.html"
    context_object_name = "records"
    paginate_by = 20
    login_url = '/admin/login/'

    def get_queryset(self):
        queryset = super().get_queryset().select_related("employee", "employee__client")
        employee_id = self.request.GET.get("employee")
        month = self.request.GET.get("month")
        year = self.request.GET.get("year")
        query = self.request.GET.get("q")

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if month:
            queryset = queryset.filter(month=month)
        if year:
            queryset = queryset.filter(year=year)
        if query:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=query)
                | Q(employee__last_name__icontains=query)
                | Q(employee__client__name__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_client = self.get_current_client()
        
        # Nur Employees von FIRMA-Clients anzeigen
        if current_client and current_client.client_type == "FIRMA":
            employees = Employee.objects.filter(client=current_client).order_by("last_name")
        else:
            employees = Employee.objects.none()
        
        context["employees"] = employees
        context["selected_employee"] = self.request.GET.get("employee", "")
        context["selected_month"] = self.request.GET.get("month", "")
        context["selected_year"] = self.request.GET.get("year", "")
        context["query"] = self.request.GET.get("q", "")
        context["months"] = [(i, month_name[i]) for i in range(1, 13)]
        # Performance + Konsistenz: Years nur für den aktuellen Mandanten (wie die Liste selbst).
        if current_client and current_client.client_type == "FIRMA" and current_client.lohn_aktiv:
            years = (
                PayrollRecord.objects.filter(employee__client=current_client)
                .values_list("year", flat=True)
                .distinct()
                .order_by("-year")
            )
        else:
            years = PayrollRecord.objects.none().values_list("year", flat=True)
        context["years"] = list(years)
        return context


class PayrollRecordMixin:
    """Mixin für PayrollRecord-Views mit gemeinsamer Logik."""
    
    def get_hours_total(self, employee, month, year):
        from decimal import Decimal
        time_records = TimeRecord.objects.filter(
            employee=employee, date__month=month, date__year=year
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

    def form_valid(self, form):
        # Prüfe ob Employee zum current_client gehört (nur FIRMA-Clients)
        employee = form.cleaned_data["employee"]
        current_client = self.get_current_client()
        
        if current_client and current_client.client_type == "FIRMA" and current_client.lohn_aktiv and employee.client != current_client:
            form.add_error("employee", "Dieser Mitarbeiter gehört nicht zum ausgewählten Mandanten.")
            return self.form_invalid(form)
        
        month = form.cleaned_data["month"]
        year = form.cleaned_data["year"]
        hours_total = self.get_hours_total(employee, month, year)
        self.hours_total = hours_total
        gross_salary = form.cleaned_data.get("gross_salary")

        if employee.hourly_rate == 0 and not gross_salary:
            form.add_error("gross_salary", "Bitte Bruttolohn angeben.")
            return self.form_invalid(form)

        self.object = form.save(commit=False)
        # clean() wird automatisch durch form.save() aufgerufen
        self.object.save()
        self.object.items.all().delete()

        if employee.hourly_rate > 0:
            wage_type = self.ensure_wage_type(
                "GRUNDLOHN_STUNDEN", "Grundlohn Stunden"
            )
            self.object.items.create(
                wage_type=wage_type,
                quantity=hours_total,
                amount=employee.hourly_rate,
                description="Automatisch berechneter Stundenlohn.",
            )

            # Ferienentschädigung automatisch hinzufügen (nur bei Stundenlöhnen)
            from adealohn.vacation_calculator import VacationCalculator
            base_salary = hours_total * employee.hourly_rate
            vacation_weeks = getattr(employee, "vacation_weeks", 5) or 5
            vacation_allowance = VacationCalculator.calculate_vacation_allowance(
                base_salary, vacation_weeks
            )

            if vacation_allowance > 0:
                # Ferienentschädigung als Zulage (AHV/ALV/NBU-pflichtig, aber NICHT BVG-pflichtig)
                vacation_wage_type = self.ensure_wage_type(
                    "FERIENENTSCHAEDIGUNG", "Ferienentschädigung"
                )
                # Setze BVG-relevant auf False für Ferienentschädigung
                if vacation_wage_type.bvg_relevant:
                    vacation_wage_type.bvg_relevant = False
                    vacation_wage_type.save(update_fields=["bvg_relevant"])

                self.object.items.create(
                    wage_type=vacation_wage_type,
                    quantity=Decimal("1.0"),
                    amount=vacation_allowance,
                    description=f"Automatisch berechnete Ferienentschädigung ({vacation_weeks} Wochen).",
                )
        else:
            wage_type = self.ensure_wage_type(
                "GRUNDLOHN_MONAT", "Grundlohn Monatslohn"
            )
            self.object.items.create(
                wage_type=wage_type,
                quantity=Decimal("1.0"),
                amount=gross_salary,
                description="Manuell erfasster Monatslohn.",
            )

        self.object.recompute_bases_from_items()
        self.object.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("adealohn:payroll-detail", args=[self.object.pk])


class PayrollRecordDetailView(LoginRequiredMixin, TenantObjectMixin, DetailView):
    model = PayrollRecord
    template_name = "adealohn/payroll/detail.html"
    context_object_name = "record"
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
            wage_type__code__startswith='SPESEN_'
        ).select_related('wage_type').order_by('wage_type__code', 'id')
        
        context["spesen_items"] = spesen_items
        context["summe_spesen"] = sum(item.total for item in spesen_items)
        
        # Privatanteile: Alle PayrollItems mit WageTypes, deren code mit "PRIVATANTEIL_" beginnt
        privatanteil_items = self.object.items.filter(
            wage_type__code__startswith='PRIVATANTEIL_'
        ).select_related('wage_type').order_by('wage_type__code', 'id')
        
        context["privatanteil_items"] = privatanteil_items
        context["summe_privatanteile"] = sum(item.total for item in privatanteil_items)
        
        return context


class PayrollRecordUpdateView(LockedPayrollFormGuardMixin, LoginRequiredMixin, TenantObjectMixin, PayrollRecordMixin, UpdateView):
    model = PayrollRecord
    form_class = PayrollRecordForm
    template_name = "adealohn/payroll/form.html"
    login_url = '/admin/login/'
    locked_reason = "mehr bearbeitet werden"
    
    def get_form(self, form_class=None):
        """Filtere Employee-Feld nach current_client."""
        form = super().get_form(form_class)
        current_client = self.get_current_client()
        
        if current_client and current_client.client_type == "FIRMA":
            form.fields["employee"].queryset = Employee.objects.filter(client=current_client)
        else:
            form.fields["employee"].queryset = Employee.objects.none()
        
        return form

    def form_valid(self, form):
        employee = form.cleaned_data["employee"]
        month = form.cleaned_data["month"]
        year = form.cleaned_data["year"]
        
        # Stunden: Zuerst aus TimeRecords, falls vorhanden, sonst manuell eingegeben
        hours_from_records = self.get_hours_total(employee, month, year)
        hours_manual = form.cleaned_data.get("hours_manual") or Decimal("0")
        
        # Wenn TimeRecords vorhanden sind, diese verwenden, sonst manuell eingegebene Stunden
        if hours_from_records > 0:
            hours_total = hours_from_records
        else:
            hours_total = hours_manual
        
        self.hours_total = hours_total
        gross_salary = form.cleaned_data.get("gross_salary")

        if employee.hourly_rate == 0 and not gross_salary:
            form.add_error("gross_salary", "Bitte Bruttolohn angeben.")
            return self.form_invalid(form)

        self.object = form.save(commit=False)
        # clean() wird automatisch durch form.save() aufgerufen
        self.object.save()
        self.object.items.all().delete()

        if employee.hourly_rate > 0:
            wage_type = self.ensure_wage_type(
                "GRUNDLOHN_STUNDEN", "Grundlohn Stunden"
            )
            self.object.items.create(
                wage_type=wage_type,
                quantity=hours_total,
                amount=employee.hourly_rate,
                description="Automatisch berechneter Stundenlohn.",
            )

            # Ferienentschädigung automatisch hinzufügen (nur bei Stundenlöhnen)
            from adealohn.vacation_calculator import VacationCalculator
            base_salary = hours_total * employee.hourly_rate
            vacation_weeks = getattr(employee, "vacation_weeks", 5) or 5
            vacation_allowance = VacationCalculator.calculate_vacation_allowance(
                base_salary, vacation_weeks
            )

            if vacation_allowance > 0:
                # Ferienentschädigung als Zulage (AHV/ALV/NBU-pflichtig, aber NICHT BVG-pflichtig)
                vacation_wage_type = self.ensure_wage_type(
                    "FERIENENTSCHAEDIGUNG", "Ferienentschädigung"
                )
                # Setze BVG-relevant auf False für Ferienentschädigung
                if vacation_wage_type.bvg_relevant:
                    vacation_wage_type.bvg_relevant = False
                    vacation_wage_type.save(update_fields=["bvg_relevant"])

                self.object.items.create(
                    wage_type=vacation_wage_type,
                    quantity=Decimal("1.0"),
                    amount=vacation_allowance,
                    description=f"Automatisch berechnete Ferienentschädigung ({vacation_weeks} Wochen).",
                )
        else:
            wage_type = self.ensure_wage_type(
                "GRUNDLOHN_MONAT", "Grundlohn Monatslohn"
            )
            self.object.items.create(
                wage_type=wage_type,
                quantity=Decimal("1.0"),
                amount=gross_salary,
                description="Manuell erfasster Monatslohn.",
            )

        self.object.recompute_bases_from_items()
        self.object.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("adealohn:payroll-detail", args=[self.object.pk])


class PayrollRecordDeleteView(LockedPayrollGuardMixin, LoginRequiredMixin, TenantObjectMixin, DeleteView):
    model = PayrollRecord
    template_name = "adealohn/payroll/confirm_delete.html"
    context_object_name = "record"
    success_url = reverse_lazy("adealohn:payroll-list")
    login_url = '/admin/login/'
    locked_reason = "gelöscht werden"
    
class FamilyAllowanceNachzahlungView(LockedPayrollGuardMixin, LoginRequiredMixin, TenantObjectMixin, PayrollRecordMixin, DetailView):
    """View für die Erfassung von Familienzulagen-Nachzahlungen."""
    model = PayrollRecord
    template_name = "adealohn/payroll/family_allowance_nachzahlung.html"
    context_object_name = "payroll_record"
    login_url = '/admin/login/'
    locked_reason = "mehr bearbeitet werden"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = FamilyAllowanceNachzahlungForm(payroll_record=self.object)
        context['month_name'] = month_name[self.object.month]
        
        # FamilyAllowanceParameter für aktuelles Jahr
        fam_params = FamilyAllowanceParameter.objects.filter(year=self.object.year).first()
        context['fam_params'] = fam_params
        
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = FamilyAllowanceNachzahlungForm(request.POST, payroll_record=self.object)

        if form.is_valid():
            zulagenart = form.cleaned_data['zulagenart']
            anzahl_monate = form.cleaned_data['anzahl_monate']
            monatsbetrag = form.cleaned_data['monatsbetrag']
            beschreibung = form.cleaned_data.get('description', '')
            sva_entscheid = form.cleaned_data.get('sva_entscheid')

            # WageType bestimmen
            if zulagenart == 'KINDERZULAGE':
                wage_type = WageType.objects.get(code='KINDERZULAGE')
            else:
                wage_type = WageType.objects.get(code='AUSBILDUNGSZULAGE')

            # Beschreibung auto-generieren falls leer
            if not beschreibung:
                monate_namen = [month_name[i] for i in range(1, 13)]
                start_monat = self.object.month - anzahl_monate + 1
                if start_monat < 1:
                    start_monat += 12
                end_monat = self.object.month
                beschreibung = f"Nachzahlung {wage_type.name} {monate_namen[start_monat-1]}-{monate_namen[end_monat-1]} {self.object.year}"
                if sva_entscheid:
                    beschreibung += f" (SVA-Entscheid {sva_entscheid.entscheid})"

            return create_payroll_item_and_recompute(
                payroll=self.object,
                wage_type=wage_type,
                quantity=anzahl_monate,
                amount=monatsbetrag,
                description=beschreibung,
            )

        # Form-Fehler: Formular erneut anzeigen
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class PayrollItemSpesenCreateView(LockedPayrollGuardMixin, LoginRequiredMixin, TenantObjectMixin, DetailView):
    """View für die Erfassung von Spesen als PayrollItem."""
    model = PayrollRecord
    template_name = "adealohn/payroll/spesen_create.html"
    context_object_name = "payroll_record"
    login_url = '/admin/login/'
    locked_reason = "mehr bearbeitet werden"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PayrollItemSpesenForm(payroll_record=self.object)
        context['month_name'] = month_name[self.object.month]
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = PayrollItemSpesenForm(request.POST, payroll_record=self.object)

        if form.is_valid():
            wage_type_code = form.cleaned_data['wage_type']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', '')

            wage_type = WageType.objects.get(code=wage_type_code)

            return create_payroll_item_and_recompute(
                payroll=self.object,
                wage_type=wage_type,
                quantity=Decimal("1.0"),
                amount=amount,
                description=description,
            )

        # Form-Fehler: Formular erneut anzeigen
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


class PayrollItemPrivatanteilCreateView(LockedPayrollGuardMixin, LoginRequiredMixin, TenantObjectMixin, DetailView):
    """View für die Erfassung von Privatanteilen (Auto/Telefon) als PayrollItem."""
    model = PayrollRecord
    template_name = "adealohn/payroll/privatanteil_create.html"
    context_object_name = "payroll_record"
    login_url = '/admin/login/'
    locked_reason = "mehr bearbeitet werden"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PayrollItemPrivatanteilForm(payroll_record=self.object)
        context['month_name'] = month_name[self.object.month]
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = PayrollItemPrivatanteilForm(request.POST, payroll_record=self.object)

        if form.is_valid():
            wage_type_code = form.cleaned_data['wage_type']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', '')

            wage_type = WageType.objects.get(code=wage_type_code)

            return create_payroll_item_and_recompute(
                payroll=self.object,
                wage_type=wage_type,
                quantity=Decimal("1.0"),
                amount=amount,
                description=description,
            )

        # Form-Fehler: Formular erneut anzeigen
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)
