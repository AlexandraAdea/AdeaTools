# 🔧 Lokales Tool starten - Problem beheben

## Mögliche Probleme:

### 1. DEBUG ist False
**Problem:** `DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'`
- Wenn `DJANGO_DEBUG` nicht gesetzt ist, wird `False` verwendet
- Lokal sollte `DEBUG = True` sein

**Lösung:** Prüfe `.env` Datei oder setze Environment-Variable:
```powershell
$env:DJANGO_DEBUG="True"
python manage.py runserver
```

### 2. ALLOWED_HOSTS ist leer
**Problem:** `ALLOWED_HOSTS` könnte leer sein

**Lösung:** Prüfe `.env` oder setze:
```powershell
$env:DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1"
```

### 3. Datenbank-Verbindung
**Problem:** PostgreSQL wird versucht statt SQLite

**Lösung:** Prüfe ob `DATABASE_URL` gesetzt ist - sollte leer sein für lokale Entwicklung

---

## ✅ Schnelle Lösung:

**Erstelle/Prüfe `.env` Datei:**
```
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

**ODER starte mit expliziten Werten:**
```powershell
cd C:\AdeaTools\AdeaCore
$env:DJANGO_DEBUG="True"
$env:DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1"
python manage.py runserver
```

---

## 🔍 Fehler prüfen:

**Was genau passiert beim Start?**
- Fehlermeldung?
- Startet nicht?
- Crash?

Bitte die genaue Fehlermeldung senden!

