"""
Management-Command zum Wiederherstellen eines Backups.
"""

from django.core.management.base import BaseCommand
from pathlib import Path
from adeacore.backup import get_backup_manager


class Command(BaseCommand):
    help = 'Stellt ein Backup wieder her'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_path',
            type=str,
            help='Pfad zum Backup-Verzeichnis (z.B. backups/auto_20251126_145026_test)',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Bestätigt die Wiederherstellung (erforderlich)',
        )

    def handle(self, *args, **options):
        backup_path_str = options['backup_path']
        backup_path = Path(backup_path_str)
        
        if not options['confirm']:
            self.stdout.write(
                self.style.ERROR(
                    f'WARNUNG: Dieses Command wird die aktuelle Datenbank durch das Backup ersetzen!\n'
                    f'Backup: {backup_path}\n'
                    f'Verwenden Sie --confirm, um fortzufahren.'
                )
            )
            return

        backup_manager = get_backup_manager()
        
        self.stdout.write(f'Wiederherstelle Backup: {backup_path}')
        
        if backup_manager.restore_backup(backup_path):
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Backup erfolgreich wiederhergestellt!\n'
                    f'Die Datenbank wurde aus {backup_path} wiederhergestellt.\n'
                    f'Ein Backup der aktuellen Datenbank wurde erstellt (before_restore).'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    '\n❌ Fehler beim Wiederherstellen des Backups!\n'
                    'Bitte prüfen Sie die Logs für Details.'
                )
            )




