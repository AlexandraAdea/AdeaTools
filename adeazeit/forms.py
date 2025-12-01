from django import forms
from django.db import models
from datetime import date
from .models import EmployeeInternal, ServiceType, ZeitProject, TimeEntry, Absence, Task
from adeacore.models import Client
from .permissions import can_view_all_entries, get_accessible_employees


class EmployeeInternalForm(forms.ModelForm):
    # Login-Zugang Felder (nicht im Model, sondern für User-Erstellung)
    create_login = forms.BooleanField(
        required=False,
        label="Login-Zugang erstellen",
        help_text="Aktivieren Sie diese Option, um automatisch einen Benutzer-Zugang für diesen Mitarbeiter zu erstellen.",
        widget=forms.CheckboxInput(attrs={"class": "adea-checkbox", "onchange": "toggleLoginFields(this)"}),
    )
    login_username = forms.CharField(
        required=False,
        max_length=150,
        label="Benutzername",
        help_text="Wird automatisch aus Mitarbeiterkürzel generiert, falls leer.",
        widget=forms.TextInput(attrs={"class": "adea-input"}),
    )
    login_password = forms.CharField(
        required=False,
        label="Passwort",
        help_text="Wird automatisch generiert, falls leer (Format: Code123).",
        widget=forms.PasswordInput(attrs={"class": "adea-input"}),
    )
    login_email = forms.EmailField(
        required=False,
        label="E-Mail",
        help_text="Optional - für Passwort-Reset und Benachrichtigungen.",
        widget=forms.EmailInput(attrs={"class": "adea-input"}),
    )
    login_role = forms.ChoiceField(
        required=False,
        choices=[
            ("mitarbeiter", "Mitarbeiter"),
            ("manager", "Manager"),
            ("admin", "Admin"),
        ],
        initial="mitarbeiter",
        label="Rolle",
        help_text="Berechtigungsstufe für AdeaZeit.",
        widget=forms.Select(attrs={"class": "adea-select"}),
    )
    
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
            # Finanzen - stundensatz entfernt (nur in Admin verfügbar)
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
            "employment_start": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "employment_end": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            # Legacy-Felder aus Form entfernt
            # "eintrittsdatum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            # "austrittsdatum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            # "stundensatz": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),  # Entfernt, da Feld nicht mehr in fields
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hilfe-Text für alle Felder
        self.fields["employment_percent"].help_text = "Alle Arbeitszeitmodelle werden manuell erfasst und können jederzeit geändert werden."
        
        # Wenn Bearbeitung: Prüfe ob bereits Login existiert
        if self.instance and self.instance.pk:
            from .models import UserProfile
            try:
                profile = UserProfile.objects.get(employee=self.instance)
                # Zeige bestehenden Zugang an
                self.fields["create_login"].initial = True
                self.fields["create_login"].widget.attrs["disabled"] = True
                self.fields["login_username"].initial = profile.user.username
                self.fields["login_username"].widget.attrs["readonly"] = True
                self.fields["login_password"].widget.attrs["placeholder"] = "Nur ändern wenn neues Passwort gesetzt werden soll"
                # Bestehende Rolle anzeigen
                from django.contrib.auth.models import Group
                from .permissions import ROLE_ADMIN, ROLE_MANAGER, ROLE_MITARBEITER
                user_groups = profile.user.groups.values_list('name', flat=True)
                if ROLE_ADMIN in user_groups:
                    self.fields["login_role"].initial = "admin"
                elif ROLE_MANAGER in user_groups:
                    self.fields["login_role"].initial = "manager"
                else:
                    self.fields["login_role"].initial = "mitarbeiter"
            except UserProfile.DoesNotExist:
                pass

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
        
        # Validierung für Login-Felder
        create_login = cleaned_data.get("create_login")
        if create_login:
            login_username = cleaned_data.get("login_username", "").strip()
            login_password = cleaned_data.get("login_password", "").strip()
            
            # Wenn Username leer, generiere aus Code
            if not login_username:
                code = cleaned_data.get("code", "")
                if code:
                    login_username = code.lower()
                else:
                    raise forms.ValidationError({
                        "login_username": "Benutzername ist erforderlich wenn Login erstellt wird."
                    })
            
            # Prüfe ob Username bereits existiert (nur bei Neuanlage)
            if not self.instance.pk:
                from django.contrib.auth.models import User
                if User.objects.filter(username=login_username).exists():
                    raise forms.ValidationError({
                        "login_username": f"Benutzername '{login_username}' existiert bereits."
                    })
            else:
                # Bei Bearbeitung: Prüfe nur wenn Username geändert wurde
                from django.contrib.auth.models import User
                from .models import UserProfile
                try:
                    profile = UserProfile.objects.get(employee=self.instance)
                    if profile.user.username != login_username:
                        if User.objects.filter(username=login_username).exists():
                            raise forms.ValidationError({
                                "login_username": f"Benutzername '{login_username}' existiert bereits."
                            })
                except UserProfile.DoesNotExist:
                    if User.objects.filter(username=login_username).exists():
                        raise forms.ValidationError({
                            "login_username": f"Benutzername '{login_username}' existiert bereits."
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
            "rate",
        ]
        widgets = {
            "mitarbeiter": forms.Select(attrs={"class": "adea-select"}),
            "client": forms.Select(attrs={"class": "adea-select"}),
            "datum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "start": forms.TimeInput(attrs={"class": "adea-input", "type": "time"}),
            "ende": forms.TimeInput(attrs={"class": "adea-input", "type": "time"}),
            "dauer": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01", "readonly": True}),
            "service_type": forms.Select(attrs={"class": "adea-select"}),
            "kommentar": forms.Textarea(attrs={"class": "adea-textarea", "rows": 3}),
            "billable": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "rate": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01", "placeholder": "Wird automatisch gesetzt"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter Mitarbeiter nach Rolle
        from .permissions import get_accessible_employees, can_view_all_entries
        
        if self.user:
            if can_view_all_entries(self.user):
                # Admin/Manager: Alle aktiven Mitarbeitenden
                today = date.today()
                self.fields["mitarbeiter"].queryset = EmployeeInternal.objects.filter(
                    aktiv=True
                ).filter(
                    models.Q(employment_end__isnull=True) | models.Q(employment_end__gte=today)
                )
            else:
                # Mitarbeiter: Nur sich selbst
                accessible_employees = get_accessible_employees(self.user)
                self.fields["mitarbeiter"].queryset = accessible_employees
                # Setze automatisch auf eigenen Mitarbeiter
                if accessible_employees.exists():
                    self.fields["mitarbeiter"].initial = accessible_employees.first()
                    # Feld auf readonly setzen für Mitarbeiter
                    self.fields["mitarbeiter"].widget.attrs['readonly'] = True
                    self.fields["mitarbeiter"].widget.attrs['style'] = 'background: #f5f5f7; cursor: not-allowed;'
        else:
            # Fallback: Alle aktiven Mitarbeitenden
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
            "date_from": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "date_to": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "full_day": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "hours": forms.NumberInput(attrs={"class": "adea-input", "step": "0.01"}),
            "comment": forms.Textarea(attrs={"class": "adea-textarea", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter Mitarbeiter nach Rolle
        from .permissions import get_accessible_employees, can_view_all_entries
        
        if self.user:
            if can_view_all_entries(self.user):
                # Admin/Manager: Alle aktiven Mitarbeitenden
                today = date.today()
                self.fields["employee"].queryset = EmployeeInternal.objects.filter(
                    aktiv=True
                ).filter(
                    models.Q(employment_end__isnull=True) | models.Q(employment_end__gte=today)
                )
            else:
                # Mitarbeiter: Nur sich selbst
                accessible_employees = get_accessible_employees(self.user)
                self.fields["employee"].queryset = accessible_employees
                # Setze automatisch auf eigenen Mitarbeiter
                if accessible_employees.exists():
                    self.fields["employee"].initial = accessible_employees.first()
                    # Feld auf readonly setzen für Mitarbeiter
                    self.fields["employee"].widget.attrs['readonly'] = True
                    self.fields["employee"].widget.attrs['style'] = 'background: #f5f5f7; cursor: not-allowed;'
        else:
            # Fallback: Alle aktiven Mitarbeitenden
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
            "client",
            "beschreibung",
            "status",
            "prioritaet",
            "fälligkeitsdatum",
            "notizen",
        ]
        widgets = {
            "titel": forms.TextInput(attrs={"class": "adea-input", "placeholder": "z.B. Steuererklärung Müller AG"}),
            "client": forms.Select(attrs={"class": "adea-select"}),
            "beschreibung": forms.Textarea(attrs={"class": "adea-textarea", "rows": 3}),
            "status": forms.Select(attrs={"class": "adea-select"}),
            "prioritaet": forms.Select(attrs={"class": "adea-select"}),
            "fälligkeitsdatum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "notizen": forms.Textarea(attrs={"class": "adea-textarea", "rows": 4, "placeholder": "Notizen zum aktuellen Stand (z.B. 'Warte auf Belege vom Kunden')"}),
        }
        help_texts = {
            "titel": "Kurze Beschreibung der Aufgabe",
            "client": "Optional: Mandant zuordnen",
            "fälligkeitsdatum": "Wichtig für Treuhand: Steuerfristen, MwSt-Abgaben, etc.",
            "notizen": "Notizen zum aktuellen Stand ('Wo geblieben')",
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter Mandanten: Alle Clients (FIRMA und PRIVAT)
        self.fields["client"].queryset = Client.objects.all().order_by("name")
        self.fields["client"].required = False
        
        # Mitarbeiter-Feld hinzufügen
        if self.user and can_view_all_entries(self.user):
            # Admin/Manager: Kann Mitarbeiter auswählen
            active_employees = EmployeeInternal.objects.filter(aktiv=True).order_by("name")
            if not active_employees.exists():
                # Keine aktiven Mitarbeiter - zeige Warnung
                self.fields["mitarbeiter"] = forms.ModelChoiceField(
                    queryset=active_employees,
                    widget=forms.Select(attrs={"class": "adea-select", "disabled": True}),
                    required=True,
                    label="Mitarbeiterin",
                    help_text="⚠️ Keine aktiven Mitarbeiter gefunden. Bitte erstellen Sie zuerst einen Mitarbeiter."
                )
            else:
                self.fields["mitarbeiter"] = forms.ModelChoiceField(
                    queryset=active_employees,
                    widget=forms.Select(attrs={"class": "adea-select"}),
                    required=True,
                    label="Mitarbeiterin"
                )
            if self.instance and self.instance.pk:
                self.fields["mitarbeiter"].initial = self.instance.mitarbeiter
        else:
            # Mitarbeiter: Automatisch auf sich selbst setzen (wird in View gemacht)
            # Feld wird nicht angezeigt
            pass
        
        # Wenn Bearbeitung: Status kann geändert werden
        if self.instance and self.instance.pk:
            pass
        else:
            # Bei Neuanlage: Status auf OFFEN setzen
            self.fields["status"].initial = 'OFFEN'
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Prüfe, ob Mitarbeiter gesetzt wurde (für Admin/Manager)
        if self.user and can_view_all_entries(self.user):
            if 'mitarbeiter' not in cleaned_data or not cleaned_data.get('mitarbeiter'):
                raise forms.ValidationError({
                    'mitarbeiter': 'Bitte wählen Sie einen Mitarbeiter aus.'
                })
        
        return cleaned_data
