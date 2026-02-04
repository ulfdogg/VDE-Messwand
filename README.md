# VDE Messwand System

Ein modernes Prüfungs- und Trainingssystem für VDE 0100-600 elektrische Installationsprüfungen mit Modbus RTU-gesteuerter Relais-Hardware.

## Übersicht

Das VDE Messwand System ist eine webbasierte Anwendung zur Steuerung von 64 Relais (2 Module mit je 32 Relais) für die Simulation verschiedener elektrischer Prüfszenarien. Es unterstützt verschiedene Messgeräte (Fluke, Benning, Gossen Metrawatt) und bietet sowohl einen Trainings- als auch einen Prüfungsmodus.

## Features

### Kernfunktionen
- **Prüfungsmodus**: Vollständiger Prüfungsdurchlauf mit Fehlersuche und Dokumentation
- **Übungsmodus**: Kategoriebasiertes Training für verschiedene Messgeräte
- **Manueller Modus**: Direkte Steuerung einzelner Relais und Gruppen
- **Live-Monitoring**: Echtzeit-Anzeige aller Relais-Zustände
- **Stromkreis-Filterung**: Einzelne Stromkreise (z.B. Wallbox) können global deaktiviert werden

### Verwaltungsfunktionen
- **Relais-Verwaltung**: Gruppierung, Benennung und Kategorisierung
- **Stromkreis-Management**: Definition und Verwaltung von Stromkreisen
- **Training-Konfiguration**: Kategoriebasierte Relais-Mappings
- **Datenbank**: Speicherung aller Prüfungsergebnisse
- **Excel Import/Export**: Relais-Konfigurationen im- und exportieren

### Netzwerk-Features
- **WiFi-Hotspot**: Integrierter Access Point für direkten Zugriff ohne Router
- **Netzwerk-Management**: WLAN-Verbindung über Web-Interface konfigurieren

### Hardware-Integration
- **Modbus RTU**: Kommunikation über serielle Schnittstelle
- **64 Relais**: 2 Module mit je 32 Relais
- **Live-Status**: Auslesen des tatsächlichen Hardware-Status
- **GPIO-Monitor**: Überwachung von Notaus-Schaltern
- **Power-Button (J2)**: Externer Ein-Taster am Raspberry Pi 5

## Technologie-Stack

- **Backend**: Python 3.11+ mit Flask
- **Frontend**: HTML5, CSS3 (Glass-Design), Vanilla JavaScript
- **Datenbank**: SQLite
- **Hardware**: Modbus RTU über pySerial
- **Deployment**: Raspberry Pi 5 optimiert

---

## Schnellinstallation

### Automatische Installation (empfohlen)

Das mitgelieferte Install-Script konfiguriert das System vollständig:

```bash
cd /home/vde/vde-messwand
sudo ./install.sh
```

Das Script führt folgende Schritte aus:
1. Fragt nach dem Hostnamen (wird auch für Hotspot-SSID verwendet)
2. Aktualisiert das System (apt update/upgrade)
3. Installiert alle benötigten Pakete
4. Konfiguriert Benutzerrechte
5. Richtet Python-Umgebung ein
6. Konfiguriert den Hotspot mit der SSID basierend auf dem Hostnamen
7. Erstellt und aktiviert den Systemd-Service
8. Konfiguriert den Power-Button (optional nur zum Einschalten)
9. Initialisiert die Datenbank
10. Startet das System neu

---

## Manuelle Installation

### Voraussetzungen

**Hardware:**
- Raspberry Pi 5 (empfohlen)
- 2x Modbus RTU Relais-Module (je 32 Relais)
- USB-zu-RS485 Adapter oder GPIO-basierter RS485 HAT
- Stromversorgung für Relais-Module
- Optional: Taster am J2-Header (Power-Button)
- Optional: Notaus-Schalter an GPIO 17/27

**Software:**
- Raspberry Pi OS (Bookworm oder neuer)
- Python 3.11 oder höher

### Schritt 1: System aktualisieren

```bash
sudo apt update
sudo apt upgrade -y
```

### Schritt 2: Pakete installieren

```bash
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-serial \
    python3-smbus \
    python3-rpi.gpio \
    git \
    network-manager \
    curl \
    evtest \
    i2c-tools
```

### Schritt 3: Hostname setzen

Der Hostname wird für den Hotspot-SSID verwendet:

```bash
# Hostname setzen (z.B. VDE-Messwand-1)
sudo hostnamectl set-hostname VDE-Messwand-1

# In /etc/hosts eintragen
sudo nano /etc/hosts
# Zeile hinzufügen: 127.0.1.1    VDE-Messwand-1
```

### Schritt 4: Benutzerberechtigungen

```bash
# Benutzer zu Gruppen hinzufügen
sudo usermod -a -G dialout $USER
sudo usermod -a -G gpio $USER
sudo usermod -a -G i2c $USER

# Sudoers für nmcli ohne Passwort
sudo tee /etc/sudoers.d/vde-messwand << 'EOF'
vde ALL=(ALL) NOPASSWD: /usr/bin/nmcli
vde ALL=(ALL) NOPASSWD: /usr/bin/iwconfig
vde ALL=(ALL) NOPASSWD: /sbin/shutdown
vde ALL=(ALL) NOPASSWD: /sbin/reboot
EOF
sudo chmod 440 /etc/sudoers.d/vde-messwand
```

### Schritt 5: Repository klonen (falls nötig)

```bash
cd ~
git clone https://github.com/ulfdogg/VDE0100-600_Messwand.git vde-messwand
cd vde-messwand
```

### Schritt 6: Virtuelle Umgebung erstellen

```bash
python3 -m venv venv
source venv/bin/activate
```

### Schritt 7: Python-Abhängigkeiten installieren

```bash
pip install --upgrade pip
pip install Flask==2.3.3 smbus2==0.4.2 pyserial gunicorn RPi.GPIO
```

### Schritt 8: Serielle Schnittstelle konfigurieren

```bash
# Verfügbare Ports anzeigen
ls -l /dev/ttyUSB* /dev/ttyAMA* /dev/ttyACM* 2>/dev/null

# In config.py anpassen falls nötig:
# SERIAL_PORT = '/dev/ttyACM0'
```

### Schritt 9: Hotspot-SSID anpassen

In `network_manager.py` die SSID an den Hostnamen anpassen:

```python
HOTSPOT_SSID = 'VDE-Messwand-1'  # Anpassen!
HOTSPOT_PASSWORD = 'vde12345'
```

### Schritt 10: Datenbank initialisieren

```bash
python3 -c "from database import init_db; init_db()"
```

### Schritt 11: Systemd-Service erstellen

```bash
sudo tee /etc/systemd/system/vde-messwand.service << 'EOF'
[Unit]
Description=VDE Messwand Flask App
After=network.target

[Service]
User=vde
Group=vde
WorkingDirectory=/home/vde/vde-messwand
ExecStart=/home/vde/vde-messwand/venv/bin/python app.py
Restart=always
RestartSec=10
Environment="PATH=/home/vde/vde-messwand/venv/bin"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vde-messwand.service
sudo systemctl start vde-messwand.service
```

---

## Raspberry Pi 5: Power-Button (J2-Header)

Der Raspberry Pi 5 hat einen J2-Header für einen externen Power-Button.

### Hardware-Anschluss

Ein NO (Normally Open) Taster wird an den J2-Jumper angeschlossen:
- J2 befindet sich neben dem RTC-Batterieanschluss
- [Offizielle Dokumentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#add-your-own-power-button)

### Power-Button nur zum Einschalten konfigurieren

Standardmäßig kann der Button ein- UND ausschalten. Um nur Einschalten zu erlauben:

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

#### 2. labwc Desktop-Konfiguration (falls Wayland/labwc verwendet wird)

```bash
mkdir -p ~/.config/labwc
cp /etc/xdg/labwc/rc.xml ~/.config/labwc/rc.xml
```

In `~/.config/labwc/rc.xml` die Power-Button Keybind-Aktion entfernen:

```xml
<!-- Vorher -->
<keybind key="XF86PowerOff" onRelease="yes">
  <action name="Execute">
    <command>pwrkey</command>
  </action>
</keybind>

<!-- Nachher (Aktion entfernt) -->
<keybind key="XF86PowerOff" onRelease="yes">
</keybind>
```

#### 3. Power-Button-Events blockieren (empfohlen)

```bash
# Systemd-Service erstellen
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
sudo systemctl start block-power-button.service
```

**Hinweis:** `/dev/input/event0` ist beim Pi 5 standardmäßig der `pwr_button`.
Prüfen mit: `cat /proc/bus/input/devices | grep -A5 pwr_button`

### Ergebnis

Nach der Konfiguration:
- Einschalten per Button funktioniert (Hardware/PMIC gesteuert)
- Herunterfahren per Button ist deaktiviert (Linux ignoriert den Tastendruck)

---

## WiFi-Hotspot

Das System kann einen eigenen WiFi-Hotspot erstellen für direkten Zugriff ohne Router.

### Hotspot aktivieren

1. Navigiere zu **Admin-Panel** -> **Netzwerk**
2. Aktiviere den Toggle "WiFi Hotspot"
3. Verbinde dich mit:
   - **SSID:** (entspricht dem Hostnamen, z.B. `VDE-Messwand-1`)
   - **Passwort:** `vde12345`
4. Öffne im Browser: `http://192.168.50.1`

### Hotspot-Konfiguration

Die Einstellungen können in `network_manager.py` angepasst werden:

```python
HOTSPOT_SSID = 'VDE-Messwand-1'   # Wird durch install.sh automatisch gesetzt
HOTSPOT_PASSWORD = 'vde12345'
HOTSPOT_IP = '192.168.50.1'
```

### Anforderungen für Hotspot

- NetworkManager muss installiert sein (Standard auf Raspberry Pi OS)
- wlan0 Interface muss verfügbar sein
- sudo-Rechte für nmcli (wird durch install.sh konfiguriert)

---

## GPIO-Monitor (Notaus)

Das System kann einen Notaus-Schalter überwachen.

### Konfiguration in config.py

```python
# GPIO-Pins für Schließer-Überwachung (BCM-Nummerierung)
GPIO_MONITOR_PIN1 = 17  # GPIO 17 (physisch Pin 11)
GPIO_MONITOR_PIN2 = 27  # GPIO 27 (physisch Pin 13)

# Warnung-Text
GPIO_WARNING_TEXT = "NOTAUS BETÄTIGT"

# Shutdown-Timeout in Sekunden
GPIO_SHUTDOWN_TIMEOUT = 120
```

### Funktionsweise

- Ein Schließer wird zwischen Pin 17 und Pin 27 angeschlossen
- Geschlossener Schließer (LOW) = Warnung aktiv
- Nach 120 Sekunden aktivem Notaus: automatisches Herunterfahren

---

## Projekt-Struktur

```
vde-messwand/
├── app.py                      # Haupt-Flask-Anwendung
├── config.py                   # Konfigurationsdatei
├── database.py                 # Datenbank-Management
├── requirements.txt            # Python-Abhängigkeiten
├── install.sh                  # Automatisches Installations-Script
│
├── modbus_controller.py        # Modbus RTU Kommunikation
├── relay_controller.py         # Relais-Steuerung
├── serial_handler.py           # Serielle Schnittstelle
├── network_manager.py          # WiFi/Hotspot-Verwaltung
├── gpio_monitor.py             # GPIO-Überwachung (Notaus)
│
├── relais_manager.py           # Relais-Verwaltung
├── training_manager.py         # Training-Konfiguration
├── stromkreis_manager.py       # Stromkreis-Management
├── settings_manager.py         # System-Einstellungen
├── group_manager.py            # Gruppen-Manager
│
├── exam_utils.py               # Prüfungsmodus-Logik
├── relais_excel.py             # Excel Import/Export
├── relais_templates.py         # Relais-Templates
├── read_relay_status.py        # CLI-Tool für Status
│
├── gunicorn_config.py          # Gunicorn-Konfiguration
├── cleanup_gpio.py             # GPIO Cleanup-Script
├── diagnose_modbus.py          # Modbus-Diagnose
│
├── templates/                  # HTML-Templates
│   ├── base.html
│   ├── index.html
│   ├── exam_mode.html
│   ├── manual_mode.html
│   ├── training_*.html
│   ├── admin_*.html
│   └── relay_status.html
│
├── static/
│   ├── css/style.css
│   ├── script.js
│   └── script_pi.js
│
└── fehler_config.csv           # Fehler-Konfiguration
```

---

## Verwendung

### Anwendung starten

```bash
# Manuell (Entwicklung)
cd /home/vde/vde-messwand
source venv/bin/activate
python3 app.py

# Via Systemd-Service (Produktion)
sudo systemctl start vde-messwand
```

Die Anwendung ist erreichbar unter:
- Lokal: `http://localhost` (Port 80)
- Im Netzwerk: `http://<IP-ADRESSE>`
- Bei Hotspot: `http://192.168.50.1`

### Admin-Bereich

Der Admin-Bereich ist PIN-geschützt (Standard: 1234).

**Funktionen:**
- Datenbank - Prüfungsergebnisse anzeigen
- Netzwerk - WLAN/Hotspot-Einstellungen
- Relais-Verwaltung - Gruppierung und Benennung
- Konfiguration - Stromkreise und Kategorien
- Übungsmodus-Verwaltung - Training-Mappings
- Relay Status Monitor - Live Hardware-Status
- Test-Durchlauf - Alle Relais testen

### Prüfungsmodus

1. Prüfungsnummer eingeben
2. Stromkreise für 7 Prüfpunkte auswählen
3. Prüfung durchführen
4. Gefundene Fehler dokumentieren
5. Ergebnis speichern

### Übungsmodus

1. Messgerät auswählen (Fluke, Benning, Gossen, Allgemein)
2. Kategorie wählen (z.B. RISO, Zi, RCD)
3. Zugeordnete Relais werden automatisch aktiviert

### Manueller Modus

- Einzelne Relais ein-/ausschalten
- Gruppen aktivieren/deaktivieren
- Stromkreise direkt steuern

---

## Service-Verwaltung

```bash
# Status prüfen
sudo systemctl status vde-messwand

# Neustart
sudo systemctl restart vde-messwand

# Stoppen
sudo systemctl stop vde-messwand

# Logs anzeigen
sudo journalctl -u vde-messwand -f

# Logs der letzten Stunde
sudo journalctl -u vde-messwand --since "1 hour ago"
```

---

## Hardware-Konfiguration

### Modbus RTU Setup

**Verkabelung:**
- A/B-Leitungen an Modbus-Module
- GND-Verbindung
- 120Ω Abschlusswiderstände an Bus-Enden

**Parameter (in config.py):**
```python
SERIAL_PORT = '/dev/ttyACM0'  # oder /dev/ttyUSB0
BAUD_RATE = 9600
SERIAL_TIMEOUT = 1.0
```

**Modbus-Module:**
```python
MODBUS_MODULES = {
    0: {'slave_id': 1, 'base_addr': 0, 'name': 'Modul 1'},
    1: {'slave_id': 2, 'base_addr': 32, 'name': 'Modul 2'}
}
```

### Hardware-Test

```bash
# Status aller Relais auslesen
cd /home/vde/vde-messwand
source venv/bin/activate
python3 read_relay_status.py

# Modbus-Diagnose
python3 diagnose_modbus.py
```

---

## Troubleshooting

### Serielle Verbindung

```bash
# Verfügbare Ports anzeigen
ls -l /dev/ttyUSB* /dev/ttyAMA* /dev/ttyACM*

# Berechtigungen prüfen
groups $USER  # Sollte 'dialout' enthalten
```

### Hotspot startet nicht

```bash
# NetworkManager prüfen
systemctl status NetworkManager

# wlan0 prüfen
ip link show wlan0

# Logs anzeigen
journalctl -u NetworkManager -f
```

### Service startet nicht

```bash
# Logs prüfen
sudo journalctl -u vde-messwand -n 50

# Manuell testen
cd /home/vde/vde-messwand
source venv/bin/activate
python3 app.py
```

### Datenbank zurücksetzen

```bash
rm vde_messwand.db
python3 -c "from database import init_db; init_db()"
```

---

## API-Endpunkte

### Relais-Steuerung
- `POST /api/relay/on` - Relais einschalten
- `POST /api/relay/off` - Relais ausschalten
- `POST /api/relay/reset` - Alle Relais zurücksetzen
- `GET /api/relay_status` - Status aller Relais

### Training
- `POST /api/training/activate` - Kategorie aktivieren
- `GET /api/training/mappings` - Mappings abrufen
- `POST /api/training/update` - Mapping aktualisieren

### Netzwerk
- `POST /api/network/hotspot/toggle` - Hotspot ein/aus
- `GET /api/network/status` - Netzwerk-Status
- `POST /api/network/wifi/connect` - Mit WLAN verbinden
- `GET /api/network/wifi/scan` - WLANs scannen

### Einstellungen
- `POST /api/wallbox/toggle` - Wallbox aktivieren/deaktivieren

---

## Konfigurationsdateien

### JSON-Dateien
- `relay_groups.json` - Relais-Gruppierungen
- `relay_names.json` - Relais-Benennungen
- `training_config.json` - Training-Mappings
- `stromkreis_config.json` - Stromkreis-Definitionen
- `settings.json` - System-Einstellungen
- `hotspot_state.json` - Hotspot-Status

### Weitere Dateien
- `fehler_config.csv` - Liste aller verfügbaren Fehler
- `config.py` - Zentrale Konfiguration

---

## Changelog

### v1.2 (aktuell)
- **Install-Script**: Vollautomatische Installation mit Hostname-Abfrage
- **Power-Button**: Konfiguration für J2-Header (nur Einschalten)
- **Dokumentation**: Erweiterte README mit allen Details

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
