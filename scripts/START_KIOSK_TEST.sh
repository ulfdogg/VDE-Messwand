#!/bin/bash
# VDE Messwand - Kiosk Test Quick-Start

echo "======================================================"
echo "🖥️  VDE MESSWAND - KIOSK SIMULATION"
echo "======================================================"
echo ""
echo "IP-Adresse: 10.100.72.191:8000"
echo "Display: Raspberry Pi Display (:0)"
echo ""
echo "======================================================"
echo ""
echo "Dieser Test zeigt den Browser IM VOLLBILD auf dem"
echo "Pi-Display, genau wie ein echter Benutzer am Kiosk."
echo ""
echo "======================================================"
echo ""

# Prüfe DISPLAY
if [ -z "$DISPLAY" ]; then
    echo "⚙️  Setze DISPLAY=:0"
    export DISPLAY=:0
fi

# Prüfe Server
echo "🔍 Prüfe ob Server läuft..."
if curl -s http://10.100.72.191:8000 > /dev/null; then
    echo "✅ Server läuft!"
else
    echo "❌ Server läuft NICHT auf 10.100.72.191:8000"
    echo ""
    echo "Starte den Server zuerst:"
    echo "  gunicorn -b 10.100.72.191:8000 app:app"
    echo ""
    exit 1
fi

echo ""
echo "======================================================"
echo "WÄHLE TEST-MODUS:"
echo "======================================================"
echo ""
echo "  1) VISUAL TEST - Mit Screenshots"
echo "     → Browser im Vollbild auf Display"
echo "     → Macht automatisch Screenshots"
echo "     → Gut zum Debuggen"
echo ""
echo "  2) KIOSK SIMULATOR - Wie echter Benutzer"
echo "     → Realistische Wartezeiten"
echo "     → Verschiedene Szenarien"
echo "     → Continuous-Mode verfügbar"
echo ""
echo "  3) BEIDE (nacheinander)"
echo ""

read -p "Eingabe (1-3): " MODE

cd /home/vde/VDE-Messwand

# Aktiviere venv falls vorhanden
if [ -d "venv" ]; then
    echo "🔧 Aktiviere Virtual Environment..."
    source venv/bin/activate
fi

if [ "$MODE" = "1" ]; then
    echo ""
    echo "🚀 Starte Visual Test..."
    echo "   (Browser öffnet sich gleich im VOLLBILD)"
    echo ""
    sleep 2
    python stress_test_visual.py

elif [ "$MODE" = "2" ]; then
    echo ""
    echo "🚀 Starte Kiosk Simulator..."
    echo "   (Browser öffnet sich gleich im VOLLBILD)"
    echo ""
    sleep 2
    python kiosk_simulator.py

elif [ "$MODE" = "3" ]; then
    echo ""
    echo "🚀 Starte beide Tests nacheinander..."
    echo ""
    echo "Teil 1: Visual Test"
    python stress_test_visual.py

    echo ""
    echo "Teil 2: Kiosk Simulator"
    python kiosk_simulator.py

else
    echo "❌ Ungültige Eingabe"
    exit 1
fi

echo ""
echo "======================================================"
echo "✅ TEST ABGESCHLOSSEN"
echo "======================================================"
