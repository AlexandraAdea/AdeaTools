from django import forms
from decimal import Decimal

from adeacore.models import Employee, PayrollRecord
from adealohn.models import FamilyAllowanceParameter, WageType


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "client",
            "first_name",
            "last_name",
            "role",
            "hourly_rate",
            "weekly_hours",
            "nbu_pflichtig",
            "is_rentner",
            "ahv_freibetrag_aktiv",
            "qst_pflichtig",
            "qst_tarif",
            "qst_kinder",
            "qst_kirchensteuer",
            "qst_prozent",
            "qst_fixbetrag",
        ]
        labels = {
            "client": "Mandant",
            "first_name": "Vorname",
            "last_name": "Nachname",
            "role": "Rolle",
            "hourly_rate": "Stundensatz (CHF)",
            "weekly_hours": "Wöchentliche Stunden",
            "nbu_pflichtig": "NBU-pflichtig",
            "is_rentner": "Rentner/in",
            "ahv_freibetrag_aktiv": "AHV-Freibetrag aktiv",
            "qst_pflichtig": "QST-pflichtig",
            "qst_tarif": "QST-Tarif",
            "qst_kinder": "QST-Kinder",
            "qst_kirchensteuer": "QST-Kirchensteuer",
            "qst_prozent": "QST-Prozent",
            "qst_fixbetrag": "QST-Fixbetrag (CHF)",
        }
        widgets = {
            "client": forms.Select(attrs={"class": "adea-select"}),
            "first_name": forms.TextInput(attrs={"class": "adea-input"}),
            "last_name": forms.TextInput(attrs={"class": "adea-input"}),
            "role": forms.TextInput(attrs={"class": "adea-input"}),
            "hourly_rate": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.1",
                    "min": "0",
                }
            ),
            "weekly_hours": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.1",
                    "min": "0",
                }
            ),
            "nbu_pflichtig": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "is_rentner": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "ahv_freibetrag_aktiv": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "qst_pflichtig": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "qst_tarif": forms.TextInput(attrs={"class": "adea-input", "maxlength": "5"}),
            "qst_kinder": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "min": "0",
                }
            ),
            "qst_kirchensteuer": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "qst_prozent": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "qst_fixbetrag": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.05",
                    "min": "0",
                }
            ),
        }


class PayrollRecordForm(forms.ModelForm):
    show_gross_salary_field = True

    class Meta:
        model = PayrollRecord
        fields = [
            "employee",
            "month",
            "year",
            "status",
            "gross_salary",
        ]
        labels = {
            "employee": "Mitarbeiter",
            "month": "Monat",
            "year": "Jahr",
            "status": "Status",
            "gross_salary": "Bruttolohn (CHF)",
        }
        widgets = {
            "employee": forms.Select(attrs={"class": "adea-select"}),
            "month": forms.NumberInput(
                attrs={"class": "adea-input", "min": 1, "max": 12}
            ),
            "year": forms.NumberInput(
                attrs={"class": "adea-input", "min": 2000, "max": 2100}
            ),
            "status": forms.Select(attrs={"class": "adea-select"}),
            "gross_salary": forms.NumberInput(
                attrs={"class": "adea-input", "step": "0.05", "min": "0"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        employee_id = self.data.get("employee") or self.initial.get("employee")
        employee = None
        if employee_id:
            try:
                employee = Employee.objects.get(pk=employee_id)
            except Employee.DoesNotExist:
                employee = None
        elif self.instance and self.instance.pk:
            employee = self.instance.employee
        
        # Wenn gesperrt, Status-Feld readonly machen
        if self.instance and self.instance.pk and self.instance.is_locked():
            self.fields["status"].widget.attrs["readonly"] = True
            self.fields["status"].widget.attrs["disabled"] = True
        
        if employee and employee.hourly_rate > 0:
            self.fields["gross_salary"].required = False
            self.fields["gross_salary"].widget = forms.HiddenInput()
            self.show_gross_salary_field = False
        else:
            self.show_gross_salary_field = True


class FamilyAllowanceNachzahlungForm(forms.Form):
    """Form für die Erfassung von Familienzulagen-Nachzahlungen."""
    
    ZULAGENART_CHOICES = [
        ('KINDERZULAGE', 'Kinderzulage'),
        ('AUSBILDUNGSZULAGE', 'Ausbildungszulage'),
    ]
    
    zulagenart = forms.ChoiceField(
        choices=ZULAGENART_CHOICES,
        widget=forms.Select(attrs={"class": "adea-select"}),
        label="Zulagenart",
    )
    anzahl_monate = forms.IntegerField(
        min_value=1,
        max_value=24,
        widget=forms.NumberInput(attrs={"class": "adea-input", "min": 1, "max": 24}),
        label="Anzahl Monate",
        help_text="Anzahl Monate für die Nachzahlung (z.B. 3 für April–Juni)",
    )
    monatsbetrag = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.05", "min": "0"}),
        label="Monatsbetrag (CHF)",
        help_text="Monatlicher Betrag der Zulage",
    )
    beschreibung = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "adea-input"}),
        label="Beschreibung",
        help_text="Wird automatisch generiert, falls leer",
    )
    sva_entscheid = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "adea-input"}),
        label="SVA-Entscheid (optional)",
        help_text="Referenz zum SVA-Entscheid (z.B. FAK-2025-12345)",
    )
    
    def __init__(self, *args, payroll_record=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.payroll_record = payroll_record
        
        # Vorgabewert aus FamilyAllowanceParameter setzen
        if payroll_record:
            year = payroll_record.year
            try:
                params = FamilyAllowanceParameter.objects.get(year=year)
                # Standardwert für Kinderzulage setzen
                self.fields['monatsbetrag'].initial = params.monatlich_kinderzulage
            except FamilyAllowanceParameter.DoesNotExist:
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        anzahl_monate = cleaned_data.get('anzahl_monate')
        monatsbetrag = cleaned_data.get('monatsbetrag')
        
        if anzahl_monate and monatsbetrag:
            # Gesamtbetrag berechnen
            cleaned_data['gesamtbetrag'] = Decimal(str(anzahl_monate)) * monatsbetrag
        
        return cleaned_data


class PayrollItemSpesenForm(forms.Form):
    """Form für die Erfassung von Spesen als PayrollItem."""
    
    wage_type = forms.ModelChoiceField(
        queryset=WageType.objects.filter(code__startswith='SPESEN_'),
        widget=forms.Select(attrs={"class": "adea-select"}),
        label="Spesenart",
        help_text="Wählen Sie die Art der Spesen aus",
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.05", "min": "0"}),
        label="Betrag (CHF)",
        help_text="Spesenbetrag",
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "adea-input"}),
        label="Beschreibung (optional)",
        help_text="Zusätzliche Informationen zu den Spesen",
    )
    
    def __init__(self, *args, payroll_record=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.payroll_record = payroll_record
        # Nur aktive Spesen-WageTypes anzeigen
        self.fields['wage_type'].queryset = WageType.objects.filter(
            code__startswith='SPESEN_',
            is_active=True
        ).order_by('code')


class PayrollItemPrivatanteilForm(forms.Form):
    """Form für die Erfassung von Privatanteilen (Auto/Telefon) als PayrollItem."""
    
    wage_type = forms.ModelChoiceField(
        queryset=WageType.objects.filter(code__startswith='PRIVATANTEIL_'),
        widget=forms.Select(attrs={"class": "adea-select"}),
        label="Privatanteil",
        help_text="Wählen Sie die Art des Privatanteils aus",
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.05", "min": "0"}),
        label="Betrag (CHF)",
        help_text="Privatanteil-Betrag (voll AHV-/Steuer-/QST-pflichtig)",
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "adea-input"}),
        label="Beschreibung (optional)",
        help_text="Zusätzliche Informationen zum Privatanteil",
    )
    
    def __init__(self, *args, payroll_record=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.payroll_record = payroll_record
        # Nur aktive Privatanteil-WageTypes anzeigen
        self.fields['wage_type'].queryset = WageType.objects.filter(
            code__startswith='PRIVATANTEIL_',
            is_active=True
        ).order_by('code')

