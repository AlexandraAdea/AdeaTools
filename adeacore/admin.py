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
    list_display = ("name", "client_type", "zahlungsverhalten", "city", "email", "mwst_nr", "created_at")
    search_fields = ("name", "city", "email", "mwst_nr")
    list_filter = ("client_type", "zahlungsverhalten", "city")
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
                "fields": ("mwst_pflichtig", "mwst_nr", "rechnungs_email", "zahlungsziel_tage", "zahlungsverhalten"),
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
        "bruttolohn",
        "nettolohn",
        "qst_abzug",
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
                    "bruttolohn",
                    "nettolohn",
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
                    "qst_abzug",
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
        "qst_abzug",
        "nettolohn",
    )


@admin.register(models.CompanyData)
class CompanyDataAdmin(admin.ModelAdmin):
    """Admin für Firmendaten (Singleton)."""
    list_display = ("company_name", "city", "mwst_nr", "email")
    fieldsets = (
        (
            "Firmendaten",
            {
                "fields": ("company_name",),
                "description": "Name der Firma (Adea Treuhand).",
            },
        ),
        (
            "Adresse",
            {
                "fields": ("street", "house_number", "zipcode", "city", "country"),
            },
        ),
        (
            "Kontakt",
            {
                "fields": ("email", "phone", "website"),
            },
        ),
        (
            "Rechnungsdaten",
            {
                "fields": ("mwst_nr", "iban"),
                "description": "MWST-Nummer im Format 'CHE-XXX.XXX.XXX MWST' und IBAN für QR-Rechnungen.",
            },
        ),
    )
    
    def has_add_permission(self, request):
        """Verhindert das Hinzufügen mehrerer Instanzen."""
        if models.CompanyData.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        """Verhindert das Löschen der Firmendaten."""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Leitet zur Bearbeitungsseite weiter, wenn nur eine Instanz existiert."""
        instance = models.CompanyData.get_instance()
        if instance:
            return self.change_view(request, str(instance.pk), extra_context)
        return super().changelist_view(request, extra_context)


class InvoiceItemInline(admin.TabularInline):
    """Inline für Rechnungspositionen."""
    model = models.InvoiceItem
    extra = 0
    fields = ("service_date", "service_type_code", "employee_name", "description", "quantity", "unit_price", "net_amount", "vat_rate", "vat_amount", "gross_amount")
    readonly_fields = ("service_date", "service_type_code", "employee_name", "description", "quantity", "unit_price", "net_amount", "vat_rate", "vat_amount", "gross_amount")
    can_delete = False


@admin.register(models.Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin für Rechnungen."""
    list_display = ("invoice_number", "client", "invoice_date", "due_date", "amount", "payment_status", "created_at")
    list_filter = ("payment_status", "invoice_date", "due_date")
    search_fields = ("invoice_number", "client__name")
    autocomplete_fields = ("client", "created_by")
    readonly_fields = ("invoice_number", "created_at", "updated_at", "remaining_amount")
    inlines = [InvoiceItemInline]
    fieldsets = (
        (
            "Grunddaten",
            {
                "fields": ("client", "invoice_number", "invoice_date", "due_date"),
            },
        ),
        (
            "Beträge",
            {
                "fields": ("net_amount", "vat_rate", "vat_amount", "amount", "paid_amount", "remaining_amount"),
            },
        ),
        (
            "Zahlungsstatus",
            {
                "fields": ("payment_status", "payment_date"),
            },
        ),
        (
            "Beschreibung",
            {
                "fields": ("description",),
            },
        ),
        (
            "Metadaten",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    
    def remaining_amount(self, obj):
        """Berechnet den offenen Betrag."""
        if obj:
            return obj.amount - obj.paid_amount
        return None
    remaining_amount.short_description = "Offener Betrag"

