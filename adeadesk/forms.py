from django import forms

from adeacore.models import Client, Event, Document


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            # Grunddaten
            "name",
            "client_type",
            # Kontakt
            "email",
            "phone",
            "kontaktperson_name",
            # Adresse
            "street",
            "house_number",
            "zipcode",
            "city",
            # MWST & Rechnungsdaten (nur FIRMA)
            "mwst_pflichtig",
            "mwst_nr",
            "rechnungs_email",
            "zahlungsziel_tage",
            # Steuerdaten (nur PRIVAT)
            "geburtsdatum",
            "steuerkanton",
            # Weitere Daten
            "interne_notizen",
            # Module-Aktivierung
            "lohn_aktiv",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "adea-input"}),
            "client_type": forms.Select(attrs={"class": "adea-select"}),
            "email": forms.EmailInput(attrs={"class": "adea-input"}),
            "phone": forms.TextInput(attrs={"class": "adea-input"}),
            "kontaktperson_name": forms.TextInput(attrs={"class": "adea-input"}),
            "street": forms.TextInput(attrs={"class": "adea-input"}),
            "house_number": forms.TextInput(attrs={"class": "adea-input"}),
            "zipcode": forms.TextInput(attrs={"class": "adea-input"}),
            "city": forms.TextInput(attrs={"class": "adea-input"}),
            "mwst_pflichtig": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "mwst_nr": forms.TextInput(attrs={"class": "adea-input"}),
            "rechnungs_email": forms.EmailInput(attrs={"class": "adea-input"}),
            "zahlungsziel_tage": forms.NumberInput(attrs={"class": "adea-input", "min": 0}),
            "geburtsdatum": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "steuerkanton": forms.TextInput(attrs={"class": "adea-input"}),
            "interne_notizen": forms.Textarea(attrs={"class": "adea-textarea", "rows": 4}),
        }
        help_texts = {
            "client_type": "FIRMA = für Lohnbuchhaltung, PRIVAT = nur für Zeiterfassung",
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bedingte Anzeige basierend auf client_type
        # Prüfe zuerst POST-Daten, dann instance, dann initial
        client_type = None
        if self.data and 'client_type' in self.data:
            client_type = self.data.get('client_type')
        elif self.instance and self.instance.pk:
            client_type = self.instance.client_type
        elif 'client_type' in self.initial:
            client_type = self.initial.get('client_type')
        else:
            client_type = 'FIRMA'  # Default
        
        # Felder für PRIVAT ausblenden wenn FIRMA
        if client_type == "FIRMA":
            self.fields['geburtsdatum'].required = False
            self.fields['steuerkanton'].required = False
            # Setze Default-Werte für versteckte Felder
            if not self.data:  # Nur bei GET-Request
                self.fields['geburtsdatum'].widget = forms.HiddenInput()
                self.fields['steuerkanton'].widget = forms.HiddenInput()
        # Felder für FIRMA ausblenden wenn PRIVAT
        elif client_type == "PRIVAT":
            self.fields['mwst_pflichtig'].required = False
            self.fields['mwst_nr'].required = False
            self.fields['rechnungs_email'].required = False
            self.fields['zahlungsziel_tage'].required = False
            self.fields['kontaktperson_name'].required = False
            # Setze Default-Werte für versteckte Felder
            if not self.data:  # Nur bei GET-Request
                self.fields['mwst_pflichtig'].widget = forms.HiddenInput()
                self.fields['mwst_nr'].widget = forms.HiddenInput()
            self.fields['rechnungs_email'].widget = forms.HiddenInput()
            self.fields['zahlungsziel_tage'].widget = forms.HiddenInput()
            self.fields['kontaktperson_name'].widget = forms.HiddenInput()
            self.fields['lohn_aktiv'].widget = forms.HiddenInput()
    
    def clean(self):
        """Bereinige Felder basierend auf client_type."""
        cleaned_data = super().clean()
        client_type = cleaned_data.get('client_type')
        
        # Bei PRIVAT: Setze FIRMA-Felder auf Default-Werte
        if client_type == "PRIVAT":
            cleaned_data['mwst_pflichtig'] = False
            cleaned_data['mwst_nr'] = ''  # MWST-Nr = UID (Property)
            cleaned_data['rechnungs_email'] = None
            cleaned_data['zahlungsziel_tage'] = 30  # Default
            cleaned_data['kontaktperson_name'] = ''
            cleaned_data['lohn_aktiv'] = False  # PRIVAT kann nie Lohn haben
        
        # Bei FIRMA: Setze PRIVAT-Felder auf None
        elif client_type == "FIRMA":
            cleaned_data['geburtsdatum'] = None
            cleaned_data['steuerkanton'] = ''
        
        return cleaned_data


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "event_type",
            "title",
            "description",
            "start_date",
            "end_date",
            "reminder_date",
            "is_recurring",
            "recurring_pattern",
        ]
        widgets = {
            "event_type": forms.Select(attrs={"class": "adea-select"}),
            "title": forms.TextInput(attrs={"class": "adea-input"}),
            "description": forms.Textarea(attrs={"class": "adea-textarea", "rows": 4}),
            "start_date": forms.DateTimeInput(attrs={"class": "adea-input", "type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"class": "adea-input", "type": "datetime-local"}),
            "reminder_date": forms.DateTimeInput(attrs={"class": "adea-input", "type": "datetime-local"}),
            "is_recurring": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "recurring_pattern": forms.TextInput(attrs={"class": "adea-input"}),
        }


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            "document_type",
            "title",
            "description",
            "file",
        ]
        widgets = {
            "document_type": forms.Select(attrs={"class": "adea-select"}),
            "title": forms.TextInput(attrs={"class": "adea-input"}),
            "description": forms.Textarea(attrs={"class": "adea-textarea", "rows": 4}),
            "file": forms.FileInput(attrs={"class": "adea-input"}),
        }




