# 🔧 Render Setup NACH erfolgreichem Build

**WICHTIG:** Diese Schritte müssen auf Render ausgeführt werden, nachdem der Build erfolgreich war!

---

## ✅ SCHRITT 1: Migration ausführen

**In Render Shell:**
```bash
python manage.py migrate
```

**Erwartete Ausgabe:**
- Alle Migrations werden angewendet
- Keine Fehler

---

## ✅ SCHRITT 2: Rollen initialisieren

**In Render Shell:**
```bash
python manage.py init_roles
```

**Erwartete Ausgabe:**
```
[OK] Rolle "AdeaZeit Admin" erstellt
[OK] Rolle "AdeaZeit Manager" erstellt
[OK] Rolle "AdeaZeit Mitarbeiter" erstellt

3 Rollen erstellt.
```

---

## ✅ SCHRITT 3: Superuser erstellen

**In Render Shell:**
```bash
python manage.py createsuperuser
```

**Folge den Anweisungen:**
- Username: (z.B. `aivanova` oder `admin`)
- Email: (optional)
- Password: (sicheres Passwort!)

**WICHTIG:** Dieser Superuser hat automatisch Admin-Rechte!

---

## ✅ SCHRITT 4: Daten migrieren (OPTIONAL)

Falls du Daten von lokal nach Render migrieren möchtest:

### Option A: Daten exportieren/importieren

**Lokal (PowerShell):**
```powershell
cd C:\AdeaTools\AdeaCore
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > export_render.json
```

**Auf Render Shell:**
```bash
# Lade export_render.json hoch (via Render Dashboard → Disk oder manuell)
python manage.py loaddata export_render.json
```

### Option B: Neu starten

- Erstelle Superuser (Schritt 3)
- Erstelle Benutzer über Django Admin
- Erfasse Daten neu

---

## ✅ SCHRITT 5: Testen

1. Öffne: `https://adeacore-web.onrender.com`
2. Logge dich mit dem Superuser ein
3. Prüfe:
   - ✅ AdeaDesk funktioniert
   - ✅ AdeaZeit funktioniert
   - ✅ AdeaLohn funktioniert (falls aktiviert)
   - ✅ CRM-Features sind sichtbar

---

## 🔍 FEHLERBEHEBUNG

### Problem: "No such table"
**Lösung:** Migration nicht ausgeführt → Schritt 1 wiederholen

### Problem: "Group does not exist"
**Lösung:** Rollen nicht initialisiert → Schritt 2 wiederholen

### Problem: "Cannot login"
**Lösung:** Superuser nicht erstellt → Schritt 3 wiederholen

### Problem: "AdeaLohn nicht sichtbar"
**Lösung:** Prüfe ob `can_access_adelohn` in Context Processor korrekt ist

---

## 📋 CHECKLISTE

- [ ] Migration ausgeführt (`python manage.py migrate`)
- [ ] Rollen initialisiert (`python manage.py init_roles`)
- [ ] Superuser erstellt (`python manage.py createsuperuser`)
- [ ] Login funktioniert
- [ ] AdeaDesk sichtbar und funktioniert
- [ ] AdeaZeit sichtbar und funktioniert
- [ ] AdeaLohn sichtbar (falls aktiviert)
- [ ] CRM-Features sichtbar

---

**Nach diesen Schritten sollte alles funktionieren! 🎉**

