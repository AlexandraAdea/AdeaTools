"""
Views für Live-Tracking Timer.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

from adeazeit.models import RunningTimeEntry, TimeEntry, EmployeeInternal, ServiceType, ZeitProject, UserProfile
from adeacore.models import Client


@login_required
@require_http_methods(["POST"])
def start_timer(request):
    """
    Startet einen neuen Timer.
    Stoppt automatisch einen eventuell laufenden Timer.
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        employee = profile.employee
        if not employee:
            return JsonResponse({
                'success': False,
                'error': 'Kein Mitarbeiter zugeordnet.'
            }, status=400)
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Kein Benutzerprofil gefunden.'
        }, status=400)
    
    # Hole Parameter
    client_id = request.POST.get('client_id')
    service_type_id = request.POST.get('service_type_id')
    projekt_id = request.POST.get('projekt_id')
    beschreibung = request.POST.get('beschreibung', '')
    
    if not service_type_id:
        return JsonResponse({
            'success': False,
            'error': 'Service-Typ ist erforderlich.'
        }, status=400)
    
    # Validierung
    service_type = get_object_or_404(ServiceType, pk=service_type_id)
    client = None
    if client_id:
        client = get_object_or_404(Client, pk=client_id)
    
    projekt = None
    if projekt_id:
        projekt = get_object_or_404(ZeitProject, pk=projekt_id)
    
    with transaction.atomic():
        # Stoppe laufenden Timer (falls vorhanden)
        existing_timer = RunningTimeEntry.objects.filter(mitarbeiter=employee).first()
        if existing_timer:
            # Stoppe automatisch
            _stop_and_save_timer(existing_timer)
        
        # Erstelle neuen Timer
        timer = RunningTimeEntry.objects.create(
            mitarbeiter=employee,
            client=client,
            service_type=service_type,
            projekt=projekt,
            beschreibung=beschreibung,
        )
    
    return JsonResponse({
        'success': True,
        'timer_id': timer.id,
        'start_time': timer.start_time.isoformat(),
        'client': client.name if client else 'Interne Leistungen',
        'service_type': service_type.name,
    })


@login_required
@require_http_methods(["POST"])
def stop_timer(request):
    """
    Stoppt den laufenden Timer und speichert als TimeEntry.
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        employee = profile.employee
        if not employee:
            return JsonResponse({
                'success': False,
                'error': 'Kein Mitarbeiter zugeordnet.'
            }, status=400)
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Kein Benutzerprofil gefunden.'
        }, status=400)
    
    timer = RunningTimeEntry.objects.filter(mitarbeiter=employee).first()
    if not timer:
        return JsonResponse({
            'success': False,
            'error': 'Kein laufender Timer gefunden.'
        }, status=404)
    
    time_entry = _stop_and_save_timer(timer)
    
    return JsonResponse({
        'success': True,
        'time_entry_id': time_entry.id,
        'duration': float(time_entry.dauer),
        'datum': time_entry.datum.isoformat(),
    })


@login_required
@require_http_methods(["POST"])
def cancel_timer(request):
    """
    Bricht den Timer ab ohne zu speichern.
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        employee = profile.employee
        if not employee:
            return JsonResponse({
                'success': False,
                'error': 'Kein Mitarbeiter zugeordnet.'
            }, status=400)
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Kein Benutzerprofil gefunden.'
        }, status=400)
    
    # Lösche Timer ohne zu speichern
    deleted_count = RunningTimeEntry.objects.filter(mitarbeiter=employee).delete()[0]
    
    if deleted_count == 0:
        return JsonResponse({
            'success': False,
            'error': 'Kein laufender Timer gefunden.'
        }, status=404)
    
    return JsonResponse({
        'success': True,
        'message': 'Timer abgebrochen.'
    })


@login_required
@require_http_methods(["GET"])
def get_timer_status(request):
    """
    Liefert Status des laufenden Timers (für JavaScript Live-Update).
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        employee = profile.employee
        if not employee:
            return JsonResponse({'is_running': False})
    except UserProfile.DoesNotExist:
        return JsonResponse({'is_running': False})
    
    timer = RunningTimeEntry.objects.filter(mitarbeiter=employee).first()
    
    if not timer:
        return JsonResponse({
            'is_running': False
        })
    
    return JsonResponse({
        'is_running': True,
        'timer_id': timer.id,
        'start_time': timer.start_time.isoformat(),
        'duration_seconds': timer.get_duration_seconds(),
        'client': timer.client.name if timer.client else 'Interne Leistungen',
        'service_type': timer.service_type.name,
        'beschreibung': timer.beschreibung,
    })


def _stop_and_save_timer(timer: RunningTimeEntry) -> TimeEntry:
    """
    Hilfsfunktion: Stoppt Timer und speichert als TimeEntry.
    """
    from decimal import Decimal
    
    # Berechne Dauer
    duration_hours = timer.get_duration_hours()
    
    # Hole Rate vom Service-Typ
    rate = timer.service_type.standard_rate if timer.service_type.standard_rate else Decimal('0.00')
    betrag = duration_hours * rate  # Beide Decimal
    
    # Erstelle TimeEntry
    time_entry = TimeEntry.objects.create(
        mitarbeiter=timer.mitarbeiter,
        client=timer.client,
        service_type=timer.service_type,
        project=timer.projekt,
        datum=timer.datum,
        start=timer.start_time.time(),
        ende=timezone.now().time(),
        dauer=duration_hours,
        kommentar=timer.beschreibung,
        billable=True,
        rate=rate,
        betrag=betrag,
    )
    
    # Lösche Timer
    timer.delete()
    
    return time_entry
