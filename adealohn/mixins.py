"""
Mixins für AdeaLohn Views.

- Multi-Tenant: setze/validiere `request.current_client`
- Guards: verhindere Änderungen an gesperrten PayrollRecords
"""

from __future__ import annotations

from django.http import Http404, HttpResponseForbidden


class LockedPayrollGuardMixin:
    """
    Guard gegen Änderungen an gesperrten PayrollRecords.

    Erwartet, dass die View `get_object()` liefert und das Objekt `is_locked()` hat.
    """

    #: Textfragment nach "kann nicht ..." (z.B. "mehr bearbeitet werden", "gelöscht werden")
    locked_reason: str = "mehr bearbeitet werden"

    def get_locked_forbidden_message(self, obj) -> str:
        return (
            f"Dieser Lohnlauf ist gesperrt (Status: {obj.get_status_display()}) "
            f"und kann nicht {self.locked_reason}."
        )

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.is_locked():
            return HttpResponseForbidden(self.get_locked_forbidden_message(self.object))
        return super().dispatch(request, *args, **kwargs)


class LockedPayrollFormGuardMixin(LockedPayrollGuardMixin):
    """
    Variante für (Update)Forms: zeigt Fehlermeldung im Formular statt nur 403.
    """

    def form_valid(self, form):
        obj = getattr(self, "object", None) or self.get_object()
        if obj and obj.is_locked():
            form.add_error(None, self.get_locked_forbidden_message(obj))
            return self.form_invalid(form)
        return super().form_valid(form)

from adeacore.models import Client


class TenantMixin:
    """
    Mixin für AdeaLohn-Views, das den aktiven Mandanten (Client) setzt.
    Liest aus request.session["active_client_id"] und setzt request.current_client.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Setze current_client aus Session (nur FIRMA-Clients mit aktiviertem Lohnmodul)."""
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

