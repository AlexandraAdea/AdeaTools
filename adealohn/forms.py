from django import forms
from decimal import Decimal

from adeacore.models import Employee, PayrollRecord
from adealohn.models import (
    FamilyAllowanceParameter, WageType, PayrollItem,
    AHVParameter, ALVParameter, VKParameter, KTGParameter, UVGParameter, FAKParameter
)


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "client",
            "personalnummer",
            "first_name",
            "last_name",
            "geburtsdatum",
            "ahv_nummer",
            "street",
            "zipcode",
            "city",
            "country",
            "email",
            "phone",
            "mobile",
            "zivilstand",
            "eintrittsdatum",
            "austrittsdatum",
            "role",
            "taetigkeit_branche",
            "hourly_rate",
            "monthly_salary",
            "weekly_hours",
            "pensum",
            "iban",
            "vacation_weeks",
            "nbu_pflichtig",
            "is_rentner",
            "ahv_freibetrag_aktiv",
            "qst_pflichtig",
            "qst_tarif",
            "qst_kinder",
            "qst_kirchensteuer",
            "qst_fixbetrag",
            # qst_prozent entfernt - wird pro PayrollRecord gespeichert (ändert sich monatlich)
        ]
        labels = {
            "client": "Mandant",
            "personalnummer": "Personal-Nr.",
            "first_name": "Vorname",
            "last_name": "Nachname",
            "geburtsdatum": "Geburtsdatum",
            "ahv_nummer": "AHV-Nummer",
            "street": "Strasse",
            "zipcode": "PLZ",
            "city": "Ort",
            "country": "Land",
            "email": "E-Mail",
            "phone": "Telefon",
            "mobile": "Mobil",
            "zivilstand": "Zivilstand",
            "eintrittsdatum": "Eintrittsdatum",
            "austrittsdatum": "Austrittsdatum",
            "role": "Rolle/Tätigkeit",
            "taetigkeit_branche": "Tätigkeit/Branche",
            "hourly_rate": "Stundensatz (CHF)",
            "monthly_salary": "Monatslohn (CHF)",
            "weekly_hours": "Wöchentliche Stunden",
            "pensum": "Arbeitspensum (%)",
            "iban": "IBAN",
            "vacation_weeks": "Ferienwochen",
            "nbu_pflichtig": "NBU-pflichtig",
            "is_rentner": "Rentner/in",
            "ahv_freibetrag_aktiv": "AHV-Freibetrag aktiv",
            "qst_pflichtig": "QST-pflichtig",
            "qst_tarif": "QST-Tarif",
            "qst_kinder": "Anzahl Kinder",
            "qst_kirchensteuer": "Kirchensteuer",
            "qst_fixbetrag": "QST-Fixbetrag (CHF)",
        }
        widgets = {
            "client": forms.Select(attrs={"class": "adea-select"}),
            "personalnummer": forms.TextInput(attrs={"class": "adea-input"}),
            "first_name": forms.TextInput(attrs={"class": "adea-input"}),
            "last_name": forms.TextInput(attrs={"class": "adea-input"}),
            "geburtsdatum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "ahv_nummer": forms.TextInput(attrs={"class": "adea-input"}),
            "street": forms.TextInput(attrs={"class": "adea-input"}),
            "zipcode": forms.TextInput(attrs={"class": "adea-input"}),
            "city": forms.TextInput(attrs={"class": "adea-input"}),
            "country": forms.TextInput(attrs={"class": "adea-input"}),
            "email": forms.EmailInput(attrs={"class": "adea-input"}),
            "phone": forms.TextInput(attrs={"class": "adea-input"}),
            "mobile": forms.TextInput(attrs={"class": "adea-input"}),
            "zivilstand": forms.Select(attrs={"class": "adea-select"}),
            "eintrittsdatum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "austrittsdatum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "role": forms.TextInput(attrs={"class": "adea-input"}),
            "taetigkeit_branche": forms.TextInput(attrs={"class": "adea-input", "placeholder": "z.B. Coiffeur, Gastro"}),
            "hourly_rate": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "monthly_salary": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.01",
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
            "vacation_weeks": forms.Select(attrs={"class": "adea-select"}),
            "nbu_pflichtig": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "is_rentner": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "ahv_freibetrag_aktiv": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "qst_pflichtig": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "qst_tarif": forms.TextInput(attrs={"class": "adea-input", "maxlength": "5"}),
            "qst_kinder": forms.NumberInput(attrs={"class": "adea-input", "min": "0", "max": "10"}),
            "qst_kirchensteuer": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "qst_fixbetrag": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.01",
                    "min": "0",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_rentner = cleaned_data.get('is_rentner')
        ahv_freibetrag_aktiv = cleaned_data.get('ahv_freibetrag_aktiv')
        weekly_hours = cleaned_data.get('weekly_hours')
        nbu_pflichtig = cleaned_data.get('nbu_pflichtig')

        if ahv_freibetrag_aktiv and not is_rentner:
            self.add_error('ahv_freibetrag_aktiv', 'AHV-Freibetrag kann nur bei Rentnern aktiviert werden.')
        
        # NBU-Validierung: Nur ab 8h/Woche, und nur wenn weekly_hours ausgefüllt ist
        if nbu_pflichtig and weekly_hours is not None and weekly_hours > 0 and weekly_hours < Decimal("8"):
            self.add_error('nbu_pflichtig', 'NBU-Pflicht gilt nur ab 8 Stunden pro Woche. Bitte wöchentliche Stunden anpassen oder NBU-Pflicht deaktivieren.')
        
        return cleaned_data


class PayrollRecordForm(forms.ModelForm):
    show_bruttolohn_field = True
    hours_manual = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        min_value=Decimal("0"),
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01", "min": "0"}),
        label="Stunden (manuell)",
        help_text="Manuell erfasste Stunden für diesen Monat. Wird ignoriert, wenn Zeiteinträge vorhanden sind.",
    )

    class Meta:
        model = PayrollRecord
        fields = [
            "employee", "month", "year", "status", "bruttolohn", "qst_prozent",
            "manual_bvg_employee", "manual_bvg_employer",
        ]
        labels = {
            "employee": "Mitarbeiter",
            "month": "Monat",
            "year": "Jahr",
            "status": "Status",
            "bruttolohn": "Bruttolohn (CHF)",
            "qst_prozent": "QST-Prozentsatz (%)",
            "manual_bvg_employee": "BVG Arbeitnehmer (manuell, CHF)",
            "manual_bvg_employer": "BVG Arbeitgeber (manuell, CHF)",
        }
        widgets = {
            "employee": forms.Select(attrs={"class": "adea-select"}),
            "month": forms.Select(attrs={"class": "adea-select"}, choices=[
                (1, "Januar"), (2, "Februar"), (3, "März"), (4, "April"),
                (5, "Mai"), (6, "Juni"), (7, "Juli"), (8, "August"),
                (9, "September"), (10, "Oktober"), (11, "November"), (12, "Dezember")
            ]),
            "year": forms.NumberInput(attrs={"class": "adea-input", "min": "2000", "max": "2100"}),
            "status": forms.Select(attrs={"class": "adea-select"}),
            "bruttolohn": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "qst_prozent": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "manual_bvg_employee": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.05",
                    "min": "0",
                }
            ),
            "manual_bvg_employer": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.05",
                    "min": "0",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        employee = self.instance.employee if self.instance and self.instance.pk else None
        
        # QST-Prozent nur anzeigen, wenn Mitarbeiter QST-pflichtig ist
        if employee and not employee.qst_pflichtig:
            self.fields['qst_prozent'].widget = forms.HiddenInput()
            self.fields['qst_prozent'].required = False
        else:
            self.fields['qst_prozent'].help_text = "QST-Prozentsatz für diesen Monat (z.B. 4.30 für 4.30%). Kann monatlich variieren bei Stundenlöhnen."
        
        # BVG-Felder: Hilfe-Text hinzufügen
        self.fields['manual_bvg_employee'].help_text = "Manueller BVG-Arbeitnehmerbeitrag (falls nicht automatisch berechnet). Wird zu berechneten Beiträgen addiert."
        self.fields['manual_bvg_employer'].help_text = "Manueller BVG-Arbeitgeberbeitrag (falls nicht automatisch berechnet). Wird zu berechneten Beiträgen addiert."
        self.fields['manual_bvg_employee'].required = False
        self.fields['manual_bvg_employer'].required = False
        
        # Stunden-Feld nur bei Stundenlöhnen anzeigen
        if employee and employee.hourly_rate > 0:
            self.fields["bruttolohn"].required = False
            self.fields["bruttolohn"].widget = forms.HiddenInput()
            self.show_bruttolohn_field = False
            self.fields["hours_manual"].help_text = "Stunden manuell eingeben, falls keine Zeiteinträge vorhanden sind. Wird automatisch aus Zeiteinträgen berechnet, wenn vorhanden."
        elif employee and employee.monthly_salary > 0:
            # Bei Monatslohn: Bruttolohn-Feld anzeigen (kann überschrieben werden)
            if not self.instance.pk:  # Nur bei neuem PayrollRecord
                self.fields["bruttolohn"].initial = employee.monthly_salary
            self.fields["bruttolohn"].help_text = f"Monatslohn (Standard: {employee.monthly_salary} CHF vom Mitarbeiter). Kann für diesen Monat überschrieben werden."
            self.fields["hours_manual"].widget = forms.HiddenInput()
            self.fields["hours_manual"].required = False
            self.show_bruttolohn_field = True
        else:
            # Weder Stunden- noch Monatslohn definiert
            self.fields["hours_manual"].widget = forms.HiddenInput()
            self.fields["hours_manual"].required = False
            self.show_bruttolohn_field = True


class FamilyAllowanceNachzahlungForm(forms.ModelForm):
    class Meta:
        model = PayrollItem
        fields = ["wage_type", "quantity", "amount", "description"]
        labels = {
            "wage_type": "Zulagenart",
            "quantity": "Anzahl Monate",
            "amount": "Monatsbetrag (CHF)",
            "description": "Beschreibung",
        }
        widgets = {
            "wage_type": forms.Select(attrs={"class": "adea-select"}),
            "quantity": forms.NumberInput(attrs={"class": "adea-input", "min": "1", "step": "1"}),
            "amount": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01", "min": "0"}),
            "description": forms.TextInput(attrs={"class": "adea-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur Kinderzulage anzeigen (vereinfacht - keine Unterscheidung mehr)
        self.fields["wage_type"].queryset = WageType.objects.filter(
            code__in=["KINDERZULAGE", "FAMILIENZULAGE"]  # FAMILIENZULAGE für Rückwärtskompatibilität
        )


class FamilyAllowanceLaufendForm(forms.ModelForm):
    """Formular für laufende Familienzulagen (nicht Nachzahlungen)."""
    class Meta:
        model = PayrollItem
        fields = ["wage_type", "amount", "description"]
        labels = {
            "wage_type": "Zulagenart",
            "amount": "Monatsbetrag (CHF)",
            "description": "Beschreibung (z.B. Name des Kindes)",
        }
        widgets = {
            "wage_type": forms.Select(attrs={"class": "adea-select"}),
            "amount": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01", "min": "0"}),
            "description": forms.TextInput(attrs={"class": "adea-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur Kinderzulage anzeigen
        self.fields["wage_type"].queryset = WageType.objects.filter(
            code__in=["KINDERZULAGE", "FAMILIENZULAGE"]  # FAMILIENZULAGE für Rückwärtskompatibilität
        )


class PayrollItemSpesenForm(forms.ModelForm):
    class Meta:
        model = PayrollItem
        fields = ["wage_type", "amount", "description"]
        labels = {
            "wage_type": "Spesenart",
            "amount": "Betrag (CHF)",
            "description": "Beschreibung",
        }
        widgets = {
            "wage_type": forms.Select(attrs={"class": "adea-select"}),
            "amount": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "description": forms.TextInput(attrs={"class": "adea-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur Spesen-WageTypes anzeigen
        self.fields["wage_type"].queryset = WageType.objects.filter(
            code__startswith="SPESEN_"
        )


class PayrollItemPrivatanteilForm(forms.ModelForm):
    class Meta:
        model = PayrollItem
        fields = ["wage_type", "amount", "description"]
        labels = {
            "wage_type": "Privatanteil",
            "amount": "Betrag (CHF)",
            "description": "Beschreibung",
        }
        widgets = {
            "wage_type": forms.Select(attrs={"class": "adea-select"}),
            "amount": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "description": forms.TextInput(attrs={"class": "adea-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nur Privatanteil-WageTypes anzeigen
        self.fields["wage_type"].queryset = WageType.objects.filter(
            code__startswith="PRIVATANTEIL_"
        )


class PayrollItemGeneralForm(forms.ModelForm):
    """Allgemeines Formular zum Hinzufügen von PayrollItems (Prämien, Trinkgeld, BVG-Zusatzbeiträge, etc.)"""
    class Meta:
        model = PayrollItem
        fields = ["wage_type", "quantity", "amount", "description"]
        labels = {
            "wage_type": "Lohnart",
            "quantity": "Menge",
            "amount": "Betrag (CHF)",
            "description": "Beschreibung",
        }
        widgets = {
            "wage_type": forms.Select(attrs={"class": "adea-select"}),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "adea-input",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "description": forms.TextInput(attrs={"class": "adea-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Zeige alle WageTypes außer den speziellen (Grundlohn, Ferienentschädigung, Spesen, Privatanteil, Familienzulagen)
        # Verwende Helper-Funktion für konsistente Filterung
        from .helpers import filter_wage_types_by_code
        
        excluded_codes = [
            "GRUNDLOHN_STUNDEN", "GRUNDLOHN_MONAT", "FERIENENTSCHAEDIGUNG",
            "KINDERZULAGE", "FAMILIENZULAGE",  # Familienzulagen werden separat erfasst
            "BVG_AN", "BVG_AG",  # BVG-Beiträge sind keine Lohnarten - werden direkt im PayrollRecord erfasst
        ]
        excluded_prefixes = ["SPESEN_", "PRIVATANTEIL_"]
        
        queryset = WageType.objects.filter(is_active=True)  # Nur aktive WageTypes
        queryset = filter_wage_types_by_code(queryset, excluded_codes, excluded_prefixes)
        
        self.fields["wage_type"].queryset = queryset.order_by("name")
        self.fields["quantity"].initial = Decimal("1")
        self.fields["quantity"].help_text = "Menge (z.B. 1 für einmalige Zahlung, Stunden für stundenbasierte Zulagen)"


class InsuranceRatesForm(forms.Form):
    """
    Formular für alle Versicherungsansätze (Arbeitgeber-Ebene) pro Jahr.
    Kombiniert alle Parameter-Models in einem Formular.
    """
    year = forms.IntegerField(
        label="Jahr",
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={"class": "adea-input"}),
        help_text="Jahr für diese Versicherungsansätze",
    )
    
    # AHV
    ahv_rate_employee = forms.DecimalField(
        label="AHV Rate Arbeitnehmer (%)",
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="z.B. 5.3 für 5.3%",
    )
    ahv_rate_employer = forms.DecimalField(
        label="AHV Rate Arbeitgeber (%)",
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="z.B. 5.3 für 5.3%",
    )
    ahv_rentner_freibetrag = forms.DecimalField(
        label="AHV Rentnerfreibetrag (CHF/Monat)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="Standard: 1'400 CHF",
    )
    
    # ALV
    alv_rate_employee = forms.DecimalField(
        label="ALV Rate Arbeitnehmer (%)",
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="z.B. 1.1 für 1.1%",
    )
    alv_rate_employer = forms.DecimalField(
        label="ALV Rate Arbeitgeber (%)",
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="z.B. 1.1 für 1.1%",
    )
    alv_max_annual = forms.DecimalField(
        label="ALV Max. versichertes Jahreseinkommen (CHF)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="Standard: 148'200 CHF",
    )
    
    # FAK
    fak_canton = forms.CharField(
        label="Kanton (FAK)",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={"class": "adea-input"}),
        help_text="Kanton für FAK-Rate (z.B. 'AG', 'ZH'). Leer = DEFAULT",
    )
    fak_rate_employer = forms.DecimalField(
        label="FAK Rate Arbeitgeber (%)",
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="z.B. 1.0 für 1.0%",
    )
    
    # VK
    vk_rate_employer = forms.DecimalField(
        label="VK Rate Arbeitgeber (%)",
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="z.B. 3.0 für 3.0%",
    )
    
    # UVG
    bu_rate_employer = forms.DecimalField(
        label="BU Rate Arbeitgeber (%)",
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="z.B. 0.644 für 0.644%",
    )
    nbu_rate_employee = forms.DecimalField(
        label="NBU Rate Arbeitnehmer (%)",
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="z.B. 2.3 für 2.3%",
    )
    uvg_max_annual = forms.DecimalField(
        label="UVG Max. versichertes Jahreseinkommen (CHF)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="Standard: 148'200 CHF",
    )
    
    # KTG
    ktg_rate_employee = forms.DecimalField(
        label="KTG Rate Arbeitnehmer (%)",
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="z.B. 0.5 für 0.5%",
    )
    ktg_rate_employer = forms.DecimalField(
        label="KTG Rate Arbeitgeber (%)",
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="z.B. 0.5 für 0.5%",
    )
    ktg_max_basis = forms.DecimalField(
        label="KTG Max. Basis (CHF)",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
        help_text="Standard: 300'000 CHF",
    )
