"""
Management Command zum Erstellen eines Superusers für Render.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Erstellt einen Superuser für Render (falls noch keiner existiert)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Benutzername für den Superuser',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@adea-treuhand.ch',
            help='E-Mail für den Superuser',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Passwort für den Superuser (wird aus Environment-Variable gelesen wenn nicht angegeben)',
        )

    def handle(self, *args, **options):
        import os
        
        # Erstelle alle Benutzer (Aivanova, ai, ei)
        self.create_all_users()
    
    def create_all_users(self):
        """Erstellt alle benötigten Benutzer aus Environment-Variablen."""
        import os
        
        # 1. Erstelle Superuser (Aivanova)
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'Aivanova')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'alexandra@adea-treuhand.ch')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if password:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': 'Anna',
                    'last_name': 'Ivanova',
                    'is_superuser': True,
                    'is_staff': True,
                }
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Superuser "{username}" erstellt')
                )
            else:
                user.is_superuser = True
                user.is_staff = True
                user.set_password(password)
                if not user.email:
                    user.email = email
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Superuser "{username}" aktualisiert')
                )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  DJANGO_SUPERUSER_PASSWORD nicht gesetzt - überspringe "{username}"')
            )
        
        # 2. Erstelle Benutzer "ai"
        ai_password = os.environ.get('DJANGO_USER_AI_PASSWORD')
        if ai_password:
            user, created = User.objects.get_or_create(
                username='ai',
                defaults={
                    'email': 'ai@adea-treuhand.ch',
                    'first_name': 'AI',
                    'last_name': 'User',
                }
            )
            user.set_password(ai_password)
            user.save()
            if created:
                self.stdout.write(self.style.SUCCESS('✅ Benutzer "ai" erstellt'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ Benutzer "ai" aktualisiert'))
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  DJANGO_USER_AI_PASSWORD nicht gesetzt - überspringe "ai"')
            )
        
        # 3. Erstelle Benutzer "ei"
        ei_password = os.environ.get('DJANGO_USER_EI_PASSWORD')
        if ei_password:
            user, created = User.objects.get_or_create(
                username='ei',
                defaults={
                    'email': 'ei@adea-treuhand.ch',
                    'first_name': 'EI',
                    'last_name': 'User',
                }
            )
            user.set_password(ei_password)
            user.save()
            if created:
                self.stdout.write(self.style.SUCCESS('✅ Benutzer "ei" erstellt'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ Benutzer "ei" aktualisiert'))
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  DJANGO_USER_EI_PASSWORD nicht gesetzt - überspringe "ei"')
            )

