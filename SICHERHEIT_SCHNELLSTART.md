# 🔒 Sicherheit - Schnellstart

**Für lokale Entwicklung:**

## 1. .env Datei erstellen

**Windows:**
```bash
cd C:\AdeaTools\AdeaCore
ERSTELLE_ENV.bat
```

**Oder manuell:**
```bash
copy env.example .env
```

---

## 2. .env Datei bearbeiten

Öffnen Sie `.env` und prüfen Sie die Werte:

```env
DJANGO_SECRET_KEY=<wird automatisch generiert>
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

**Für Development:** Diese Werte sind OK!

---

## 3. Server starten

```bash
python manage.py runserver
```

**Fertig!** Die App läuft jetzt mit sicheren Settings.

---

## ⚠️ WICHTIG FÜR PRODUCTION

**Wenn Sie die App online hosten (Railway, Azure, etc.):**

1. **Neuen SECRET_KEY generieren:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **Environment-Variablen im Hosting-Service setzen:**
   ```
   DJANGO_SECRET_KEY=<neuer-generierter-key>
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=ihre-domain.ch,ihre-domain.railway.app
   ```

3. **HTTPS aktivieren** (wird automatisch durch Security-Headers erzwungen)

---

## ✅ WAS WURDE VERBESSERT

- ✅ SECRET_KEY aus Environment-Variablen (nicht mehr im Code)
- ✅ DEBUG = False für Production
- ✅ ALLOWED_HOSTS konfiguriert
- ✅ HTTPS & Security-Headers aktiviert
- ✅ Session-Sicherheit verbessert
- ✅ CSRF-Schutz verbessert
- ✅ .env Support für einfache Konfiguration

**Details:** Siehe `SICHERHEIT_IMPLEMENTIERT.md`



