# 🔧 Benutzer-Daten auf Render korrigieren

## Problem:
- "Anna Ivanova" wird angezeigt (falsch)
- Lokal war alles richtig

## ✅ Lösung: Benutzer-Daten korrigieren

**In Render Shell:**
```python
from django.contrib.auth.models import User

# Zeige alle Benutzer
print("=== AKTUELLE BENUTZER ===")
for user in User.objects.all():
    print(f"{user.username}: first='{user.first_name}', last='{user.last_name}', email='{user.email}'")

# Korrigiere Aivanova (falls leer)
aivanova = User.objects.get(username="Aivanova")
if not aivanova.first_name and not aivanova.last_name:
    # Setze auf leer oder auf richtigen Namen
    aivanova.first_name = ""
    aivanova.last_name = ""
    aivanova.save()
    print("✅ Aivanova korrigiert")

# Korrigiere ai (falls falsch)
try:
    ai = User.objects.get(username="ai")
    # Prüfe was lokal richtig ist
    # Falls lokal first_name="Alexandra" war, dann:
    ai.first_name = "Alexandra"  # Oder was lokal richtig war
    ai.last_name = "Ivanova"     # Oder was lokal richtig war
    ai.save()
    print("✅ ai korrigiert")
except:
    pass

exit()
```

---

## ODER: Daten neu importieren

Falls die Daten beim Import verloren gingen, importiere nochmal:

```python
import json
import urllib.request
from django.core import serializers
from django.db import transaction

url = "https://raw.githubusercontent.com/AlexandraAdea/AdeaTools/main/AdeaCore/export_render_complete_utf8.json"
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode('utf-8'))

# Importiere NUR Benutzer neu
with transaction.atomic():
    for obj in serializers.deserialize("json", json.dumps(data)):
        if obj.object.__class__.__name__ == 'User':
            obj.save()
            print(f"✅ {obj.object.username} importiert")

exit()
```

