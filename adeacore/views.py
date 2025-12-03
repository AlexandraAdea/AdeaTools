from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from datetime import date, timedelta
from decimal import Decimal

from adeacore.models import Client, Employee
from adeazeit.models import EmployeeInternal, TimeEntry, Absence
from adealohn.models import PayrollRecord


def home(request):
    """Startseite."""
    return render(request, 'home.html')


def datenschutz(request):
    """Datenschutzerklärung."""
    return render(request, 'datenschutz.html')


def impressum(request):
    """Impressum."""
    return render(request, 'impressum.html')


@login_required(login_url='/admin/login/')
def admin_dashboard(request):
    """Admin-Dashboard mit Übersicht aller Bereiche."""
    today = date.today()
    this_month_start = date(today.year, today.month, 1)
    
    # Statistiken
    stats = {
        'clients': {
            'total': Client.objects.count(),
            'firma': Client.objects.filter(client_type='FIRMA').count(),
            'privat': Client.objects.filter(client_type='PRIVAT').count(),
            'lohn_aktiv': Client.objects.filter(lohn_aktiv=True).count(),
        },
        'employees_internal': {
            'total': EmployeeInternal.objects.count(),
            'active': EmployeeInternal.objects.filter(aktiv=True).count(),
        },
        'employees_payroll': {
            'total': Employee.objects.count(),
            'active': Employee.objects.filter(client__lohn_aktiv=True).count(),
        },
        'time_entries': {
            'today': TimeEntry.objects.filter(datum=today).count(),
            'this_month': TimeEntry.objects.filter(datum__gte=this_month_start).count(),
            'total_hours_today': TimeEntry.objects.filter(datum=today).aggregate(
                total=Sum('dauer')
            )['total'] or Decimal('0.00'),
        },
        'absences': {
            'active': Absence.objects.filter(
                date_from__lte=today,
                date_to__gte=today
            ).count(),
        },
        'payroll': {
            'this_month': PayrollRecord.objects.filter(
                month=today.month,
                year=today.year
            ).count(),
            'pending': PayrollRecord.objects.filter(status='ENTWURF').count(),
            'completed': PayrollRecord.objects.filter(status='ABGERECHNET').count(),
        },
    }
    
    # Letzte Aktivitäten
    recent_time_entries = TimeEntry.objects.select_related(
        'mitarbeiter', 'client'
    ).order_by('-created_at')[:5]
    
    recent_absences = Absence.objects.select_related(
        'employee'
    ).order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_time_entries': recent_time_entries,
        'recent_absences': recent_absences,
        'today': today,
    }
    
    return render(request, 'admin/dashboard.html', context)


def global_logout(request):
    """
    Zentrale Logout-Funktion für alle Bereiche (AdeaZeit, AdeaDesk, AdeaLohn).
    Löscht alle Sessions und meldet den Benutzer fensterübergreifend ab.
    """
    if request.user.is_authenticated:
        username = request.user.get_full_name() or request.user.username
        user = request.user
        
        # Audit-Log vor Logout
        from adeacore.audit import get_audit_logger, get_client_ip, get_user_agent
        audit_logger = get_audit_logger()
        audit_logger.log_action(
            user=user,
            action='LOGOUT',
            model_name='User',
            object_id=user.pk,
            object_repr=user.username,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        # Lösche alle Session-Daten
        request.session.flush()
        # Logout durchführen
        logout(request)
        messages.success(request, f'Sie wurden erfolgreich abgemeldet.')
    
    # Weiterleitung zur Login-Seite
    # Prüfe, von welchem Bereich der Logout kam
    referer = request.META.get('HTTP_REFERER', '')
    if '/zeit/' in referer:
        return redirect('adeazeit:login')
    elif '/desk/' in referer:
        # Prüfe ob AdeaDesk Login existiert, sonst AdeaZeit Login
        try:
            from django.urls import reverse
            reverse('adeadesk:login')
            return redirect('adeadesk:login')
        except:
            return redirect('adeazeit:login')
    elif '/lohn/' in referer:
        # Prüfe ob AdeaLohn Login existiert, sonst AdeaZeit Login
        try:
            from django.urls import reverse
            reverse('adealohn:login')
            return redirect('adealohn:login')
        except:
            return redirect('adeazeit:login')
    else:
        # Standard: Weiterleitung zur AdeaZeit Login-Seite
        return redirect('adeazeit:login')

