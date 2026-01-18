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

### Verwaltungsfunktionen
- **Relais-Verwaltung**: Gruppierung, Benennung und Kategorisierung
- **Stromkreis-Management**: Definition und Verwaltung von Stromkreisen
- **Training-Konfiguration**: Kategoriebasierte Relais-Mappings
- **Datenbank**: Speicherung aller Prüfungsergebnisse
- **Excel Import/Export**: Relais-Konfigurationen im- und exportieren

### Hardware-Integration
- **Modbus RTU**: Kommunikation über serielle Schnittstelle
- **64 Relais**: 2 Module mit je 32 Relais
- **Live-Status**: Auslesen des tatsächlichen Hardware-Status

## Technologie-Stack

- **Backend**: Python 3.11+ mit Flask
- **Frontend**: HTML5, CSS3 (Glass-Design), Vanilla JavaScript
- **Datenbank**: SQLite
- **Hardware**: Modbus RTU über pySerial
- **Deployment**: Raspberry Pi optimiert

## Installation

### Voraussetzungen

**Hardware:**
- Raspberry Pi 4 (empfohlen) oder Raspberry Pi 3
- 2x Modbus RTU Relais-Module (je 32 Relais)
- USB-zu-RS485 Adapter oder GPIO-basierter RS485 HAT
- Stromversorgung für Relais-Module

**Software:**
- Raspberry Pi OS (Bullseye oder neuer)
- Python 3.11 oder höher
- Git

### Schritt-für-Schritt Installation

#### 1. System aktualisieren

```bash
sudo apt update
sudo apt upgrade -y
```

#### 2. Python und Abhängigkeiten installieren

```bash
# Python 3.11 installieren (falls nicht vorhanden)
sudo apt install python3 python3-pip python3-venv -y

# System-Pakete für serielle Kommunikation
sudo apt install python3-serial -y

# Git installieren (falls nicht vorhanden)
sudo apt install git -y
```

#### 3. Repository klonen

```bash
cd ~
git clone https://github.com/ulfdogg/VDE0100-600_Messwand.git
cd VDE0100-600_Messwand
```

#### 4. Virtuelle Umgebung erstellen

```bash
python3 -m venv venv
source venv/bin/activate
```

**Wichtig:** Die virtuelle Umgebung muss bei jedem Start aktiviert werden!

#### 5. Python-Abhängigkeiten installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Installierte Pakete:**
- `Flask==2.3.3` - Webframework
- `smbus2==0.4.2` - I2C-Kommunikation
- `pyserial` - Serielle Schnittstelle (wird automatisch installiert)

#### 6. Berechtigungen für serielle Schnittstelle

```bash
# Benutzer zur dialout-Gruppe hinzufügen
sudo usermod -a -G dialout $USER

# Neustart erforderlich, oder sofort aktivieren:
sudo su - $USER
```

#### 7. Serielle Schnittstelle identifizieren

```bash
# Verfügbare serielle Ports anzeigen
ls -l /dev/ttyUSB* /dev/ttyAMA* 2>/dev/null

# Meist:
# /dev/ttyUSB0 - USB-zu-RS485 Adapter
# /dev/ttyAMA0 - GPIO UART (auf Raspberry Pi)
```

#### 8. Konfiguration anpassen

Bearbeite [config.py](config.py) für deine Hardware:

```python
# Serielle Schnittstelle
SERIAL_PORT = '/dev/ttyUSB0'  # Anpassen an deine Hardware!
BAUD_RATE = 9600
SERIAL_TIMEOUT = 1.0

# Modbus-Module
MODBUS_MODULES = [
    {'slave_id': 1, 'name': 'Modul 1', 'relays': 32},
    {'slave_id': 2, 'name': 'Modul 2', 'relays': 32}
]

# Server-Einstellungen
HOST = '0.0.0.0'  # Auf allen Netzwerkschnittstellen hören
PORT = 5000
DEBUG = False     # In Produktion auf False setzen!
```

#### 9. Datenbank initialisieren

```bash
python3 -c "from database import init_db; init_db()"
```

Dies erstellt die SQLite-Datenbank `exams.db` für Prüfungsergebnisse.

#### 10. Hardware-Test (Optional)

```bash
# Status aller Relais auslesen
python3 read_relay_status.py

# Erwartete Ausgabe:
# ✅ Verbunden mit /dev/ttyUSB0
# 📦 Modul 1 (Slave ID: 1)
# Relais 0-31 Status...
```

Falls Fehler auftreten:
- Prüfe SERIAL_PORT in config.py
- Prüfe Verkabelung (A/B-Leitungen)
- Prüfe Modbus Slave IDs der Hardware
- Prüfe Berechtigungen (dialout-Gruppe)

#### 11. Anwendung starten

```bash
# Im vde-messwand Verzeichnis
source venv/bin/activate
python3 app.py
```

**Ausgabe:**
```
✅ Real Modbus RTU connected on /dev/ttyUSB0
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.XXX:5000
```

Die Anwendung ist nun erreichbar unter:
- Lokal: `http://localhost:5000`
- Im Netzwerk: `http://<RASPBERRY-PI-IP>:5000`

### Autostart beim Systemstart (Optional)

#### Systemd Service erstellen

```bash
sudo nano /etc/systemd/system/vde-messwand.service
```

Inhalt:
```ini
[Unit]
Description=VDE Messwand Web Application
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/VDE0100-600_Messwand
Environment="PATH=/home/pi/VDE0100-600_Messwand/venv/bin"
ExecStart=/home/pi/VDE0100-600_Messwand/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Service aktivieren:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable vde-messwand.service
sudo systemctl start vde-messwand.service

# Status prüfen
sudo systemctl status vde-messwand.service

# Logs anzeigen
sudo journalctl -u vde-messwand.service -f
```

### Ersteinrichtung über Web-Interface

1. Öffne `http://<RASPBERRY-PI-IP>:5000`
2. Gehe zu **Admin Panel** (PIN-Eingabe erforderlich)
3. Konfiguriere:
   - **Relais-Verwaltung**: Relais benennen und gruppieren
   - **Konfiguration**: Stromkreise definieren
   - **Übungsmodus-Verwaltung**: Training-Mappings einrichten
   - **Einstellungen**: Admin-PIN ändern

### Update der Anwendung

```bash
cd ~/VDE0100-600_Messwand
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Falls Service läuft:
sudo systemctl restart vde-messwand.service
```

## Projekt-Struktur

```
vde-messwand/
├── app.py                      # Haupt-Flask-Anwendung
├── config.py                   # Konfigurationsdatei
├── database.py                 # Datenbank-Management
├── requirements.txt            # Python-Abhängigkeiten
│
├── Controller/
│   ├── modbus_controller.py    # Modbus RTU Kommunikation
│   ├── relay_controller.py     # Relais-Steuerung
│   └── serial_handler.py       # Serielle Schnittstelle
│
├── Manager/
│   ├── relais_manager.py       # Relais-Verwaltung
│   ├── training_manager.py     # Training-Konfiguration
│   ├── stromkreis_manager.py   # Stromkreis-Management
│   ├── settings_manager.py     # System-Einstellungen
│   └── group_manager.py        # Legacy Gruppen-Manager
│
├── Utils/
│   ├── exam_utils.py           # Prüfungsmodus-Logik
│   ├── relais_excel.py         # Excel Import/Export
│   ├── relais_templates.py     # Relais-Templates
│   └── read_relay_status.py    # CLI-Tool für Status
│
├── templates/                  # HTML-Templates
│   ├── base.html              # Basis-Template
│   ├── index.html             # Startseite
│   ├── exam_mode.html         # Prüfungsmodus
│   ├── manual_mode.html       # Manueller Modus
│   ├── training_*.html        # Training-Seiten
│   ├── admin_*.html           # Admin-Bereich
│   └── relay_status.html      # Live-Monitor
│
├── static/
│   ├── css/
│   │   └── style.css          # Haupt-Stylesheet
│   ├── script.js              # Haupt-JavaScript
│   └── script_pi.js           # Pi-spezifische Scripts
│
└── fehler_config.csv          # Fehler-Konfiguration
```

## Verwendung

### Admin-Bereich

Der Admin-Bereich ist PIN-geschützt (Standard: im System konfigurierbar).

**Funktionen:**
- 📊 Datenbank - Prüfungsergebnisse anzeigen
- 🌐 Netzwerk - WLAN-Einstellungen
- 🔌 Relais-Verwaltung - Gruppierung und Benennung
- ⚙️ Konfiguration - Stromkreise und Kategorien
- 🎓 Übungsmodus-Verwaltung - Training-Mappings
- 📟 Relay Status Monitor - Live Hardware-Status
- 🔧 Test-Durchlauf - Alle Relais testen

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
4. Hilfetext mit aktiven Relais wird angezeigt

### Manueller Modus

- Einzelne Relais ein-/ausschalten
- Gruppen aktivieren/deaktivieren
- Stromkreise direkt steuern

## Hardware-Konfiguration

### Modbus RTU Setup

**Verkabelung:**
- A/B-Leitungen an Modbus-Module
- GND-Verbindung
- 120Ω Abschlusswiderstände an Bus-Enden

**Parameter:**
- Baudrate: 9600
- Datenbits: 8
- Parität: None
- Stopbits: 2
- Timeout: 1.0s

### Relais-Gruppierung

Das System verwendet ein zahlenbasiertes Gruppierungssystem:
- `group_number = 0`: Einzelnes Relais (keine Gruppe)
- `group_number = 1-20`: Gruppennummer

**Beispiel:**
```python
# Relais 5, 10, 15 in Gruppe 1
relais_manager.update_relais_group(5, 1)
relais_manager.update_relais_group(10, 1)
relais_manager.update_relais_group(15, 1)
```

## Datenbank-Schema

### Prüfungen (exams)
```sql
- id: INTEGER PRIMARY KEY
- exam_number: TEXT (eindeutig)
- timestamp: DATETIME
- duration: INTEGER (Sekunden)
- stromkreis_1 bis stromkreis_7: TEXT
- fehler_gefunden: TEXT (JSON Array)
```

## API-Endpunkte

### Relais-Steuerung
- `POST /api/relay/on` - Relais einschalten
- `POST /api/relay/off` - Relais ausschalten
- `POST /api/relay/reset` - Alle Relais zurücksetzen
- `GET /api/relay_status` - Status aller Relais auslesen

### Training
- `POST /api/training/activate` - Kategorie aktivieren
- `GET /api/training/mappings` - Mappings abrufen
- `POST /api/training/update` - Mapping aktualisieren

### Gruppen & Stromkreise
- `POST /api/group/activate` - Gruppe aktivieren
- `POST /api/stromkreis/activate` - Stromkreis aktivieren

### Admin
- `POST /admin/login` - Admin-Login
- `GET /admin/database` - Prüfungsdaten
- `POST /admin/export` - Excel-Export

## CLI-Tools

### Relais-Status auslesen
```bash
python3 read_relay_status.py
```

Zeigt den aktuellen Status aller 64 Relais an.

## Konfigurationsdateien

### JSON-Konfigurationen
- `relay_groups.json` - Relais-Gruppierungen
- `relay_names.json` - Relais-Benennungen
- `training_config.json` - Training-Mappings
- `stromkreis_config.json` - Stromkreis-Definitionen
- `settings.json` - System-Einstellungen

### Fehler-Datenbank
`fehler_config.csv` - Liste aller verfügbaren Fehler für Prüfungen

## Entwicklung

### Code-Stil
- PEP 8 für Python
- Deutsche Kommentare und Dokumentation
- Modulare Architektur mit Manager-Pattern

### Testing
```bash
# Hardware-Test (alle Relais durchschalten)
Zugriff über: Admin Panel → Test-Durchlauf

# Status-Monitor
Zugriff über: Admin Panel → Relay Status Monitor
```

## Troubleshooting

### Serielle Verbindung
```bash
# Verfügbare Ports anzeigen
ls -l /dev/ttyUSB* /dev/ttyAMA*

# Berechtigungen prüfen
sudo usermod -a -G dialout $USER
```

### Modbus-Kommunikation
```bash
# Debug-Ausgabe aktivieren (in modbus_controller.py)
print(f"TX: {frame.hex()}")
print(f"RX: {response.hex()}")
```

### Datenbank zurücksetzen
```bash
rm *.db
python3 -c "from database import init_db; init_db()"
```

## Lizenz

Dieses Projekt ist für Bildungszwecke im Bereich der elektrischen Installationsprüfung entwickelt.



## Changelog

### v1.0 (Initial Release)
- Modulare Architektur mit Manager-System
- Kategoriebasierte Training-Struktur
- Live Relay Status Monitor
- Excel Import/Export
- Glass-Card Design
- Modbus RTU Integration
- Vollständiger Prüfungsmodus
