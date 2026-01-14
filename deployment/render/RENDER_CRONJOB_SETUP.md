# 🕐 Render Cron Job Setup - Aufgaben-Archivierung

## ✅ Automatische Archivierung nach 7 Tagen

Die Aufgaben-Archivierung läuft jetzt automatisch täglich um 02:00 UTC (03:00 MEZ / 04:00 MESZ).

---

## 📋 Setup in Render Dashboard

### Option 1: Über render.yaml (Empfohlen)

Die `render.yaml` Datei ist bereits erstellt und wird automatisch von Render erkannt.

**Was zu tun ist:**
1. Gehe zu Render Dashboard
2. Klicke auf "New" → "Cron Job"
3. Render erkennt automatisch die `render.yaml` und fragt, ob du den Cron Job erstellen möchtest
4. Klicke auf "Create Cron Job"

**Oder manuell:**

1. Gehe zu Render Dashboard → **New** → **Cron Job**
2. **Name:** `archive-completed-tasks`
3. **Schedule:** `0 2 * * *` (täglich um 02:00 UTC)
4. **Command:** `cd AdeaCore && python manage.py archive_completed_tasks`
5. **Environment:** Python 3.11
6. **Environment Variables:**
   - `DJANGO_SETTINGS_MODULE` = `adeacore.settings.production`
   - Alle anderen Variablen vom Web-Service übernehmen (Database URL, etc.)

---

## 🧪 Testen

### Lokal testen:
```bash
cd AdeaCore
python manage.py archive_completed_tasks --dry-run
```

### Auf Render testen:
1. Gehe zu Render Dashboard → Cron Job → "archive-completed-tasks"
2. Klicke auf "Run Now" (manueller Test)
3. Prüfe die Logs

---

## 📊 Was passiert?

- **Täglich um 02:00 UTC** wird das Command ausgeführt
- Findet alle Aufgaben mit:
  - `status = 'ERLEDIGT'`
  - `erledigt_am < heute - 7 Tage`
  - `archiviert = False`
- Setzt `archiviert = True` für diese Aufgaben
- Aufgaben verschwinden aus der normalen Liste
- Sind weiterhin im Archiv sichtbar (`/zeit/aufgaben/archiv/`)

---

## 🔍 Logs prüfen

1. Gehe zu Render Dashboard → Cron Job → "archive-completed-tasks"
2. Klicke auf "Logs"
3. Du siehst:
   - `✅ X Aufgabe(n) erfolgreich archiviert.` (bei Erfolg)
   - `Keine Aufgaben zum Archivieren gefunden.` (wenn nichts zu tun ist)

---

## ⚙️ Schedule anpassen

Die Schedule ist in `render.yaml` definiert:
```yaml
schedule: "0 2 * * *"  # Täglich um 02:00 UTC
```

**Cron-Format:** `Minute Stunde Tag Monat Wochentag`

**Beispiele:**
- `0 2 * * *` = Täglich um 02:00 UTC
- `0 3 * * *` = Täglich um 03:00 UTC
- `0 2 * * 1` = Jeden Montag um 02:00 UTC
- `0 */6 * * *` = Alle 6 Stunden

**UTC vs MEZ/MESZ:**
- UTC = Coordinated Universal Time
- MEZ (Winter) = UTC + 1 Stunde
- MESZ (Sommer) = UTC + 2 Stunden

---

## ✅ Fertig!

Nach dem Setup läuft die Archivierung automatisch. Keine weitere Aktion nötig!



