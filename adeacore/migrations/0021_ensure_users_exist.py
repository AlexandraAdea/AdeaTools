# Generated migration to ensure users exist

from django.db import migrations
import os


def ensure_users_exist(apps, schema_editor):
    """Stellt sicher, dass die benötigten Benutzer existieren.
    
    WICHTIG: Passwörter müssen über Environment-Variablen gesetzt werden!
    Falls keine Environment-Variablen gesetzt sind, werden die Benutzer NICHT erstellt.
    """
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Erstelle Superuser (Aivanova) - nur wenn noch nicht vorhanden
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'Aivanova')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'alexandra@adea-treuhand.ch')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    
    # WICHTIG: Nur erstellen wenn Passwort gesetzt ist (aus Sicherheitsgründen)
    if password:
        if not User.objects.filter(username=username).exists():
            # Erstelle neuen Superuser
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name='Anna',
                last_name='Ivanova',
            )
        else:
            # Stelle sicher, dass der Benutzer Superuser-Rechte hat und Passwort aktualisiert wird
            user = User.objects.get(username=username)
            user.is_superuser = True
            user.is_staff = True
            user.set_password(password)  # Aktualisiere Passwort falls geändert
            if not user.email:
                user.email = email
            user.save()
    else:
        # Kein Passwort gesetzt - Benutzer wird nicht erstellt
        # Dies ist beabsichtigt aus Sicherheitsgründen
        pass
    
    # Erstelle normale Benutzer (ai und ei) - nur wenn noch nicht vorhanden
    # Benutzer "ai"
    ai_password = os.environ.get('DJANGO_USER_AI_PASSWORD')
    if ai_password and not User.objects.filter(username='ai').exists():
        User.objects.create_user(
            username='ai',
            email='ai@adea-treuhand.ch',
            password=ai_password,
            first_name='AI',
            last_name='User',
        )
    
    # Benutzer "ei"
    ei_password = os.environ.get('DJANGO_USER_EI_PASSWORD')
    if ei_password and not User.objects.filter(username='ei').exists():
        User.objects.create_user(
            username='ei',
            email='ei@adea-treuhand.ch',
            password=ei_password,
            first_name='EI',
            last_name='User',
        )


def reverse_users(apps, schema_editor):
    """Reverse migration - entfernt die Benutzer nicht (zu gefährlich)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('adeacore', '0020_create_initial_superuser'),
    ]

    operations = [
        migrations.RunPython(ensure_users_exist, reverse_users),
    ]

