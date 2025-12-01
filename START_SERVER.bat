@echo off
REM Einfaches Start-Skript für den Django-Server
cd /d "%~dp0"

echo ========================================
echo AdeaCore Django Server starten
echo ========================================
echo.

REM Prüfe ob .env existiert, sonst erstelle sie
if not exist .env (
    echo .env-Datei fehlt - erstelle aus env.example...
    copy env.example .env >nul
    echo .env-Datei erstellt!
    echo.
)

echo Starte Django Server auf http://127.0.0.1:8000
echo.
echo Druecke Strg+C zum Beenden
echo.

python manage.py runserver 127.0.0.1:8000

pause

