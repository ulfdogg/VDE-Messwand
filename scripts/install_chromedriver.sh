#!/bin/bash
# Installiere ChromeDriver für Raspberry Pi

echo "======================================================"
echo "ChromeDriver Installation für Raspberry Pi"
echo "======================================================"

# Methode 1: Versuche über apt
echo ""
echo "📦 Versuche Installation über apt..."
sudo apt-get update
sudo apt-get install -y chromium-chromedriver

# Prüfe ob erfolgreich
if which chromedriver > /dev/null 2>&1; then
    echo "✅ ChromeDriver erfolgreich installiert!"
    chromedriver --version
    exit 0
fi

# Methode 2: Manuelle Installation
echo ""
echo "⚠️  apt-Installation fehlgeschlagen"
echo "📦 Versuche manuelle Installation..."

# Prüfe Architektur
ARCH=$(uname -m)
echo "Architektur: $ARCH"

if [ "$ARCH" = "armv7l" ] || [ "$ARCH" = "aarch64" ]; then
    echo "✅ ARM-Architektur erkannt (Raspberry Pi)"

    # Download ChromeDriver für ARM
    DRIVER_VERSION="114.0.5735.90"
    echo "Lade ChromeDriver $DRIVER_VERSION für ARM..."

    cd /tmp
    wget -O chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/$DRIVER_VERSION/chromedriver_linux64.zip

    if [ $? -eq 0 ]; then
        unzip -o chromedriver_linux64.zip
        sudo mv chromedriver /usr/local/bin/
        sudo chmod +x /usr/local/bin/chromedriver

        echo "✅ ChromeDriver manuell installiert!"
        chromedriver --version
    else
        echo "❌ Download fehlgeschlagen"
    fi
else
    echo "⚠️  Unbekannte Architektur: $ARCH"
fi

echo ""
echo "======================================================"
which chromedriver || echo "❌ ChromeDriver NICHT gefunden!"
echo "======================================================"
