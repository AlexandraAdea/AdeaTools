"""
Django Management Command für tägliche automatische Backups.

Verwendung:
    python manage.py daily_backup

Kann per Cronjob oder Task Scheduler ausgeführt werden.
"""

from django.core.management.base import BaseCommand
from adeacore.backup import get_backup_manager
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Erstellt ein tägliches Backup der Datenbank und wichtiger Dateien'

    def add_arguments(self, parser):
        parser.add_argument(
            '--description',
            type=str,
            help='Beschreibung für das Backup',
            default='täglich'
        )

    def handle(self, *args, **options):
        """Führt das Backup aus."""
        try:
            backup_manager = get_backup_manager()
            backup_path = backup_manager.create_backup(
                backup_type='auto',
                description=options.get('description', 'täglich')
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Backup erfolgreich erstellt: {backup_path}'
                )
            )
            
            # Zeige Backup-Statistiken
            backups = backup_manager.list_backups()
            self.stdout.write(f'Anzahl verfügbarer Backups: {len(backups)}')
            
            if backups:
                latest = backups[0]
                self.stdout.write(
                    f'Neuestes Backup: {latest.get("timestamp", "unbekannt")} '
                    f'({latest.get("type", "unbekannt")})'
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Fehler beim Erstellen des Backups: {e}')
            )
            logger.error(f"Backup fehlgeschlagen: {e}", exc_info=True)
            raise



