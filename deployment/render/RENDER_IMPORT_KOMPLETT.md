# ✅ Kompletter Import-Code für Render

## In Render Shell ausführen:

```python
import json
import urllib.request
from django.core import serializers
from django.db import transaction
from django.contrib.auth.models import User

# Lade Daten von GitHub
url = "https://raw.githubusercontent.com/AlexandraAdea/AdeaTools/main/AdeaCore/export_render_complete_utf8.json"
print("Lade Daten von GitHub...")
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode('utf-8'))

print(f"✅ {len(data)} Objekte geladen")

# Prüfe Benutzer-Daten vor Import
print("\n📋 Benutzer im Export:")
for obj in data:
    if obj.get('model') == 'auth.user':
        fields = obj.get('fields', {})
        print(f"  {fields.get('username')}: first='{fields.get('first_name', '')}', last='{fields.get('last_name', '')}', email='{fields.get('email', '')}'")

# Importiere Daten
print("\n🔄 Importiere Daten...")
with transaction.atomic():
    imported = 0
    errors = 0
    for obj in serializers.deserialize("json", json.dumps(data)):
        try:
            obj.save()
            imported += 1
            if imported % 20 == 0:
                print(f"  {imported} Objekte importiert...")
        except Exception as e:
            print(f"⚠️ Fehler bei {obj.object}: {e}")
            errors += 1

print(f"\n✅ Import abgeschlossen!")
print(f"   Importiert: {imported}")
print(f"   Fehler: {errors}")

# Prüfe ob Daten korrekt importiert wurden
print(f"\n📊 Datenbank-Status nach Import:")
print(f"   Benutzer: {User.objects.count()}")
for user in User.objects.all():
    print(f"     - {user.username}: first='{user.first_name}', last='{user.last_name}', full='{user.get_full_name()}'")

from adeacore.models import Client
from adeazeit.models import EmployeeInternal
print(f"   Clients: {Client.objects.count()}")
print(f"   Mitarbeitende: {EmployeeInternal.objects.count()}")

exit()
```

---

## Nach Import: Passwörter setzen

```python
from django.contrib.auth.models import User

# Setze Passwörter für alle Benutzer
for user in User.objects.all():
    # Verwende dein bekanntes Passwort
    user.set_password("DEIN_BEKANNTES_PASSWORT")
    user.save()
    print(f"✅ Passwort für {user.username} gesetzt")

exit()
```

