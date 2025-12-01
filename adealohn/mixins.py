"""
Mixin für Multi-Mandanten-Funktionalität in AdeaLohn.
Nutzt Client als Mandant und setzt request.current_client.
"""
from django.http import HttpResponseForbidden, Http404
from adeacore.models import Client
from .permissions import can_access_adelohn, can_access_client_lohn


class TenantMixin:
    """
    Mixin für AdeaLohn-Views, das den aktiven Mandanten (Client) setzt.
    Liest aus request.session["active_client_id"] und setzt request.current_client.
    Prüft auch Berechtigungen.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Setze current_client aus Session und prüfe Berechtigungen."""
        # Prüfe zuerst ob User überhaupt Zugriff auf AdeaLohn hat
        if not can_access_adelohn(request.user):
            return HttpResponseForbidden("Sie haben keine Berechtigung für AdeaLohn. Bitte kontaktieren Sie den Administrator.")
        
        active_client_id = request.session.get("active_client_id")
        
        if active_client_id:
            try:
                client = Client.objects.get(pk=active_client_id)
                # Sicherheitsprüfung: Nur FIRMA-Clients mit aktiviertem Lohnmodul erlauben
                if client.client_type != "FIRMA" or not client.lohn_aktiv:
                    # Client ist keine Firma oder Lohnmodul nicht aktiviert, entferne aus Session
                    request.session.pop("active_client_id", None)
                    request.current_client = None
                else:
                    # Prüfe ob User Zugriff auf diesen spezifischen Client hat
                    if not can_access_client_lohn(request.user, client):
                        request.session.pop("active_client_id", None)
                        request.current_client = None
                        return HttpResponseForbidden("Sie haben keine Berechtigung für diesen Mandanten in AdeaLohn.")
                    request.current_client = client
            except Client.DoesNotExist:
                # Client existiert nicht mehr, entferne aus Session
                request.session.pop("active_client_id", None)
                request.current_client = None
        else:
            request.current_client = None
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_current_client(self):
        """Hilfsmethode um current_client zu erhalten."""
        return getattr(self.request, "current_client", None)
    
    def require_client(self):
        """Prüft ob ein Client ausgewählt ist, sonst 403."""
        if not self.get_current_client():
            return HttpResponseForbidden("Bitte wählen Sie zuerst einen Mandanten aus.")
        return None


class TenantFilterMixin(TenantMixin):
    """
    Mixin für Listen-Views, das automatisch nach current_client filtert.
    """
    
    def get_queryset(self):
        """Filtere Queryset nach current_client und lohn_aktiv."""
        qs = super().get_queryset()
        current_client = self.get_current_client()
        
        if current_client is not None:
            # Zusätzliche Sicherheitsprüfung: Nur Clients mit aktiviertem Lohnmodul
            if not current_client.lohn_aktiv:
                return qs.none()
            
            # Für PayrollRecord: Filtere über employee__client
            if hasattr(qs.model, 'employee'):
                qs = qs.filter(employee__client=current_client, employee__client__lohn_aktiv=True)
            # Für Employee: Filtere direkt nach client
            elif hasattr(qs.model, 'client'):
                qs = qs.filter(client=current_client, client__lohn_aktiv=True)
        
        return qs


class TenantObjectMixin(TenantMixin):
    """
    Mixin für Detail/Update/Delete-Views, das prüft ob Objekt zum current_client gehört.
    """
    
    def get_object(self, queryset=None):
        """Prüfe ob Objekt zum aktuellen Mandanten gehört und Lohnmodul aktiviert ist."""
        obj = super().get_object(queryset)
        current_client = self.get_current_client()
        
        if current_client is not None:
            # Zusätzliche Sicherheitsprüfung: Lohnmodul muss aktiviert sein
            if not current_client.lohn_aktiv:
                raise Http404("Lohnmodul für diesen Mandanten nicht aktiviert.")
            
            # Prüfe über employee.client für PayrollRecord
            if hasattr(obj, 'employee'):
                if obj.employee.client != current_client or not obj.employee.client.lohn_aktiv:
                    raise Http404("Kein Zugriff auf diesen Mandanten.")
            # Prüfe direkt client für Employee
            elif hasattr(obj, 'client'):
                if obj.client != current_client or not obj.client.lohn_aktiv:
                    raise Http404("Kein Zugriff auf diesen Mandanten.")
        
        return obj

