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
# Werden aus stromkreise.json geladen und sind über die UI verwaltbar
STROMKREISE = {}

# Relais-Gruppen — werden aus relay_groups.json geladen und sind über die UI verwaltbar
RELAY_GROUPS = {}

# Relais-Namen — werden aus relay_names.json / relais_config.json geladen und sind über die UI verwaltbar
RELAY_NAMES = {}

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
