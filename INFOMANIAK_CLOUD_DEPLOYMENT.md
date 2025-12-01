# 🚀 Deployment auf Infomaniak Cloud - Anleitung

**Hosting:** Infomaniak Cloud  
**Datum:** 2025-11-26  
**Status:** ✅ **Bereit für Deployment**

---

## 📋 ÜBERSICHT

Infomaniak Cloud bietet:
- ✅ **Schweizer Rechenzentren** (DSGVO/DSG-konform)
- ✅ **Managed Hosting** (einfach zu verwenden)
- ✅ **PostgreSQL** Datenbanken verfügbar
- ✅ **HTTPS** automatisch (Let's Encrypt)
- ✅ **Günstig:** Ab ~5 CHF/Monat
- ✅ **Schnell:** Gute Performance

---

## 🔧 VORBEREITUNG

### 1. Infomaniak Cloud Account erstellen

1. Gehen Sie zu: https://www.infomaniak.com/de/cloud
2. Erstellen Sie einen Account
3. Wählen Sie einen Plan (z.B. "Cloud VPS" oder "Managed Hosting")

### 2. Domain konfigurieren (optional)

- Eigene Domain verwenden (z.B. `adeatools.ch`)
- Oder Infomaniak-Subdomain verwenden (z.B. `adeatools.infomaniak.cloud`)

### 3. PostgreSQL-Datenbank einrichten

**In Infomaniak Cloud Dashboard:**
1. Gehen Sie zu "Datenbanken"
2. Erstellen Sie eine PostgreSQL-Datenbank
3. Notieren Sie:
   - Host
   - Port (Standard: 5432)
   - Datenbankname
   - Benutzername
   - Passwort

---

## 🔐 ENVIRONMENT-VARIABLEN SETZEN

### In Infomaniak Cloud Dashboard:

**Gehen Sie zu:** Einstellungen → Environment-Variablen

**Setzen Sie folgende Variablen:**

```env
# KRITISCH - SICHERHEIT
DJANGO_SECRET_KEY=<generierter-50-zeichen-schlüssel>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=ihre-domain.infomaniak.cloud,ihre-domain.ch
ADEATOOLS_ENCRYPTION_KEY=<generierter-fernet-key>

# DATENBANK (PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/adeatools

# E-MAIL (Optional - Infomaniak SMTP)
EMAIL_HOST=smtp.infomaniak.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@adea-treuhand.ch
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@adea-treuhand.ch
```

---

## 🔑 SCHLÜSSEL GENERIEREN

### SECRET_KEY generieren:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Beispiel-Output:**
```
django-insecure-abc123xyz789...
```

### ADEATOOLS_ENCRYPTION_KEY generieren:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Beispiel-Output:**
```
gAAAAABk1X2Ymmkh*!qs(260sgiv9qcc*=#e(^5^68j#s!7i2=
```

**⚠️ WICHTIG:** Speichern Sie beide Schlüssel sicher! Bei Verlust sind Daten nicht mehr zugänglich!

---

## 📦 DEPLOYMENT-SCHRITTE

### Schritt 1: Code hochladen

**Option A: Git (empfohlen)**
```bash
# In Infomaniak Cloud: Git Repository einrichten
git clone https://github.com/ihr-repo/adeatools.git
cd adeatools/AdeaCore
```

**Option B: FTP/SFTP**
- Laden Sie alle Dateien hoch
- Struktur beibehalten

### Schritt 2: Python-Umgebung einrichten

**In Infomaniak Cloud SSH-Terminal:**

```bash
# Python-Version prüfen (sollte 3.9+ sein)
python3 --version

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt
pip install psycopg2-binary  # Für PostgreSQL
pip install python-dotenv  # Für .env Support
```

### Schritt 3: Datenbank konfigurieren

**Erstellen Sie `AdeaCore/.env`:**

```env
DJANGO_SECRET_KEY=<ihr-secret-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=ihre-domain.infomaniak.cloud,ihre-domain.ch
ADEATOOLS_ENCRYPTION_KEY=<ihr-encryption-key>

DATABASE_URL=postgresql://user:password@host:5432/adeatools
```

**Oder:** Setzen Sie Environment-Variablen direkt in Infomaniak Cloud Dashboard.

### Schritt 4: Datenbank-Migration

```bash
# Migrationen ausführen
python manage.py migrate

# Superuser erstellen (falls noch nicht vorhanden)
python manage.py createsuperuser
```

### Schritt 5: Static Files sammeln

```bash
# STATIC_ROOT in settings.py setzen
# Dann:
python manage.py collectstatic --noinput
```

**In `settings.py` hinzufügen:**
```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### Schritt 6: WSGI-Konfiguration

**Infomaniak Cloud verwendet meist Gunicorn:**

```bash
# Gunicorn installieren
pip install gunicorn

# Starten Sie die App:
gunicorn adeacore.wsgi:application --bind 0.0.0.0:8000
```

**Oder:** Infomaniak Cloud kann auch automatisch WSGI-Apps starten.

---

## 🔄 MIGRATION VON SQLITE ZU POSTGRESQL

### Schritt 1: Daten exportieren

**Lokal (mit SQLite):**

```bash
python manage.py dumpdata > backup.json
```

### Schritt 2: PostgreSQL-Datenbank einrichten

**In Infomaniak Cloud Dashboard:**
- PostgreSQL-Datenbank erstellen
- Zugangsdaten notieren

### Schritt 3: Datenbank in settings.py ändern

**In `AdeaCore/adeacore/settings.py`:**

```python
import os
from urllib.parse import urlparse

# PostgreSQL-Konfiguration
if 'DATABASE_URL' in os.environ:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.environ['DATABASE_URL'])
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': get_env_variable('DB_NAME', 'adeatools'),
            'USER': get_env_variable('DB_USER', 'adeatools'),
            'PASSWORD': get_env_variable('DB_PASSWORD', ''),
            'HOST': get_env_variable('DB_HOST', 'localhost'),
            'PORT': get_env_variable('DB_PORT', '5432'),
        }
    }
```

**Oder installieren Sie `dj-database-url`:**
```bash
pip install dj-database-url
```

### Schritt 4: Daten importieren

```bash
# Migrationen ausführen
python manage.py migrate

# Daten importieren
python manage.py loaddata backup.json
```

---

## 🔐 HTTPS KONFIGURATION

**Infomaniak Cloud bietet automatisch HTTPS:**
- Let's Encrypt Zertifikate
- Automatische Erneuerung
- Keine zusätzliche Konfiguration nötig

**In Django (bereits implementiert):**
- Security-Headers werden automatisch aktiviert wenn `DEBUG=False`
- HTTPS wird erzwungen

---

## 📋 BACKUP-STRATEGIE FÜR INFOMANIAK CLOUD

### Option 1: Automatische Backups (empfohlen)

**Cronjob einrichten:**

```bash
# Täglich um 23:00 Uhr
0 23 * * * cd /path/to/AdeaCore && /path/to/venv/bin/python manage.py daily_backup
```

### Option 2: Infomaniak Cloud Backup-Service

- Nutzen Sie Infomaniak Cloud Backup-Service
- Automatische tägliche Backups
- Einfache Wiederherstellung

### Option 3: Manuelle Backups

```bash
# Regelmäßig manuell:
python manage.py daily_backup
```

---

## 🔍 MONITORING & LOGS

### Logs prüfen:

**In Infomaniak Cloud Dashboard:**
- Application Logs
- Error Logs
- Access Logs

**Django Logs:**
- `logs/audit_2025.jsonl` - Audit-Logs
- `logs/adealohn.log` - Application Logs

### Monitoring einrichten:

**Empfohlene Tools:**
- Infomaniak Cloud Monitoring (falls verfügbar)
- Sentry (für Error-Tracking)
- Uptime-Monitoring

---

## ✅ DEPLOYMENT-CHECKLISTE

### Vor Deployment:

- [ ] **Infomaniak Cloud Account** erstellt
- [ ] **Domain** konfiguriert (oder Subdomain)
- [ ] **PostgreSQL-Datenbank** eingerichtet
- [ ] **SECRET_KEY** generiert und gesetzt
- [ ] **ADEATOOLS_ENCRYPTION_KEY** generiert und gesetzt
- [ ] **DEBUG = False** gesetzt
- [ ] **ALLOWED_HOSTS** konfiguriert
- [ ] **DATABASE_URL** konfiguriert
- [ ] **Code** hochgeladen
- [ ] **Dependencies** installiert
- [ ] **Migrationen** ausgeführt
- [ ] **Static Files** gesammelt
- [ ] **Superuser** erstellt
- [ ] **Backup** vor Migration erstellt

### Nach Deployment:

- [ ] **HTTPS** funktioniert
- [ ] **Login** funktioniert
- [ ] **Daten** sind vorhanden
- [ ] **Verschlüsselung** funktioniert
- [ ] **Audit-Logs** funktionieren
- [ ] **Backups** automatisch eingerichtet
- [ ] **Monitoring** eingerichtet
- [ ] **Datenschutzerklärung** veröffentlicht

---

## 🆘 TROUBLESHOOTING

### Problem: Datenbank-Verbindung fehlgeschlagen

**Lösung:**
- Prüfen Sie `DATABASE_URL` oder Datenbank-Credentials
- Prüfen Sie Firewall-Regeln in Infomaniak Cloud
- Prüfen Sie ob PostgreSQL-Service läuft

### Problem: Static Files werden nicht geladen

**Lösung:**
```bash
python manage.py collectstatic --noinput
```

### Problem: 500 Internal Server Error

**Lösung:**
- Prüfen Sie Logs in Infomaniak Cloud Dashboard
- Prüfen Sie ob `DEBUG=False` gesetzt ist
- Prüfen Sie Environment-Variablen

### Problem: Verschlüsselung funktioniert nicht

**Lösung:**
- Prüfen Sie ob `ADEATOOLS_ENCRYPTION_KEY` gesetzt ist
- Prüfen Sie ob Key korrekt ist (muss Fernet-Format haben)

---

## 📞 SUPPORT

### Infomaniak Cloud Support:
- Website: https://www.infomaniak.com/de/support
- E-Mail: support@infomaniak.com
- Telefon: +41 22 820 35 44

### AdeaTools Support:
- E-Mail: alexandra@adea-treuhand.ch

---

## ✅ FAZIT

**Deployment auf Infomaniak Cloud ist vorbereitet!**

**Vorteile:**
- ✅ Schweizer Rechenzentren (DSGVO/DSG-konform)
- ✅ Günstig (~5 CHF/Monat)
- ✅ Einfach zu verwenden
- ✅ Automatisches HTTPS
- ✅ PostgreSQL verfügbar

**Nächste Schritte:**
1. Infomaniak Cloud Account erstellen
2. PostgreSQL-Datenbank einrichten
3. Environment-Variablen setzen
4. Code deployen
5. Migration durchführen

---

**Bereit für Infomaniak Cloud Deployment! 🚀**



