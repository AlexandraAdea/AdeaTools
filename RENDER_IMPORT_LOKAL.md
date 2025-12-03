# Daten von lokal zu Render importieren

## Problem
Die Datei `fixtures/production_data_utf8.json` ist auf GitHub, aber nicht auf Render verfügbar.

## Lösung: Direkter Import via Copy-Paste

### Schritt 1: Daten von GitHub holen (nach 5-10 Minuten)

```bash
# In Render Shell
wget https://raw.githubusercontent.com/AlexandraAdea/AdeaTools/main/AdeaCore/fixtures/production_data_utf8.json -O /tmp/data.json

python manage.py loaddata /tmp/data.json
```

### Schritt 2: ODER neuen Deploy triggern

Damit `fixtures/` auf Render verfügbar wird:
1. Render Dashboard → Web Service
2. "Manual Deploy" → "Deploy latest commit"
3. Warten auf Build
4. Dann: `python manage.py loaddata fixtures/production_data_utf8.json`

### Schritt 3: ODER Passwörter für bestehende User setzen

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User

# Setze Passwörter für alle User
for user in User.objects.all():
    user.set_password("DEIN-PASSWORT")
    user.save()
    print(f"✅ {user.username}")

exit()
```

Dann mit den bestehenden 30 importierten Objekten arbeiten.

