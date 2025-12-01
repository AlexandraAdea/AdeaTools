# 🚀 Schnellstart: Deployment auf Infomaniak Cloud

**Hosting:** Infomaniak Cloud  
**Dauer:** ~2 Stunden  
**Schwierigkeit:** 🟡 Mittel

---

## 📋 SCHNELLSTART-CHECKLISTE

### 1. Vorbereitung (30 Min)

- [ ] Infomaniak Cloud Account erstellen
- [ ] Domain/Subdomain konfigurieren
- [ ] PostgreSQL-Datenbank einrichten
- [ ] SSH-Zugang einrichten

### 2. Schlüssel generieren (10 Min)

```bash
# SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**⚠️ WICHTIG:** Beide Schlüssel sicher speichern!

### 3. Environment-Variablen setzen (10 Min)

**In Infomaniak Cloud Dashboard:**

```
DJANGO_SECRET_KEY=<generierter-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=ihre-domain.infomaniak.cloud
ADEATOOLS_ENCRYPTION_KEY=<generierter-key>
DATABASE_URL=postgresql://user:password@host:5432/adeatools
```

### 4. Code deployen (30 Min)

```bash
# Via Git (empfohlen)
git clone https://github.com/ihr-repo/adeatools.git
cd adeatools/AdeaCore

# Oder via FTP/SFTP
```

### 5. Dependencies installieren (10 Min)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 6. Datenbank migrieren (20 Min)

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 7. App starten (10 Min)

```bash
gunicorn adeacore.wsgi:application --bind 0.0.0.0:8000
```

**Oder:** Infomaniak Cloud kann automatisch WSGI-Apps starten.

---

## 🔐 KRITISCHE CONFIGURATION

### Environment-Variablen (MUSS gesetzt werden):

```env
DJANGO_SECRET_KEY=<50-zeichen-schlüssel>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=ihre-domain.infomaniak.cloud
ADEATOOLS_ENCRYPTION_KEY=<fernet-key>
DATABASE_URL=postgresql://user:password@host:5432/adeatools
```

### PostgreSQL-Konfiguration:

**In `settings.py` bereits implementiert:**
- Automatische Erkennung von `DATABASE_URL`
- Fallback zu SQLite für Development

---

## 📊 KOSTEN-ÜBERSICHT INFOMANIAK CLOUD

| Service | Kosten/Monat | Beschreibung |
|---------|--------------|--------------|
| **Cloud VPS** | ~5-10 CHF | Basis-Paket für kleine Apps |
| **Managed Hosting** | ~10-20 CHF | Mit Support |
| **PostgreSQL** | ~5 CHF | Datenbank (falls nicht inklusive) |
| **Domain** | ~10-20 CHF/Jahr | Eigene Domain (optional) |

**GESAMT:** ~10-30 CHF/Monat

---

## ✅ NACH DEPLOYMENT

### 1. Testen:

- [ ] HTTPS funktioniert
- [ ] Login funktioniert
- [ ] Daten sind vorhanden
- [ ] Verschlüsselung funktioniert
- [ ] Backups funktionieren

### 2. Backups einrichten:

```bash
# Cronjob: Täglich um 23:00 Uhr
0 23 * * * cd /path/to/AdeaCore && /path/to/venv/bin/python manage.py daily_backup
```

### 3. Monitoring:

- Logs überwachen
- Error-Tracking einrichten (optional)
- Uptime-Monitoring einrichten

---

## 🆘 HILFE

**Detaillierte Anleitung:** Siehe `INFOMANIAK_CLOUD_DEPLOYMENT.md`

**Support:**
- Infomaniak: https://www.infomaniak.com/de/support
- AdeaTools: alexandra@adea-treuhand.ch

---

**Bereit für Deployment! 🚀**



