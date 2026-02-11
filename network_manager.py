"""
Netzwerk-Manager für WiFi-Hotspot (Access Point) Mode
"""
import subprocess
import os
import json
import time

# Konfigurationsdatei für Hotspot-Status
HOTSPOT_STATE_FILE = '/home/vde/VDE-Messwand/hotspot_state.json'

# Hotspot-Konfiguration
HOTSPOT_SSID = 'VDE-Messwand-2'
HOTSPOT_PASSWORD = 'vde12345'
HOTSPOT_IP = '192.168.50.1'
HOTSPOT_CON_NAME = 'Hotspot'  # NetworkManager Verbindungsname (nicht SSID!)

def get_hotspot_state():
    """Liest den aktuellen Hotspot-Status"""
    try:
        if os.path.exists(HOTSPOT_STATE_FILE):
            with open(HOTSPOT_STATE_FILE, 'r') as f:
                return json.load(f)
        return {'active': False}
    except Exception as e:
        print(f"Error reading hotspot state: {e}")
        return {'active': False}


def save_hotspot_state(active):
    """Speichert den Hotspot-Status"""
    try:
        with open(HOTSPOT_STATE_FILE, 'w') as f:
            json.dump({'active': active}, f)
        return True
    except Exception as e:
        print(f"Error saving hotspot state: {e}")
        return False


def is_hotspot_active():
    """Prüft ob der Hotspot aktiv ist"""
    try:
        # Prüfe ob wlan0 als AP läuft
        result = subprocess.run(['iwconfig', 'wlan0'],
                              capture_output=True, text=True, timeout=5)
        return 'Mode:Master' in result.stdout
    except Exception as e:
        print(f"Error checking hotspot: {e}")
        return False


def start_hotspot():
    """
    Startet den WiFi-Hotspot (Access Point Mode)
    Verwendet nmcli für moderne NetworkManager-basierte Systeme
    """
    try:
        print("🔄 Starting WiFi Hotspot...")

        # Stoppe bestehende WiFi-Verbindungen
        subprocess.run(['sudo', 'nmcli', 'radio', 'wifi', 'on'],
                      capture_output=True, timeout=10)
        time.sleep(1)

        # Trenne aktive WiFi-Verbindungen
        result = subprocess.run(['nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show', '--active'],
                              capture_output=True, text=True, timeout=10)

        for line in result.stdout.strip().split('\n'):
            if line and '802-11-wireless' in line:
                conn_name = line.split(':')[0]
                print(f"  Disconnecting: {conn_name}")
                subprocess.run(['sudo', 'nmcli', 'connection', 'down', conn_name],
                             capture_output=True, timeout=10)

        time.sleep(2)

        # Lösche alte Hotspot-Verbindung falls vorhanden
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', HOTSPOT_CON_NAME],
                      capture_output=True, timeout=10)

        # Erstelle neuen Hotspot
        cmd = [
            'sudo', 'nmcli', 'device', 'wifi', 'hotspot',
            'ifname', 'wlan0',
            'ssid', HOTSPOT_SSID,
            'password', HOTSPOT_PASSWORD
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(f"✅ Hotspot started: {HOTSPOT_SSID}")
            save_hotspot_state(True)
            return True, f"Hotspot '{HOTSPOT_SSID}' gestartet (Passwort: {HOTSPOT_PASSWORD})"
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            print(f"❌ Failed to start hotspot: {error_msg}")
            return False, f"Fehler: {error_msg}"

    except subprocess.TimeoutExpired:
        return False, "Timeout beim Starten des Hotspots"
    except Exception as e:
        print(f"❌ Error starting hotspot: {e}")
        return False, f"Fehler: {str(e)}"


def stop_hotspot():
    """
    Stoppt den WiFi-Hotspot und aktiviert WiFi-Client-Mode
    """
    try:
        print("🔄 Stopping WiFi Hotspot...")

        # Deaktiviere Hotspot-Verbindung (verwende Verbindungsname, nicht SSID!)
        result = subprocess.run(['sudo', 'nmcli', 'connection', 'down', HOTSPOT_CON_NAME],
                              capture_output=True, text=True, timeout=10)
        print(f"  Connection down result: {result.returncode}")

        time.sleep(2)

        # Lösche Hotspot-Verbindung
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', HOTSPOT_CON_NAME],
                      capture_output=True, timeout=10)

        time.sleep(1)

        # Aktiviere WiFi-Radio (falls deaktiviert)
        subprocess.run(['sudo', 'nmcli', 'radio', 'wifi', 'on'],
                      capture_output=True, timeout=10)

        time.sleep(2)

        # Versuche automatisch mit gespeicherten Netzwerken zu verbinden
        print("  Trying to reconnect to saved WiFi networks...")
        subprocess.run(['sudo', 'nmcli', 'device', 'set', 'wlan0', 'managed', 'yes'],
                      capture_output=True, timeout=10)

        # Trigger WiFi reconnect
        subprocess.run(['sudo', 'nmcli', 'device', 'connect', 'wlan0'],
                      capture_output=True, timeout=10)

        print("✅ Hotspot stopped")
        save_hotspot_state(False)
        return True, "Hotspot gestoppt - Verbinde mit gespeicherten Netzwerken..."

    except subprocess.TimeoutExpired:
        return False, "Timeout beim Stoppen des Hotspots"
    except Exception as e:
        print(f"❌ Error stopping hotspot: {e}")
        return False, f"Fehler: {str(e)}"


def toggle_hotspot():
    """Toggle zwischen Hotspot und WiFi-Client Mode"""
    if is_hotspot_active():
        return stop_hotspot()
    else:
        return start_hotspot()


def get_wifi_networks():
    """Scannt nach verfügbaren WiFi-Netzwerken"""
    try:
        result = subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'list'],
                              capture_output=True, text=True, timeout=15)

        networks = []
        for line in result.stdout.split('\n')[1:]:  # Skip header
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    # Format: * SSID MODE CHAN RATE SIGNAL BARS SECURITY
                    in_use = parts[0] == '*'
                    ssid = parts[1] if not in_use else parts[2] if len(parts) > 2 else ''
                    if ssid and ssid != '--':
                        networks.append({
                            'ssid': ssid,
                            'in_use': in_use
                        })

        return networks[:10]  # Limit to 10 networks
    except Exception as e:
        print(f"Error scanning WiFi: {e}")
        return []


def connect_to_wifi(ssid, password=''):
    """Verbindet mit einem WiFi-Netzwerk"""
    try:
        # Stoppe Hotspot falls aktiv
        if is_hotspot_active():
            stop_hotspot()
            time.sleep(2)

        # Verbinde mit Netzwerk
        if password:
            cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password]
        else:
            cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            return True, f"Verbunden mit '{ssid}'"
        else:
            error_msg = result.stderr if result.stderr else "Unbekannter Fehler"
            return False, f"Verbindung fehlgeschlagen: {error_msg}"

    except subprocess.TimeoutExpired:
        return False, "Timeout bei WiFi-Verbindung"
    except Exception as e:
        return False, f"Fehler: {str(e)}"


def get_current_connection():
    """Gibt Informationen über die aktuelle Verbindung zurück"""
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show', '--active'],
                              capture_output=True, text=True, timeout=10)

        connections = []
        for line in result.stdout.strip().split('\n'):
            if line and 'wlan0' in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    connections.append({
                        'name': parts[0],
                        'type': parts[1]
                    })

        return connections
    except Exception as e:
        print(f"Error getting connection info: {e}")
        return []


def get_network_info():
    """Gibt Netzwerk-Informationen zurück (IP, etc.)"""
    try:
        result = subprocess.run(['ip', 'addr', 'show', 'wlan0'],
                              capture_output=True, text=True, timeout=5)

        ip_address = None
        for line in result.stdout.split('\n'):
            if 'inet ' in line:
                ip_address = line.strip().split()[1].split('/')[0]
                break

        return {
            'interface': 'wlan0',
            'ip': ip_address,
            'hotspot_active': is_hotspot_active()
        }
    except Exception as e:
        print(f"Error getting network info: {e}")
        return {'interface': 'wlan0', 'ip': None, 'hotspot_active': False}


def get_ethernet_info():
    """Gibt Ethernet-Informationen zurück (nur wenn verbunden)"""
    try:
        # Prüfe ob Kabel verbunden ist
        with open('/sys/class/net/eth0/carrier', 'r') as f:
            carrier = f.read().strip()

        if carrier != '1':
            return None  # Kein Kabel verbunden

        # Hole IP-Adresse
        result = subprocess.run(['ip', 'addr', 'show', 'eth0'],
                              capture_output=True, text=True, timeout=5)

        ip_address = None
        for line in result.stdout.split('\n'):
            if 'inet ' in line:
                ip_address = line.strip().split()[1].split('/')[0]
                break

        # Hole Geschwindigkeit
        try:
            with open('/sys/class/net/eth0/speed', 'r') as f:
                speed = f.read().strip()
        except:
            speed = None

        return {
            'interface': 'eth0',
            'ip': ip_address,
            'speed': speed,
            'connected': True
        }
    except Exception as e:
        return None
