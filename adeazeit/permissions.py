"""
Rollen und Berechtigungen für AdeaZeit.

Rollen:
- ADMIN: Vollzugriff auf alles
- MANAGER: Kann alles sehen und bearbeiten, aber nicht löschen
- MITARBEITER: Kann nur eigene Zeiteinträge sehen/bearbeiten
"""
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


# Rollen-Namen
ROLE_ADMIN = "AdeaZeit Admin"
ROLE_MANAGER = "AdeaZeit Manager"
ROLE_MITARBEITER = "AdeaZeit Mitarbeiter"


def get_user_role(user):
    """
    Gibt die Rolle des Users zurück.
    
    Returns:
        str: Rolle (ROLE_ADMIN, ROLE_MANAGER, ROLE_MITARBEITER) oder None
    """
    if not user.is_authenticated:
        return None
    
    # Prüfe Groups
    group_names = user.groups.values_list('name', flat=True)
    
    if ROLE_ADMIN in group_names:
        return ROLE_ADMIN
    elif ROLE_MANAGER in group_names:
        return ROLE_MANAGER
    elif ROLE_MITARBEITER in group_names:
        return ROLE_MITARBEITER
    
    # Fallback: Superuser = Admin
    if user.is_superuser:
        return ROLE_ADMIN
    
    return None


def has_role(user, role):
    """Prüft, ob der User eine bestimmte Rolle hat."""
    return get_user_role(user) == role


def is_admin(user):
    """Prüft, ob der User Admin ist."""
    return has_role(user, ROLE_ADMIN) or (user.is_authenticated and user.is_superuser)


def is_manager_or_admin(user):
    """Prüft, ob der User Manager oder Admin ist."""
    role = get_user_role(user)
    return role in [ROLE_ADMIN, ROLE_MANAGER] or (user.is_authenticated and user.is_superuser)


def can_view_all_entries(user):
    """Prüft, ob der User alle Zeiteinträge sehen kann."""
    return is_manager_or_admin(user)


def can_edit_all_entries(user):
    """Prüft, ob der User alle Zeiteinträge bearbeiten kann."""
    return is_manager_or_admin(user)


def can_delete_entries(user):
    """Prüft, ob der User Zeiteinträge löschen kann."""
    return is_admin(user)


def can_manage_employees(user):
    """Prüft, ob der User Mitarbeitende verwalten kann."""
    return is_manager_or_admin(user)


def can_manage_service_types(user):
    """Prüft, ob der User Service-Typen verwalten kann."""
    return is_manager_or_admin(user)


def can_manage_absences(user):
    """Prüft, ob der User Abwesenheiten verwalten kann."""
    return is_manager_or_admin(user)


def can_view_reports(user):
    """Prüft, ob der User Reports sehen kann."""
    return is_manager_or_admin(user)


def get_accessible_employees(user):
    """
    Gibt die für den User zugänglichen Mitarbeitenden zurück.
    
    - ADMIN/MANAGER: Alle Mitarbeitenden
    - MITARBEITER: Nur der User selbst (über UserProfile verknüpft)
    """
    from .models import EmployeeInternal
    
    if can_view_all_entries(user):
        return EmployeeInternal.objects.all()
    
    # MITARBEITER: Versuche, EmployeeInternal über UserProfile zu finden
    try:
        from .models import UserProfile
        profile = UserProfile.objects.filter(user=user).first()
        if profile and profile.employee:
            return EmployeeInternal.objects.filter(pk=profile.employee.pk)
    except:
        pass
    
    # Fallback: Versuche über Username zu finden (für Migration)
    try:
        employee = EmployeeInternal.objects.filter(
            Q(code__iexact=user.username) | 
            Q(name__icontains=user.get_full_name()) |
            Q(name__icontains=user.username)
        ).first()
        
        if employee:
            return EmployeeInternal.objects.filter(pk=employee.pk)
    except:
        pass
    
    return EmployeeInternal.objects.none()


def get_accessible_time_entries(user):
    """
    Gibt die für den User zugänglichen Zeiteinträge zurück.
    
    - ADMIN/MANAGER: Alle Zeiteinträge
    - MITARBEITER: Nur eigene Zeiteinträge
    """
    from .models import TimeEntry
    
    if can_view_all_entries(user):
        return TimeEntry.objects.all()
    
    # MITARBEITER: Nur eigene Einträge
    accessible_employees = get_accessible_employees(user)
    return TimeEntry.objects.filter(mitarbeiter__in=accessible_employees)


def get_accessible_absences(user):
    """
    Gibt die für den User zugänglichen Abwesenheiten zurück.
    
    - ADMIN/MANAGER: Alle Abwesenheiten
    - MITARBEITER: Nur eigene Abwesenheiten
    """
    from .models import Absence
    
    if can_view_all_entries(user):
        return Absence.objects.all()
    
    # MITARBEITER: Nur eigene Abwesenheiten
    accessible_employees = get_accessible_employees(user)
    return Absence.objects.filter(employee__in=accessible_employees)

