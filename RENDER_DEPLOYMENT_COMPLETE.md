# 🚀 Render Deployment - Vollständige Anleitung

**Datum:** 2025-11-26  
**Status:** ✅ Alle Dateien vorbereitet

---

## ✅ WAS WURDE VORBEREITET

### 1. ✅ `requirements.txt` erstellt
- Django 5.1.2
- gunicorn (Production Server)
- whitenoise (Statische Dateien)
- psycopg2-binary (PostgreSQL)
- dj-database-url (Datenbank-URL Parsing)
- cryptography (Verschlüsselung)
- python-dotenv (Environment-Variablen)

### 2. ✅ `settings.py` für Production angepasst
- Environment-Variablen Support
- PostgreSQL Support (automatisch wenn DATABASE_URL gesetzt)
- DEBUG aus Environment
- ALLOWED_HOSTS aus Environment
- STATIC_ROOT für collectstatic
- WhiteNoise für statische Dateien
- Security Settings für Production

### 3. ✅ Render-Konfiguration dokumentiert

---

## 📋 SCHRITT-FÜR-SCHRITT ANLEITUNG

### SCHRITT 1: Code zu GitHub pushen

**Öffne PowerShell/Terminal:**

```powershell
cd C:\AdeaTools\AdeaCore
```

**1.1 Prüfe Status:**
```powershell
git status
```

**1.2 Füge alle Änderungen hinzu:**
```powershell
git add .
```

**1.3 Committe alle Änderungen:**
```powershell
git commit -m "Render Deployment: Production Settings, requirements.txt, Build Commands"
```

**1.4 Pushe zu GitHub:**
```powershell
git push origin main
```

---

### SCHRITT 2: Render Build & Start Commands korrigieren

**In Render Dashboard:**

1. Gehe zu: **Dashboard** → **adeacore-web** → **Settings** → **Build & Deploy**

2. **Ändere Build Command:**
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput
   ```

3. **Ändere Start Command:**
   ```
   gunicorn adeacore.wsgi:application --bind 0.0.0.0:$PORT
   ```

4. **Klicke auf "Save Changes"**

---

### SCHRITT 3: Environment-Variablen in Render setzen

**In Render Dashboard:**

1. Gehe zu: **Dashboard** → **adeacore-web** → **Environment**

2. **Füge folgende Variablen hinzu:**

   ```
   DJANGO_SECRET_KEY=<generiere-neuen-key>
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=adeacore-web.onrender.com
   ADEATOOLS_ENCRYPTION_KEY=<generiere-neuen-key>
   ```

3. **Secret Keys generieren:**

   **DJANGO_SECRET_KEY:**
   ```powershell
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

   **ADEATOOLS_ENCRYPTION_KEY:**
   ```powershell
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

4. **Kopiere die generierten Keys** und füge sie in Render ein

5. **Klicke auf "Save Changes"**

---

### SCHRITT 4: PostgreSQL-Datenbank hinzufügen (OPTIONAL aber empfohlen)

**In Render Dashboard:**

1. Klicke auf **"+ New"** → **PostgreSQL**

2. **Konfiguration:**
   - **Name:** `adeacore-db`
   - **Database:** `adeacore`
   - **User:** (wird automatisch generiert)
   - **Region:** Frankfurt (EU Central) - **gleich wie Web Service!**
   - **Plan:** Starter (kostenlos) oder höher

3. **Klicke auf "Create Database"**

4. **DATABASE_URL wird automatisch gesetzt** - keine manuelle Eingabe nötig!

---

### SCHRITT 5: Ersten Build starten

**In Render Dashboard:**

1. Gehe zu: **Dashboard** → **adeacore-web** → **Manual Deploy**

2. **Klicke auf "Deploy latest commit"**

3. **Warte auf Build** (5-10 Minuten)

4. **Prüfe Logs** falls Fehler auftreten

---

### SCHRITT 6: Datenbank-Migrationen ausführen

**Nach erfolgreichem Build:**

1. Gehe zu: **Dashboard** → **adeacore-web** → **Shell**

2. **Führe Migrationen aus:**
   ```bash
   python manage.py migrate
   ```

3. **Erstelle Superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

---

## 🔍 FEHLERBEHEBUNG

### Problem: "ModuleNotFoundError: No module named 'dj_database_url'"
**Lösung:** Prüfe ob `requirements.txt` korrekt gepusht wurde

### Problem: "Static files not found"
**Lösung:** Prüfe ob `collectstatic` im Build Command enthalten ist

### Problem: "ALLOWED_HOSTS error"
**Lösung:** Prüfe ob `DJANGO_ALLOWED_HOSTS` in Render Environment gesetzt ist

### Problem: "Database connection failed"
**Lösung:** Prüfe ob PostgreSQL-Datenbank erstellt wurde und `DATABASE_URL` gesetzt ist

---

## ✅ CHECKLISTE

- [ ] Code zu GitHub gepusht
- [ ] Build Command korrigiert
- [ ] Start Command korrigiert
- [ ] DJANGO_SECRET_KEY gesetzt
- [ ] DJANGO_DEBUG=False gesetzt
- [ ] DJANGO_ALLOWED_HOSTS gesetzt
- [ ] ADEATOOLS_ENCRYPTION_KEY gesetzt
- [ ] PostgreSQL-Datenbank erstellt (optional)
- [ ] Build erfolgreich
- [ ] Migrationen ausgeführt
- [ ] Superuser erstellt (optional)

---

## 🎉 FERTIG!

Nach allen Schritten sollte deine AdeaTools-Anwendung auf Render laufen!

**URL:** `https://adeacore-web.onrender.com`

---

## 📞 SUPPORT

Bei Problemen:
1. Prüfe Render Logs: **Dashboard** → **adeacore-web** → **Logs**
2. Prüfe Build Logs: **Dashboard** → **adeacore-web** → **Events**
3. Prüfe Environment-Variablen: **Dashboard** → **adeacore-web** → **Environment**

