# Generated migration to force create users (even if previous migrations ran)

from django.db import migrations
import os


def force_create_users(apps, schema_editor):
    """Erstellt Benutzer, auch wenn vorherige Migrationen bereits ausgeführt wurden.
    
    Diese Migration wird IMMER ausgeführt, auch wenn 0020 und 0021 bereits liefen.
    """
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Erstelle Superuser (Aivanova) - prüfe ob existiert, erstelle wenn nicht
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
            # Neuer Benutzer: Setze Passwort
            user.set_password(password)
            user.save()
        else:
            # Bestehender Benutzer: Stelle sicher, dass Rechte korrekt sind und Passwort aktualisiert wird
            user.is_superuser = True
            user.is_staff = True
            user.set_password(password)  # Aktualisiere Passwort
            if not user.email:
                user.email = email
            user.save()
    
    # Erstelle normale Benutzer (ai und ei)
    # Benutzer "ai"
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
        if created:
            user.set_password(ai_password)
            user.save()
        elif ai_password:
            # Aktualisiere Passwort auch wenn Benutzer bereits existiert
            user.set_password(ai_password)
            user.save()
    
    # Benutzer "ei"
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
        if created:
            user.set_password(ei_password)
            user.save()
        elif ei_password:
            # Aktualisiere Passwort auch wenn Benutzer bereits existiert
            user.set_password(ei_password)
            user.save()


def reverse_force_create(apps, schema_editor):
    """Reverse migration - entfernt die Benutzer nicht (zu gefährlich)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('adeacore', '0021_ensure_users_exist'),
    ]

    operations = [
        migrations.RunPython(force_create_users, reverse_force_create),
    ]

