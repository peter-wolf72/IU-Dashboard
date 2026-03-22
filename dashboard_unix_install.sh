#!/bin/bash
# Wechselt in das Verzeichnis, in dem die Datei liegt, 
# egal von wo aus sie aufgerufen wurde.
cd "$(dirname "$0")"
# Farben für eine bessere Lesbarkeit
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Student Dashboard - Installationsassistent ===${NC}"
echo "Dieses Skript bereitet die Laufzeitumgebung für das Dashboard vor."
echo "GitHub Repository: https://github.com/peter-wolf72/IU-Dashboard"
echo "------------------------------------------------------------"

# 1. Verzeichnis-Abfrage
echo -e "${GREEN}[Schritt 1/6] Verzeichniswahl${NC}"
echo "Das Dashboard kann im aktuellen Ordner oder in einem neuen Verzeichnis installiert werden."
read -p "Möchtest du im aktuellen Verzeichnis installieren? (j) oder Pfad angeben: " TARGET_DIR

if [ "$TARGET_DIR" != "j" ] && [ "$TARGET_DIR" != "" ]; then
    echo "Erstelle Verzeichnis: $TARGET_DIR..."
    mkdir -p "$TARGET_DIR"
    cd "$TARGET_DIR" || exit
else
    echo "Installation verbleibt im aktuellen Verzeichnis."
fi

# 2.1 Prüfung auf curl
echo -ne "\n${GREEN}[Prüfung] Suche nach curl...${NC}"

if ! command -v curl &> /dev/null; then
    echo -e "\n${BLUE}curl wurde nicht gefunden.${NC}"
    echo "Versuche automatische Installation..."

    # Abfrage des Paketmanagers für die automatische Installation
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y curl
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y curl
    elif command -v brew &> /dev/null; then
        brew install curl
    else
        echo -e "${BLUE}Automatisches Setup nicht möglich.${NC}"
        echo "Bitte installiere curl manuell mit folgendem Befehl:"
        echo -e "${GREEN}sudo apt install curl${NC}  (für Ubuntu/Debian)"
        echo -e "${GREEN}brew install curl${NC}      (für macOS)"
        exit 1
    fi
else
    echo " OK."
fi

# 2.2 Dateien laden (via curl)
echo -e "\n${GREEN}[Schritt 2/6] Datenübertragung${NC}"
echo "Lade die benötigten Programmmodule direkt von GitHub..."
REPO_URL="https://raw.githubusercontent.com/peter-wolf72/IU-Dashboard/main"
FILES=("main.py" "model.py" "view.py" "controller.py" "repositories.py" "services.py" "database.py" "dashboard.db" "requirements.txt")

for file in "${FILES[@]}"; do
    echo "  -> Lade $file..."
    curl -L -O -s "$REPO_URL/$file"
done

# 3. Systemprüfung: Python & Tkinter (Schritt 3 aus dem Original) 
echo -e "\n${GREEN}[Schritt 3/6] Systemprüfung (Python & GUI-Support)${NC}" 

# Installation von Python und dem oft fehlenden Tkinter (python3-tk)
if ! command -v python3 &> /dev/null || ! python3 -c "import tkinter" &> /dev/null; then
    echo "Python3 oder Tkinter (GUI) wurde nicht gefunden. Installiere nach..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y python3 python3-venv python3-pip python3-tk 
    elif command -v brew &> /dev/null; then
        brew install python tcl-tk
    else
        echo "Bitte installiere Python3 und python3-tk manuell."
        exit 1
    fi
fi

# Version prüfen
if ! command -v python3 &> /dev/null; then
    echo "FEHLER: Python konnte nicht installiert werden."
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Gefunden: Python $PY_VERSION"

REQUIRED_MAJOR=3
REQUIRED_MINOR=10

MAJOR=$(echo $PY_VERSION | cut -d. -f1)
MINOR=$(echo $PY_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt "$REQUIRED_MAJOR" ] || { [ "$MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$MINOR" -lt "$REQUIRED_MINOR" ]; }; then
    echo "FEHLER: Python 3.10+ erforderlich."
    exit 1
fi

echo "Python OK."


# 4. Virtuelle Umgebung (VENV)
echo -e "\n${GREEN}[Schritt 4/6] Isolation der Umgebung${NC}"
echo "Erstelle eine virtuelle Umgebung (venv), um Systemkonflikte zu vermeiden..."
python3 -m venv venv
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    echo "Installiere Abhängigkeiten aus requirements.txt..."
    pip install -r requirements.txt --quiet
else
    echo "Keine requirements.txt gefunden, überspringe Installation externer Pakete."
fi
echo "Umgebung erfolgreich vorbereitet."

# 5. Start-Datei lokal erzeugen ---
echo -e "\n${GREEN}[Schritt 5/6] Erstelle Start-Datei...${NC}"

# Prüfen, ob Mac (für die Endung .command)
if [[ "$OSTYPE" == "darwin"* ]]; then
    START_FILE="dashboard_start.command"
else
    START_FILE="dashboard_start.sh"
fi

# Die Datei direkt "hinschreiben"
cat <<EOF > "$START_FILE"
#!/bin/bash
cd "\$(dirname "\$0")"
source venv/bin/activate
python3 main.py
EOF

# Ausführbar machen
chmod +x "$START_FILE"
echo "Datei $START_FILE wurde erfolgreich erstellt."

# 6. Abschluss und Start
echo -e "\n${GREEN}[Schritt 6/6] Abschluss${NC}"
echo "------------------------------------------------------------"
echo "Die Installation ist abgeschlossen."
read -p "Möchtest du das Student Dashboard jetzt starten? (j/n): " START_CHOICE

if [ "$START_CHOICE" == "j" ]; then
    echo "Starte Anwendung..."
    python3 main.py
else
    echo -e "\nDu kannst das Programm jederzeit per Doppelklick auf die"
    echo -e "Datei '$START_FILE' im Installationsordner starten."
fi