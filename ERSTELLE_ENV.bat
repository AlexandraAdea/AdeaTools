@echo off
REM Erstellt .env Datei aus env.example mit neuem SECRET_KEY

echo ========================================
echo AdeaTools - .env Datei erstellen
echo ========================================
echo.

REM Prüfe ob .env bereits existiert
if exist .env (
    echo WARNUNG: .env existiert bereits!
    echo Soll die bestehende .env Datei überschrieben werden? (J/N)
    set /p overwrite=
    if /i not "%overwrite%"=="J" (
        echo Abgebrochen.
        pause
        exit /b
    )
)

REM Generiere neuen SECRET_KEY
echo Generiere neuen SECRET_KEY...
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" > temp_secret.txt
set /p NEW_SECRET_KEY=<temp_secret.txt
del temp_secret.txt

REM Kopiere env.example zu .env
echo Kopiere env.example zu .env...
copy env.example .env >nul

REM Ersetze SECRET_KEY in .env
echo Setze SECRET_KEY in .env...
powershell -Command "(Get-Content .env) -replace 'DJANGO_SECRET_KEY=.*', 'DJANGO_SECRET_KEY=%NEW_SECRET_KEY%' | Set-Content .env"

echo.
echo ========================================
echo Fertig!
echo ========================================
echo.
echo .env Datei wurde erstellt mit neuem SECRET_KEY.
echo Bitte prüfen Sie .env und passen Sie die Werte an!
echo.
pause




