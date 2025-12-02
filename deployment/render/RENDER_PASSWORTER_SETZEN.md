# 🔐 Passwörter für Render-Benutzer setzen

## Problem:
Benutzer haben kein Passwort oder Passwort ist unbekannt.

## ✅ Lösung: Passwörter in Render Shell setzen

**In Render Shell:**
```bash
python manage.py shell
```

**Dann in Python Shell:**

```python
from django.contrib.auth.models import User

# Setze Passwort für Aivanova
aivanova = User.objects.get(username="Aivanova")
aivanova.set_password("DEIN_SICHERES_PASSWORT_HIER")
aivanova.save()
print("✅ Passwort für Aivanova gesetzt")

# Setze Passwort für ai
try:
    ai_user = User.objects.get(username="ai")
    ai_user.set_password("DEIN_PASSWORT_HIER")
    ai_user.save()
    print("✅ Passwort für ai gesetzt")
except User.DoesNotExist:
    print("⚠️ Benutzer 'ai' existiert nicht")

# Setze Passwort für ei
try:
    ei_user = User.objects.get(username="ei")
    ei_user.set_password("DEIN_PASSWORT_HIER")
    ei_user.save()
    print("✅ Passwort für ei gesetzt")
except User.DoesNotExist:
    print("⚠️ Benutzer 'ei' existiert nicht")

# Zeige alle Benutzer
print("\n=== ALLE BENUTZER ===")
for user in User.objects.all():
    print(f"{user.username}: {user.email or 'keine Email'}")

exit()
```

---

## 🔑 Passwort-Generierung (optional)

Falls du sichere Passwörter generieren möchtest:

```python
import secrets
import string

def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for i in range(length))

# Generiere Passwort
password = generate_password(12)
print(f"Generiertes Passwort: {password}")

# Setze für Benutzer
user = User.objects.get(username="Aivanova")
user.set_password(password)
user.save()
print(f"✅ Passwort für {user.username} gesetzt: {password}")
```

---

## ⚠️ WICHTIG:

- **Sichere Passwörter verwenden!** (mindestens 12 Zeichen)
- **Passwörter sicher aufbewahren!**
- **Nicht in Git committen!**

---

## 📝 Schnell-Version:

```python
from django.contrib.auth.models import User

# Setze Passwort für alle Benutzer
for user in User.objects.all():
    user.set_password("TempPass123!")  # ÄNDERE DIESES PASSWORT!
    user.save()
    print(f"✅ Passwort für {user.username} gesetzt")

exit()
```

