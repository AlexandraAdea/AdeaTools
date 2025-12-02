@echo off
REM AdeaTools - Git Push Script für Render Deployment
REM Führt alle notwendigen Git-Operationen aus

echo ========================================
echo AdeaTools - Git Push für Render
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Prüfe Git-Status...
git status
echo.
pause

echo [2/4] Füge alle Änderungen hinzu...
git add .
echo.
pause

echo [3/4] Committe Änderungen...
git commit -m "Render Deployment: Production Settings, requirements.txt, Build Commands"
echo.
pause

echo [4/4] Pushe zu GitHub...
git push origin main
echo.

echo ========================================
echo Fertig! Code wurde zu GitHub gepusht.
echo ========================================
echo.
echo Nächste Schritte:
echo 1. Gehe zu Render Dashboard
echo 2. Korrigiere Build/Start Commands
echo 3. Setze Environment-Variablen
echo 4. Starte Build
echo.
pause

