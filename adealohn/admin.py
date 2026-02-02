from django.contrib import admin

from adealohn.models import (
    WageType, PayrollItem, KTGParameter, BVGParameter, QSTParameter, 
    FamilyAllowanceParameter, UVGParameter, FAKParameter, AHVParameter, 
    ALVParameter, VKParameter
)
from adeacore.models import PayrollRecord


@admin.register(WageType)
class WageTypeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "category",
        "is_lohnwirksam",
        "ahv_relevant",
        "is_active",
    )
    list_filter = ("category", "is_active", "ahv_relevant")
    search_fields = ("code", "name", "description")
    fieldsets = (
        (
            "Grunddaten",
            {
                "fields": ("code", "name", "category", "description", "is_active"),
            },
        ),
        (
            "Lohnwirksamkeit",
            {
                "fields": ("is_lohnwirksam",),
                "description": "Ist diese Lohnart lohnwirksam (gehört zum Bruttolohn)?",
            },
        ),
        (
            "Sozialversicherungen",
            {
                "fields": ("ahv_relevant", "alv_relevant", "uv_relevant", "bvg_relevant"),
                "description": "Welche Sozialversicherungen sind auf diese Lohnart anwendbar?",
            },
        ),
        (
            "Steuern",
            {
                "fields": ("qst_relevant", "taxable"),
                "description": "QST-Relevanz und Steuerpflicht",
            },
        ),
    )
    
    def get_queryset(self, request):
        """Filter für Spesen-WageTypes hinzufügen."""
        qs = super().get_queryset(request)
        if request.GET.get('spesen') == '1':
            qs = qs.filter(code__startswith='SPESEN_')
        return qs
    
    def changelist_view(self, request, extra_context=None):
        """Hinzufügen eines Links für Spesen-Filter."""
        extra_context = extra_context or {}
        extra_context['show_spesen_filter'] = True
        return super().changelist_view(request, extra_context)


@admin.register(PayrollItem)
class PayrollItemAdmin(admin.ModelAdmin):
    list_display = ("payroll", "wage_type", "quantity", "amount", "total")
    list_filter = ("wage_type",)
    search_fields = ("payroll__employee__first_name", "wage_type__name")
    autocomplete_fields = ("payroll", "wage_type")


@admin.register(AHVParameter)
class AHVParameterAdmin(admin.ModelAdmin):
    list_display = ("year", "rate_employee", "rate_employer", "rentner_freibetrag_monat")
    fieldsets = (
        (
            "Jahr",
            {
                "fields": ("year",),
                "description": "Jahr für diese AHV-Parameter (einzigartig)",
            },
        ),
        (
            "AHV-Beitragssätze",
            {
                "fields": ("rate_employee", "rate_employer"),
                "description": "Beitragssätze als Dezimalzahl (z.B. 0.0530 für 5.3%)",
            },
        ),
        (
            "Rentnerfreibetrag",
            {
                "fields": ("rentner_freibetrag_monat",),
                "description": "Rentnerfreibetrag pro Monat (Standard: 1'400 CHF)",
            },
        ),
    )
    ordering = ["-year"]


@admin.register(ALVParameter)
class ALVParameterAdmin(admin.ModelAdmin):
    list_display = ("year", "rate_employee", "rate_employer", "max_annual_insured_salary")
    fieldsets = (
        (
            "Jahr",
            {
                "fields": ("year",),
                "description": "Jahr für diese ALV-Parameter (einzigartig)",
            },
        ),
        (
            "ALV-Beitragssätze",
            {
                "fields": ("rate_employee", "rate_employer"),
                "description": "Beitragssätze als Dezimalzahl (z.B. 0.0110 für 1.1%)",
            },
        ),
        (
            "Lohnobergrenze",
            {
                "fields": ("max_annual_insured_salary",),
                "description": "Maximal versichertes Jahreseinkommen (Standard: 148'200 CHF)",
            },
        ),
    )
    ordering = ["-year"]


@admin.register(VKParameter)
class VKParameterAdmin(admin.ModelAdmin):
    list_display = ("year", "rate_employer")
    fieldsets = (
        (
            "Jahr",
            {
                "fields": ("year",),
                "description": "Jahr für diese VK-Parameter (einzigartig)",
            },
        ),
        (
            "VK-Beitragssatz",
            {
                "fields": ("rate_employer",),
                "description": "VK-Beitragssatz Arbeitgeber (in % des Total AHV-Beitrags, z.B. 0.03 für 3.0%). Aktueller Satz kann auf AHV-Rechnung gefunden werden.",
            },
        ),
    )
    ordering = ["-year"]


@admin.register(KTGParameter)
class KTGParameterAdmin(admin.ModelAdmin):
    list_display = ("year", "ktg_rate_employee", "ktg_rate_employer", "ktg_max_basis")
    fieldsets = (
        (
            "Jahr",
            {
                "fields": ("year",),
                "description": "Jahr für diese KTG-Parameter (einzigartig)",
            },
        ),
        (
            "KTG-Beitragssätze",
            {
                "fields": ("ktg_rate_employee", "ktg_rate_employer"),
                "description": "Beitragssätze als Dezimalzahl (z.B. 0.0050 für 0.5%)",
            },
        ),
        (
            "Bemessungsgrundlage",
            {
                "fields": ("ktg_max_basis",),
                "description": "Optional: Maximale Bemessungsgrundlage (z.B. 300000.00 für Jahreslohn)",
            },
        ),
    )
    ordering = ["-year"]


@admin.register(FAKParameter)
class FAKParameterAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "canton",
        "fak_rate_employer",
    )
    list_filter = ("year", "canton")
    search_fields = ("canton",)
    fieldsets = (
        (
            "Jahr und Kanton",
            {
                "fields": ("year", "canton"),
                "description": "Jahr und Kanton (z.B. 'AG', 'ZH', 'BE') oder 'DEFAULT' für Standard",
            },
        ),
        (
            "FAK-Beitragssatz",
            {
                "fields": ("fak_rate_employer",),
                "description": "FAK-Beitragssatz Arbeitgeber (z.B. 0.01450 für 1.450% für Aargau)",
            },
        ),
    )
    ordering = ["-year", "canton"]


@admin.register(UVGParameter)
class UVGParameterAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "bu_rate_employer",
        "nbu_rate_employee",
        "max_annual_insured_salary",
    )
    fieldsets = (
        (
            "Jahr",
            {
                "fields": ("year",),
                "description": "Jahr für diese UVG-Parameter (einzigartig)",
            },
        ),
        (
            "BU-Beitragssatz",
            {
                "fields": ("bu_rate_employer",),
                "description": "BU-Beitragssatz Arbeitgeber (z.B. 0.00644 für 0.644%)",
            },
        ),
        (
            "NBU-Beitragssatz",
            {
                "fields": ("nbu_rate_employee",),
                "description": "NBU-Beitragssatz Arbeitnehmer (z.B. 0.0230 für 2.3%)",
            },
        ),
        (
            "Lohnobergrenze",
            {
                "fields": ("max_annual_insured_salary",),
                "description": "Maximal versichertes Jahreseinkommen (Standard: 148'200 CHF)",
            },
        ),
    )
    ordering = ["-year"]


@admin.register(BVGParameter)
class BVGParameterAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "entry_threshold",
        "coordination_deduction",
        "min_insured_salary",
        "max_insured_salary",
        "employee_rate",
        "employer_rate",
    )
    fieldsets = (
        (
            "Jahr",
            {
                "fields": ("year",),
                "description": "Jahr für diese BVG-Parameter (einzigartig)",
            },
        ),
        (
            "Eintrittsschwelle",
            {
                "fields": ("entry_threshold",),
                "description": "Jahreslohn unterhalb dessen keine BVG-Pflicht besteht",
            },
        ),
        (
            "Koordinationsabzug",
            {
                "fields": ("coordination_deduction",),
                "description": "Jährlicher Koordinationsabzug",
            },
        ),
        (
            "Versicherter Lohn (Korridore)",
            {
                "fields": ("min_insured_salary", "max_insured_salary"),
                "description": "Minimum und Maximum des versicherten Lohns (jährlich)",
            },
        ),
        (
            "Beitragssätze",
            {
                "fields": ("employee_rate", "employer_rate"),
                "description": "Beitragssätze als Dezimalzahl (z.B. 0.0500 für 5%)",
            },
        ),
    )
    ordering = ["-year"]


@admin.register(QSTParameter)
class QSTParameterAdmin(admin.ModelAdmin):
    list_display = ("year", "tarif", "prozent", "fixbetrag")
    list_filter = ("year", "tarif")
    search_fields = ("year", "tarif")
    fieldsets = (
        (
            "Grunddaten",
            {
                "fields": ("year", "tarif"),
                "description": "Jahr und Tarif müssen zusammen eindeutig sein. "
                               "Tarif-Format: [Familienstand][Kinder][Kirchensteuer], z.B. 'A0N' (alleinstehend, 0 Kinder, ohne Kirche), "
                               "'A0Y' (mit Kirche), 'B1N' (verheiratet, 1 Kind, ohne Kirche), 'B1Y' (mit Kirche).",
            },
        ),
        (
            "QST-Berechnung",
            {
                "fields": ("prozent", "fixbetrag"),
                "description": "Fixbetrag hat Vorrang vor Prozentsatz",
            },
        ),
    )
    ordering = ["-year", "tarif"]


@admin.register(FamilyAllowanceParameter)
class FamilyAllowanceParameterAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "kinderzulage_betrag",
        "ausbildungszulage_betrag",
        "monatlich_kinderzulage",
        "monatlich_ausbildungszulage",
    )
    list_filter = ("year",)
    search_fields = ("year",)
    fieldsets = (
        (
            "Jahr",
            {
                "fields": ("year",),
                "description": "Jahr für diese Familienzulagen-Parameter (einzigartig). "
                               "Die Beträge werden von der Familienausgleichskasse (FAK) festgelegt.",
            },
        ),
        (
            "Jährliche Beträge",
            {
                "fields": ("kinderzulage_betrag", "ausbildungszulage_betrag"),
                "description": "Jährliche Beträge gemäss FamZG. Die monatlichen Beträge werden automatisch berechnet (jährlich / 12).",
            },
        ),
        (
            "Monatliche Beträge (automatisch berechnet)",
            {
                "fields": ("monatlich_kinderzulage", "monatlich_ausbildungszulage"),
                "description": "Diese Felder werden automatisch aus den jährlichen Beträgen berechnet und sind nicht editierbar.",
            },
        ),
    )
    readonly_fields = ("monatlich_kinderzulage", "monatlich_ausbildungszulage")
    ordering = ["-year"]
