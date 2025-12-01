"""
Permission-Mixins für AdeaDesk Views.
"""
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin


class AdeaDeskAccessMixin(LoginRequiredMixin):
    """
    Mixin für Views, die allen eingeloggten Benutzern Zugriff geben.
    Für Lesen von Client-Daten und CRM-Features.
    """
    login_url = '/zeit/login/'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AdminOrManagerRequiredMixin(LoginRequiredMixin):
    """
    Mixin für Views, die Admin oder Manager erfordern.
    Nutzt AdeaZeit-Rollen-System.
    Für Erstellen/Bearbeiten/Löschen von Clients.
    """
    login_url = '/zeit/login/'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Prüfe ob User Admin oder Manager ist
        try:
            from adeazeit.permissions import is_manager_or_admin
            if not is_manager_or_admin(request.user):
                return HttpResponseForbidden("Sie haben keine Berechtigung für diese Seite. Nur Administratoren und Manager haben Zugriff auf diese Funktion.")
        except ImportError:
            # Falls adeazeit nicht verfügbar ist, nur Superuser erlauben
            if not request.user.is_superuser:
                return HttpResponseForbidden("Sie haben keine Berechtigung für diese Seite.")
        
        return super().dispatch(request, *args, **kwargs)

