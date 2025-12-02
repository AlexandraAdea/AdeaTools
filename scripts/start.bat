@echo off
REM AdeaTools - Server starten
echo ========================================
echo   AdeaTools - Development Server
echo ========================================
echo.

cd /d "%~dp0\.."

REM Prüfe ob Port bereits belegt
netstat -ano | findstr ":8000" >nul
if %errorlevel% == 0 (
    echo WARNUNG: Port 8000 ist bereits belegt!
    echo Bitte beende den anderen Prozess.
    pause
    exit /b 1
)

echo Starte Django Development Server...
echo.
echo Browser: http://127.0.0.1:8000
echo.
echo Zum Beenden: Strg+C
echo.

python manage.py runserver

pause

