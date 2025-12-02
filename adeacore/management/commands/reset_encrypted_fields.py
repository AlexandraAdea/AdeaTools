"""
Management-Command zum Zurücksetzen verschlüsselter Felder.

WARNUNG: Dieses Command löscht alle verschlüsselten Daten!
Verwenden Sie es nur, wenn die Verschlüsselung nicht mehr funktioniert
(z.B. wenn der Encryption-Key verloren gegangen ist).
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from adeacore.models import Client, Employee


class Command(BaseCommand):
    help = 'Setzt verschlüsselte Felder zurück (löscht verschlüsselte Daten)'

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
                    'WARNUNG: Dieses Command löscht alle verschlüsselten Daten!\n'
                    'Verwenden Sie --confirm, um fortzufahren.'
                )
            )
            return

        with transaction.atomic():
            # Setze verschlüsselte Felder bei Clients zurück
            clients_updated = 0
            for client in Client.objects.all():
                updated = False
                if client.email:
                    client.email = ''
                    updated = True
                if client.phone:
                    client.phone = ''
                    updated = True
                if client.street:
                    client.street = ''
                    updated = True
                if client.house_number:
                    client.house_number = ''
                    updated = True
                if client.zipcode:
                    client.zipcode = ''
                    updated = True
                if client.city:
                    client.city = ''
                    updated = True
                if client.mwst_nr:
                    client.mwst_nr = ''
                    updated = True
                if client.rechnungs_email:
                    client.rechnungs_email = ''
                    updated = True
                if client.geburtsdatum:
                    client.geburtsdatum = None
                    updated = True
                if client.steuerkanton:
                    client.steuerkanton = ''
                    updated = True
                
                if updated:
                    client.save()
                    clients_updated += 1

            # Setze verschlüsselte Felder bei Employees zurück
            employees_updated = 0
            for employee in Employee.objects.all():
                updated = False
                if employee.email:
                    employee.email = ''
                    updated = True
                if employee.phone:
                    employee.phone = ''
                    updated = True
                if employee.street:
                    employee.street = ''
                    updated = True
                if employee.house_number:
                    employee.house_number = ''
                    updated = True
                if employee.zipcode:
                    employee.zipcode = ''
                    updated = True
                if employee.city:
                    employee.city = ''
                    updated = True
                if employee.geburtsdatum:
                    employee.geburtsdatum = None
                    updated = True
                
                if updated:
                    employee.save()
                    employees_updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Verschlüsselte Felder zurückgesetzt:\n'
                    f'  - {clients_updated} Clients aktualisiert\n'
                    f'  - {employees_updated} Employees aktualisiert\n\n'
                    f'Bitte geben Sie die Daten neu ein. Der Encryption-Key ist jetzt in .env gespeichert.'
                )
            )




