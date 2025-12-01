"""
Benutzerfreundliche Login-View für Mitarbeiter.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from adeacore.rate_limiting import rate_limit_login, get_client_ip, reset_login_rate_limit
from adeacore.audit import get_audit_logger


@require_http_methods(["GET", "POST"])
@rate_limit_login
def employee_login(request):
    """
    Benutzerfreundliche Login-Seite für Mitarbeiter.
    
    Mit Rate-Limiting: Maximal 5 Login-Versuche in 5 Minuten pro IP-Adresse.
    """
    if request.user.is_authenticated:
        # Bereits eingeloggt, weiterleiten
        return redirect('adeazeit:timeentry-day')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        ip_address = get_client_ip(request)
        
        if not username or not password:
            messages.error(request, 'Bitte geben Sie Benutzername und Passwort ein.')
            return render(request, 'adeazeit/login.html')
        
        # Authentifiziere Benutzer
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login erfolgreich
            login(request, user)
            
            # Rate-Limit zurücksetzen nach erfolgreichem Login
            reset_login_rate_limit(username, ip_address)
            
            # Audit-Log
            audit_logger = get_audit_logger()
            audit_logger.log_action(
                user=user,
                action='LOGIN',
                model_name='User',
                object_id=user.pk,
                object_repr=user.username,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            
            # Weiterleitung zur Zeiterfassung
            next_url = request.GET.get('next', 'adeazeit:timeentry-day')
            return redirect(next_url)
        else:
            # Login fehlgeschlagen
            messages.error(request, 'Falsche Zugangsdaten. Bitte versuchen Sie es erneut.')
            
            # Audit-Log für fehlgeschlagenen Login-Versuch
            audit_logger = get_audit_logger()
            audit_logger.log_action(
                user=None,
                action='LOGIN_FAILED',
                model_name='User',
                object_id=None,
                object_repr=username,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                details=f"Fehlgeschlagener Login-Versuch für Benutzer: {username}"
            )
    
    return render(request, 'adeazeit/login.html')


@require_http_methods(["GET", "POST"])
def employee_logout(request):
    """
    Logout-View für Mitarbeiter.
    Weiterleitung zur zentralen Logout-Funktion für fensterübergreifende Abmeldung.
    """
    return redirect('global-logout')

