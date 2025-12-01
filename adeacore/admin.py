from django.contrib import admin
from django.utils.html import format_html

from . import models


class SVAEntscheidInline(admin.TabularInline):
    """Inline-Anzeige für SVA-Entscheide im Employee-Admin."""
    model = models.SVAEntscheid
    extra = 0
    fields = ("entscheid", "von_datum", "bis_datum", "betrag_monatlich", "is_aktiv_display")
    readonly_fields = ("is_aktiv_display",)
    verbose_name = "SVA-Entscheid"
    verbose_name_plural = "SVA-Entscheide"

    def is_aktiv_display(self, obj):
        """Zeigt an, ob der Entscheid aktuell aktiv ist."""
        if obj and obj.pk:
            if obj.is_aktiv():
                return format_html('<span style="color: green;">✓ Aktiv</span>')
            else:
                return format_html('<span style="color: red;">✗ Inaktiv</span>')
        return "-"

    is_aktiv_display.short_description = "Status"


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "client_type", "city", "email", "mwst_nr", "created_at")
    search_fields = ("name", "city", "email", "mwst_nr")
    list_filter = ("client_type", "city")
    fieldsets = (
        (
            "Grunddaten",
            {
                "fields": ("name", "client_type"),
                "description": "Name und Typ des Mandanten. FIRMA = für Lohnbuchhaltung, PRIVAT = nur für Zeiterfassung.",
            },
        ),
        (
            "Kontakt",
            {
                "fields": ("email", "phone", "kontaktperson_name"),
            },
        ),
        (
            "Adresse",
            {
                "fields": ("street", "house_number", "zipcode", "city"),
            },
        ),
        (
            "MWST & Rechnungsdaten (nur FIRMA)",
            {
                "fields": ("mwst_pflichtig", "mwst_nr", "rechnungs_email", "zahlungsziel_tage"),
                "classes": ("collapse",),
            },
        ),
        (
            "Steuerdaten (nur PRIVAT)",
            {
                "fields": ("geburtsdatum", "steuerkanton"),
                "classes": ("collapse",),
            },
        ),
        (
            "Weitere Daten",
            {
                "fields": ("uid", "interne_notizen"),
            },
        ),
        (
            "Module-Aktivierung",
            {
                "fields": ("lohn_aktiv",),
                "description": "Aktivierung der Module für diesen Mandanten.",
            },
        ),
    )
    ordering = ("name",)


# CRM-Models registrieren
@admin.register(models.Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('client', 'communication_type', 'subject', 'date', 'created_by')
    list_filter = ('communication_type', 'date')
    search_fields = ('subject', 'content', 'client__name')
    date_hierarchy = 'date'


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('client', 'title', 'event_type', 'start_date', 'created_by')
    list_filter = ('event_type', 'start_date', 'is_recurring')
    search_fields = ('title', 'description', 'client__name')
    date_hierarchy = 'start_date'


@admin.register(models.Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'invoice_date', 'amount', 'payment_status', 'due_date')
    list_filter = ('payment_status', 'invoice_date')
    search_fields = ('invoice_number', 'client__name')
    date_hierarchy = 'invoice_date'


@admin.register(models.Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'document_type', 'created_at', 'uploaded_by')
    list_filter = ('document_type', 'created_at')
    search_fields = ('title', 'description', 'client__name')


@admin.register(models.Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "client",
        "role",
        "hourly_rate",
        "weekly_hours",
        "nbu_pflichtig",
        "qst_pflichtig",
        "qst_tarif",
        "is_rentner",
        "ahv_freibetrag_aktiv",
    )
    search_fields = ("first_name", "last_name", "client__name", "role", "qst_tarif")
    list_filter = (
        "client",
        "role",
        "is_rentner",
        "ahv_freibetrag_aktiv",
        "nbu_pflichtig",
        "qst_pflichtig",
        "qst_kirchensteuer",
    )
    autocomplete_fields = ("client",)
    
    def get_form(self, request, obj=None, **kwargs):
        """Filtert Client-Feld auf FIRMA-Clients mit aktiviertem Lohnmodul."""
        form = super().get_form(request, obj, **kwargs)
        # Nur FIRMA-Clients mit aktiviertem Lohnmodul für Employee erlauben
        form.base_fields['client'].queryset = models.Client.objects.filter(
            client_type="FIRMA",
            lohn_aktiv=True
        )
        return form
    inlines = [SVAEntscheidInline]
    fieldsets = (
        (
            "Grunddaten",
            {
                "fields": ("client", "first_name", "last_name", "role", "hourly_rate"),
            },
        ),
        (
            "Arbeitszeit & Versicherungen",
            {
                "fields": (
                    "weekly_hours",
                    "nbu_pflichtig",
                    "is_rentner",
                    "ahv_freibetrag_aktiv",
                ),
            },
        ),
        (
            "Quellensteuer (QST)",
            {
                "fields": (
                    "qst_pflichtig",
                    "qst_tarif",
                    "qst_kinder",
                    "qst_kirchensteuer",
                    "qst_prozent",
                    "qst_fixbetrag",
                ),
                "description": "QST-Parameter: Fixbetrag hat Vorrang vor Prozentsatz, dann QSTParameter. "
                               "Tarif wird automatisch aus Familienstand, Kindern und Kirchensteuer generiert "
                               "(Format: A0N, A0Y, B1N, B1Y etc.).",
            },
        ),
    )


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "created_at")
    search_fields = ("name", "client__name")
    list_filter = ("client",)
    autocomplete_fields = ("client",)


@admin.register(models.TimeRecord)
class TimeRecordAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "client",
        "employee",
        "project",
        "hours",
    )
    search_fields = ("description", "employee__first_name", "employee__last_name")
    list_filter = ("client", "project")
    autocomplete_fields = ("client", "employee", "project")
    date_hierarchy = "date"


@admin.register(models.SVAEntscheid)
class SVAEntscheidAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "entscheid",
        "von_datum",
        "bis_datum",
        "betrag_monatlich",
        "is_aktiv_display",
    )
    list_filter = ("von_datum", "bis_datum")
    search_fields = (
        "employee__first_name",
        "employee__last_name",
        "entscheid",
        "beschreibung",
    )
    autocomplete_fields = ("employee",)
    date_hierarchy = "von_datum"
    fieldsets = (
        (
            "Mitarbeiter",
            {
                "fields": ("employee",),
            },
        ),
        (
            "Entscheid",
            {
                "fields": ("entscheid", "von_datum", "bis_datum"),
                "description": "Entscheid-Nummer und Gültigkeitszeitraum der Familienzulage.",
            },
        ),
        (
            "Betrag",
            {
                "fields": ("betrag_monatlich",),
                "description": "Monatlicher Betrag der Familienzulage in CHF.",
            },
        ),
        (
            "Zusätzliche Informationen",
            {
                "fields": ("beschreibung",),
                "classes": ("collapse",),
            },
        ),
    )
    ordering = ["-von_datum", "employee__last_name"]

    def is_aktiv_display(self, obj):
        """Zeigt an, ob der Entscheid aktuell aktiv ist."""
        if obj.is_aktiv():
            return format_html('<span style="color: green;">✓ Aktiv</span>')
        else:
            return format_html('<span style="color: red;">✗ Inaktiv</span>')

    is_aktiv_display.short_description = "Status"


@admin.register(models.PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "month",
        "year",
        "status",
        "gross_salary",
        "net_salary",
        "qst_amount",
        "created_at",
    )
    search_fields = ("employee__first_name", "employee__last_name")
    list_filter = ("year", "month", "status")
    autocomplete_fields = ("employee",)
    
    def get_form(self, request, obj=None, **kwargs):
        """Filtert Employee-Feld auf Employees von FIRMA-Clients."""
        form = super().get_form(request, obj, **kwargs)
        # Nur Employees von FIRMA-Clients erlauben
        form.base_fields['employee'].queryset = models.Employee.objects.filter(
            client__client_type="FIRMA"
        ).select_related('client')
        return form
    fieldsets = (
        (
            "Grunddaten",
            {
                "fields": ("employee", "month", "year", "status"),
            },
        ),
        (
            "Berechnete Werte",
            {
                "fields": (
                    "gross_salary",
                    "net_salary",
                    "ahv_basis",
                    "ahv_effective_basis",
                    "ahv_employee",
                    "ahv_employer",
                    "alv_basis",
                    "alv_effective_basis",
                    "alv_employee",
                    "alv_employer",
                    "uv_basis",
                    "uvg_effective_basis",
                    "bu_employer",
                    "bu_employee",
                    "nbu_employee",
                    "ktg_effective_basis",
                    "ktg_employee",
                    "ktg_employer",
                    "bvg_basis",
                    "bvg_insured_salary",
                    "bvg_employee",
                    "bvg_employer",
                    "qst_basis",
                    "qst_amount",
                ),
            },
        ),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Mache alle Felder readonly wenn PayrollRecord gesperrt ist."""
        readonly = list(self.readonly_fields)
        if obj and obj.is_locked():
            # Wenn gesperrt, alle Felder readonly außer Status (für manuelle Entsperrung)
            all_fields = [f.name for f in self.model._meta.fields]
            readonly = [f for f in all_fields if f != 'status']
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        """Verhindere Löschen von gesperrten PayrollRecords."""
        if obj and obj.is_locked():
            return False
        return super().has_delete_permission(request, obj)
    readonly_fields = (
        "ahv_basis",
        "ahv_effective_basis",
        "ahv_employee",
        "ahv_employer",
        "alv_basis",
        "alv_effective_basis",
        "alv_employee",
        "alv_employer",
        "uv_basis",
        "uvg_effective_basis",
        "bu_employer",
        "bu_employee",
        "nbu_employee",
        "ktg_effective_basis",
        "ktg_employee",
        "ktg_employer",
        "bvg_basis",
        "bvg_insured_salary",
        "bvg_employee",
        "bvg_employer",
        "qst_basis",
        "qst_amount",
        "net_salary",
    )

