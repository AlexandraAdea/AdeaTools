"""
Formulare für AdeaRechnung.
"""
from django import forms
from adeacore.models import AkontoPlan


class AkontoPlanForm(forms.ModelForm):
    """Formular zum Erstellen/Bearbeiten eines Akonto-Plans."""

    class Meta:
        model = AkontoPlan
        fields = [
            "client",
            "amount",
            "interval",
            "start_date",
            "end_date",
            "active",
            "notes",
        ]
        widgets = {
            "client": forms.Select(attrs={"class": "adea-input"}),
            "amount": forms.NumberInput(attrs={"class": "adea-input", "min": "0.01", "step": "0.01"}),
            "interval": forms.Select(attrs={"class": "adea-input"}),
            "start_date": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "adea-input", "type": "date"}),
            "active": forms.CheckboxInput(attrs={"class": "adea-checkbox"}),
            "notes": forms.Textarea(attrs={"class": "adea-input", "rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            self.add_error("amount", "Der Akonto-Betrag muss grösser als 0 sein.")

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "Das Enddatum darf nicht vor dem Startdatum liegen.")

        return cleaned_data
