from django.contrib import admin
from adeacore.models import ClientNote


@admin.register(ClientNote)
class ClientNoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'note_type', 'note_date', 'status', 'created_by', 'created_at']
    list_filter = ['note_type', 'status', 'archiviert', 'note_date', 'created_at']
    search_fields = ['title', 'content', 'client__name']
    readonly_fields = ['created_by', 'created_at', 'updated_at', 'erledigt_am']
    date_hierarchy = 'note_date'
    
    fieldsets = (
        ('Grunddaten', {
            'fields': ('client', 'title', 'content', 'note_type', 'note_date')
        }),
        ('Status', {
            'fields': ('status', 'archiviert', 'erledigt_am')
        }),
        ('Verknüpfung', {
            'fields': ('task',)
        }),
        ('Metadaten', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nur bei neuen Objekten
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
