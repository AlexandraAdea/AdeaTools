# 🚀 Render-Konfiguration für AdeaTools

## ✅ SCHRITT 2: Render Build & Start Commands korrigieren

### Aktuelle (FALSCHE) Commands:
```
Build Command: AdeaCore/ $ pip install -r requirements.txt && python manage.py collectst...
Start Command: AdeaCore/ $ gunicorn adeacore.wsgi:application
```

### ✅ Korrekte Commands (für Root Directory = `AdeaCore`):

**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command:**
```bash
gunicorn adeacore.wsgi:application --bind 0.0.0.0:$PORT
```

---

## 📋 Was du in Render machen musst:

1. **Gehe zu Render Dashboard** → `adeacore-web` → **Settings**
2. **Klicke auf "Build & Deploy"** (rechts im Menü)
3. **Ändere die Commands:**

   **Build Command:**
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput
   ```
   
   **Start Command:**
   ```
   gunicorn adeacore.wsgi:application --bind 0.0.0.0:$PORT
   ```

4. **Klicke auf "Save Changes"**

---

## ⚠️ WICHTIG:

- **Root Directory** muss `AdeaCore` sein (ist bereits korrekt)
- **$PORT** ist automatisch von Render gesetzt - NICHT ändern!
- `--noinput` verhindert Fragen bei collectstatic

---

## 🔄 Nächster Schritt:

Nach dem Speichern wird Render automatisch einen neuen Build starten.

