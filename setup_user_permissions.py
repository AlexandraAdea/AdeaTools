#!/usr/bin/env python
"""
Setup Permissions für Mitarbeiter (Alexandra, Eugen)
"""
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

# Gruppe erstellen
group, created = Group.objects.get_or_create(name='Mitarbeiter')

if created:
    print("✅ Gruppe 'Mitarbeiter' erstellt")
else:
    print("ℹ️  Gruppe 'Mitarbeiter' existiert bereits")

# Permissions hinzufügen
permissions_to_add = [
    # AdeaDesk
    ('adeadesk', 'client', 'view_client'),
    
    # AdeaZeit
    ('adeazeit', 'timeentry', 'view_timeentry'),
    ('adeazeit', 'timeentry', 'add_timeentry'),
    ('adeazeit', 'timeentry', 'change_timeentry'),
    ('adeazeit', 'timeentry', 'delete_timeentry'),
    
    # AdeaLohn
    ('adealohn', 'payrollrecord', 'view_payrollrecord'),
]

for app_label, model_name, codename in permissions_to_add:
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model_name)
        perm = Permission.objects.get(content_type=ct, codename=codename)
        group.permissions.add(perm)
        print(f"✅ Permission hinzugefügt: {codename}")
    except Exception as e:
        print(f"⚠️  Fehler bei {codename}: {e}")

# Users zur Gruppe hinzufügen
usernames = ['alexandra', 'eugen']

for username in usernames:
    try:
        user = User.objects.get(username=username)
        user.groups.add(group)
        user.save()
        print(f"✅ {username} zur Gruppe 'Mitarbeiter' hinzugefügt")
    except User.DoesNotExist:
        print(f"⚠️  User '{username}' nicht gefunden!")

print("\n🎉 Permissions setup abgeschlossen!")
print("\n📋 Teste jetzt:")
print("1. Logout als Aivanova")
print("2. Login als 'alexandra' oder 'eugen'")
print("3. Module sollten jetzt sichtbar sein!")






