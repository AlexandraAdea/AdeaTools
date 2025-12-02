# 🚀 Render Deployment - Schritt für Schritt

**Aktualisierte Anleitung mit neuer Settings-Struktur**

---

## Voraussetzungen

- ✅ GitHub Repository: `https://github.com/AlexandraAdea/AdeaTools`
- ✅ Render Account: `https://render.com`
- ✅ Lokale Daten funktionieren korrekt

---

## SCHRITT 1: Render Web Service erstellen

1. Gehe zu https://render.com/dashboard
2. Klicke **"New +"** → **"Web Service"**
3. Verbinde dein GitHub Repository: `AlexandraAdea/AdeaTools`
4. Konfiguration:
   - **Name:** `adeatools` (oder dein Wunschname)
   - **Region:** Frankfurt (EU Central)
   - **Branch:** `main`
   - **Root Directory:** `AdeaCore`
   - **Runtime:** Python 3
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - **Start Command:**
     ```bash
     gunicorn adeacore.wsgi:application
     ```

5. Klicke **"Create Web Service"** (noch NICHT deployen!)

---

## SCHRITT 2: PostgreSQL Datenbank erstellen

1. In Render Dashboard: **"New +"** → **"PostgreSQL"**
2. Konfiguration:
   - **Name:** `adeatools-db`
   - **Database:** `adeatools`
   - **User:** `adeatools`
   - **Region:** Frankfurt (EU Central) - **GLEICHE wie Web Service!**
   - **Plan:** Free
3. Klicke **"Create Database"**
4. Warte bis Database "Available" ist
5. **Kopiere die Internal Database URL** (sieht aus wie `postgresql://...`)

---

## SCHRITT 3: Environment Variables setzen

In deinem Web Service → **"Environment"** Tab:

### Kritische Variablen (MÜSSEN gesetzt sein):

1. **DJANGO_DEBUG**
   ```
   DJANGO_DEBUG=False
   ```

2. **DJANGO_SECRET_KEY** (neuen Key generieren!)
   ```bash
   # Lokal ausführen:
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Dann setzen:
   ```
   DJANGO_SECRET_KEY=<generierter-key>
   ```

3. **DJANGO_ALLOWED_HOSTS**
   ```
   DJANGO_ALLOWED_HOSTS=<deine-app-name>.onrender.com
   ```
   Beispiel: `DJANGO_ALLOWED_HOSTS=adeatools.onrender.com`

4. **ADEATOOLS_ENCRYPTION_KEY** (⚠️ KRITISCH!)
   ```
   ADEATOOLS_ENCRYPTION_KEY=wuWgA6jbfNsWuUZWc1QDU6UoWRleM-b4A0_NowTSDqw=
   ```
   **WICHTIG:** Exakt der gleiche Key wie lokal, damit Daten lesbar bleiben!

5. **DATABASE_URL**
   - Verbinde die PostgreSQL Database:
   - In Web Service → "Environment" → "Add Environment Variable"
   - Klicke auf "Add from database" und wähle `adeatools-db`
   - ODER kopiere die "Internal Database URL" manuell

---

## SCHRITT 4: Manual Deploy

1. Klicke **"Manual Deploy"** → **"Deploy latest commit"**
2. Warte auf Build (5-10 Minuten)
3. Prüfe Logs auf Fehler

---

## SCHRITT 5: Post-Deployment Setup

**Im Render Shell** (Web Service → "Shell"):

```bash
# 1. Rollen initialisieren
python manage.py init_roles

# 2. Superuser erstellen
python manage.py createsuperuser
# Username: Aivanova
# Email: alexandra@adea-treuhand.ch
# Password: <dein-passwort>

# 3. Daten importieren (optional)
python manage.py loaddata fixtures/test_data.json

# 4. Passwörter setzen (nach Import)
python manage.py shell
```

In der Shell:
```python
from django.contrib.auth.models import User
for user in User.objects.all():
    user.set_password("<dein-passwort>")
    user.save()
exit()
```

---

## ⚠️ KRITISCHE PUNKTE

1. **ADEATOOLS_ENCRYPTION_KEY:** MUSS exakt gleich sein wie lokal!
2. **DJANGO_ALLOWED_HOSTS:** Auf Render-URL setzen
3. **DATABASE_URL:** Interne URL verwenden (nicht External)
4. **Region:** Database und Web Service in gleicher Region

---

## Bereit?

Ich habe die Dateien vorbereitet:
- ✅ `Procfile` erstellt
- ✅ `build.sh` erstellt
- ✅ `.env.render` als Dokumentation erstellt
- ✅ Deployment-Anleitung aktualisiert

Soll ich diese Dateien committen und pushen, oder möchtest du sie zuerst prüfen?
