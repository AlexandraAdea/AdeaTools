@echo off
REM Erstellt Benutzer-Zugänge für Mitarbeitende
REM Benutzerfreundlich und intuitiv

cd /d "%~dp0"

echo ========================================
echo AdeaZeit - Benutzer-Zugange erstellen
echo ========================================
echo.

python manage.py create_user_access

echo.
pause




