"""
Management-Command zum Erstellen von Benutzer-Zugängen für Mitarbeitende.

Verwendung:
    python manage.py create_user_access
    
Das Command zeigt alle Mitarbeitenden ohne Zugang an und erstellt interaktiv Zugänge.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
from adeazeit.models import EmployeeInternal, UserProfile
from adeazeit.permissions import (
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_MITARBEITER,
)


class Command(BaseCommand):
    help = 'Erstellt Benutzer-Zugänge für Mitarbeitende'

    def add_arguments(self, parser):
        parser.add_argument(
            '--employee-code',
            type=str,
            help='Mitarbeiterkürzel (z.B. AI) - erstellt Zugang für diesen Mitarbeiter',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Benutzername (optional, wird sonst automatisch generiert)',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Passwort (optional, wird sonst interaktiv abgefragt)',
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['admin', 'manager', 'mitarbeiter'],
            default='mitarbeiter',
            help='Rolle: admin, manager oder mitarbeiter (Standard: mitarbeiter)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='E-Mail-Adresse (optional)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== AdeaZeit - Benutzer-Zugang erstellen ===\n'))
        
        # Prüfe ob Rollen existieren
        self.ensure_roles_exist()
        
        # Hole alle Mitarbeitenden
        employees = EmployeeInternal.objects.filter(aktiv=True).order_by('name')
        
        if not employees.exists():
            self.stdout.write(self.style.ERROR('Keine aktiven Mitarbeitenden gefunden!'))
            return
        
        # Zeige Mitarbeitende ohne Zugang
        employees_without_access = []
        for emp in employees:
            has_access = UserProfile.objects.filter(employee=emp).exists()
            if not has_access:
                employees_without_access.append(emp)
        
        if not employees_without_access and not options.get('employee_code'):
            self.stdout.write(self.style.SUCCESS('Alle Mitarbeitenden haben bereits einen Zugang!'))
            return
        
        # Wenn employee_code angegeben, nur diesen verarbeiten
        if options.get('employee_code'):
            try:
                employee = EmployeeInternal.objects.get(code=options['employee_code'])
                if UserProfile.objects.filter(employee=employee).exists():
                    self.stdout.write(self.style.WARNING(f'Mitarbeiter {employee.name} hat bereits einen Zugang!'))
                    return
                self.create_user_for_employee(employee, options)
            except EmployeeInternal.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Mitarbeiter mit Code "{options["employee_code"]}" nicht gefunden!'))
                return
        else:
            # Interaktive Auswahl
            self.stdout.write('Mitarbeitende ohne Zugang:\n')
            for idx, emp in enumerate(employees_without_access, 1):
                self.stdout.write(f'  {idx}. {emp.name} ({emp.code}) - {emp.function_title}')
            
            if not employees_without_access:
                return
            
            self.stdout.write('\nFür welche Mitarbeitenden sollen Zugänge erstellt werden?')
            self.stdout.write('  [Enter] = Alle')
            self.stdout.write('  [Nummer] = Einzelner Mitarbeiter (z.B. 1)')
            self.stdout.write('  [Nummer,Nummer] = Mehrere (z.B. 1,2)')
            
            choice = input('\nIhre Auswahl: ').strip()
            
            if not choice:
                # Alle erstellen
                for emp in employees_without_access:
                    self.create_user_for_employee(emp, {})
            else:
                # Einzelne auswählen
                try:
                    indices = [int(x.strip()) - 1 for x in choice.split(',')]
                    selected = [employees_without_access[i] for i in indices if 0 <= i < len(employees_without_access)]
                    
                    for emp in selected:
                        self.create_user_for_employee(emp, {})
                except (ValueError, IndexError):
                    self.stdout.write(self.style.ERROR('Ungültige Auswahl!'))
                    return

    def ensure_roles_exist(self):
        """Stelle sicher, dass alle Rollen existieren."""
        roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_MITARBEITER]
        for role_name in roles:
            Group.objects.get_or_create(name=role_name)

    def create_user_for_employee(self, employee, options):
        """Erstellt einen Benutzer-Zugang für einen Mitarbeiter."""
        self.stdout.write(f'\n--- Zugang für {employee.name} ({employee.code}) ---')
        
        # Username generieren
        if options.get('username'):
            username = options['username']
        else:
            # Automatisch: Code in Kleinbuchstaben
            username = employee.code.lower()
            # Prüfe ob bereits vorhanden
            if User.objects.filter(username=username).exists():
                # Alternative: Vorname.Nachname
                name_parts = employee.name.split()
                if len(name_parts) >= 2:
                    username = f"{name_parts[0].lower()}.{name_parts[-1].lower()}"
                else:
                    username = f"{username}2"
            
            self.stdout.write(f'Benutzername: {username}')
            confirm = input('  [Enter] = Übernehmen, [Text] = Anderen Namen eingeben: ').strip()
            if confirm:
                username = confirm
        
        # Prüfe ob Username bereits existiert
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'Benutzername "{username}" existiert bereits!'))
            return
        
        # Passwort
        if options.get('password'):
            password = options['password']
        else:
            password = input('Passwort: ').strip()
            if not password:
                self.stdout.write(self.style.ERROR('Passwort darf nicht leer sein!'))
                return
            password_confirm = input('Passwort wiederholen: ').strip()
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwörter stimmen nicht überein!'))
                return
        
        # E-Mail
        email = options.get('email') or ''
        if not email:
            email_input = input('E-Mail (optional): ').strip()
            email = email_input if email_input else ''
        
        # Rolle
        role_map = {
            'admin': ROLE_ADMIN,
            'manager': ROLE_MANAGER,
            'mitarbeiter': ROLE_MITARBEITER,
        }
        role_name = role_map.get(options.get('role', 'mitarbeiter'), ROLE_MITARBEITER)
        
        # Erstelle User
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                    first_name=employee.name.split()[0] if employee.name.split() else '',
                    last_name=' '.join(employee.name.split()[1:]) if len(employee.name.split()) > 1 else employee.name,
                )
                
                # Weise Rolle zu
                group = Group.objects.get(name=role_name)
                user.groups.add(group)
                
                # Erstelle UserProfile und verknüpfe mit EmployeeInternal
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.employee = employee
                profile.save()
                
                self.stdout.write(self.style.SUCCESS(f'\n✅ Zugang erfolgreich erstellt!'))
                self.stdout.write(f'   Benutzername: {username}')
                self.stdout.write(f'   Rolle: {role_name}')
                self.stdout.write(f'   Login: http://127.0.0.1:8000/admin/')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Fehler beim Erstellen: {e}'))





