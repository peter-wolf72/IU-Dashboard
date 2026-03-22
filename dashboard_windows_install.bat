@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ============================================================
REM  Student Dashboard - Installationsassistent (Windows Batch)
REM  Repo: https://github.com/peter-wolf72/IU-Dashboard
REM ============================================================

echo "=== Student Dashboard - Installationsassistent ==="
echo "Dieses Skript bereitet die Laufzeitumgebung fuer das Dashboard vor."
echo "GitHub Repository: https://github.com/peter-wolf72/IU-Dashboard"
echo "------------------------------------------------------------"

REM ============================================================
REM  Schritt 0/4: Python-Pruefung (MUSS vorhanden sein)
REM ============================================================
echo.
echo "[Schritt 0/4] Systempruefung (Python 3.10+ erforderlich)"

where python >nul 2>nul
if errorlevel 1 (
    echo "FEHLER: Python wurde nicht gefunden."
    echo "Bitte installiere Python 3.10 oder hoeher und achte darauf, dass 'Add Python to PATH' aktiviert ist."
    echo "Download: https://www.python.org/downloads/windows/"
    echo.
    pause
    exit /b 1
)

python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 (
    for /f "delims=" %%V in ('python --version 2^>^&1') do set "PY_VERSION=%%V"
    echo "FEHLER: Python 3.10+ erforderlich. Gefunden: %PY_VERSION%"
    echo "Bitte installiere Python 3.10 oder hoeher."
    echo "Download: https://www.python.org/downloads/windows/"
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%V in ('python --version 2^>^&1') do set "PY_VERSION=%%V"
echo "OK: %PY_VERSION%"

REM --- Prüfung auf Tkinter (GUI-Support) ---
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo.
    echo "FEHLER: Tkinter (GUI-Bibliothek) wurde nicht gefunden."
    echo "Dies passiert meist, wenn Python ohne 'tcl/tk' installiert wurde."
    echo "Bitte installiere Python neu und aktiviere 'tcl/tk and IDLE'."
    pause
    exit /b 1
)
echo "OK: Tkinter ist einsatzbereit."

REM 1) Verzeichnis-Abfrage
echo.
echo [Schritt 1/4] Verzeichniswahl
echo Das Dashboard kann im aktuellen Ordner oder in einem neuen Verzeichnis installiert werden.
set "TARGET_DIR="
set /p TARGET_DIR=Im aktuellen Verzeichnis installieren? (j) oder Pfad angeben: 

if /I not "%TARGET_DIR%"=="j" if not "%TARGET_DIR%"=="" (
    echo Erstelle Verzeichnis: "%TARGET_DIR%"...
    REM Erstellt das Verzeichnis und alle Unterverzeichnisse
    mkdir "%TARGET_DIR%" 2>nul
    
    REM Prüfen, ob das Verzeichnis jetzt existiert (egal ob neu oder schon da)
    if not exist "%TARGET_DIR%" (
        echo FEHLER: Verzeichnis konnte nicht erstellt werden oder Pfad ist ungültig.
        pause
        goto :EOF
    )
    cd /d "%TARGET_DIR%"
) else (
    echo Installation verbleibt im aktuellen Verzeichnis.
)

REM 2) Dateien laden (via curl)
echo.
echo "[Schritt 2/4] Datenuebertragung"
echo "Lade die benoetigten Programmmodule direkt von GitHub..."

set "REPO_URL=https://raw.githubusercontent.com/peter-wolf72/IU-Dashboard/main"
set "FILES=main.py model.py view.py controller.py repositories.py services.py database.py dashboard.db requirements.txt"

for %%F in (%FILES%) do (
    echo "  -> Lade %%F..."
    curl -L -s -o "%%F" "%REPO_URL%/%%F"
    if errorlevel 1 (
        echo "FEHLER: Download fehlgeschlagen fuer %%F"
        goto :EOF
    )
)

REM 3) Virtuelle Umgebung (VENV)
echo.
echo "[Schritt 3/4] Isolation der Umgebung"
echo "Erstelle eine virtuelle Umgebung (venv), um Systemkonflikte zu vermeiden..."

python -m venv venv
if errorlevel 1 (
    echo "FEHLER: Konnte venv nicht erstellen."
    goto :EOF
)

call venv\Scripts\activate.bat

if exist requirements.txt (
    echo "Installiere Abhaengigkeiten aus requirements.txt..."
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo "FEHLER: pip-Installation fehlgeschlagen."
        goto :EOF
    )
) else (
    echo "Keine requirements.txt gefunden, ueberspringe Installation externer Pakete."
)

echo "Umgebung erfolgreich vorbereitet."

REM --- Start-Datei für Windows erzeugen ---
echo "Erstelle Start-Datei dashboard_start.bat..."
(
echo @echo off
echo cd /d "%%~dp0"
echo start "" .\venv\Scripts\pythonw.exe main.py
) > dashboard_start.bat

REM 4) Abschluss und Start
echo.
echo "[Schritt 4/4] Abschluss"
echo "------------------------------------------------------------"
echo "Die Installation ist abgeschlossen."
echo "Es wurde eine Schnellstart-Datei 'dashboard_start.bat' erstellt."
echo.
set "START_CHOICE="
set /p START_CHOICE=Moechtest du das Student Dashboard jetzt starten? (j/n): 

if /I "%START_CHOICE%"=="j" (
    echo "Starte Anwendung..."
    start "" .\venv\Scripts\pythonw.exe main.py
) else (
    echo.
    echo "Du kannst das Programm jederzeit per Doppelklick auf die"
    echo "Datei 'dashboard_start.bat' im Installationsordner starten."
)

endlocal