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


class LockedPayrollFormGuardMixin:
    """
    Variante für (Update)Forms: zeigt Fehlermeldung im Formular statt nur 403.
    Unterstützt auch CreateViews, die ein PayrollRecord über kwargs['pk'] haben.
    
    WICHTIG: Erbt NICHT von LockedPayrollGuardMixin, um dispatch()-Konflikte zu vermeiden.
    """
    
    #: Textfragment nach "kann nicht ..." (z.B. "mehr bearbeitet werden", "gelöscht werden")
    locked_reason: str = "mehr bearbeitet werden"

    def get_locked_forbidden_message(self, obj) -> str:
        return (
            f"Dieser Lohnlauf ist gesperrt (Status: {obj.get_status_display()}) "
            f"und kann nicht {self.locked_reason}."
        )

    def get_payroll_record_for_guard(self):
        """
        Lädt das PayrollRecord für die Guard-Prüfung.
        Funktioniert für UpdateViews (über get_object) und CreateViews (über kwargs['pk']).
        """
        # Versuche zuerst über get_object() (für UpdateViews)
        try:
            obj = getattr(self, "object", None)
            if obj is None and hasattr(self, 'get_object'):
                try:
                    obj = self.get_object()
                except (AttributeError, NotImplementedError, TypeError):
                    # get_object() existiert nicht oder kann nicht aufgerufen werden
                    pass
            
            if obj:
                # Wenn es ein PayrollRecord ist, direkt zurückgeben
                if hasattr(obj, 'is_locked'):
                    return obj
                # Wenn es ein PayrollItem ist, hole das PayrollRecord
                if hasattr(obj, 'payroll'):
                    return obj.payroll
        except Exception:
            # Ignoriere alle Fehler und versuche kwargs-Methode
            pass
        
        # Für CreateViews: Lade PayrollRecord über kwargs['pk']
        from adeacore.models import PayrollRecord
        payroll_id = self.kwargs.get('pk')
        if payroll_id:
            try:
                return PayrollRecord.objects.get(pk=payroll_id)
            except PayrollRecord.DoesNotExist:
                raise Http404("PayrollRecord nicht gefunden.")
        
        return None

    def dispatch(self, request, *args, **kwargs):
        """Prüfe ob PayrollRecord gesperrt ist (für CreateViews)."""
        try:
            payroll_record = self.get_payroll_record_for_guard()
            if payroll_record and payroll_record.is_locked():
                return HttpResponseForbidden(self.get_locked_forbidden_message(payroll_record))
        except Http404:
            # Wenn PayrollRecord nicht gefunden wird, weiterleiten zu 404
            raise
        except Exception:
            # Bei anderen Fehlern (z.B. wenn kein pk vorhanden), einfach weiterleiten
            # Das wird später von der View selbst behandelt
            pass
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        payroll_record = self.get_payroll_record_for_guard()
        if payroll_record and payroll_record.is_locked():
            form.add_error(None, self.get_locked_forbidden_message(payroll_record))
            return self.form_invalid(form)
        return super().form_valid(form)

from adeacore.tenancy import resolve_current_client


class TenantMixin:
    """
    Mixin für AdeaLohn-Views, das den aktiven Mandanten (Client) setzt.
    Liest aus request.session["active_client_id"] und setzt request.current_client.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Setze current_client aus Session (nur FIRMA-Clients mit aktiviertem Lohnmodul)."""
        resolve_current_client(request)
        
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

