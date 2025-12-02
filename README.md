# AdeaTools - AdeaCore

**Zentrale Django-Anwendung für AdeaTools Suite**

---

## 🚀 Schnellstart

### Lokale Entwicklung

```powershell
# Server starten
.\scripts\start.bat

# Oder manuell:
python manage.py runserver
```

### Setup (Erstinstallation)

```powershell
# Migrationen ausführen
.\scripts\setup.bat

# Oder manuell:
python manage.py migrate
python manage.py createsuperuser
python manage.py init_roles
```

---

## 📁 Projektstruktur

```
AdeaCore/
├── adeacore/              # Haupt-App
│   ├── settings/          # Settings-Struktur
│   │   ├── __init__.py   # Lädt je nach DEBUG
│   │   ├── base.py       # Gemeinsame Settings
│   │   ├── local.py      # Lokale Development
│   │   └── production.py # Production (Render)
│   └── ...
├── adeadesk/             # CRM-Modul
├── adeazeit/             # Zeiterfassung
├── adealohn/             # Lohnabrechnung
├── deployment/
│   └── render/           # Render-Deployment-Dokumentation
├── docs/
│   └── archive/          # Archivierte Dokumentation
├── fixtures/              # Test-Daten
├── scripts/               # Utility-Scripts
│   ├── start.bat         # Server starten
│   └── setup.bat         # Setup & Migrationen
└── .env                   # Environment-Variablen (nicht im Git)
```

---

## ⚙️ Settings-Struktur

Die Settings sind jetzt getrennt nach Umgebung:

- **Lokal (`DEBUG=True`)**: `adeacore.settings.local`
  - SQLite Datenbank
  - File-Logging
  - Keine Production-Security

- **Production (`DEBUG=False`)**: `adeacore.settings.production`
  - PostgreSQL (aus `DATABASE_URL`)
  - WhiteNoise für statische Dateien
  - Production-Security aktiviert

Die richtige Settings-Datei wird automatisch geladen basierend auf `DJANGO_DEBUG` Environment-Variable.

---

## 🔐 Environment-Variablen

Erstelle `.env` Datei im Root-Verzeichnis:

```env
# Verschlüsselungsschlüssel (WICHTIG: Muss gleich bleiben!)
ADEATOOLS_ENCRYPTION_KEY=dein-schlüssel-hier

# Django Settings (optional)
DJANGO_SECRET_KEY=dein-secret-key
DJANGO_DEBUG=True          # False für Production
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (nur für Production)
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

---

## 📚 Dokumentation

- **Render Deployment**: `deployment/render/`
- **Archivierte Docs**: `docs/archive/`
- **Sicherheit**: Siehe `README_SECURITY.md`

---

## 🛠️ Entwicklung

### Migrationen

```powershell
python manage.py makemigrations
python manage.py migrate
```

### Superuser erstellen

```powershell
python manage.py createsuperuser
```

### Rollen initialisieren

```powershell
python manage.py init_roles
```

---

## 📦 Module

- **AdeaDesk**: CRM-System für Mandantenverwaltung
- **AdeaZeit**: Zeiterfassung für Mitarbeitende
- **AdeaLohn**: Lohnabrechnung und Sozialversicherungen

---

## 🔄 Deployment

Siehe `deployment/render/` für Render-Deployment-Anleitung.

---

**Version:** 2.0  
**Django:** 5.1.2  
**Python:** 3.11+

