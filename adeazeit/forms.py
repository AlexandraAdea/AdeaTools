from django import forms
from django.db import models
from datetime import date
from .models import EmployeeInternal, ServiceType, ZeitProject, TimeEntry, Absence, Task
from adeacore.models import Client


class EmployeeInternalForm(forms.ModelForm):
    class Meta:
        model = EmployeeInternal
        fields = [
            # Stammdaten
            "code",
            "name",
            "function_title",
            "rolle",
            # Arbeitszeitmodell
            "employment_percent",
            "weekly_soll_hours",
            "weekly_working_days",
            # Ferien & Feiertage
            "vacation_days_per_year",
            "work_canton",
            "holiday_model",
            # Beschäftigung
            "employment_start",
            "employment_end",
            # Legacy-Felder aus Form entfernt (nur in Admin verfügbar)
            # "eintrittsdatum",
            # "austrittsdatum",
            # Finanzen
            "stundensatz",
            # Status & Notizen
            "aktiv",
            "notes",
        ]
        widgets = {
            "code": forms.TextInput(attrs={"class": "adea-input"}),
            "name": forms.TextInput(attrs={"class": "adea-input"}),
            "function_title": forms.TextInput(attrs={"class": "adea-input"}),
            "rolle": forms.TextInput(attrs={"class": "adea-input"}),
            "employment_percent": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
            "weekly_soll_hours": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
            "weekly_working_days": forms.NumberInput(attrs={"class": "adea-input", "step": "0.1"}),
            "vacation_days_per_year": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
            "work_canton": forms.TextInput(attrs={"class": "adea-input"}),
            "holiday_model": forms.TextInput(attrs={"class": "adea-input"}),
            "employment_start": forms.DateInput(attrs={"class": "adea-input", "type": "date"}, format="%Y-%m-%d"),
            "employment_end": forms.DateInput(attrs={"class": "adea-input", "type": "date"}, format="%Y-%m-%d"),
            # Legacy-Felder aus Form entfernt
            # "eintrittsdatum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            # "austrittsdatum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "stundensatz": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
            "aktiv": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "notes": forms.Textarea(attrs={"class": "adea-textarea", "rows": 4}),
        }
        help_texts = {
            "code": "Eindeutiger Kurzcode für den Mitarbeiter (z.B. MM, EMP001, AM)",
            "employment_percent": "Beispiel: 100.00, 60.00",
            "weekly_soll_hours": "Gesamte wöchentliche Sollstunden (z.B. 42.00 oder 40.00)",
            "weekly_working_days": "z.B. 5.0 / 4.5 / 4.0",
            "vacation_days_per_year": "z.B. 20.00 / 25.00",
            "work_canton": "Für zukünftige Feiertagsmodelle",
            "holiday_model": "Freitext",
            "stundensatz": "Koeffizient für die Verrechnung von Services (z.B. 0.5 = 50% des Standard-Stundensatzes, 1.3 = 30% Aufschlag)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hilfe-Text für alle Felder
        self.fields["employment_percent"].help_text = "Alle Arbeitszeitmodelle werden manuell erfasst und können jederzeit geändert werden."

    def clean(self):
        cleaned_data = super().clean()
        employment_percent = cleaned_data.get("employment_percent")
        weekly_soll_hours = cleaned_data.get("weekly_soll_hours")
        employment_start = cleaned_data.get("employment_start")
        employment_end = cleaned_data.get("employment_end")
        
        if employment_percent is not None and employment_percent <= 0:
            raise forms.ValidationError({
                "employment_percent": "Beschäftigungsgrad muss größer als 0 sein."
            })
        
        if weekly_soll_hours is not None and weekly_soll_hours <= 0:
            raise forms.ValidationError({
                "weekly_soll_hours": "Wöchentliche Sollstunden müssen größer als 0 sein."
            })
        
        if employment_end and employment_start and employment_end < employment_start:
            raise forms.ValidationError({
                "employment_end": "Beschäftigungsende darf nicht vor Beschäftigungsbeginn liegen."
            })
        
        return cleaned_data


class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = ["code", "name", "standard_rate", "billable", "description"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "adea-input"}),
            "name": forms.TextInput(attrs={"class": "adea-input"}),
            "standard_rate": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
            "billable": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "description": forms.Textarea(attrs={"class": "adea-textarea", "rows": 3}),
        }


class ZeitProjectForm(forms.ModelForm):
    class Meta:
        model = ZeitProject
        fields = ["client", "name", "aktiv"]
        widgets = {
            "client": forms.Select(attrs={"class": "adea-select"}),
            "name": forms.TextInput(attrs={"class": "adea-input"}),
            "aktiv": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
        }


class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = [
            "mitarbeiter",
            "client",
            "datum",
            "start",
            "ende",
            "dauer",
            "service_type",
            "kommentar",
            "billable",
            "verrechnet",
            "rate",
        ]
        widgets = {
            "mitarbeiter": forms.Select(attrs={"class": "adea-select"}),
            "client": forms.Select(attrs={"class": "adea-select"}),
            "datum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}, format="%Y-%m-%d"),
            "start": forms.TimeInput(attrs={"class": "adea-input", "type": "time"}),
            "ende": forms.TimeInput(attrs={"class": "adea-input", "type": "time"}),
            "dauer": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01", "readonly": True}),
            "service_type": forms.Select(attrs={"class": "adea-select"}),
            "kommentar": forms.Textarea(attrs={"class": "adea-textarea", "rows": 3}),
            "billable": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "verrechnet": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "rate": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01", "placeholder": "Wird automatisch gesetzt"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter: Nur aktive Mitarbeitende (employment_end ist None oder >= heute)
        today = date.today()
        self.fields["mitarbeiter"].queryset = EmployeeInternal.objects.filter(
            aktiv=True
        ).filter(
            models.Q(employment_end__isnull=True) | models.Q(employment_end__gte=today)
        )
        # Filter: Alle Clients (FIRMA und PRIVAT)
        self.fields["client"].queryset = Client.objects.all().order_by("name")
        # Mandant ist optional für interne Arbeiten
        self.fields["client"].required = False


class AbsenceForm(forms.ModelForm):
    class Meta:
        model = Absence
        fields = ["employee", "absence_type", "date_from", "date_to", "full_day", "hours", "comment"]
        widgets = {
            "employee": forms.Select(attrs={"class": "adea-select"}),
            "absence_type": forms.Select(attrs={"class": "adea-select"}),
            "date_from": forms.DateInput(attrs={"class": "adea-input", "type": "date"}, format="%Y-%m-%d"),
            "date_to": forms.DateInput(attrs={"class": "adea-input", "type": "date"}, format="%Y-%m-%d"),
            "full_day": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "hours": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
            "comment": forms.Textarea(attrs={"class": "adea-textarea", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter: Nur aktive Mitarbeitende
        today = date.today()
        self.fields["employee"].queryset = EmployeeInternal.objects.filter(
            aktiv=True
        ).filter(
            models.Q(employment_end__isnull=True) | models.Q(employment_end__gte=today)
        )
        
        # JavaScript für Stunden-Feld
        self.fields["full_day"].widget.attrs["onchange"] = "toggleHoursField(this)"


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "titel",
            "beschreibung",
            "status",
            "prioritaet",
            "fälligkeitsdatum",
            "notizen",
            "client",
            "mitarbeiter",
        ]
        widgets = {
            "titel": forms.TextInput(attrs={"class": "adea-input"}),
            "beschreibung": forms.Textarea(attrs={"class": "adea-textarea", "rows": 4}),
            "status": forms.Select(attrs={"class": "adea-select"}),
            "prioritaet": forms.Select(attrs={"class": "adea-select"}),
            "fälligkeitsdatum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}, format="%Y-%m-%d"),
            "notizen": forms.Textarea(attrs={"class": "adea-textarea", "rows": 3}),
            "client": forms.Select(attrs={"class": "adea-select"}),
            "mitarbeiter": forms.Select(attrs={"class": "adea-select"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter: Nur aktive Mitarbeitende
        today = date.today()
        self.fields["mitarbeiter"].queryset = EmployeeInternal.objects.filter(
            aktiv=True
        ).filter(
            models.Q(employment_end__isnull=True) | models.Q(employment_end__gte=today)
        )
        # Filter: Alle Clients
        self.fields["client"].queryset = Client.objects.all().order_by("name")
        # Client ist optional
        self.fields["client"].required = False
