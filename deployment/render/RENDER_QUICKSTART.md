# ⚡ Render Quickstart - Schnellübersicht

## 🎯 5-Minuten-Deployment

### 1️⃣ Code pushen
```powershell
cd C:\AdeaTools\AdeaCore
git add .
git commit -m "Render Deployment"
git push origin main
```

### 2️⃣ Render Commands korrigieren
**Build:** `pip install -r requirements.txt && python manage.py collectstatic --noinput`  
**Start:** `gunicorn adeacore.wsgi:application --bind 0.0.0.0:$PORT`

### 3️⃣ Environment-Variablen setzen
```
DJANGO_SECRET_KEY=<generieren>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=adeacore-web.onrender.com
ADEATOOLS_ENCRYPTION_KEY=<generieren>
```

### 4️⃣ Build starten
**Manual Deploy** → **Deploy latest commit**

### 5️⃣ Migrationen ausführen
**Shell:** `python manage.py migrate`

---

## ✅ Fertig!

**URL:** `https://adeacore-web.onrender.com`

---

**Detaillierte Anleitung:** Siehe `RENDER_DEPLOYMENT_COMPLETE.md`

