from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout as auth_logout
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum, Q
from datetime import date, timedelta
from decimal import Decimal

from adeacore.models import Client, Employee
from adeazeit.models import EmployeeInternal, TimeEntry, Absence
from adealohn.models import PayrollRecord


def staff_required(user):
    """Prüft ob User Staff-Mitglied ist."""
    return user.is_authenticated and user.is_staff


@login_required(login_url='/login/')
@user_passes_test(staff_required, login_url='/login/')
def admin_dashboard(request):
    """Admin-Dashboard mit Übersicht aller Bereiche - nur für Staff-User."""
    if not request.user.is_staff:
        raise PermissionDenied("Zugriff verweigert: Nur Administratoren können auf das Dashboard zugreifen.")
    today = date.today()
    this_month_start = date(today.year, today.month, 1)
    
    # Statistiken
    client_stats = Client.objects.aggregate(
        total=Count("id"),
        firma=Count("id", filter=Q(client_type="FIRMA")),
        privat=Count("id", filter=Q(client_type="PRIVAT")),
        lohn_aktiv=Count("id", filter=Q(lohn_aktiv=True)),
    )
    employee_internal_stats = EmployeeInternal.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(aktiv=True)),
    )
    employee_payroll_stats = Employee.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(client__lohn_aktiv=True)),
    )
    time_entry_stats = TimeEntry.objects.aggregate(
        today=Count("id", filter=Q(datum=today)),
        this_month=Count("id", filter=Q(datum__gte=this_month_start)),
        total_hours_today=Sum("dauer", filter=Q(datum=today)),
    )
    payroll_stats = PayrollRecord.objects.aggregate(
        this_month=Count("id", filter=Q(month=today.month, year=today.year)),
        pending=Count("id", filter=Q(status="ENTWURF")),
        completed=Count("id", filter=Q(status="ABGERECHNET")),
    )
    absence_stats = Absence.objects.aggregate(
        active=Count("id", filter=Q(date_from__lte=today, date_to__gte=today)),
    )

    stats = {
        'clients': {
            'total': client_stats["total"],
            'firma': client_stats["firma"],
            'privat': client_stats["privat"],
            'lohn_aktiv': client_stats["lohn_aktiv"],
        },
        'employees_internal': {
            'total': employee_internal_stats["total"],
            'active': employee_internal_stats["active"],
        },
        'employees_payroll': {
            'total': employee_payroll_stats["total"],
            'active': employee_payroll_stats["active"],
        },
        'time_entries': {
            'today': time_entry_stats["today"],
            'this_month': time_entry_stats["this_month"],
            'total_hours_today': time_entry_stats["total_hours_today"] or Decimal('0.00'),
        },
        'absences': {
            'active': absence_stats["active"],
        },
        'payroll': {
            'this_month': payroll_stats["this_month"],
            'pending': payroll_stats["pending"],
            'completed': payroll_stats["completed"],
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
    """Logout-Funktion für normale User (nicht nur Admin)."""
    auth_logout(request)
    return redirect('home')


def session_heartbeat(request):
    """Heartbeat-Endpoint um Session während aktiver Eingabe zu verlängern."""
    if request.user.is_authenticated:
        # Session wird automatisch verlängert durch SESSION_SAVE_EVERY_REQUEST = True
        from django.http import JsonResponse
        return JsonResponse({"status": "ok", "authenticated": True})
    else:
        from django.http import JsonResponse
        return JsonResponse({"status": "expired", "authenticated": False}, status=401)

