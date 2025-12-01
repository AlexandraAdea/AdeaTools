"""
Management-Command zum Initialisieren der Rollen für AdeaZeit.

Verwendung:
    python manage.py init_roles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from adeazeit.permissions import (
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_MITARBEITER,
)


class Command(BaseCommand):
    help = 'Initialisiert die Rollen für AdeaZeit (Admin, Manager, Mitarbeiter)'

    def handle(self, *args, **options):
        # Erstelle Rollen-Groups
        roles = [
            (ROLE_ADMIN, "Vollzugriff auf alle Funktionen"),
            (ROLE_MANAGER, "Kann alles sehen und bearbeiten, aber nicht löschen"),
            (ROLE_MITARBEITER, "Kann nur eigene Zeiteinträge sehen und bearbeiten"),
        ]
        
        created_count = 0
        for role_name, description in roles:
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] Rolle "{role_name}" erstellt')
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'[INFO] Rolle "{role_name}" existiert bereits')
                )
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n{created_count} Rollen erstellt.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nAlle Rollen existieren bereits.')
            )
        
        self.stdout.write('\nVerwendung:')
        self.stdout.write('  - Weisen Sie Benutzern Rollen im Django Admin zu (Groups)')
        self.stdout.write('  - Oder verwenden Sie: python manage.py shell')
        self.stdout.write('    >>> from django.contrib.auth.models import User, Group')
        self.stdout.write(f'    >>> user = User.objects.get(username="...")')
        self.stdout.write(f'    >>> group = Group.objects.get(name="{ROLE_ADMIN}")')
        self.stdout.write(f'    >>> user.groups.add(group)')

