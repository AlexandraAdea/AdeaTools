# Generated migration to initialize AdeaZeit roles and assign users

from django.db import migrations
from django.contrib.auth.models import Group
import os


def init_roles_and_assign_users(apps, schema_editor):
    """Initialisiert AdeaZeit-Rollen und weist Benutzern Rollen zu."""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Rollen-Namen (aus adeazeit.permissions)
    ROLE_ADMIN = "AdeaZeit Admin"
    ROLE_MANAGER = "AdeaZeit Manager"
    ROLE_MITARBEITER = "AdeaZeit Mitarbeiter"
    
    # Erstelle Rollen-Groups falls noch nicht vorhanden
    admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
    manager_group, _ = Group.objects.get_or_create(name=ROLE_MANAGER)
    mitarbeiter_group, _ = Group.objects.get_or_create(name=ROLE_MITARBEITER)
    
    # Weise Superuser-Benutzer (Aivanova) die Admin-Rolle zu
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'Aivanova')
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        if user.is_superuser:
            # Superuser = Admin
            if admin_group not in user.groups.all():
                user.groups.add(admin_group)
    
    # Weise normale Benutzer (ai, ei) die Mitarbeiter-Rolle zu
    for username in ['ai', 'ei']:
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            # Normale Benutzer = Mitarbeiter (Standard)
            if not user.is_superuser:
                if mitarbeiter_group not in user.groups.all():
                    user.groups.add(mitarbeiter_group)


def reverse_roles(apps, schema_editor):
    """Reverse migration - entfernt Rollen-Zuweisungen nicht (zu gefährlich)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('adeazeit', '0013_add_sachbearbeiter_to_client'),  # Letzte Migration von adeazeit
        ('adeacore', '0021_ensure_users_exist'),  # Benutzer müssen existieren
    ]

    operations = [
        migrations.RunPython(init_roles_and_assign_users, reverse_roles),
    ]

