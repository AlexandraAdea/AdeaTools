"""
Permission-Mixins für AdeaZeit Views.
"""
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from .permissions import (
    is_admin,
    is_manager_or_admin,
    can_view_all_entries,
    can_edit_all_entries,
    can_delete_entries,
    can_manage_employees,
    can_manage_service_types,
    can_manage_absences,
    get_accessible_time_entries,
    get_accessible_employees,
    get_accessible_absences,
)


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Basis-Mixin für Rollenprüfung.
    """
    login_url = '/zeit/login/'
    required_role = None  # Muss in Subklassen überschrieben werden
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if self.required_role:
            from .permissions import has_role
            if not has_role(request.user, self.required_role):
                return HttpResponseForbidden("Sie haben keine Berechtigung für diese Aktion.")
        
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin für Admin-only Views."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not is_admin(request.user):
            return HttpResponseForbidden("Diese Aktion erfordert Admin-Rechte.")
        
        return super().dispatch(request, *args, **kwargs)


class ManagerOrAdminRequiredMixin(RoleRequiredMixin):
    """Mixin für Manager oder Admin Views."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not is_manager_or_admin(request.user):
            return HttpResponseForbidden("Diese Aktion erfordert Manager- oder Admin-Rechte.")
        
        return super().dispatch(request, *args, **kwargs)


class FilterByRoleMixin:
    """
    Mixin, das get_queryset() automatisch nach Rolle filtert.
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Wenn User alle Einträge sehen kann, keine Filterung
        if can_view_all_entries(self.request.user):
            return queryset
        
        # Sonst: Filter nach zugänglichen Objekten
        # Dies muss in Subklassen überschrieben werden, da wir nicht wissen,
        # welches Model verwendet wird
        return queryset


class TimeEntryFilterMixin(FilterByRoleMixin):
    """Mixin für TimeEntry Views - filtert nach Rolle."""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return get_accessible_time_entries(self.request.user)


class EmployeeFilterMixin(FilterByRoleMixin):
    """Mixin für Employee Views - filtert nach Rolle."""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return get_accessible_employees(self.request.user)


class AbsenceFilterMixin(FilterByRoleMixin):
    """Mixin für Absence Views - filtert nach Rolle."""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return get_accessible_absences(self.request.user)


class CanEditMixin:
    """
    Mixin für Edit-Views - prüft Bearbeitungsrechte.
    Standard-Implementierung - kann in Subklassen überschrieben werden.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Prüfe, ob User alle Einträge bearbeiten kann
        if can_edit_all_entries(request.user):
            return super().dispatch(request, *args, **kwargs)
        
        # Für spezifische Views (wie TimeEntryUpdateView) wird dispatch überschrieben
        # Diese Basis-Implementierung wird nur verwendet, wenn nicht überschrieben
        return super().dispatch(request, *args, **kwargs)


class CanDeleteMixin:
    """
    Mixin für Delete-Views - prüft Löschrechte.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Nur Admins können löschen
        if not can_delete_entries(request.user):
            return HttpResponseForbidden("Nur Administratoren können Einträge löschen.")
        
        return super().dispatch(request, *args, **kwargs)


