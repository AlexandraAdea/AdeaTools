# 🔧 Render Build Command - WICHTIG!

## Aktueller Build Command

```
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

## Erweiterter Build Command (mit Benutzer-Erstellung)

Falls Migrationen die Benutzer nicht erstellen, fügen Sie diesen Command hinzu:

```
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py create_superuser
```

## So ändern Sie den Build Command in Render:

1. Gehen Sie zu Render → Ihr Service → Settings
2. Scrollen Sie zu "Build Command"
3. Ändern Sie den Command zu:
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py create_superuser
   ```
4. Speichern Sie die Änderungen
5. Deployen Sie erneut

## Was passiert:

1. `pip install -r requirements.txt` - Installiert Dependencies
2. `python manage.py collectstatic --noinput` - Sammelt Static Files
3. `python manage.py migrate` - Führt Migrationen aus
4. `python manage.py create_superuser` - Erstellt Benutzer aus Environment-Variablen

## Wichtig:

- Die Environment-Variablen müssen gesetzt sein:
  - `DJANGO_SUPERUSER_USERNAME`
  - `DJANGO_SUPERUSER_PASSWORD`
  - `DJANGO_USER_AI_PASSWORD`
  - `DJANGO_USER_EI_PASSWORD`

- Das Command ist idempotent: Es erstellt Benutzer nur wenn sie nicht existieren, oder aktualisiert sie wenn sie existieren.

