# 🚀 Render NEUSTART - Einfache Lösung

## Problem:
- 500-Fehler beim Login
- Alte/inkonsistente Datenbank
- Komplizierter Migrations-Prozess

## ✅ EINFACHE LÖSUNG: Datenbank zurücksetzen

### Option 1: Datenbank komplett löschen und neu erstellen (EMPFOHLEN)

**In Render Dashboard:**
1. Gehe zu **PostgreSQL-Datenbank** → **Settings**
2. Klicke auf **"Delete Database"** (⚠️ ACHTUNG: Alle Daten gehen verloren!)
3. Erstelle neue PostgreSQL-Datenbank
4. DATABASE_URL wird automatisch aktualisiert

**Dann in Render Shell:**
```bash
# 1. Migrationen ausführen (auf leere DB)
python manage.py migrate

# 2. Rollen erstellen
python manage.py init_roles

# 3. Superuser erstellen
python manage.py createsuperuser
```

**Dann:**
- Logge dich mit dem neuen Superuser ein
- Erstelle Benutzer über Django Admin
- Erfasse Daten neu

---

### Option 2: Daten von lokal migrieren

**Lokal (PowerShell):**
```powershell
cd C:\AdeaTools\AdeaCore
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > export_render.json
```

**Auf Render:**
1. Lade `export_render.json` hoch (via Render Disk oder manuell)
2. In Shell:
```bash
python manage.py migrate
python manage.py loaddata export_render.json
```

---

## 🔍 500-Fehler beheben

**Prüfe Render Logs:**
- Render Dashboard → `adeacore-web` → **Logs**
- Suche nach Fehlermeldungen

**Häufige Ursachen:**
1. Fehlende Environment-Variablen
2. Datenbank-Verbindungsfehler
3. Fehlende statische Dateien
4. Fehler in settings.py

---

## 💡 MEIN VORSCHLAG:

**Option 1 ist am einfachsten:**
1. Datenbank löschen
2. Neu erstellen
3. Migrationen ausführen
4. Superuser erstellen
5. Neu starten

**Dauert nur 5 Minuten und alles funktioniert!**

