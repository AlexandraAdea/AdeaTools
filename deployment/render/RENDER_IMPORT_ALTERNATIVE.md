# 🔄 Alternative: Daten direkt auf Render importieren

## Problem:
Die JSON-Datei ist noch nicht auf Render verfügbar.

## ✅ Lösung: Daten direkt in Render Shell eingeben

**In Render Shell:**
```bash
python manage.py shell
```

**Dann kopiere diesen Code (ersetzt die Daten):**

```python
import json
from django.core import serializers
from django.contrib.auth.models import User
from adeacore.models import Client
from adeazeit.models import EmployeeInternal

# Lade die JSON-Datei von GitHub oder kopiere den Inhalt
# Option 1: Von GitHub herunterladen
import urllib.request
url = "https://raw.githubusercontent.com/AlexandraAdea/AdeaTools/main/AdeaCore/export_render_complete_utf8.json"
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode('utf-8'))

# Option 2: Oder kopiere den Inhalt der Datei direkt hier rein
# data = json.loads('''HIER_KOMPLETTEN_JSON_INHALT_EINFÜGEN''')

# Importiere die Daten
for obj in serializers.deserialize("json", json.dumps(data)):
    obj.save()

print("✅ Daten importiert!")
```

---

## ODER: Warte auf nächsten Build

Render lädt die Datei automatisch beim nächsten Build. Dann:

```bash
cd ~/project/src
python manage.py loaddata export_render_complete_utf8.json
```

