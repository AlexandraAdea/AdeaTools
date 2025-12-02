# 🔧 Daten wiederherstellen - Verschlüsselungsschlüssel fehlt

## Problem
Die Daten werden wieder als verschlüsselte Strings angezeigt, weil der Verschlüsselungsschlüssel (`ADEATOOLS_ENCRYPTION_KEY`) fehlt oder geändert wurde.

---

## ✅ Lösung 1: Alten Schlüssel wiederherstellen

**Der alte Schlüssel war:**
```
ADEATOOLS_ENCRYPTION_KEY=wuWgA6jbfNsWuUZWc1QDU6UoWRleM-b4A0_NowTSDqw=
```

**Schritte:**
1. Erstelle `.env` Datei in `AdeaCore/`:
   ```
   ADEATOOLS_ENCRYPTION_KEY=wuWgA6jbfNsWuUZWc1QDU6UoWRleM-b4A0_NowTSDqw=
   ```

2. Server neu starten

3. Daten sollten wieder lesbar sein ✅

---

## ✅ Lösung 2: Neuen Schlüssel verwenden (Daten neu eingeben)

Falls der alte Schlüssel nicht mehr verfügbar ist:

1. **Erstelle `.env` Datei** mit neuem Schlüssel:
   ```powershell
   cd C:\AdeaTools\AdeaCore
   python -c "from cryptography.fernet import Fernet; print('ADEATOOLS_ENCRYPTION_KEY=' + Fernet.generate_key().decode('utf-8'))"
   ```

2. Kopiere den generierten Key in `.env`

3. **Verschlüsselte Felder zurücksetzen:**
   ```python
   python manage.py shell
   ```
   
   ```python
   from adeacore.models import Client
   from adeazeit.models import EmployeeInternal
   
   # Setze alle verschlüsselten Felder auf leer
   for client in Client.objects.all():
       client.email = ""
       client.phone = ""
       client.street = ""
       client.house_number = ""
       client.postal_code = ""
       client.city = ""
       client.vat_number = ""
       client.invoice_email = ""
       client.save()
   
   for emp in EmployeeInternal.objects.all():
       emp.email = ""
       emp.phone = ""
       emp.street = ""
       emp.house_number = ""
       emp.postal_code = ""
       emp.city = ""
       emp.birth_date = None
       emp.save()
   
   print("✅ Alle verschlüsselten Felder zurückgesetzt")
   exit()
   ```

4. **Daten neu eingeben** über die Web-Oberfläche

---

## 🔍 Prüfen: Welcher Schlüssel wird verwendet?

```powershell
cd C:\AdeaTools\AdeaCore
python manage.py shell
```

```python
import os
from dotenv import load_dotenv
load_dotenv()

key = os.environ.get('ADEATOOLS_ENCRYPTION_KEY')
if key:
    print(f"✅ Key gefunden: {key[:30]}...")
else:
    print("❌ KEIN KEY GEFUNDEN - wird neu generiert!")
    
exit()
```

---

## ⚠️ WICHTIG

**Der Verschlüsselungsschlüssel muss IMMER gleich bleiben!**

- ✅ `.env` Datei NICHT löschen
- ✅ `.env` NICHT ins Git hochladen (bereits in `.gitignore`)
- ✅ Bei Deployment: Gleichen Key verwenden

