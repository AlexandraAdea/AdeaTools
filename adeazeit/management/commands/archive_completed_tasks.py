"""
Management-Command zum Archivieren von erledigten Aufgaben nach 7 Tagen.

Verwendung:
    python manage.py archive_completed_tasks

Dieses Command sollte täglich ausgeführt werden (z.B. via Cronjob oder Django-Q).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from adeazeit.models import Task


class Command(BaseCommand):
    help = 'Archiviert erledigte Aufgaben, die älter als 7 Tage sind'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Zeigt an, welche Aufgaben archiviert würden, ohne sie tatsächlich zu archivieren',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Berechne Datum vor 7 Tagen
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # Finde erledigte Aufgaben, die älter als 7 Tage sind und noch nicht archiviert
        tasks_to_archive = Task.objects.filter(
            status='ERLEDIGT',
            erledigt_am__lt=seven_days_ago,
            archiviert=False
        )
        
        count = tasks_to_archive.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Keine Aufgaben zum Archivieren gefunden.')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY-RUN] {count} Aufgabe(n) würden archiviert werden:')
            )
            for task in tasks_to_archive[:10]:  # Zeige erste 10
                self.stdout.write(
                    f'  - {task.titel} (erledigt am: {task.erledigt_am.strftime("%d.%m.%Y %H:%M")})'
                )
            if count > 10:
                self.stdout.write(f'  ... und {count - 10} weitere')
            self.stdout.write('\nFühren Sie den Befehl ohne --dry-run aus, um zu archivieren.')
        else:
            # Archiviere die Aufgaben
            archived_count = tasks_to_archive.update(archiviert=True)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {archived_count} Aufgabe(n) erfolgreich archiviert.'
                )
            )

