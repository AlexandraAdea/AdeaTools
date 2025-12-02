# 🔍 Render Diagnose - Warum sieht es alt aus?

## Prüfe in Render Shell:

```python
from django.contrib.auth.models import User, Group
from adeacore.models import Client
from adeazeit.models import EmployeeInternal

# 1. Prüfe Benutzer und Rollen
print("=== BENUTZER ===")
for user in User.objects.all():
    groups = [g.name for g in user.groups.all()]
    print(f"{user.username}: Groups={groups}, Superuser={user.is_superuser}")

# 2. Prüfe ob Rollen existieren
print("\n=== ROLLEN ===")
for group in Group.objects.all():
    print(f"{group.name}: {group.user_set.count()} Benutzer")

# 3. Prüfe Clients (Mandanten)
print("\n=== CLIENTS ===")
print(f"Anzahl Clients: {Client.objects.count()}")
for client in Client.objects.all()[:5]:
    print(f"  - {client.name} ({client.client_type})")

# 4. Prüfe Mitarbeitende
print("\n=== MITARBEITENDE ===")
print(f"Anzahl Mitarbeitende: {EmployeeInternal.objects.count()}")
for emp in EmployeeInternal.objects.all()[:5]:
    print(f"  - {emp.name} ({emp.code})")

# 5. Prüfe Context Processor Berechtigungen
print("\n=== BERECHTIGUNGEN TEST ===")
from adeacore.context_processors import adeazeit_permissions
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

# Simuliere Request mit Aivanova
try:
    aivanova = User.objects.get(username="Aivanova")
    factory = RequestFactory()
    request = factory.get('/')
    request.user = aivanova
    perms = adeazeit_permissions(request)
    print(f"Aivanova Berechtigungen: {perms}")
except Exception as e:
    print(f"Fehler: {e}")

exit()
```

---

## Mögliche Probleme:

1. **Keine Clients** → AdeaDesk sieht leer aus
2. **Keine Mitarbeitende** → AdeaZeit sieht leer aus  
3. **Rollen nicht zugewiesen** → Admin-Bereich nicht sichtbar
4. **AdeaLohn nicht aktiviert** → AdeaLohn nicht sichtbar

---

## Lösung:

Falls Daten fehlen, müssen sie von lokal migriert werden oder neu erfasst werden.

