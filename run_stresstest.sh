#!/bin/bash
# VDE Messwand - Stresstest Quick-Start Script

set -e  # Exit on error

echo "======================================================"
echo "VDE MESSWAND - STRESSTEST"
echo "======================================================"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Prüfe ob Server läuft
echo -e "\n${BLUE}[1/4]${NC} Prüfe ob Server läuft..."
if curl -s http://localhost:8000 > /dev/null; then
    echo -e "${GREEN}✅ Server läuft auf Port 8000${NC}"
else
    echo -e "${RED}❌ Server läuft NICHT!${NC}"
    echo -e "${YELLOW}Soll der Server gestartet werden? (j/n)${NC}"
    read -r START_SERVER

    if [ "$START_SERVER" = "j" ] || [ "$START_SERVER" = "J" ]; then
        echo "Starte Server mit Gunicorn..."
        cd /home/vde/vde-messwand
        gunicorn -b 0.0.0.0:8000 app:app --daemon
        sleep 3

        if curl -s http://localhost:8000 > /dev/null; then
            echo -e "${GREEN}✅ Server erfolgreich gestartet${NC}"
        else
            echo -e "${RED}❌ Server-Start fehlgeschlagen${NC}"
            exit 1
        fi
    else
        echo "Bitte starte den Server manuell:"
        echo "  gunicorn -b 0.0.0.0:8000 app:app"
        exit 1
    fi
fi

# Prüfe Dependencies
echo -e "\n${BLUE}[2/4]${NC} Prüfe Python-Dependencies..."

if python3 -c "import requests" 2>/dev/null; then
    echo -e "${GREEN}✅ requests installiert${NC}"
else
    echo -e "${YELLOW}⚠️  requests fehlt - installiere...${NC}"
    pip3 install requests
fi

# Prüfe ob Selenium gebraucht wird
SELENIUM_AVAILABLE=false
if python3 -c "import selenium" 2>/dev/null; then
    SELENIUM_AVAILABLE=true
    echo -e "${GREEN}✅ selenium installiert${NC}"
else
    echo -e "${YELLOW}⚠️  selenium nicht installiert (optional für GUI-Tests)${NC}"
fi

# Test-Auswahl
echo -e "\n${BLUE}[3/4]${NC} Wähle Test-Typ:"
echo "  1) Simple API-Test (schnell, empfohlen)"
echo "  2) GUI-Test mit Selenium (benötigt Chromium)"
echo ""
read -p "Eingabe (1 oder 2): " TEST_TYPE

cd /home/vde/vde-messwand

if [ "$TEST_TYPE" = "1" ]; then
    echo -e "\n${BLUE}[4/4]${NC} Starte Simple Stresstest..."
    echo "======================================================"
    python3 stress_test_simple.py

elif [ "$TEST_TYPE" = "2" ]; then
    if [ "$SELENIUM_AVAILABLE" = false ]; then
        echo -e "${RED}❌ Selenium nicht installiert!${NC}"
        echo "Installiere mit: pip3 install -r requirements_test.txt"
        echo "Und: sudo apt-get install chromium-chromedriver"
        exit 1
    fi

    # Prüfe Chromium
    if ! command -v chromium-browser &> /dev/null && ! command -v chromium &> /dev/null; then
        echo -e "${YELLOW}⚠️  Chromium nicht gefunden${NC}"
        echo "Installiere mit: sudo apt-get install chromium-browser chromium-chromedriver"
        exit 1
    fi

    echo -e "\n${BLUE}[4/4]${NC} Starte GUI Stresstest..."
    echo "======================================================"
    python3 stress_test.py

else
    echo -e "${RED}❌ Ungültige Eingabe${NC}"
    exit 1
fi

# Zeige Fehler-Log falls vorhanden
echo ""
echo "======================================================"
if [ -f "stress_test_errors.json" ]; then
    ERROR_COUNT=$(python3 -c "import json; print(json.load(open('stress_test_errors.json'))['total_errors'])" 2>/dev/null || echo "?")
    if [ "$ERROR_COUNT" != "0" ]; then
        echo -e "${RED}⚠️  Fehler gefunden: stress_test_errors.json${NC}"
        echo "Zeige erste Fehler:"
        head -n 30 stress_test_errors.json
    else
        echo -e "${GREEN}✅ KEINE FEHLER!${NC}"
    fi
fi

if [ -f "stress_test_simple_errors.json" ]; then
    ERROR_COUNT=$(python3 -c "import json; print(len(json.load(open('stress_test_simple_errors.json'))))" 2>/dev/null || echo "?")
    if [ "$ERROR_COUNT" != "0" ]; then
        echo -e "${RED}⚠️  Fehler gefunden: stress_test_simple_errors.json${NC}"
    else
        echo -e "${GREEN}✅ KEINE FEHLER!${NC}"
    fi
fi

echo "======================================================"
echo -e "${GREEN}Test abgeschlossen!${NC}"
