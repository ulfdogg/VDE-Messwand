#!/bin/bash
#
# VDE Messwand - Installations-Script
# ====================================
# Dieses Script installiert und konfiguriert das VDE Messwand System vollständig.
#
# Verwendung: sudo ./install.sh
#

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Variablen
# Installationsverzeichnis = dort wo install.sh liegt
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_USER="vde"
DEFAULT_HOSTNAME="VDE-Messwand"
KIOSK_URL="http://localhost"

# ============================================================================
# Funktionen
# ============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}======================================================"
    echo " VDE MESSWAND - INSTALLATIONS-SCRIPT"
    echo "======================================================${NC}"
    echo ""
}

print_step() {
    echo ""
    echo -e "${BLUE}[STEP $1]${NC} $2"
    echo "------------------------------------------------------"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNUNG]${NC} $1"
}

print_error() {
    echo -e "${RED}[FEHLER]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Dieses Script muss als root ausgeführt werden!"
        echo "Verwendung: sudo ./install.sh"
        exit 1
    fi
}

# ============================================================================
# Hauptprogramm
# ============================================================================

print_header

check_root

# ----------------------------------------------------------------------------
# Schritt 1: Hostname abfragen
# ----------------------------------------------------------------------------
print_step "1/12" "System-Konfiguration"

echo ""
echo "Der Hostname wird für folgende Zwecke verwendet:"
echo "  - Systemname (hostname)"
echo "  - WiFi-Hotspot SSID"
echo "  - Netzwerkidentifikation"
echo ""
read -p "Hostname eingeben [Standard: $DEFAULT_HOSTNAME]: " INPUT_HOSTNAME

HOSTNAME="${INPUT_HOSTNAME:-$DEFAULT_HOSTNAME}"
# Entferne Leerzeichen und Sonderzeichen für SSID
SSID=$(echo "$HOSTNAME" | tr ' ' '-' | tr -cd '[:alnum:]-_')

echo ""
echo -e "  Hostname:    ${GREEN}$HOSTNAME${NC}"
echo -e "  Hotspot-SSID: ${GREEN}$SSID${NC}"
echo ""
read -p "Ist das korrekt? [J/n]: " CONFIRM
if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
    echo "Abbruch durch Benutzer."
    exit 0
fi

# ----------------------------------------------------------------------------
# Schritt 2: System aktualisieren
# ----------------------------------------------------------------------------
print_step "2/12" "System aktualisieren (apt update && upgrade)"

apt update
apt upgrade -y

print_success "System aktualisiert"

# ----------------------------------------------------------------------------
# Schritt 3: Pakete installieren
# ----------------------------------------------------------------------------
print_step "3/12" "Erforderliche Pakete installieren"

apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-serial \
    python3-smbus \
    python3-rpi.gpio \
    python3-libgpiod \
    git \
    network-manager \
    curl \
    evtest \
    i2c-tools \
    rsync \
    unclutter \
    wlr-randr \
    wayvnc \
    fonts-noto-color-emoji

print_success "Pakete installiert"

# Bildschirmtastatur und Keyring deaktivieren (Kiosk-Mode)
echo "Deaktiviere Bildschirmtastatur und Keyring..."
apt remove -y squeekboard 2>/dev/null || true

# Keyring: systemd user services maskieren
sudo -u $SERVICE_USER systemctl --user mask gnome-keyring-daemon.service gnome-keyring-daemon.socket 2>/dev/null || true

# Keyring: D-Bus activation deaktivieren (wichtig!)
mv /usr/share/dbus-1/services/org.gnome.keyring.service /usr/share/dbus-1/services/org.gnome.keyring.service.disabled 2>/dev/null || true
mv /usr/share/dbus-1/services/org.gnome.keyring.PrivatePrompter.service /usr/share/dbus-1/services/org.gnome.keyring.PrivatePrompter.service.disabled 2>/dev/null || true
mv /usr/share/dbus-1/services/org.gnome.keyring.SystemPrompter.service /usr/share/dbus-1/services/org.gnome.keyring.SystemPrompter.service.disabled 2>/dev/null || true

# Keyring: Autostart deaktivieren
mkdir -p "/home/$SERVICE_USER/.config/autostart"
cat > "/home/$SERVICE_USER/.config/autostart/gnome-keyring-secrets.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=GNOME Keyring: Secret Service
Hidden=true
EOF
cat > "/home/$SERVICE_USER/.config/autostart/gnome-keyring-pkcs11.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=GNOME Keyring: PKCS#11 Component
Hidden=true
EOF
cat > "/home/$SERVICE_USER/.config/autostart/gnome-keyring-ssh.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=GNOME Keyring: SSH Agent
Hidden=true
EOF
chown -R $SERVICE_USER:$SERVICE_USER "/home/$SERVICE_USER/.config/autostart"

print_success "Bildschirmtastatur und Keyring komplett deaktiviert (systemd + D-Bus + Autostart)"

# ----------------------------------------------------------------------------
# Schritt 4: Display-Konfiguration
# ----------------------------------------------------------------------------
print_step "4/12" "Display konfigurieren (7\" Touchscreen)"

CONFIG_FILE="/boot/firmware/config.txt"

# Prüfen ob Display-Overlay bereits vorhanden
if ! grep -q "dtoverlay=vc4-kms-dsi-7inch" "$CONFIG_FILE"; then
    # Unter [all] Section hinzufügen
    if grep -q "^\[all\]" "$CONFIG_FILE"; then
        # Nach [all] einfügen
        sed -i '/^\[all\]$/a \\n# Manuelles Overlay für offizielles 7" Touchscreen Display\ndtoverlay=vc4-kms-dsi-7inch' "$CONFIG_FILE"
        print_success "Display-Overlay hinzugefügt"
    else
        # [all] Section erstellen
        echo -e "\n[all]\n# Manuelles Overlay für offizielles 7\" Touchscreen Display\ndtoverlay=vc4-kms-dsi-7inch" >> "$CONFIG_FILE"
        print_success "Display-Overlay und [all] Section hinzugefügt"
    fi
else
    print_warning "Display-Overlay bereits vorhanden"
fi

# labwc Autostart erstellen (Display-Rotation, VNC, Cursor ausblenden)
LABWC_DIR="/home/$SERVICE_USER/.config/labwc"
mkdir -p "$LABWC_DIR"
cat > "$LABWC_DIR/autostart" << 'AUTOSTART_EOF'
#!/bin/bash
# VDE Messwand - labwc Autostart (KEIN Panel/Tastatur/Desktop!)

# WICHTIG: Diese Datei überschreibt /etc/xdg/labwc/autostart
# Dadurch werden wf-panel, pcmanfm, lxsession-xdg-autostart etc. NICHT gestartet

# Wayland Umgebung setzen
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/1000

# Keyring deaktivieren (keine Passwort-Popups)
export GNOME_KEYRING_CONTROL=
export GNOME_KEYRING_PID=

# Display konfigurieren (nur DSI-1 nutzen, DSI-2 deaktivieren)
wlr-randr --output DSI-2 --off 2>/dev/null || true
wlr-randr --output DSI-1 --transform 270 2>/dev/null || true

# VNC Server starten (Wayland-kompatibel, nur DSI-1 Display)
wayvnc -o DSI-1 0.0.0.0 5900 &

# Mauszeiger ausblenden
unclutter -idle 0.1 &

# WICHTIG: Wir starten hier KEIN Panel, keine Tastatur, keinen Desktop!
# Chromium wird von kiosk.service gestartet
AUTOSTART_EOF
chmod +x "$LABWC_DIR/autostart"
chown -R $SERVICE_USER:$SERVICE_USER "$LABWC_DIR"

print_success "Display-Overlay konfiguriert + labwc Autostart erstellt (Rotation 270°, VNC, Cursor)"

# ----------------------------------------------------------------------------
# Schritt 6: Hostname setzen
# ----------------------------------------------------------------------------
print_step "5/12" "Hostname konfigurieren"

# Aktuellen Hostname speichern
OLD_HOSTNAME=$(hostname)

# Hostname setzen
hostnamectl set-hostname "$HOSTNAME"

# /etc/hosts aktualisieren
sed -i "s/$OLD_HOSTNAME/$HOSTNAME/g" /etc/hosts 2>/dev/null || true

# Falls nicht vorhanden, Eintrag hinzufügen
if ! grep -q "$HOSTNAME" /etc/hosts; then
    echo "127.0.1.1       $HOSTNAME" >> /etc/hosts
fi

print_success "Hostname gesetzt: $HOSTNAME"

# ----------------------------------------------------------------------------
# Schritt 7: Benutzerberechtigungen
# ----------------------------------------------------------------------------
print_step "6/12" "Benutzerberechtigungen konfigurieren"

# Benutzer zu notwendigen Gruppen hinzufügen
usermod -a -G dialout $SERVICE_USER 2>/dev/null || true
usermod -a -G gpio $SERVICE_USER 2>/dev/null || true
usermod -a -G i2c $SERVICE_USER 2>/dev/null || true
usermod -a -G spi $SERVICE_USER 2>/dev/null || true

# Sudoers-Eintrag für nmcli ohne Passwort
SUDOERS_FILE="/etc/sudoers.d/VDE-Messwand"
cat > "$SUDOERS_FILE" << 'EOF'
# VDE Messwand - Netzwerk-Rechte
vde ALL=(ALL) NOPASSWD: /usr/bin/nmcli
vde ALL=(ALL) NOPASSWD: /usr/bin/iwconfig
vde ALL=(ALL) NOPASSWD: /sbin/shutdown
vde ALL=(ALL) NOPASSWD: /sbin/reboot
EOF
chmod 440 "$SUDOERS_FILE"

print_success "Benutzerberechtigungen konfiguriert"

# ----------------------------------------------------------------------------
# Schritt 8: Virtuelle Umgebung und Python-Abhängigkeiten
# ----------------------------------------------------------------------------
print_step "7/12" "Python-Umgebung einrichten"

cd "$INSTALL_DIR"

# Virtuelle Umgebung erstellen (falls nicht vorhanden)
if [ ! -d "venv" ]; then
    sudo -u $SERVICE_USER python3 -m venv venv
    print_success "Virtuelle Umgebung erstellt"
else
    print_warning "Virtuelle Umgebung existiert bereits"
fi

# Abhängigkeiten installieren
sudo -u $SERVICE_USER bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u $SERVICE_USER bash -c "source venv/bin/activate && pip install Flask==2.3.3 smbus2==0.4.2 pyserial gunicorn RPi.GPIO openpyxl gpiod"

print_success "Python-Abhängigkeiten installiert"

# ----------------------------------------------------------------------------
# Schritt 9: Hotspot-Konfiguration aktualisieren
# ----------------------------------------------------------------------------
print_step "8/12" "Hotspot-Konfiguration anpassen"

# network_manager.py mit korrekter SSID aktualisieren
NETWORK_MANAGER_FILE="$INSTALL_DIR/network_manager.py"
if [ -f "$NETWORK_MANAGER_FILE" ]; then
    sed -i "s/HOTSPOT_SSID = .*/HOTSPOT_SSID = '$SSID'/" "$NETWORK_MANAGER_FILE"
    print_success "Hotspot-SSID gesetzt: $SSID"
else
    print_warning "network_manager.py nicht gefunden"
fi

# ----------------------------------------------------------------------------
# Schritt 10: Systemd-Service einrichten
# ----------------------------------------------------------------------------
print_step "9/12" "Systemd-Service einrichten"

SERVICE_FILE="/etc/systemd/system/VDE-Messwand.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=VDE Messwand Flask App
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python app.py
Restart=always
RestartSec=10
Environment="PATH=$INSTALL_DIR/venv/bin"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable VDE-Messwand.service

# Python Berechtigung für Port 80 (ohne Root)
PYTHON_BIN=$(readlink -f /usr/bin/python3)
setcap 'cap_net_bind_service=+ep' "$PYTHON_BIN"

print_success "Systemd-Service eingerichtet und aktiviert"

# ----------------------------------------------------------------------------
# Schritt 11: Power-Button (J2) konfigurieren
# ----------------------------------------------------------------------------
print_step "10/12" "Power-Button (J2-Header) konfigurieren"

echo "Der Raspberry Pi 5 hat einen J2-Header für einen externen Power-Button."
echo "Standard: Button kann Ein- UND Ausschalten"
echo ""
read -p "Soll der Button NUR zum Einschalten funktionieren? [J/n]: " DISABLE_POWEROFF

if [[ ! "$DISABLE_POWEROFF" =~ ^[Nn]$ ]]; then
    # systemd-logind konfigurieren
    mkdir -p /etc/systemd/logind.conf.d
    cat > /etc/systemd/logind.conf.d/no-power-button.conf << 'EOF'
[Login]
HandlePowerKey=ignore
HandlePowerKeyLongPress=ignore
EOF
    systemctl restart systemd-logind 2>/dev/null || true

    # labwc Desktop-Konfiguration (falls vorhanden)
    LABWC_USER_CONFIG="/home/$SERVICE_USER/.config/labwc/rc.xml"
    LABWC_SYSTEM_CONFIG="/etc/xdg/labwc/rc.xml"

    if [ -f "$LABWC_SYSTEM_CONFIG" ]; then
        mkdir -p "/home/$SERVICE_USER/.config/labwc"
        if [ ! -f "$LABWC_USER_CONFIG" ]; then
            cp "$LABWC_SYSTEM_CONFIG" "$LABWC_USER_CONFIG"
            chown $SERVICE_USER:$SERVICE_USER "$LABWC_USER_CONFIG"
        fi
        # Power-Button-Aktion entfernen
        sed -i 's/<action name="Execute">.*<command>pwrkey<\/command>.*<\/action>//' "$LABWC_USER_CONFIG" 2>/dev/null || true
    fi

    # evtest-basierter Blocker als Service
    cat > /etc/systemd/system/block-power-button.service << 'EOF'
[Unit]
Description=Block power button input events
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/evtest --grab /dev/input/event0
Restart=always
RestartSec=1

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable block-power-button.service

    print_success "Power-Button nur zum Einschalten konfiguriert"
else
    print_warning "Power-Button-Konfiguration übersprungen"
fi

# ----------------------------------------------------------------------------
# Schritt 12: Datenbank initialisieren
# ----------------------------------------------------------------------------
print_step "11/12" "Datenbank initialisieren"

cd "$INSTALL_DIR"
if [ ! -f "vde_messwand.db" ]; then
    sudo -u $SERVICE_USER bash -c "source venv/bin/activate && python3 -c 'from database import init_db; init_db()'"
    print_success "Datenbank initialisiert"
else
    print_warning "Datenbank existiert bereits"
fi

# ----------------------------------------------------------------------------
# Schritt 13: Kiosk-Modus konfigurieren
# ----------------------------------------------------------------------------
print_step "12/12" "Kiosk-Modus einrichten (Autologin + Chromium)"

# Chromium installieren falls nicht vorhanden
if ! command -v chromium &> /dev/null && ! command -v chromium-browser &> /dev/null; then
    apt install -y chromium-browser
    print_success "Chromium installiert"
else
    print_warning "Chromium bereits installiert"
fi

# Autologin für User 'vde' konfigurieren
AUTOLOGIN_DIR="/etc/systemd/system/getty@tty1.service.d"
mkdir -p "$AUTOLOGIN_DIR"
cat > "$AUTOLOGIN_DIR/autologin.conf" << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $SERVICE_USER --noclear %I \$TERM
EOF
print_success "Autologin für Benutzer '$SERVICE_USER' konfiguriert"

# Kiosk-Modus als systemd-Service einrichten
KIOSK_SERVICE="/etc/systemd/system/kiosk.service"
cat > "$KIOSK_SERVICE" << EOF
[Unit]
Description=Chromium Kiosk Modus für Benutzer $SERVICE_USER
After=graphical.target sound.target VDE-Messwand.service
Wants=sound.target
Requires=VDE-Messwand.service

[Service]
User=$SERVICE_USER
Type=simple
# Wayland statt X11 (für labwc)
Environment=WAYLAND_DISPLAY=wayland-0
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
Environment=PULSE_SERVER=unix:/run/user/1000/pulse/native
# Warte bis Flask-Server wirklich antwortet (max 60 Sekunden)
ExecStartPre=/bin/bash -c 'for i in \$(seq 1 60); do curl -s http://localhost >/dev/null 2>&1 && exit 0; sleep 1; done; exit 1'
# Chromium im Wayland-Modus starten (verhindert unsichtbares Fenster)
ExecStart=/usr/bin/chromium --ozone-platform=wayland --enable-features=UseOzonePlatform --kiosk --incognito --noerrdialogs --disable-infobars --autoplay-policy=no-user-gesture-required --check-for-update-interval=31536000 $KIOSK_URL
Restart=always
RestartSec=10

[Install]
WantedBy=graphical.target
EOF

systemctl daemon-reload
systemctl enable kiosk.service

print_success "Kiosk-Modus als systemd-Service konfiguriert (kiosk.service)"

# ============================================================================
# Zusammenfassung
# ============================================================================

echo ""
echo -e "${CYAN}======================================================"
echo " INSTALLATION ABGESCHLOSSEN"
echo "======================================================${NC}"
echo ""
echo -e "  ${GREEN}Hostname:${NC}      $HOSTNAME"
echo -e "  ${GREEN}Hotspot-SSID:${NC}  $SSID"
echo -e "  ${GREEN}Hotspot-PW:${NC}    vde12345"
echo -e "  ${GREEN}Install-Dir:${NC}   $INSTALL_DIR"
echo -e "  ${GREEN}Service:${NC}       VDE-Messwand.service"
echo -e "  ${GREEN}Kiosk-Service:${NC} kiosk.service (systemd)"
echo ""
echo "Nächste Schritte:"
echo "  1. Neustart durchführen: sudo reboot"
echo "  2. Nach Neustart:"
echo "     - Automatischer Login als '$SERVICE_USER'"
echo "     - kiosk.service startet Chromium automatisch im Kiosk-Modus"
echo "     - Web-Interface wird auf dem Display angezeigt"
echo ""
echo "Web-Zugriff von anderen Geräten:"
echo "     - http://$HOSTNAME.local (falls mDNS aktiv)"
echo "     - http://<IP-ADRESSE>"
echo "     - Bei Hotspot: http://192.168.50.1"
echo ""
echo "Service-Befehle:"
echo "  sudo systemctl status VDE-Messwand"
echo "  sudo systemctl restart VDE-Messwand"
echo "  sudo journalctl -u VDE-Messwand -f"
echo ""
echo -e "${YELLOW}WICHTIG: Bitte jetzt neu starten!${NC}"
echo ""
read -p "Jetzt neu starten? [J/n]: " REBOOT_NOW
if [[ ! "$REBOOT_NOW" =~ ^[Nn]$ ]]; then
    echo "System wird neu gestartet..."
    reboot
fi
