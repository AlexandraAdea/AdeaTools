from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, EmployeeInternal, ServiceType, ZeitProject, TimeEntry, Absence, Holiday, Task


# UserProfile Inline für User Admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "AdeaZeit Profil"
    fields = ("employee",)


# Erweitere User Admin um UserProfile
class ExtendedUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, ExtendedUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "employee", "created_at")
    list_filter = ("employee", "created_at")
    search_fields = ("user__username", "user__email", "employee__name", "employee__code")
    fieldsets = (
        ("Benutzer", {
            "fields": ("user",)
        }),
        ("Mitarbeiter-Zuordnung", {
            "fields": ("employee",),
            "description": "Verknüpft den Django User mit einem EmployeeInternal für Zeiterfassung."
        }),
    )


@admin.register(EmployeeInternal)
class EmployeeInternalAdmin(admin.ModelAdmin):
    list_display = ("name", "function_title", "employment_percent", "weekly_soll_hours", "employment_start", "employment_end")
    list_filter = ("function_title", "aktiv")
    search_fields = ("name", "function_title", "code")
    fieldsets = (
        ("Stammdaten", {
            "fields": ("code", "name", "function_title", "rolle", "aktiv")
        }),
        ("Arbeitszeitmodell", {
            "fields": ("employment_percent", "weekly_soll_hours", "weekly_working_days")
        }),
        ("Ferien & Feiertage", {
            "fields": ("vacation_days_per_year", "work_canton", "holiday_model")
        }),
        ("Beschäftigung", {
            "fields": ("employment_start", "employment_end"),
            "description": "Verwende employment_start/employment_end für neue Einträge."
        }),
        ("Legacy-Daten (nur Migration)", {
            "fields": ("eintrittsdatum", "austrittsdatum"),
            "classes": ("collapse",),
            "description": "Veraltete Felder - nur für Datenmigration. Verwende employment_start/employment_end."
        }),
        ("Finanzen", {
            "fields": ("stundensatz",),
            "description": "Koeffizient für die Verrechnung von Services (z.B. 1.3 = 30% Aufschlag auf Standard-Stundensatz)"
        }),
        ("Notizen", {
            "fields": ("notes",)
        }),
    )


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "standard_rate", "billable")
    list_filter = ("billable",)
    search_fields = ("code", "name")
    fieldsets = (
        ("Grunddaten", {
            "fields": ("code", "name", "description")
        }),
        ("Verrechnung", {
            "fields": ("standard_rate", "billable")
        }),
    )


@admin.register(ZeitProject)
class ZeitProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "aktiv", "created_at")
    list_filter = ("aktiv", "client")
    search_fields = ("name", "client__name")
    fieldsets = (
        ("Grunddaten", {
            "fields": ("client", "name", "aktiv")
        }),
    )


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("datum", "mitarbeiter", "client", "service_type", "dauer", "betrag", "billable")
    list_filter = ("datum", "mitarbeiter", "client", "service_type", "billable")
    search_fields = ("mitarbeiter__name", "client__name", "kommentar")
    date_hierarchy = "datum"
    fieldsets = (
        ("Zeit", {
            "fields": ("mitarbeiter", "datum", "start", "ende", "dauer")
        }),
        ("Mandant & Projekt", {
            "fields": ("client", "project")
        }),
        ("Service", {
            "fields": ("service_type", "kommentar")
        }),
        ("Verrechnung", {
            "fields": ("billable", "rate", "betrag")
        }),
    )
    readonly_fields = ("betrag",)


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ("employee", "absence_type", "date_from", "date_to", "full_day", "hours")
    list_filter = ("absence_type", "date_from", "employee", "full_day")
    search_fields = ("employee__name", "comment")
    date_hierarchy = "date_from"
    fieldsets = (
        ("Abwesenheit", {
            "fields": ("employee", "absence_type", "date_from", "date_to", "full_day", "hours", "comment")
        }),
    )


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ("date", "name", "canton", "is_official")
    list_filter = ("canton", "is_official")
    search_fields = ("name",)
    date_hierarchy = "date"
    fieldsets = (
        ("Feiertag", {
            "fields": ("name", "date", "canton", "is_official")
        }),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("titel", "mitarbeiter", "client", "status", "prioritaet", "fälligkeitsdatum", "erstellt_am")
    list_filter = ("status", "prioritaet", "fälligkeitsdatum", "mitarbeiter")
    search_fields = ("titel", "beschreibung", "notizen", "mitarbeiter__name", "client__name")
    date_hierarchy = "fälligkeitsdatum"
    fieldsets = (
        ("Aufgabe", {
            "fields": ("titel", "beschreibung", "status", "prioritaet")
        }),
        ("Zuordnung", {
            "fields": ("mitarbeiter", "client")
        }),
        ("Fälligkeit", {
            "fields": ("fälligkeitsdatum",)
        }),
        ("Notizen", {
            "fields": ("notizen",)
        }),
        ("Zeitstempel", {
            "fields": ("erstellt_am", "erledigt_am", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("erstellt_am", "erledigt_am", "updated_at")
