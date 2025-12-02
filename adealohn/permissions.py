"""
Berechtigungen für AdeaLohn.
"""
from django.http import HttpResponseForbidden


def can_access_adelohn(user):
    """
    Prüft, ob der User Zugriff auf AdeaLohn hat.
    
    Zugriff haben:
    - Admin/Manager (AdeaZeit)
    - Sachbearbeiter, die einem Client zugeordnet sind
    """
    if not user.is_authenticated:
        return False
    
    # Admin/Manager haben immer Zugriff
    try:
        from adeazeit.permissions import is_manager_or_admin
        if is_manager_or_admin(user):
            return True
    except ImportError:
        # Falls adeazeit nicht verfügbar ist, nur Superuser erlauben
        if user.is_superuser:
            return True
    
    # Prüfe ob User Sachbearbeiter für einen Client ist
    try:
        from adeazeit.models import UserProfile, EmployeeInternal
        from adeacore.models import Client
        
        # Versuche EmployeeInternal über UserProfile zu finden
        profile = UserProfile.objects.filter(user=user).first()
        if profile and profile.employee:
            employee = profile.employee
            # Prüfe ob dieser Employee als Sachbearbeiter für einen Client zugeordnet ist
            clients = Client.objects.filter(
                sachbearbeiter=employee,
                client_type="FIRMA",
                lohn_aktiv=True
            )
            if clients.exists():
                return True
    except Exception:
        pass
    
    return False


def can_access_client_lohn(user, client):
    """
    Prüft, ob der User Zugriff auf AdeaLohn für einen spezifischen Client hat.
    
    Args:
        user: Django User
        client: Client-Objekt
    
    Returns:
        bool: True wenn Zugriff, sonst False
    """
    if not user.is_authenticated or not client:
        return False
    
    # Admin/Manager haben immer Zugriff
    try:
        from adeazeit.permissions import is_manager_or_admin
        if is_manager_or_admin(user):
            return True
    except ImportError:
        if user.is_superuser:
            return True
    
    # Prüfe ob User Sachbearbeiter für diesen Client ist
    try:
        from adeazeit.models import UserProfile, EmployeeInternal
        
        # Versuche EmployeeInternal über UserProfile zu finden
        profile = UserProfile.objects.filter(user=user).first()
        if profile and profile.employee:
            employee = profile.employee
            # Prüfe ob dieser Employee als Sachbearbeiter für diesen Client zugeordnet ist
            if client.sachbearbeiter == employee and client.client_type == "FIRMA" and client.lohn_aktiv:
                return True
    except Exception:
        pass
    
    return False




