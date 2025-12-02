@echo off
REM AdeaTools - Setup & Migrationen
echo ========================================
echo   AdeaTools - Setup
echo ========================================
echo.

cd /d "%~dp0\.."

echo Fuehre Migrationen aus...
python manage.py migrate

echo.
echo Setup abgeschlossen!
echo.
echo Weitere Optionen:
echo   - Superuser erstellen: python manage.py createsuperuser
echo   - Rollen initialisieren: python manage.py init_roles
echo   - Daten importieren: python manage.py loaddata fixtures/test_data.json
echo.

pause

