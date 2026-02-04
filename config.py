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
DATABASE_PATH = 'vde_messwand.db'

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

# Stromkreis-Definitionen
STROMKREISE = {
    1: {
        'name': 'CEE 16A',
        'relays': list(range(0, 10)),
        'description': 'CEE Steckdose 16A'
    },
    2: {
        'name': 'Herdanschlussdose',
        'relays': list(range(10, 20)),
        'description': 'Herdanschlussdose 400V'
    },
    3: {
        'name': 'Steckdose+Lampe 1',
        'relays': list(range(20, 30)),
        'description': 'Steckdosenkreis mit Beleuchtung'
    },
    4: {
        'name': 'Steckdose+Lampe 2',
        'relays': list(range(30, 40)),
        'description': 'Steckdosenkreis mit Beleuchtung'
    },
    5: {
        'name': 'Badsteckdose über RCBO',
        'relays': list(range(40, 50)),
        'description': 'Badezimmer mit RCBO'
    },
    6: {
        'name': 'Wallbox',
        'relays': list(range(50, 60)),
        'description': 'E-Auto Ladestation'
    },
    7: {
        'name': 'RLO',
        'relays': list(range(60, 64)),
        'description': 'RLO Messungen'
    }
}

# Relais-Gruppen (werden immer zusammen geschaltet)
# WICHTIG: Diese Gruppen sind im Code fest definiert.
# Für dynamische Verwaltung siehe Admin-Panel -> Gruppen-Verwaltung
RELAY_GROUPS = {
    'CEE_GRUPPE_1': {
        'relays': [3, 4],  # Relais 4 und 5 in der Benennung mit Start bei 1
        'name': 'CEE Gruppe L1+L2',
        'description': 'Diese beiden Relais werden immer zusammen geschaltet'
    },
    # Weitere fest definierte Gruppen hier einfügen
}

# Beim Programmstart werden zusätzlich Gruppen aus relay_groups.json geladen

# Relais-Namen (optional: für detaillierte Beschriftung einzelner Relais)
RELAY_NAMES = {
    # Beispiele - hier kannst du jeden Relais individuell benennen
    0: 'CEE L1',
    1: 'CEE L2',
    2: 'CEE L3',
    # Relais 3 und 4 sind Teil der Gruppe 'CEE_GRUPPE_1'
    5: 'CEE N-Fehler',
    # ... weitere nach Bedarf
}

# Admin Login
ADMIN_PASSWORD = '1234'

# Prüfungs-Einstellungen
DEFAULT_EXAM_RELAY_COUNT = 3  # Anzahl zufälliger Fehler
EXAM_NUMBER_PREFIX = 'VDE'

# ==================== GPIO-MONITOR KONFIGURATION ====================
# GPIO-Pins für Schließer-Überwachung (BCM-Nummerierung)
# Der Schließer wird zwischen Pin1 und Pin2 angeschlossen
# Geschlossener Schließer (LOW) = Warnung aktiv
GPIO_MONITOR_PIN1 = 17  # GPIO 17 (physisch Pin 11)
GPIO_MONITOR_PIN2 = 27  # GPIO 27 (physisch Pin 13)

# Warnung-Text (erscheint wenn Schließer geschlossen ist)
GPIO_WARNING_TEXT = "NOTAUS BETÄTIGT"

# Shutdown-Timeout in Sekunden (wenn Notaus für diese Zeit aktiv bleibt)
# Standard: 120 Sekunden (2 Minuten)
GPIO_SHUTDOWN_TIMEOUT = 120
