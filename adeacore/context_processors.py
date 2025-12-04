"""
Context Processors für AdeaTools.
"""
from adeacore.models import Client


def current_client(request):
    """
    Fügt current_client zum Template-Context hinzu.
    Nur für AdeaLohn-Views relevant.
    Prüft dass nur FIRMA-Clients verwendet werden.
    """
    active_client_id = request.session.get("active_client_id")
    
    if active_client_id:
        try:
            client = Client.objects.get(pk=active_client_id)
            # Sicherheitsprüfung: Nur FIRMA-Clients mit aktiviertem Lohnmodul erlauben
            if client.client_type != "FIRMA" or not client.lohn_aktiv:
                request.session.pop("active_client_id", None)
                return {"current_client": None}
            return {"current_client": client}
        except Client.DoesNotExist:
            request.session.pop("active_client_id", None)
            return {"current_client": None}
    
    return {"current_client": None}


def adeazeit_permissions(request):
    """
    Fügt AdeaZeit-Berechtigungen zum Template-Context hinzu.
    """
    if not request.user.is_authenticated:
        return {
            "adeazeit_is_admin": False,
            "adeazeit_is_manager": False,
            "adeazeit_can_manage_employees": False,
            "adeazeit_can_manage_service_types": False,
            "adeazeit_can_manage_absences": False,
            "adeazeit_can_delete": False,
        }
    
    try:
        from adeazeit.permissions import (
            is_admin,
            is_manager_or_admin,
            can_manage_employees,
            can_manage_service_types,
            can_manage_absences,
            can_delete_entries,
        )
        
        return {
            "adeazeit_is_admin": is_admin(request.user),
            "adeazeit_is_manager": is_manager_or_admin(request.user),
            "adeazeit_can_manage_employees": can_manage_employees(request.user),
            "adeazeit_can_manage_service_types": can_manage_service_types(request.user),
            "adeazeit_can_manage_absences": can_manage_absences(request.user),
            "adeazeit_can_delete": can_delete_entries(request.user),
        }
    except ImportError:
        # Falls adeazeit nicht installiert ist
        return {
            "adeazeit_is_admin": False,
            "adeazeit_is_manager": False,
            "adeazeit_can_manage_employees": False,
            "adeazeit_can_manage_service_types": False,
            "adeazeit_can_manage_absences": False,
            "adeazeit_can_delete": False,
        }


def adealohn_permissions(request):
    """
    Fügt AdeaLohn-Berechtigungen zum Template-Context hinzu.
    """
    if not request.user.is_authenticated:
        return {
            "adealohn_is_visible": False,
        }
    
    # AdeaLohn ist für alle eingeloggten User sichtbar (mit Berechtigungsprüfung in Views)
    return {
        "adealohn_is_visible": request.user.has_perm('adealohn.view_payrollrecord') or request.user.is_staff,
    }


def running_timer(request):
    """
    Fügt den aktuell laufenden Timer zum Template-Context hinzu.
    Für AdeaZeit Live-Tracking Feature.
    """
    if not request.user.is_authenticated:
        return {'running_timer': None}
    
    try:
        from adeazeit.models import RunningTimeEntry, UserProfile
        
        # Verknüpfung über UserProfile → EmployeeInternal
        user_profile = UserProfile.objects.get(user=request.user)
        if user_profile.employee:
            timer = RunningTimeEntry.objects.filter(mitarbeiter=user_profile.employee).first()
            return {'running_timer': timer}
    except Exception:
        # Falls Model nicht existiert, Import fehlschlägt, oder kein UserProfile
        # Fail gracefully - kein Timer verfügbar
        pass
    
    return {'running_timer': None}

