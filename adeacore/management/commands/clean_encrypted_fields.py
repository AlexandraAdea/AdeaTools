"""
Management-Command zum Bereinigen nicht entschlüsselbarer verschlüsselter Felder.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from adeacore.models import Client, Employee


class Command(BaseCommand):
    help = 'Bereinigt verschlüsselte Felder, die nicht mehr entschlüsselt werden können'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Bestätigt die Aktion (erforderlich)',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.ERROR(
                    'WARNUNG: Dieses Command löscht verschlüsselte Felder, die nicht mehr entschlüsselt werden können!\n'
                    'Verwenden Sie --confirm, um fortzufahren.'
                )
            )
            return

        encrypted_fields_client = ['city', 'email', 'phone', 'street', 'zipcode', 'mwst_nr', 'rechnungs_email', 'steuerkanton']
        encrypted_fields_employee = ['city', 'email', 'phone', 'street', 'zipcode', 'steuerkanton']

        with transaction.atomic():
            # Bereinige Clients
            clients_updated = 0
            for client in Client.objects.all():
                updated = False
                for field in encrypted_fields_client:
                    val = getattr(client, field)
                    if val and isinstance(val, str) and len(val) > 50 and val.startswith('Z0FBQUFBQnBK'):
                        setattr(client, field, '')
                        updated = True
                        self.stdout.write(f'  Client "{client.name}": {field} bereinigt')
                
                if updated:
                    client.save()
                    clients_updated += 1

            # Bereinige Employees
            employees_updated = 0
            for employee in Employee.objects.all():
                updated = False
                for field in encrypted_fields_employee:
                    val = getattr(employee, field)
                    if val and isinstance(val, str) and len(val) > 50 and val.startswith('Z0FBQUFBQnBK'):
                        setattr(employee, field, '')
                        updated = True
                        self.stdout.write(f'  Employee "{employee.name}": {field} bereinigt')
                
                if updated:
                    employee.save()
                    employees_updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'\nBereinigung abgeschlossen:\n'
                    f'  - {clients_updated} Clients aktualisiert\n'
                    f'  - {employees_updated} Employees aktualisiert'
                )
            )



