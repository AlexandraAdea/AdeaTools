# 🔐 Render Environment-Variablen

## 📋 Notwendige Variablen für Render

### 1. **DJANGO_SECRET_KEY**
**Beschreibung:** Django Secret Key für Session-Verschlüsselung  
**Wichtig:** Muss einzigartig und geheim sein!

**Generieren:**
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Beispiel:**
```
DJANGO_SECRET_KEY=django-insecure-abc123xyz789...
```

---

### 2. **DJANGO_DEBUG**
**Beschreibung:** Debug-Modus (NUR für Development!)  
**Wert:** `False` für Production

**Setzen:**
```
DJANGO_DEBUG=False
```

---

### 3. **DJANGO_ALLOWED_HOSTS**
**Beschreibung:** Erlaubte Domains für die Anwendung  
**Wert:** Deine Render-URL

**Setzen:**
```
DJANGO_ALLOWED_HOSTS=adeacore-web.onrender.com
```

**Hinweis:** Wenn du eine Custom Domain hast, füge beide hinzu:
```
DJANGO_ALLOWED_HOSTS=adeacore-web.onrender.com,deine-domain.ch
```

---

### 4. **ADEATOOLS_ENCRYPTION_KEY**
**Beschreibung:** Verschlüsselungsschlüssel für sensible Daten (AES-256)  
**Wichtig:** Muss einzigartig und geheim sein!

**Generieren:**
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Beispiel:**
```
ADEATOOLS_ENCRYPTION_KEY=gAAAAABl...
```

---

### 5. **DATABASE_URL** (Automatisch)
**Beschreibung:** PostgreSQL-Verbindungs-URL  
**Wert:** Wird automatisch von Render gesetzt, wenn PostgreSQL-Datenbank erstellt wird

**NICHT manuell setzen!** Render setzt diese Variable automatisch.

---

## 🚀 In Render setzen

1. Gehe zu: **Dashboard** → **adeacore-web** → **Environment**
2. Klicke auf **"+ Add Environment Variable"**
3. Füge jede Variable einzeln hinzu
4. Klicke auf **"Save Changes"**

---

## ⚠️ WICHTIG

- **NIEMALS** Secret Keys in Git committen!
- **NIEMALS** Secret Keys teilen!
- **IMMER** neue Keys für Production generieren!
- **IMMER** `DJANGO_DEBUG=False` für Production!

---

## 🔄 Keys neu generieren

Falls du die Keys neu generieren musst:

**DJANGO_SECRET_KEY:**
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**ADEATOOLS_ENCRYPTION_KEY:**
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**WICHTIG:** Wenn du `ADEATOOLS_ENCRYPTION_KEY` änderst, sind alle verschlüsselten Daten unlesbar!  
Nur ändern, wenn du die Daten neu eingeben kannst.

