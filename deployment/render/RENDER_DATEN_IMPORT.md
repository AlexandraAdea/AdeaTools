# 🚀 Render: Daten von lokal importieren

## ✅ SCHRITT 1: Daten exportiert (lokal)

Die Daten wurden exportiert zu: `export_render_complete.json`

---

## ✅ SCHRITT 2: Datei auf Render hochladen

**Option A: Via Render Disk (empfohlen)**
1. Render Dashboard → `adeacore-web` → **Disk**
2. Klicke auf **"Upload"**
3. Lade `export_render_complete.json` hoch

**Option B: Via Git (falls Datei < 100MB)**
```powershell
cd C:\AdeaTools\AdeaCore
git add export_render_complete.json
git commit -m "Add: Daten-Export für Render"
git push origin main
```

---

## ✅ SCHRITT 3: Auf Render importieren

**In Render Shell:**
```bash
# 1. Prüfe ob Datei vorhanden ist
ls -la export_render_complete.json

# 2. Importiere Daten
python manage.py loaddata export_render_complete.json

# 3. Prüfe ob Daten importiert wurden
python manage.py shell
```

**In Python Shell:**
```python
from django.contrib.auth.models import User
from adeacore.models import Client
from adeazeit.models import EmployeeInternal

print(f"Benutzer: {User.objects.count()}")
print(f"Clients: {Client.objects.count()}")
print(f"Mitarbeitende: {EmployeeInternal.objects.count()}")

# Zeige alle Benutzer
for user in User.objects.all():
    print(f"  - {user.username}")

exit()
```

---

## ⚠️ WICHTIG:

- **Passwörter werden NICHT exportiert!** (Django-Sicherheit)
- Du musst Passwörter nach dem Import neu setzen
- Sessions werden nicht importiert (das ist OK)

---

## 🔑 Nach Import: Passwörter setzen

```python
from django.contrib.auth.models import User

# Setze Passwörter für alle Benutzer
for user in User.objects.all():
    # Verwende bekannte Passwörter oder setze neue
    user.set_password("DEIN_PASSWORT")
    user.save()
    print(f"✅ Passwort für {user.username} gesetzt")

exit()
```

---

## ✅ FERTIG!

Nach dem Import sollten alle Daten auf Render sein!

