# 🔐 Render Benutzer-Setup - WICHTIG!

## ⚠️ Problem

**Lokale Benutzer existieren NICHT in der Render-Datenbank!**

- Lokale SQLite-Datenbank enthält: Aivanova, ai, ei
- Render PostgreSQL-Datenbank ist **LEER** nach Deployment
- Benutzerdaten werden **NICHT** in Git übertragen

## ✅ Lösung: Environment-Variablen in Render setzen

### Schritt 1: Gehen Sie zu Render → Ihr Service → Environment

### Schritt 2: Fügen Sie diese Environment-Variablen hinzu:

```
DJANGO_SUPERUSER_USERNAME=Aivanova
DJANGO_SUPERUSER_EMAIL=alexandra@adea-treuhand.ch
DJANGO_SUPERUSER_PASSWORD=<Ihr-sicheres-Passwort-für-Aivanova>

DJANGO_USER_AI_PASSWORD=<Ihr-sicheres-Passwort-für-ai>
DJANGO_USER_EI_PASSWORD=<Ihr-sicheres-Passwort-für-ei>
```

### Schritt 3: Deployen Sie erneut

Nach dem Deploy werden die Migrationen ausgeführt:
- `0020_create_initial_superuser` erstellt die Benutzer
- `0021_ensure_users_exist` stellt sicher, dass sie existieren
- `0022_init_roles_and_assign_users` weist AdeaZeit-Rollen zu

## 🔍 Prüfen ob es funktioniert hat

### In Render Build-Logs suchen nach:
```
Operations to perform:
  Apply all migrations: ...
Running migrations:
  ...
  Applying adeacore.0020_create_initial_superuser... OK
  Applying adeacore.0021_ensure_users_exist... OK
  Applying adeazeit.0022_init_roles_and_assign_users... OK
```

### Falls Migrationen fehlschlagen:
- Prüfen Sie, ob alle Environment-Variablen gesetzt sind
- Prüfen Sie, ob die Passwörter nicht leer sind
- Prüfen Sie die Build-Logs auf Fehlermeldungen

## 🚨 WICHTIG: Sicherheit

- **KEINE** Passwörter im Code!
- **NUR** über Environment-Variablen
- Passwörter werden in Render verschlüsselt gespeichert

## 📝 Alternative: Manuell über Django Admin

Falls Migrationen nicht funktionieren:

1. Melden Sie sich über `/admin/login/` an (falls bereits ein Superuser existiert)
2. Oder verwenden Sie Render Shell (nur auf bezahlten Plänen):
   ```bash
   python manage.py createsuperuser
   ```

## ✅ Nach erfolgreichem Setup

- Login über `/zeit/login/` sollte funktionieren
- Login über `/admin/login/` sollte funktionieren
- Admin-Dashboard unter `/admin-dashboard/` sollte erreichbar sein

