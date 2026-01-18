# WiFi-Hotspot Feature

## Übersicht

Das VDE Messwand System verfügt jetzt über einen WiFi-Hotspot-Modus (Access Point), der es ermöglicht, sich direkt mit einem Smartphone oder Tablet zu verbinden, ohne auf ein bestehendes WiFi-Netzwerk angewiesen zu sein.

## Verwendung

### Hotspot einschalten

1. Navigiere zu **Admin-Panel** → **Netzwerk**
2. Aktiviere den Toggle-Schalter bei "WiFi Hotspot (Access Point)"
3. Warte ca. 5-10 Sekunden, bis der Hotspot aktiv ist
4. Verbinde dich mit dem Handy/Tablet mit folgendem Netzwerk:
   - **SSID:** `VDE-Messwand-Setup`
   - **Passwort:** `vde12345`
5. Öffne im Browser: `http://192.168.50.1:5000` oder die angezeigte IP-Adresse

### Hotspot ausschalten

1. Deaktiviere den Toggle-Schalter
2. Das System versucht automatisch, sich mit gespeicherten WiFi-Netzwerken zu verbinden

## Technische Details

### Komponenten

- **network_manager.py**: Modul für Netzwerk-Management
  - `start_hotspot()`: Startet den Access Point
  - `stop_hotspot()`: Stoppt den Access Point und aktiviert WiFi-Client-Mode
  - `toggle_hotspot()`: Schaltet zwischen Modi um
  - `is_hotspot_active()`: Prüft den aktuellen Status

- **API-Endpunkte** (in app.py):
  - `POST /api/network/hotspot/toggle`: Toggle Hotspot an/aus
  - `GET /api/network/status`: Aktueller Netzwerk-Status
  - `POST /api/network/wifi/connect`: Mit WiFi verbinden
  - `GET /api/network/wifi/scan`: WiFi-Netzwerke scannen

- **Frontend** (admin_network.html):
  - Toggle-Schalter mit visueller Rückmeldung
  - Statusanzeige (Aktiv/Inaktiv)
  - Automatische Seiten-Aktualisierung nach Umschaltung

### Verwendete Tools

Das Feature verwendet **NetworkManager** (`nmcli`) für die Netzwerk-Verwaltung:
- `nmcli device wifi hotspot`: Erstellt einen WiFi-Hotspot
- `nmcli connection down/delete`: Stoppt/Löscht Verbindungen
- `nmcli device connect`: Verbindet mit WiFi-Netzwerken

### Systemvoraussetzungen

- NetworkManager muss installiert sein (Standard auf Raspberry Pi OS)
- `wlan0` Interface muss verfügbar sein
- `sudo`-Rechte für Netzwerk-Operationen

### Hotspot-Konfiguration

Die Hotspot-Einstellungen können in `network_manager.py` angepasst werden:

```python
HOTSPOT_SSID = 'VDE-Messwand-Setup'
HOTSPOT_PASSWORD = 'vde12345'
HOTSPOT_IP = '192.168.50.1'
```

## Anwendungsfälle

1. **Ersteinrichtung**: System ohne bestehendes WiFi-Netzwerk konfigurieren
2. **Mobile Nutzung**: Direkter Zugriff vom Handy/Tablet ohne Router
3. **Feldtest**: Verwendung an Orten ohne WiFi-Infrastruktur
4. **Demonstration**: Schnelle Präsentation ohne Netzwerk-Setup

## Fehlerbehebung

### Hotspot startet nicht
- Prüfe, ob NetworkManager läuft: `systemctl status NetworkManager`
- Prüfe, ob wlan0 verfügbar ist: `ip link show wlan0`
- Prüfe Logs: `journalctl -u NetworkManager -f`

### Keine Verbindung möglich
- Warte 10-15 Sekunden nach Aktivierung
- Stelle sicher, dass das Passwort korrekt eingegeben wurde
- Prüfe, ob andere Geräte den Hotspot sehen

### Rückumschaltung funktioniert nicht
- Das System versucht automatisch, mit gespeicherten Netzwerken zu verbinden
- Falls nötig, manuell mit WiFi verbinden über die "WLAN Verbindung" Sektion
- Neustart des Systems: `sudo reboot`

## Sicherheitshinweise

- Das Standard-Passwort (`vde12345`) sollte für produktive Umgebungen geändert werden
- Der Hotspot ist nur für lokale Konfiguration gedacht
- Keine Internetverbindung über den Hotspot (nur lokaler Zugriff)
