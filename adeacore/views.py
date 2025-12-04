from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from datetime import date, timedelta
from decimal import Decimal

from adeacore.models import Client, Employee
from adeazeit.models import EmployeeInternal, TimeEntry, Absence
from adealohn.models import PayrollRecord


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

