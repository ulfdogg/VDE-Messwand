# Anlage: Programmcode – VDE Messwand

**Projektarbeit:** VDE Messwand – Interaktive Prüf- und Übungsanlage
**Datum:** 28.03.2026
**Plattform:** Raspberry Pi 5, Python 3, Flask, Modbus RTU

---

## Inhaltsverzeichnis

1. [Projektstruktur](#1-projektstruktur)
2. [Konfiguration – `config.py`](#2-konfiguration--configpy)
3. [Hauptanwendung – `app.py`](#3-hauptanwendung--apppy)
   - [Flask-Initialisierung und globale Variablen](#31-flask-initialisierung-und-globale-variablen)
   - [Prüfungsmodus-Routen](#32-prüfungsmodus-routen)
   - [Anwendungsstart und GPIO-Initialisierung](#33-anwendungsstart-und-gpio-initialisierung)
4. [Hardware-Schicht](#4-hardware-schicht)
   - [Modbus RTU Controller – `hardware/modbus_controller.py`](#41-modbus-rtu-controller)
   - [Relay Controller – `hardware/relay_controller.py`](#42-relay-controller)
   - [GPIO Monitor – `hardware/gpio_monitor.py`](#43-gpio-monitor)
5. [Manager-Module](#5-manager-module)
   - [Datenbank – `managers/database.py`](#51-datenbank)
   - [Prüfungs-Hilfsfunktionen – `managers/exam_utils.py`](#52-prüfungs-hilfsfunktionen)
   - [Relais-Verwaltung – `managers/relais_manager.py`](#53-relais-verwaltung)
   - [Übungsmodus – `managers/training_manager.py`](#54-übungsmodus)
   - [Netzwerk-Manager – `managers/network_manager.py`](#55-netzwerk-manager)

---

## 1. Projektstruktur

```
VDE-Messwand/
├── app.py                    # Flask-Hauptanwendung, alle API-Routen
├── config.py                 # Zentrale Konfiguration
├── gunicorn_config.py        # Produktions-Webserver-Konfiguration
├── requirements.txt          # Python-Abhängigkeiten
│
├── hardware/                 # Hardware-Abstraktionsschicht
│   ├── modbus_controller.py  # Modbus RTU Kommunikation
│   ├── relay_controller.py   # High-Level Relais-Steuerung
│   ├── gpio_monitor.py       # GPIO-Überwachung (Notaus)
│   └── serial_handler.py     # Serielle Schnittstelle
│
├── managers/                 # Geschäftslogik-Module
│   ├── database.py           # SQLite Datenbank
│   ├── exam_utils.py         # Prüfungslogik
│   ├── relais_manager.py     # Relais-Konfigurationsverwaltung
│   ├── training_manager.py   # Übungsmodus-Konfiguration
│   ├── network_manager.py    # WLAN / Hotspot-Verwaltung
│   ├── group_manager.py      # Relais-Gruppenverwaltung
│   ├── stromkreis_manager.py # Stromkreis-Definitionen
│   ├── settings_manager.py   # Systemeinstellungen
│   └── relais_excel.py       # Excel-Export/-Import
│
├── templates/                # Jinja2 HTML-Templates
│   ├── base.html             # Basis-Layout
│   ├── index.html            # Startseite
│   ├── exam_mode.html        # Prüfungsmodus
│   ├── manual_mode.html      # Manueller Modus
│   ├── training_mode.html    # Übungsmodus
│   └── admin_panel.html      # Admin-Bereich
│
├── static/                   # CSS, JavaScript
│   └── script.js             # Frontend-Logik
│
└── data/                     # Laufzeitdaten (JSON, SQLite)
    ├── vde_messwand.db       # Prüfungsdatenbank
    ├── relais_config.json    # Relais-Konfiguration
    └── stromkreise.json      # Stromkreis-Definitionen
```

---

## 2. Konfiguration – `config.py`

Alle systemweiten Parameter werden zentral in `config.py` definiert.

```python
"""
VDE Messwand - Zentrale Konfiguration
"""
import os

# Flask Konfiguration
SECRET_KEY = 'vde_messwand_secret_key_2024'
HOST = '0.0.0.0'
PORT = 80
DEBUG = True  # Für Produktion auf False, für Entwicklung auf True

# Datenbank
DATABASE_PATH = 'data/vde_messwand.db'

# Serial/Modbus Konfiguration
SERIAL_PORT = '/dev/ttyACM0' if os.path.exists('/dev/ttyACM0') else \
              '/dev/ttyACM1' if os.path.exists('/dev/ttyACM1') else \
              '/dev/ttyACM0'
BAUD_RATE = 9600
SERIAL_TIMEOUT = 1.0

# Modbus Module
MODBUS_MODULES = {
    0: {'slave_id': 1, 'base_addr': 0, 'name': 'Modul 1'},
    1: {'slave_id': 2, 'base_addr': 32, 'name': 'Modul 2'}
}

# Admin Login
ADMIN_PASSWORD = '1234'

# Sicherheitsrelais (letztes Relais, Index 63 = Relais 64)
# Wird vor dem Schütz der Messpannungsfreigabe geschaltet
# Immer beim Neustart AUS, Einschalten nur per Code
SAFETY_RELAY_ID = 63

# Prüfungs-Einstellungen
DEFAULT_EXAM_RELAY_COUNT = 3  # Anzahl zufälliger Fehler
EXAM_NUMBER_PREFIX = 'VDE'

# GPIO-Pins für Schließer-Überwachung (BCM-Nummerierung)
GPIO_MONITOR_PIN1 = 17  # GPIO 17 (physisch Pin 11)
GPIO_MONITOR_PIN2 = 27  # GPIO 27 (physisch Pin 13)

# Warnung-Text (erscheint wenn Schließer geschlossen ist)
GPIO_WARNING_TEXT = "NOTAUS BETÄTIGT"

# Shutdown-Timeout in Sekunden (wenn Notaus für diese Zeit aktiv bleibt)
GPIO_SHUTDOWN_TIMEOUT = 120
```

---

## 3. Hauptanwendung – `app.py`

### 3.1 Flask-Initialisierung und globale Variablen

```python
"""
VDE Messwand - Hauptanwendung
"""
from flask import Flask, render_template, request, jsonify, Response, send_file
from jinja2 import FileSystemLoader
import os, io, csv, time
from datetime import datetime

# Import eigener Module
from config import *
from managers.database import *
from hardware.relay_controller import RelayController
from managers.exam_utils import *
from managers.group_manager import *
from managers.settings_manager import *
from managers.stromkreis_manager import *
from managers.relais_manager import *
from managers.training_manager import *
from managers.network_manager import (
    is_hotspot_active, toggle_hotspot, get_wifi_networks,
    connect_to_wifi, get_current_connection, get_network_info
)
from hardware.gpio_monitor import init_gpio_monitor, get_gpio_status, cleanup_gpio

# Flask App initialisieren
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.jinja_loader = FileSystemLoader('templates', encoding='utf-8')

# Logging-Filter: /api/gpio/status aus den Logs ausblenden
import logging
class NoGPIOStatusFilter(logging.Filter):
    def filter(self, record):
        return '/api/gpio/status' not in record.getMessage()

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addFilter(NoGPIOStatusFilter())

# Globale Instanzen
relay_controller = RelayController()
exam_active = False
exam_client_ip = None     # IP des Clients, der die Prüfung gestartet hat
exam_number_current = None
exam_start_time = None    # Unix-Timestamp (time.time())


def get_client_ip():
    """Gibt die IP-Adresse des aktuellen Clients zurück (auch hinter Proxies)"""
    return request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()


def exam_lock_response():
    """Standardantwort wenn eine Prüfung aktiv ist und die Aktion blockiert wird"""
    return jsonify({
        'success': False,
        'error': 'Prüfung aktiv',
        'message': 'Diese Aktion ist während einer laufenden Prüfung gesperrt.'
    }), 423
```

### 3.2 Prüfungsmodus-Routen

```python
# ==================== PRÜFUNGSMODUS ====================

@app.route('/exam_mode')
def exam_mode():
    """Prüfungsmodus-Seite"""
    exam_settings = get_exam_settings()
    if exam_active and exam_number_current:
        number = exam_number_current
    else:
        number = generate_exam_number()
    return render_template('exam_mode.html',
                           exam_number=number,
                           exam_duration_minutes=exam_settings['exam_duration_minutes'])


@app.route('/start_exam', methods=['POST'])
def start_exam():
    """Startet eine neue Prüfung mit zufälligen Fehlern"""
    global exam_active, exam_client_ip, exam_number_current, exam_start_time
    import time as _time

    exam_number = request.json.get('exam_number')
    selected_relays = select_random_relays()

    # Relais aktivieren (Gruppen werden automatisch zusammen geschaltet)
    for relay_id in selected_relays:
        relay_controller.set_relay(relay_id, True)

    # In Datenbank speichern (wird automatisch normalisiert)
    save_examination(exam_number, selected_relays)

    exam_active = True
    exam_client_ip = get_client_ip()
    exam_number_current = exam_number
    exam_start_time = _time.time()
    return jsonify({
        'success': True,
        'selected_errors': selected_relays,
        'exam_number': exam_number
    })


@app.route('/finish_exam', methods=['POST'])
def finish_exam():
    """Beendet eine Prüfung"""
    global exam_active, exam_client_ip, exam_number_current, exam_start_time

    # Nur die IP, die die Prüfung gestartet hat, darf sie beenden
    if exam_active and exam_client_ip and get_client_ip() != exam_client_ip:
        return jsonify({
            'success': False,
            'error': 'Nicht autorisiert',
            'message': 'Nur das Gerät, das die Prüfung gestartet hat, kann sie beenden.'
        }), 403

    exam_number = request.json.get('exam_number')
    duration = request.json.get('duration', 0)

    relay_controller.reset_all_relays()
    update_examination_duration(exam_number, duration)

    exam_active = False
    exam_client_ip = None
    exam_number_current = None
    exam_start_time = None
    return jsonify({'success': True})
```

### 3.3 Anwendungsstart und GPIO-Initialisierung

```python
def initialize_app(skip_gpio_check=False):
    """Initialisiert die App einmalig"""
    init_db()

    # Lade dynamische Gruppen und Namen beim Start
    import config
    config.RELAY_GROUPS = get_all_groups()
    config.RELAY_NAMES = get_all_relay_names()

    # Initialisiere GPIO-Monitor
    gpio_pin1 = getattr(config, 'GPIO_MONITOR_PIN1', 17)
    gpio_pin2 = getattr(config, 'GPIO_MONITOR_PIN2', 27)
    from managers.settings_manager import get_gpio_shutdown_timeout
    gpio_shutdown_timeout = get_gpio_shutdown_timeout()

    # Bei Flask dev server: nur im Reloader-Prozess initialisieren
    if skip_gpio_check or os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not DEBUG:
        monitor = init_gpio_monitor(
            pin1=gpio_pin1,
            pin2=gpio_pin2,
            shutdown_timeout=gpio_shutdown_timeout
        )
        # Sicherheitsrelais beim Notaus automatisch abschalten
        def _notaus_callback():
            from config import SAFETY_RELAY_ID
            if relay_controller.safety_relay_state:
                relay_controller.safety_relay_state = False
                relay_controller.set_relay(SAFETY_RELAY_ID, False)
        if monitor:
            monitor.on_notaus_active = _notaus_callback

    # Sicherheitsrelais beim Start sicher ausschalten
    relay_controller.safety_relay_state = False
    relay_controller.set_relay(SAFETY_RELAY_ID, False)

    try:
        app.run(host=HOST, port=PORT, debug=DEBUG)
    finally:
        cleanup_gpio()


if __name__ == '__main__':
    initialize_app()
```

---

## 4. Hardware-Schicht

### 4.1 Modbus RTU Controller

`hardware/modbus_controller.py` implementiert die direkte serielle Kommunikation nach dem Modbus-RTU-Protokoll.

```python
"""
VDE Messwand - Modbus RTU Controller
"""
import struct
import time
from hardware.serial_handler import serial, SERIAL_AVAILABLE


class ModbusRTU:
    """Modbus RTU Kommunikation mit CRC-Prüfung und Retry-Logik"""

    def __init__(self, port, baudrate=9600, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.last_command_time = 0
        self.min_command_interval = 0.1  # 100 ms Mindestabstand zwischen Befehlen
        self.connect()

    def calculate_crc16(self, data):
        """CRC-16 Modbus Berechnung"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc >> 1) ^ 0xA001 if crc & 0x0001 else crc >> 1
        return struct.pack('<H', crc)

    def send_command(self, slave_id, function_code, start_addr, data, retry_count=3):
        """Modbus-Befehl senden mit Retry-Logik"""
        for attempt in range(retry_count):
            try:
                if not self.serial_conn or not self.serial_conn.is_open:
                    self.connect()

                self.wait_for_command_interval()
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()

                # Frame zusammenbauen: Slave-ID + Funktionscode + Adresse + Daten + CRC
                frame = struct.pack('>BBH', slave_id, function_code, start_addr) + data
                frame += self.calculate_crc16(frame)

                bytes_written = self.serial_conn.write(frame)
                self.serial_conn.flush()
                time.sleep(0.05)  # Wartezeit für Antwort

                # Antwort empfangen
                response = bytearray()
                start_time = time.time()
                while len(response) < 8:
                    if time.time() - start_time > self.timeout:
                        break
                    if self.serial_conn.in_waiting > 0:
                        response.extend(self.serial_conn.read(self.serial_conn.in_waiting))
                        time.sleep(0.01)
                    else:
                        time.sleep(0.01)

                # CRC der Antwort prüfen
                if len(response) >= 5:
                    received_crc = response[-2:]
                    calculated_crc = self.calculate_crc16(response[:-2])
                    if received_crc == calculated_crc:
                        return True
                    else:
                        if attempt < retry_count - 1:
                            time.sleep(0.15 * (attempt + 1))
                            continue
                else:
                    if attempt < retry_count - 1:
                        time.sleep(0.15 * (attempt + 1))
                        continue

            except Exception as e:
                if attempt < retry_count - 1:
                    time.sleep(0.1 * (attempt + 1))
                    continue

        return False

    def write_single_coil(self, slave_id, coil_addr, state):
        """Einzelnes Relais schalten (Modbus FC05)"""
        value = 0xFF00 if state else 0x0000
        data = struct.pack('>H', value)
        return self.send_command(slave_id, 0x05, coil_addr, data)

    def write_multiple_coils(self, slave_id, start_addr, states):
        """Mehrere Relais gleichzeitig schalten (Modbus FC15)"""
        num_coils = len(states)
        byte_count = (num_coils + 7) // 8

        coil_bytes = []
        for i in range(byte_count):
            byte_val = 0
            for bit in range(8):
                coil_index = i * 8 + bit
                if coil_index < num_coils and states[coil_index]:
                    byte_val |= (1 << bit)
            coil_bytes.append(byte_val)

        data = struct.pack('>HB', num_coils, byte_count) + bytes(coil_bytes)
        return self.send_command(slave_id, 0x0F, start_addr, data)
```

### 4.2 Relay Controller

`hardware/relay_controller.py` bietet eine High-Level-Schnittstelle für die 64 Relais auf 2 Modbus-Modulen.

```python
"""
VDE Messwand - Relay Controller
High-Level Relais-Steuerung
"""
import time
from hardware.modbus_controller import ModbusRTU
from config import SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT, MODBUS_MODULES, SAFETY_RELAY_ID


class RelayController:
    """High-Level Relais-Steuerung für 64 Relais auf 2 Modulen"""

    def __init__(self):
        self.active_relays = []
        self.modbus = ModbusRTU(SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT)
        self.relay_states = {0: [False] * 32, 1: [False] * 32}
        self.safety_relay_state = False  # Immer AUS beim Start

    def get_module_info(self, relay_num):
        """
        Ermittelt Modul, lokale Adresse und Slave-ID für ein Relais.
        Relais 0-31 → Modul 1 (Slave ID 1)
        Relais 32-63 → Modul 2 (Slave ID 2)
        """
        if relay_num < 32:
            return 0, relay_num, MODBUS_MODULES[0]['slave_id']
        else:
            return 1, relay_num - 32, MODBUS_MODULES[1]['slave_id']

    def set_relay(self, relay_num, state):
        """
        Schaltet ein einzelnes Relais (oder eine Gruppe, wenn es Teil einer ist).

        Args:
            relay_num: Globale Relais-Nummer (0-63)
            state: True = EIN, False = AUS
        """
        try:
            if not 0 <= relay_num <= 63:
                return False

            # Prüfen ob Teil einer Gruppe – alle Gruppenrelais zusammen schalten
            group_name, relay_group = self.get_relay_group(relay_num)
            representative = relay_group[0]

            success = True
            for relay in relay_group:
                module_idx, local_relay, slave_id = self.get_module_info(relay)
                self.relay_states[module_idx][local_relay] = state
                relay_success = self.modbus.write_single_coil(slave_id, local_relay, state)
                if not relay_success:
                    success = False
                time.sleep(0.1)  # 100 ms Pause für stabile Bus-Kommunikation

            # Nur den Repräsentanten in active_relays tracken
            if success:
                if state and representative not in self.active_relays:
                    self.active_relays.append(representative)
                elif not state and representative in self.active_relays:
                    self.active_relays.remove(representative)

            return success

        except Exception as e:
            print(f"Error setting relay {relay_num}: {e}")
            return False

    def reset_all_relays(self):
        """Setzt alle Relais auf beiden Modulen zurück (FC15 für gesamtes Modul)"""
        success = True
        for module_idx in [0, 1]:
            slave_id = MODBUS_MODULES[module_idx]['slave_id']
            states = [False] * 32
            module_success = self.modbus.write_multiple_coils(slave_id, 0, states)
            if module_success:
                self.relay_states[module_idx] = [False] * 32
            else:
                success = False
        self.active_relays = []
        return success
```

### 4.3 GPIO Monitor

`hardware/gpio_monitor.py` überwacht einen Schließerkontakt (Notaus) an zwei GPIO-Pins. Unterstützt Raspberry Pi 5 (`gpiod`) und ältere Modelle (`RPi.GPIO`).

```python
"""
GPIO Monitor für Schließer-Überwachung (Notaus)
Unterstützt Raspberry Pi 5 (gpiod) und ältere Modelle (RPi.GPIO)
"""
import time
import threading

# GPIO-Bibliothek importieren
GPIO_BACKEND = None
GPIO_AVAILABLE = False

try:
    import gpiod
    GPIO_BACKEND = 'gpiod'
    GPIO_AVAILABLE = True
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_BACKEND = 'RPi.GPIO'
        GPIO_AVAILABLE = True
    except (ImportError, RuntimeError):
        GPIO_AVAILABLE = False


class GPIOMonitor:
    """Überwacht GPIO-Pins für Schließer-Status"""

    def __init__(self, pin1=17, pin2=27, shutdown_timeout=120):
        """
        Args:
            pin1: Erster GPIO-Pin (BCM-Nummerierung)
            pin2: Zweiter GPIO-Pin (BCM-Nummerierung)
            shutdown_timeout: Sekunden bis zum automatischen Shutdown
        """
        self.pin1 = pin1
        self.pin2 = pin2
        self.is_active = False
        self.monitoring = False
        self.monitor_thread = None
        self.shutdown_timeout = shutdown_timeout
        self.notaus_start_time = None
        self.shutdown_triggered = False
        self.on_notaus_active = None  # Callback bei Notaus-Aktivierung

        if GPIO_AVAILABLE:
            try:
                if GPIO_BACKEND == 'gpiod':
                    self._init_gpiod()
                elif GPIO_BACKEND == 'RPi.GPIO':
                    self._init_rpi_gpio()
                self.start_monitoring()
            except Exception as e:
                print(f"Fehler bei GPIO-Initialisierung: {e}")

    def _read_pin_state(self):
        """Liest den aktuellen Pin-Zustand (LOW = Schließer geschlossen = Notaus aktiv)"""
        try:
            if GPIO_BACKEND == 'gpiod' and self.lines:
                values = self.lines.get_values()
                return 0 in values  # LOW an einem Pin = aktiv
            elif GPIO_BACKEND == 'RPi.GPIO':
                return (GPIO.input(self.pin1) == GPIO.LOW or
                        GPIO.input(self.pin2) == GPIO.LOW)
        except Exception:
            pass
        return False

    def _monitor_loop(self):
        """Überwachungs-Thread: prüft Schließer-Status und triggert Shutdown"""
        while self.monitoring:
            try:
                pin_active = self._read_pin_state()

                if pin_active and not self.is_active:
                    self.is_active = True
                    self.notaus_start_time = time.time()
                    if self.on_notaus_active:
                        self.on_notaus_active()

                elif not pin_active and self.is_active:
                    self.is_active = False
                    self.notaus_start_time = None

                # Automatischer Shutdown nach Timeout
                if (self.is_active and self.notaus_start_time and
                        not self.shutdown_triggered and
                        time.time() - self.notaus_start_time >= self.shutdown_timeout):
                    self.shutdown_triggered = True
                    import subprocess
                    subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=False)

            except Exception as e:
                print(f"GPIO-Monitor Fehler: {e}")

            time.sleep(0.1)  # 100 ms Polling-Intervall
```

---

## 5. Manager-Module

### 5.1 Datenbank

`managers/database.py` verwaltet alle Prüfungsdatensätze in einer SQLite-Datenbank.

```python
"""
VDE Messwand - Datenbank-Verwaltung
"""
import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH, EXAM_NUMBER_PREFIX


def init_db():
    """Initialisiert die Datenbank und erstellt die Tabelle falls nicht vorhanden"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS examinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_number TEXT UNIQUE,
            active_relays TEXT,
            timestamp DATETIME,
            duration INTEGER
        )
    ''')
    conn.commit()
    conn.close()


def generate_exam_number():
    """Generiert eine fortlaufende Prüfungsnummer (z. B. VDE-42)"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT exam_number FROM examinations ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if result:
        try:
            last_number = int(result[0].split('-')[-1])
            next_number = last_number + 1
        except:
            next_number = 1
    else:
        next_number = 1

    return f"{EXAM_NUMBER_PREFIX}-{next_number}"


def save_examination(exam_number, active_relays):
    """
    Speichert eine neue Prüfung in der Datenbank.
    Normalisiert Relais-Gruppen und speichert Klartextnamen.
    """
    normalized_relays = normalize_relay_list(active_relays)
    relay_names = relay_list_to_names(normalized_relays)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO examinations (exam_number, active_relays, timestamp, duration)
        VALUES (?, ?, ?, ?)
    ''', (exam_number, json.dumps(relay_names), datetime.now(), 0))
    conn.commit()
    conn.close()


def update_examination_duration(exam_number, duration):
    """Aktualisiert die Prüfungsdauer nach Abschluss der Prüfung"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE examinations SET duration = ? WHERE exam_number = ?',
        (duration, exam_number)
    )
    conn.commit()
    conn.close()


def get_relay_display_name(relay_num):
    """
    Gibt den Anzeigenamen für ein Relais zurück.
    Reihenfolge: relais_config.json → relay_names.json → 'Relais X'
    """
    from managers.relais_manager import get_all_relais_config
    from managers.group_manager import get_all_relay_names

    relais_config = get_all_relais_config()
    cfg = relais_config.get(relay_num, {})
    name = cfg.get('name', '').strip() if isinstance(cfg, dict) else ''
    if name:
        return name

    relay_names = get_all_relay_names()
    relay_data = relay_names.get(relay_num, {})
    if isinstance(relay_data, str):
        name = relay_data
    elif isinstance(relay_data, dict):
        name = relay_data.get('name', '')
    return name.strip() if name.strip() else f'Relais {relay_num}'
```

### 5.2 Prüfungs-Hilfsfunktionen

`managers/exam_utils.py` implementiert die zufällige Fehlerauswahl für Prüfungen, getrennt nach Stromkreisen.

```python
"""
VDE Messwand - Prüfungs-Hilfsfunktionen
"""
import random
from config import DEFAULT_EXAM_RELAY_COUNT, SAFETY_RELAY_ID
from managers.relais_manager import get_all_relais_config, get_groups_overview
from managers.stromkreis_manager import get_all_stromkreise
from managers.settings_manager import get_wallbox_enabled, get_exam_settings


def select_random_relays(count=None):
    """
    Wählt zufällige Relais aus verschiedenen Stromkreisen für eine Prüfung aus.

    Regeln:
    - Pro Stromkreis maximal ein Fehler (realistisches Prüfungsszenario)
    - Sicherheitsrelais (SAFETY_RELAY_ID) wird ausgeschlossen
    - Wallbox-Stromkreis kann per Einstellung deaktiviert werden
    - Erlaubte Stromkreise können im Admin-Bereich eingeschränkt werden

    Returns:
        Liste der ausgewählten Relais-Nummern
    """
    exam_settings = get_exam_settings()
    if count is None:
        count = exam_settings.get('exam_error_count', DEFAULT_EXAM_RELAY_COUNT)
    allowed_stromkreise = exam_settings.get('exam_allowed_stromkreise', [])

    relais_config = get_all_relais_config()
    stromkreise = get_all_stromkreise()
    wallbox_enabled = get_wallbox_enabled()

    # Erstelle Mapping: Stromkreis → verfügbare Relais
    stromkreis_to_relais = {}
    for sk_id, sk_data in stromkreise.items():
        if not wallbox_enabled and sk_data['name'] == 'Wallbox':
            continue
        if allowed_stromkreise and str(sk_id) not in allowed_stromkreise:
            continue

        relais_list = []
        for relay_num in range(64):
            if relay_num == SAFETY_RELAY_ID:
                continue
            relay_data = relais_config.get(relay_num, {})
            if relay_data.get('stromkreis') == sk_data['name']:
                relais_list.append(relay_num)

        if relais_list:
            stromkreis_to_relais[sk_id] = {
                'name': sk_data['name'],
                'relays': relais_list
            }

    available_stromkreise = list(stromkreis_to_relais.values())

    if len(available_stromkreise) < count:
        count = len(available_stromkreise)

    if count == 0:
        # Fallback: Wähle aus allen konfigurierten Relais
        effective_list = get_effective_relay_list()
        return random.sample(effective_list, min(3, len(effective_list)))

    # Pro Stromkreis einen zufälligen Vertreter wählen
    selected_stromkreise = random.sample(available_stromkreise, count)
    selected_relays = []

    for stromkreis in selected_stromkreise:
        relay_num = random.choice(stromkreis['relays'])
        selected_relays.append(relay_num)

    return selected_relays
```

### 5.3 Relais-Verwaltung

`managers/relais_manager.py` verwaltet die Konfiguration aller 64 Relais (Name, Kategorie, Stromkreis, Gruppe).

```python
"""
VDE Messwand - Modulare Relais-Verwaltung
"""
import json
import os

RELAIS_CONFIG_FILE = 'data/relais_config.json'


def load_relais_config():
    """Lädt Relais-Konfiguration aus JSON-Datei"""
    if os.path.exists(RELAIS_CONFIG_FILE):
        try:
            with open(RELAIS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading relais config: {e}")
    return {}


def save_relais_config(config):
    """Speichert Relais-Konfiguration in JSON-Datei"""
    try:
        with open(RELAIS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving relais config: {e}")
        return False


def get_relais_by_group_number(group_number):
    """
    Gibt alle Relais einer Gruppen-Nummer zurück.
    group_number = 0 → kein Gruppen-Member
    group_number 1-99 → Gruppe (alle werden gemeinsam geschaltet)
    """
    config = load_relais_config()
    relais_in_group = []
    for relay_num_str, relay_data in config.items():
        if relay_data.get('group_number') == group_number:
            relais_in_group.append(int(relay_num_str))
    return sorted(relais_in_group)


def get_groups_overview():
    """
    Gibt eine Übersicht über alle Gruppen zurück.

    Returns:
        {group_number: {name, relays, category, stromkreis}}
    """
    config = load_relais_config()
    groups = {}

    for relay_num_str, relay_data in config.items():
        group_num = relay_data.get('group_number', 0)
        if group_num and group_num > 0:
            if group_num not in groups:
                groups[group_num] = {
                    'name': relay_data.get('name', f'Gruppe {group_num}'),
                    'relays': [],
                    'category': relay_data.get('category', ''),
                    'stromkreis': relay_data.get('stromkreis', '')
                }
            groups[group_num]['relays'].append(int(relay_num_str))

    # Relais innerhalb jeder Gruppe sortieren
    for group_num in groups:
        groups[group_num]['relays'].sort()

    return groups
```

### 5.4 Übungsmodus

`managers/training_manager.py` speichert, welche Relais bei welcher Übungskategorie und welchem Messgerät-Typ aktiviert werden sollen.

```python
"""
VDE Messwand - Übungsmodus-Verwaltung
Konfiguration welche Relais bei welcher Übung/Kategorie geschaltet werden

Datenstruktur (training_config.json):
{
    "RISO": {           ← Messkategorie (z. B. Isolationswiderstand)
        "fluke": [2, 5, 9],    ← Relais für Fluke-Messgerät
        "benning": [2, 5, 9]   ← Relais für Benning-Messgerät
    },
    "Zi": {
        "fluke": [10, 15, 20]
    }
}
"""
import json
import os

TRAINING_CONFIG_FILE = 'training_config.json'


def load_training_config():
    """Lädt Übungsmodus-Konfiguration aus JSON-Datei"""
    if os.path.exists(TRAINING_CONFIG_FILE):
        try:
            with open(TRAINING_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Automatische Migration von alter Struktur (page → category)
                if config:
                    first_key = list(config.keys())[0]
                    if first_key in ['fluke', 'benning', 'gossen', 'general']:
                        return convert_old_to_new_structure(config)
                return config
        except Exception as e:
            print(f"Error loading training config: {e}")
    return {}


def convert_old_to_new_structure(old_config):
    """
    Konvertiert alte Struktur (page → category → relais)
    zur neuen Struktur (category → page → relais)
    """
    new_config = {}
    for page_id, categories in old_config.items():
        for category, relais_list in categories.items():
            if category not in new_config:
                new_config[category] = {}
            new_config[category][page_id] = relais_list
    save_training_config(new_config)
    return new_config


def get_training_relays(category, page_id):
    """
    Gibt die konfigurierten Relais für eine Übung zurück.

    Args:
        category: Messkategorie (z. B. 'RISO', 'Zi')
        page_id: Messgerät-Typ ('fluke', 'benning', 'gossen')

    Returns:
        Liste von Relais-Nummern oder leere Liste
    """
    config = load_training_config()
    return config.get(category, {}).get(page_id, [])
```

### 5.5 Netzwerk-Manager

`managers/network_manager.py` verwaltet den WLAN-Hotspot (Access Point Modus) über `nmcli`.

```python
"""
Netzwerk-Manager für WiFi-Hotspot (Access Point) Mode
"""
import subprocess
import os
import json
import time

HOTSPOT_STATE_FILE = '/home/vde/VDE-Messwand/data/hotspot_state.json'
HOTSPOT_SSID = 'VDE-Messwand-2'
HOTSPOT_PASSWORD = 'vde12345'
HOTSPOT_IP = '192.168.50.1'
HOTSPOT_CON_NAME = 'Hotspot'


def is_hotspot_active():
    """Prüft ob der Hotspot aktiv ist (wlan0 im AP-Modus)"""
    try:
        result = subprocess.run(['iwconfig', 'wlan0'],
                                capture_output=True, text=True, timeout=5)
        return 'Mode:Master' in result.stdout
    except Exception:
        return False


def start_hotspot():
    """
    Startet den WiFi-Hotspot via NetworkManager (nmcli).
    Trennt zuerst bestehende WLAN-Verbindungen.
    """
    # Bestehende WLAN-Verbindungen trennen
    result = subprocess.run(
        ['nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show', '--active'],
        capture_output=True, text=True, timeout=10
    )
    for line in result.stdout.strip().split('\n'):
        if line and '802-11-wireless' in line:
            conn_name = line.split(':')[0]
            subprocess.run(['sudo', 'nmcli', 'connection', 'down', conn_name],
                           capture_output=True, timeout=10)
    time.sleep(2)

    # Neuen Hotspot erstellen und aktivieren
    subprocess.run([
        'sudo', 'nmcli', 'connection', 'add',
        'type', 'wifi',
        'ifname', 'wlan0',
        'con-name', HOTSPOT_CON_NAME,
        'autoconnect', 'no',
        'ssid', HOTSPOT_SSID,
        'mode', 'ap',
        'ipv4.method', 'shared',
        'ipv4.addresses', f'{HOTSPOT_IP}/24',
        '802-11-wireless-security.key-mgmt', 'wpa-psk',
        '802-11-wireless-security.psk', HOTSPOT_PASSWORD
    ], capture_output=True, timeout=15)

    result = subprocess.run(
        ['sudo', 'nmcli', 'connection', 'up', HOTSPOT_CON_NAME],
        capture_output=True, text=True, timeout=15
    )
    return result.returncode == 0


def toggle_hotspot():
    """
    Schaltet den Hotspot um (EIN → AUS oder AUS → EIN).

    Returns:
        (success: bool, active: bool, message: str)
    """
    currently_active = is_hotspot_active()
    if currently_active:
        # Hotspot ausschalten
        subprocess.run(['sudo', 'nmcli', 'connection', 'down', HOTSPOT_CON_NAME],
                       capture_output=True, timeout=10)
        return True, False, "Hotspot deaktiviert"
    else:
        success = start_hotspot()
        return success, success, "Hotspot aktiviert" if success else "Fehler beim Starten"
```

---

*Ende der Anlage – Alle Dateipfade beziehen sich auf das Projektverzeichnis `/home/vde/VDE-Messwand/`*
