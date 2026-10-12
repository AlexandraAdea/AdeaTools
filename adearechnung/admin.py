from django.contrib import admin

from .models import Mahnung


@admin.register(Mahnung)
class MahnungAdmin(admin.ModelAdmin):
    list_display = ("invoice", "stufe", "datum", "zahlungsfrist", "total", "versendet_am")
    list_filter = ("stufe", "datum")
    search_fields = ("invoice__invoice_number",)
    readonly_fields = ("created_at", "erstellt_von")
