#!/usr/bin/env python
"""
Direkter Import der Daten von GitHub auf Render.
Führe aus: python RENDER_IMPORT_DIRECT.py
"""

import json
import urllib.request
from django.core import serializers
from django.db import transaction

# Lade Daten von GitHub
url = "https://raw.githubusercontent.com/AlexandraAdea/AdeaTools/main/AdeaCore/export_render_complete_utf8.json"
print(f"Lade Daten von GitHub...")
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode('utf-8'))

print(f"✅ {len(data)} Objekte geladen")

# Importiere Daten
with transaction.atomic():
    imported = 0
    errors = 0
    for obj in serializers.deserialize("json", json.dumps(data)):
        try:
            obj.save()
            imported += 1
        except Exception as e:
            print(f"⚠️ Fehler bei {obj.object}: {e}")
            errors += 1

print(f"\n✅ Import abgeschlossen!")
print(f"   Importiert: {imported}")
print(f"   Fehler: {errors}")

