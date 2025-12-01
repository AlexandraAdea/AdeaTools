# Generated migration to create initial superuser

from django.db import migrations
import os


def create_superuser(apps, schema_editor):
    """Erstellt initiale Benutzer falls sie noch nicht existieren.
    
    WICHTIG: Passwörter müssen über Environment-Variablen gesetzt werden!
    Keine Standard-Passwörter aus Datenschutzgründen.
    """
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Erstelle Superuser (Aivanova) - nur wenn noch nicht vorhanden
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'Aivanova')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'alexandra@adea-treuhand.ch')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
    
    if not password:
        # Kein Passwort gesetzt - überspringe Erstellung
        # Benutzer muss manuell über createsuperuser erstellt werden
        return
    
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='Anna',
            last_name='Ivanova',
        )
    
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


def remove_superuser(apps, schema_editor):
    """Entfernt die initialen Benutzer (reverse migration)."""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Entferne alle erstellten Benutzer
    usernames = [
        os.environ.get('DJANGO_SUPERUSER_USERNAME', 'Aivanova'),
        'ai',
        'ei',
    ]
    
    for username in usernames:
        try:
            user = User.objects.get(username=username)
            user.delete()
        except User.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('adeacore', '0019_add_crm_features'),
    ]

    operations = [
        migrations.RunPython(create_superuser, remove_superuser),
    ]

