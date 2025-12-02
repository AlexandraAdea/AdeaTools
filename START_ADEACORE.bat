@echo off
REM AdeaCore Django Server starten
REM Startet die Django-App auf http://127.0.0.1:8000

cd /d "%~dp0"

echo ========================================
echo AdeaCore - Django Server starten
echo ========================================
echo.

REM Pruefe ob Django installiert ist
python -c "import django; print('Django OK')" 2>nul
if errorlevel 1 (
    echo [FEHLER] Django nicht gefunden!
    echo Bitte installieren: pip install django
    pause
    exit /b 1
)

echo Starte Django Server auf http://127.0.0.1:8000
echo.
echo Verfuegbare Routen:
echo   - Home: http://127.0.0.1:8000/
echo   - AdeaZeit: http://127.0.0.1:8000/zeit/
echo   - Mitarbeitende: http://127.0.0.1:8000/zeit/mitarbeitende/
echo   - AdeaLohn: http://127.0.0.1:8000/lohn/
echo   - AdeaDesk: http://127.0.0.1:8000/desk/
echo   - Admin: http://127.0.0.1:8000/admin/
echo.
echo Druecke Strg+C zum Beenden
echo.

REM Server starten
python manage.py runserver 8000

pause





