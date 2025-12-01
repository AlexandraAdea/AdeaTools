"""
CRM-Forms für Kommunikation, Termine, Rechnungen und Dokumente.
"""

from django import forms
from adeacore.models import Communication, Event, Invoice, Document


class CommunicationForm(forms.ModelForm):
    """Form für Kommunikationshistorie."""
    
    class Meta:
        model = Communication
        fields = [
            'communication_type',
            'subject',
            'content',
            'date',
            'duration_minutes',
        ]
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'adea-input'}),
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'adea-input'}),
            'subject': forms.TextInput(attrs={'class': 'adea-input'}),
            'communication_type': forms.Select(attrs={'class': 'adea-select'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'adea-input', 'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop('client', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.client:
            instance.client = self.client
        if self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance


class EventForm(forms.ModelForm):
    """Form für Termine/Events."""
    
    class Meta:
        model = Event
        fields = [
            'event_type',
            'title',
            'description',
            'start_date',
            'end_date',
            'reminder_date',
            'is_recurring',
            'recurring_pattern',
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'adea-input'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'adea-input'}),
            'reminder_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'adea-input'}),
            'title': forms.TextInput(attrs={'class': 'adea-input'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'adea-input'}),
            'event_type': forms.Select(attrs={'class': 'adea-select'}),
            'recurring_pattern': forms.TextInput(attrs={'class': 'adea-input'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'adea-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop('client', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.client:
            instance.client = self.client
        if self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance


class InvoiceForm(forms.ModelForm):
    """Form für Rechnungen."""
    
    class Meta:
        model = Invoice
        fields = [
            'invoice_number',
            'invoice_date',
            'due_date',
            'amount',
            'paid_amount',
            'payment_status',
            'payment_date',
            'description',
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'adea-input'}),
            'invoice_date': forms.DateInput(attrs={'type': 'date', 'class': 'adea-input'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'adea-input'}),
            'amount': forms.NumberInput(attrs={'class': 'adea-input', 'step': '0.01', 'min': '0'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'adea-input', 'step': '0.01', 'min': '0'}),
            'payment_status': forms.Select(attrs={'class': 'adea-select'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'adea-input'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'adea-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop('client', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Setze Fälligkeitsdatum basierend auf Zahlungsziel
        if self.client and not self.instance.pk:
            from datetime import timedelta
            from django.utils import timezone
            if self.client.zahlungsziel_tage:
                self.initial['due_date'] = (timezone.now().date() + timedelta(days=self.client.zahlungsziel_tage))
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.client:
            instance.client = self.client
        if self.user:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance


class DocumentForm(forms.ModelForm):
    """Form für Dokumente."""
    
    class Meta:
        model = Document
        fields = [
            'document_type',
            'title',
            'description',
            'file',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'adea-input'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'adea-input'}),
            'document_type': forms.Select(attrs={'class': 'adea-select'}),
            'file': forms.FileInput(attrs={'class': 'adea-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.client = kwargs.pop('client', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.client:
            instance.client = self.client
        if self.user:
            instance.uploaded_by = self.user
        if commit:
            instance.save()
        return instance



