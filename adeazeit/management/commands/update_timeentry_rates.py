"""
Management-Command zum Aktualisieren der Stundensätze in bestehenden Zeiteinträgen.

Verwendung:
    python manage.py update_timeentry_rates
    
Dieses Command aktualisiert alle Zeiteinträge, deren Stundensatz nicht dem aktuellen
Standard-Stundensatz des Service-Typs entspricht. Wichtig für korrekte Fakturierung.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from adeazeit.models import TimeEntry
from adeazeit.timeentry_calc import calculate_timeentry_rate, calculate_timeentry_amount


class Command(BaseCommand):
    help = 'Aktualisiert Stundensätze und Beträge in bestehenden Zeiteinträgen basierend auf aktuellen ServiceType-Stundensätzen'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Zeigt an, welche Einträge aktualisiert würden, ohne sie tatsächlich zu ändern',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Aktualisiert ALLE Einträge, auch wenn rate bereits gesetzt ist',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS('Aktualisiere Stundensätze für Zeiteinträge...'))
        
        # Finde alle Zeiteinträge mit ServiceType und Mitarbeiter
        entries = TimeEntry.objects.select_related('service_type', 'mitarbeiter').all()
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        with transaction.atomic():
            for entry in entries:
                if not entry.service_type or not entry.mitarbeiter:
                    skipped_count += 1
                    continue
                
                current_rate = entry.rate or Decimal('0.00')
                correct_rate = calculate_timeentry_rate(service_type=entry.service_type, employee=entry.mitarbeiter)
                
                # Prüfe ob Update nötig ist
                needs_update = False
                if force:
                    # Force: Aktualisiere alle
                    needs_update = True
                elif current_rate != correct_rate:
                    # Rate weicht von der korrekten Rate ab (inkl. Koeffizient)
                    needs_update = True
                
                if needs_update:
                    old_rate = entry.rate
                    old_betrag = entry.betrag
                    
                    # Aktualisiere Rate und Betrag (mit Koeffizient)
                    entry.rate = correct_rate
                    entry.betrag = calculate_timeentry_amount(rate=correct_rate, dauer=entry.dauer)
                    
                    if not dry_run:
                        try:
                            entry.save(update_fields=['rate', 'betrag'])
                            updated_count += 1
                            if updated_count <= 10:  # Zeige erste 10 Updates
                                koeffizient_info = f" (Koeffizient: {entry.mitarbeiter.stundensatz})" if entry.mitarbeiter.stundensatz and entry.mitarbeiter.stundensatz > 0 else ""
                                self.stdout.write(
                                    f'  ✓ Aktualisiert: {entry.datum} - {entry.mitarbeiter.name} - '
                                    f'{entry.service_type.code} - Rate: {old_rate} → {correct_rate} CHF{koeffizient_info}, '
                                    f'Betrag: {old_betrag} → {entry.betrag} CHF'
                                )
                        except Exception as e:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(
                                    f'  ✗ Fehler bei Eintrag {entry.pk}: {e}'
                                )
                            )
                    else:
                        updated_count += 1
                        koeffizient_info = f" (Koeffizient: {entry.mitarbeiter.stundensatz})" if entry.mitarbeiter.stundensatz and entry.mitarbeiter.stundensatz > 0 else ""
                        self.stdout.write(
                            f'  [DRY-RUN] Würde aktualisieren: {entry.datum} - {entry.mitarbeiter.name} - '
                            f'{entry.service_type.code} - Rate: {current_rate} → {correct_rate} CHF{koeffizient_info}'
                        )
                else:
                    skipped_count += 1
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n[DRY-RUN] {updated_count} Einträge würden aktualisiert werden.'))
            self.stdout.write(self.style.WARNING(f'{skipped_count} Einträge würden übersprungen werden.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ {updated_count} Einträge aktualisiert.'))
            self.stdout.write(self.style.SUCCESS(f'  {skipped_count} Einträge übersprungen.'))
            if error_count > 0:
                self.stdout.write(self.style.ERROR(f'  {error_count} Fehler aufgetreten.'))

