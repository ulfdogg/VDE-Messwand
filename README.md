# VDE Messwand System

Ein modernes Prüfungs- und Trainingssystem für VDE 0100-600 elektrische Installationsprüfungen mit Modbus RTU-gesteuerter Relais-Hardware.

## Übersicht

Das VDE Messwand System ist eine webbasierte Anwendung zur Steuerung von 64 Relais (2 Module mit je 32 Relais) für die Simulation verschiedener elektrischer Prüfszenarien. Es bietet einen vollständigen Trainings- und Prüfungsmodus sowie eine komplette Admin-Oberfläche zur Konfiguration aller Parameter.

## Features

### Kernfunktionen
- **Prüfungsmodus**: Vollständiger Prüfungsdurchlauf mit Fehlersuche und Dokumentation
- **Übungsmodus**: Kategoriebasiertes Training mit automatischer Relais-Aktivierung
- **Manueller Modus**: Direkte Steuerung einzelner Relais und Gruppen nach Stromkreis
- **Live-Monitoring**: Echtzeit-Anzeige aller Relais-Zustände
- **Wallbox-Filterung**: Wallbox-Stromkreis kann global deaktiviert werden

### Verwaltungsfunktionen (vollständig über UI konfigurierbar)
- **Relais-Verwaltung**: Gruppierung, Benennung und Kategorisierung aller 64 Relais
- **Stromkreis-Management**: Stromkreise anlegen, bearbeiten und löschen
- **Kategorien**: Messkategorien (RISO, Zi, Zs, RCD, Drehfeld, RLO, Abriss) anlegen/löschen
- **Training-Konfiguration**: Relais-Mappings für jede Kategorie/Messseite definieren
- **Datenbank**: Speicherung und Export aller Prüfungsergebnisse (CSV)
- **Excel Import/Export**: Relais-Konfigurationen im- und exportieren

### Netzwerk-Features
- **WiFi-Hotspot**: Integrierter Access Point für direkten Zugriff ohne Router
- **Netzwerk-Management**: WLAN-Verbindung über Web-Interface konfigurieren
- **VNC-Zugriff**: Remote-Desktop über wayvnc (Wayland-kompatibel)

### Hardware-Integration
- **Modbus RTU**: Kommunikation über serielle Schnittstelle
- **64 Relais**: 2 Module mit je 32 Relais
- **Live-Status**: Auslesen des tatsächlichen Hardware-Zustands
- **GPIO-Monitor**: Überwachung von Notaus-Schaltern (GPIO 17/27)
- **Power-Button (J2)**: Externer Ein-Taster am Raspberry Pi 5

### Kiosk-Modus (für Vollbild-Betrieb)
- **Chromium im Kiosk-Modus** startet automatisch nach dem Boot
- **Autologin** für den `vde`-Benutzer ohne Passwortabfrage
- **unclutter** blendet den Mauszeiger nach 0,1 s Inaktivität aus
- **labwc Autostart** konfiguriert Display-Rotation, VNC und Cursor – ohne Panel, Taskleiste oder Desktop
- **Display-Rotation**: 270° per `wlr-randr` für das 7"-Touchscreen-Display
- **Bildschirmtastatur deaktiviert**: `squeekboard` wird entfernt
- **GNOME Keyring deaktiviert**: Keine Passwort-Popups im Kiosk-Betrieb

---

## Schnellinstallation

### Automatische Installation (empfohlen)

Das mitgelieferte Install-Script konfiguriert das System vollständig:

```bash
cd /home/vde/VDE-Messwand
sudo ./install.sh
```

Das Script führt folgende Schritte aus:
1. Fragt nach dem Hostnamen (wird auch als Hotspot-SSID verwendet)
2. Aktualisiert das System (`apt update` / `apt upgrade`)
3. Installiert alle benötigten Pakete (inkl. Kiosk-Tools)
4. Konfiguriert Display-Rotation und labwc Autostart
5. Setzt Hostname und Hotspot-SSID
6. Richtet Benutzerrechte und Sudoers-Einträge ein
7. Erstellt Python-Virtualenv und installiert Abhängigkeiten
8. Passt die Hotspot-SSID in `network_manager.py` an
9. Erstellt und aktiviert den `VDE-Messwand.service`
10. Konfiguriert den Power-Button (optional: nur Einschalten)
11. Initialisiert die SQLite-Datenbank
12. Richtet Autologin und `kiosk.service` ein
13. Startet das System neu

---

## Manuelle Installation

### Voraussetzungen

**Hardware:**
- Raspberry Pi 5 (empfohlen)
- 2x Modbus RTU Relais-Module (je 32 Relais)
- USB-zu-RS485 Adapter oder GPIO-basierter RS485 HAT
- Offizielles Raspberry Pi 7"-Touchscreen (DSI)
- Stromversorgung für Relais-Module
- Optional: Taster am J2-Header (Power-Button)
- Optional: Notaus-Schalter an GPIO 17/27

**Software:**
- Raspberry Pi OS Bookworm (oder neuer, 64-Bit)
- Python 3.11 oder höher

---

### Schritt 1: System aktualisieren

```bash
sudo apt update
sudo apt upgrade -y
```

---

### Schritt 2: Pakete installieren

```bash
sudo apt install -y \
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
```

**Paket-Erklärungen (Kiosk-relevante):**

| Paket | Zweck |
|---|---|
| `unclutter` | Mauszeiger nach Inaktivität ausblenden |
| `wlr-randr` | Display-Rotation unter Wayland (labwc) |
| `wayvnc` | VNC-Zugriff unter Wayland |
| `evtest` | Power-Button-Events blockieren (J2-Header) |
| `python3-libgpiod` | GPIO-Zugriff (gpiod-Bibliothek) |
| `rsync` | Dateisynchronisation |
| `fonts-noto-color-emoji` | Emoji-Darstellung in der Web-UI |

---

### Schritt 3: Bildschirmtastatur und Keyring deaktivieren

Im Kiosk-Betrieb muss die Bildschirmtastatur (`squeekboard`) und der GNOME Keyring deaktiviert werden, sonst erscheinen unerwünschte Popups:

```bash
# Bildschirmtastatur entfernen
sudo apt remove -y squeekboard

# Keyring systemd-Services maskieren
systemctl --user mask gnome-keyring-daemon.service gnome-keyring-daemon.socket

# Keyring D-Bus Activation deaktivieren
sudo mv /usr/share/dbus-1/services/org.gnome.keyring.service \
        /usr/share/dbus-1/services/org.gnome.keyring.service.disabled
sudo mv /usr/share/dbus-1/services/org.gnome.keyring.PrivatePrompter.service \
        /usr/share/dbus-1/services/org.gnome.keyring.PrivatePrompter.service.disabled
sudo mv /usr/share/dbus-1/services/org.gnome.keyring.SystemPrompter.service \
        /usr/share/dbus-1/services/org.gnome.keyring.SystemPrompter.service.disabled

# Keyring Autostart deaktivieren
mkdir -p ~/.config/autostart
for name in gnome-keyring-secrets gnome-keyring-pkcs11 gnome-keyring-ssh; do
    cat > ~/.config/autostart/${name}.desktop << EOF
[Desktop Entry]
Type=Application
Hidden=true
EOF
done
```

---

### Schritt 4: Display konfigurieren (7" Touchscreen)

```bash
# DSI-Overlay in /boot/firmware/config.txt eintragen
echo -e "\n[all]\ndtoverlay=vc4-kms-dsi-7inch" | sudo tee -a /boot/firmware/config.txt
```

---

### Schritt 5: labwc Autostart erstellen

labwc ist der Wayland-Compositor. Der Autostart ersetzt den System-Autostart komplett (kein Panel, keine Taskleiste, kein Desktop):

```bash
mkdir -p ~/.config/labwc
cat > ~/.config/labwc/autostart << 'EOF'
#!/bin/bash
# VDE Messwand - labwc Autostart

export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/1000

# Keyring deaktivieren
export GNOME_KEYRING_CONTROL=
export GNOME_KEYRING_PID=

# Display: DSI-2 deaktivieren, DSI-1 mit 270° Rotation
wlr-randr --output DSI-2 --off 2>/dev/null || true
wlr-randr --output DSI-1 --transform 270 2>/dev/null || true

# VNC-Server starten (nur DSI-1)
wayvnc -o DSI-1 0.0.0.0 5900 &

# Mauszeiger ausblenden (nach 0.1 s Inaktivität)
unclutter -idle 0.1 &

# Chromium wird von kiosk.service gestartet – hier NICHTS weiter starten
EOF
chmod +x ~/.config/labwc/autostart
```

**Wichtig:** Diese Datei überschreibt `/etc/xdg/labwc/autostart`. Dadurch werden `wf-panel`, `pcmanfm`, `lxsession-xdg-autostart` usw. **nicht** gestartet.

---

### Schritt 6: Hostname setzen

```bash
# Hostname setzen (z.B. VDE-Messwand-1)
sudo hostnamectl set-hostname VDE-Messwand-1

# In /etc/hosts eintragen
sudo sed -i 's/127.0.1.1.*/127.0.1.1\tVDE-Messwand-1/' /etc/hosts
```

Der Hostname wird auch als Hotspot-SSID verwendet.

---

### Schritt 7: Benutzerberechtigungen

```bash
sudo usermod -a -G dialout,gpio,i2c,spi vde

sudo tee /etc/sudoers.d/VDE-Messwand << 'EOF'
vde ALL=(ALL) NOPASSWD: /usr/bin/nmcli
vde ALL=(ALL) NOPASSWD: /usr/bin/iwconfig
vde ALL=(ALL) NOPASSWD: /sbin/shutdown
vde ALL=(ALL) NOPASSWD: /sbin/reboot
EOF
sudo chmod 440 /etc/sudoers.d/VDE-Messwand
```

---

### Schritt 8: Python-Umgebung einrichten

```bash
cd /home/vde/VDE-Messwand
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install Flask==2.3.3 smbus2==0.4.2 pyserial gunicorn RPi.GPIO openpyxl gpiod
```

---

### Schritt 9: Systemd-Service (Flask-App)

```bash
sudo tee /etc/systemd/system/VDE-Messwand.service << 'EOF'
[Unit]
Description=VDE Messwand Flask App
After=network.target

[Service]
User=vde
Group=vde
WorkingDirectory=/home/vde/VDE-Messwand
ExecStart=/home/vde/VDE-Messwand/venv/bin/python app.py
Restart=always
RestartSec=10
Environment="PATH=/home/vde/VDE-Messwand/venv/bin"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable VDE-Messwand.service

# Python darf Port 80 ohne Root binden
sudo setcap 'cap_net_bind_service=+ep' "$(readlink -f /usr/bin/python3)"
```

---

### Schritt 10: Datenbank initialisieren

```bash
source venv/bin/activate
python3 -c "from database import init_db; init_db()"
```

---

### Schritt 11: Kiosk-Modus einrichten

#### Autologin konfigurieren

```bash
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf << 'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin vde --noclear %I $TERM
EOF
```

#### kiosk.service (Chromium)

```bash
sudo tee /etc/systemd/system/kiosk.service << 'EOF'
[Unit]
Description=Chromium Kiosk Modus
After=graphical.target VDE-Messwand.service
Requires=VDE-Messwand.service

[Service]
User=vde
Type=simple
Environment=WAYLAND_DISPLAY=wayland-0
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
# Warte bis Flask-Server antwortet (max. 60 Sekunden)
ExecStartPre=/bin/bash -c 'for i in $(seq 1 60); do curl -s http://localhost >/dev/null 2>&1 && exit 0; sleep 1; done; exit 1'
ExecStart=/usr/bin/chromium \
    --ozone-platform=wayland \
    --enable-features=UseOzonePlatform \
    --kiosk \
    --incognito \
    --noerrdialogs \
    --disable-infobars \
    --autoplay-policy=no-user-gesture-required \
    --check-for-update-interval=31536000 \
    http://localhost
Restart=always
RestartSec=10

[Install]
WantedBy=graphical.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kiosk.service
```

**Chromium-Flags erklärt:**

| Flag | Zweck |
|---|---|
| `--ozone-platform=wayland` | Wayland statt X11 verwenden |
| `--kiosk` | Vollbild, kein Schließen-Button |
| `--incognito` | Kein Session-Speicher, sauberer Start |
| `--noerrdialogs` | Keine Crash-Dialoge |
| `--disable-infobars` | Keine „Chrome wird von Software verwaltet"-Banner |
| `--autoplay-policy=no-user-gesture-required` | Videos autoplay ohne Klick (für Übungsmodus) |
| `--check-for-update-interval=31536000` | Update-Check auf 1 Jahr deaktiviert |

---

## Power-Button (J2-Header, Raspberry Pi 5)

Der Raspberry Pi 5 hat einen J2-Header für einen externen Taster.

### Nur Einschalten erlauben (Ausschalten per Button deaktivieren)

#### 1. systemd-logind konfigurieren

```bash
sudo mkdir -p /etc/systemd/logind.conf.d
sudo tee /etc/systemd/logind.conf.d/no-power-button.conf << 'EOF'
[Login]
HandlePowerKey=ignore
HandlePowerKeyLongPress=ignore
EOF
sudo systemctl restart systemd-logind
```

#### 2. Power-Button-Events mit evtest blockieren

```bash
sudo tee /etc/systemd/system/block-power-button.service << 'EOF'
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

sudo systemctl daemon-reload
sudo systemctl enable block-power-button.service
```

**Hinweis:** `/dev/input/event0` ist beim Pi 5 der `pwr_button`.
Prüfen mit: `cat /proc/bus/input/devices | grep -A5 pwr_button`

#### 3. labwc Power-Key-Keybind entfernen (optional)

In `~/.config/labwc/rc.xml` den Block ändern:

```xml
<!-- Vorher -->
<keybind key="XF86PowerOff" onRelease="yes">
  <action name="Execute"><command>pwrkey</command></action>
</keybind>

<!-- Nachher (Aktion entfernt) -->
<keybind key="XF86PowerOff" onRelease="yes">
</keybind>
```

---

## WiFi-Hotspot

### Aktivieren

1. **Admin-Panel** → **Netzwerk** → Toggle „WiFi Hotspot"
2. Verbinden mit:
   - **SSID:** entspricht dem Hostnamen (z.B. `VDE-Messwand-1`)
   - **Passwort:** `vde12345`
3. Browser: `http://192.168.50.1`

### Konfiguration in `network_manager.py`

```python
HOTSPOT_SSID = 'VDE-Messwand-1'   # Wird durch install.sh automatisch gesetzt
HOTSPOT_PASSWORD = 'vde12345'
HOTSPOT_IP = '192.168.50.1'
```

---

## GPIO-Monitor (Notaus)

### Konfiguration in `config.py`

```python
GPIO_MONITOR_PIN1 = 17        # GPIO 17 (physisch Pin 11)
GPIO_MONITOR_PIN2 = 27        # GPIO 27 (physisch Pin 13)
GPIO_WARNING_TEXT = "NOTAUS BETÄTIGT"
GPIO_SHUTDOWN_TIMEOUT = 120   # Sekunden bis automatisches Herunterfahren
```

Ein Schließer wird zwischen Pin 17 und Pin 27 angeschlossen. Geschlossener Schließer = Warnung aktiv, nach 120 s automatisches Herunterfahren.

---

## Konfigurationsdateien (JSON)

Alle Einstellungen werden in JSON-Dateien gespeichert und sind vollständig über die Admin-UI bearbeitbar. Es gibt **keine hardcodierten Werte** mehr in `config.py`.

| Datei | Inhalt |
|---|---|
| `relais_config.json` | Relais-Konfiguration (Name, Gruppe, Kategorie, Stromkreis) |
| `stromkreise.json` | Stromkreis-Definitionen (Name, Relais-Bereich) |
| `kategorien.json` | Messkategorien (RISO, Zi, Zs, RCD, Drehfeld, RLO, Abriss …) |
| `training_config.json` | Relais-Mappings für Übungsmodus (Kategorie → Messseite → Relais) |
| `relay_groups.json` | Alte Gruppen-Definitionen (Kompatibilität) |
| `settings.json` | System-Einstellungen (Admin-Code, Wallbox) |
| `hotspot_state.json` | Hotspot-Status (persistent) |

---

## Projekt-Struktur

```
VDE-Messwand/
├── app.py                      # Haupt-Flask-Anwendung (Routen & API)
├── config.py                   # Basiswerte (Serial, GPIO, Ports)
├── database.py                 # SQLite-Prüfungsdatenbank
├── requirements.txt            # Python-Abhängigkeiten
├── install.sh                  # Vollautomatisches Installations-Script
│
├── modbus_controller.py        # Modbus RTU Kommunikation
├── relay_controller.py         # Relais-Steuerung (Gruppen-Logik)
├── serial_handler.py           # Serielle Schnittstelle / Dummy-Mode
├── network_manager.py          # WiFi/Hotspot-Verwaltung
├── gpio_monitor.py             # GPIO-Überwachung (Notaus)
│
├── relais_manager.py           # Neue modulare Relais-Verwaltung
├── training_manager.py         # Training-Konfiguration (Kategorie → Relais)
├── stromkreis_manager.py       # Stromkreis- und Kategorie-Management
├── settings_manager.py         # System-Einstellungen (Admin-Code, Wallbox)
├── group_manager.py            # Gruppen-Manager (Datenbank-Kompatibilität)
├── exam_utils.py               # Prüfungsmodus-Logik
├── relais_excel.py             # Excel Import/Export
├── relais_templates.py         # Relais-Vorlagen
│
├── gunicorn_config.py          # Gunicorn-Konfiguration
├── cleanup_gpio.py             # GPIO Cleanup
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── exam_mode.html
│   ├── manual_mode_pi.html
│   ├── relay_status.html
│   ├── test_mode.html
│   ├── training_mode.html
│   ├── training_spannungsfrei.html
│   ├── training_unter_spannung.html
│   ├── admin_login.html
│   ├── admin_panel.html
│   ├── admin_relais.html
│   ├── admin_config.html
│   ├── admin_training_new.html
│   ├── admin_database.html
│   ├── admin_network.html
│   └── admin_settings.html
│
├── static/
│   ├── css/style.css
│   └── videos/                 # Lehrvideos für den Übungsmodus
│
├── stromkreise.json
├── kategorien.json
├── relais_config.json
├── training_config.json
└── relay_groups.json
```

---

## Verwendung

### Anwendung starten

```bash
# Via Systemd-Service (Produktion)
sudo systemctl start VDE-Messwand

# Manuell (Entwicklung/Test)
cd /home/vde/VDE-Messwand
source venv/bin/activate
python3 app.py
```

Erreichbar unter:
- Lokal: `http://localhost` (Port 80)
- Im Netzwerk: `http://<IP-ADRESSE>`
- Bei Hotspot: `http://192.168.50.1`
- mDNS: `http://VDE-Messwand-1.local`

### Admin-Bereich

PIN-geschützt (Standard: `1234`), erreichbar über das Zahnrad-Icon.

| Seite | Funktion |
|---|---|
| Datenbank | Prüfungsergebnisse anzeigen und exportieren |
| Netzwerk | WLAN/Hotspot-Einstellungen |
| Relais-Verwaltung | Alle 64 Relais konfigurieren (Name, Gruppe, Kategorie, Stromkreis) |
| Konfiguration | Stromkreise und Messkategorien anlegen/löschen |
| Übungsmodus | Relais-Mappings für Kategorien definieren |
| Relay Status | Live Hardware-Status aller Relais |
| Test-Durchlauf | Sequenzieller Test aller 64 Relais |
| Einstellungen | Admin-Code ändern, Wallbox konfigurieren |

### Übungsmodus

1. **Übungsmodus** öffnen → Kategorie-Infos als Modal lesen (mit Video)
2. **Spannungsfrei üben**: Schutzleiter (RLO) und Isolation (RISO) mit Relais
3. **Unter Spannung üben**: Schleifenimpedanz (Zs), Zi, RCD und Drehfeld mit Relais
4. Die entsprechenden Relais werden beim Öffnen eines Abschnitts automatisch aktiviert

---

## Service-Verwaltung

```bash
# Status prüfen
sudo systemctl status VDE-Messwand
sudo systemctl status kiosk

# Neustart
sudo systemctl restart VDE-Messwand

# Logs
sudo journalctl -u VDE-Messwand -f
sudo journalctl -u kiosk -f

# Logs der letzten Stunde
sudo journalctl -u VDE-Messwand --since "1 hour ago"
```

---

## Hardware-Konfiguration

### Modbus RTU Setup

**Parameter in `config.py`:**
```python
SERIAL_PORT = '/dev/ttyACM0'  # oder /dev/ttyUSB0
BAUD_RATE = 9600
SERIAL_TIMEOUT = 1.0
```

**Modbus-Module:**
```python
MODBUS_MODULES = {
    0: {'slave_id': 1, 'base_addr': 0,  'name': 'Modul 1'},
    1: {'slave_id': 2, 'base_addr': 32, 'name': 'Modul 2'}
}
```

**Verfügbare Ports anzeigen:**
```bash
ls -l /dev/ttyUSB* /dev/ttyAMA* /dev/ttyACM* 2>/dev/null
```

---

## Troubleshooting

### Chromium startet nicht / bleibt leer

```bash
# kiosk.service Status prüfen
sudo journalctl -u kiosk -n 50

# Prüfen ob Flask läuft
curl http://localhost

# Wayland Display prüfen
ls /run/user/1000/wayland-*
```

### Mauszeiger wird nicht ausgeblendet

```bash
# Prüfen ob unclutter installiert ist
which unclutter

# Prüfen ob labwc autostart korrekt ist
cat ~/.config/labwc/autostart
```

### VNC funktioniert nicht

```bash
# wayvnc Status prüfen
ps aux | grep wayvnc

# Nur von diesem Gerät aus verbinden möglich wenn
# Wayland läuft (kein SSH-Forwarding möglich)
```

### Display falsch ausgerichtet / falsches Display aktiv

```bash
# Verbundene Ausgänge auflisten
wlr-randr

# Manuell rotieren (in der aktiven Wayland-Sitzung als vde)
wlr-randr --output DSI-1 --transform 270
```

### Serielle Verbindung

```bash
ls -l /dev/ttyUSB* /dev/ttyAMA* /dev/ttyACM*
groups $USER   # Sollte 'dialout' enthalten
```

### Hotspot startet nicht

```bash
systemctl status NetworkManager
ip link show wlan0
journalctl -u NetworkManager -f
```

### Service startet nicht

```bash
sudo journalctl -u VDE-Messwand -n 50

# Manuell testen
cd /home/vde/VDE-Messwand
source venv/bin/activate
python3 app.py
```

### Datenbank zurücksetzen

```bash
rm vde_messwand.db
python3 -c "from database import init_db; init_db()"
```

---

## API-Endpunkte (Auswahl)

### Relais-Steuerung
- `POST /set_manual_errors` – Ausgewählte Relais einschalten
- `POST /reset_relays` – Alle Relais zurücksetzen
- `GET /api/relay_status` – Status aller 64 Relais

### Training
- `POST /api/training/activate` – Relais für Kategorie/Seite aktivieren
- `GET /api/training/config` – Komplette Training-Konfiguration
- `POST /api/training/update` – Mapping aktualisieren
- `POST /api/training/delete` – Mapping löschen

### Relais-Verwaltung
- `GET /api/relais/config` – Alle Relais-Konfigurationen
- `POST /api/relais/update` – Einzelnes Relais konfigurieren
- `POST /api/relais/bulk_update` – Mehrere Relais auf einmal
- `GET /api/relais/by_category/<category>` – Relais einer Kategorie

### Stromkreise & Kategorien
- `GET /api/stromkreise` – Alle Stromkreise
- `POST /api/stromkreise/add` – Neuen Stromkreis anlegen
- `POST /api/stromkreise/update` – Stromkreis bearbeiten
- `POST /api/stromkreise/delete` – Stromkreis löschen
- `GET /api/kategorien` – Alle Kategorien
- `POST /api/kategorien/add` – Kategorie anlegen
- `POST /api/kategorien/delete` – Kategorie löschen

### Netzwerk
- `POST /api/network/hotspot/toggle` – Hotspot ein/aus
- `GET /api/network/status` – Netzwerk-Status
- `POST /api/network/wifi/connect` – Mit WLAN verbinden
- `GET /api/network/wifi/scan` – WLANs scannen

### Wallbox
- `POST /api/wallbox/toggle` – Wallbox aktivieren/deaktivieren
- `POST /api/wallbox/installed` – Wallbox als vorhanden markieren

---

## Changelog

### v2.0 (aktuell)
- **Vollständig JSON-basierte Konfiguration**: Keine hardcodierten Werte mehr in `config.py` – alle Stromkreise, Kategorien und Gruppen über die Admin-UI bearbeitbar und löschbar
- **Übungsmodus überarbeitet**: Neue Struktur mit „Spannungsfreie Messungen" und „Messungen unter Spannung" statt gerätespezifischer Seiten (Fluke/Benning/Gossen)
- **Automatische Relais-Aktivierung**: Beim Öffnen einer Messart im Übungsmodus werden die konfigurierten Relais sofort aktiviert
- **Kiosk-Konfiguration dokumentiert**: unclutter, wlr-randr, wayvnc, labwc autostart, kiosk.service, Keyring-Deaktivierung
- **Codebereinigung**: Veraltete Templates, Entwickler-Skripte und redundante API-Endpunkte entfernt

### v1.2
- **Install-Script**: Vollautomatische Installation mit Hostname-Abfrage
- **Power-Button**: Konfiguration für J2-Header (nur Einschalten)
- **Kiosk-Modus**: Chromium als systemd-Service, labwc autostart

### v1.1
- **Wallbox-Filterung**: Toggle auf Startseite zum Aktivieren/Deaktivieren
- **WiFi-Hotspot**: Integrierter Access Point

### v1.0 (Initial Release)
- Modulare Architektur mit Manager-System
- Kategoriebasierte Training-Struktur
- Live Relay Status Monitor
- Excel Import/Export
- Glass-Card Design
- Modbus RTU Integration
- Vollständiger Prüfungsmodus

---

## Lizenz

Dieses Projekt ist für Bildungszwecke im Bereich der elektrischen Installationsprüfung entwickelt.
