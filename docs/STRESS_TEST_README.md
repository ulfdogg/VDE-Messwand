# VDE Messwand - Stresstest Dokumentation

## Übersicht

Dieses Projekt enthält zwei verschiedene Stresstest-Tools für das VDE Messwand System:

1. **`stress_test.py`** - Vollständiger GUI-Test mit Selenium (simuliert echte Browserinteraktionen)
2. **`stress_test_simple.py`** - API-basierter Test (schneller, ohne Browser)

## Installation

### 1. Selenium WebDriver installieren (für GUI-Tests)

```bash
# Chromium Browser installieren (falls noch nicht vorhanden)
sudo apt-get update
sudo apt-get install chromium-browser chromium-chromedriver

# Python-Dependencies installieren
pip3 install -r requirements_test.txt
```

### 2. Für Simple Tests (nur API)

```bash
# Nur requests ist nötig
pip3 install requests
```

## Verwendung

### Option 1: Simple Stresstest (empfohlen für erste Tests)

Der einfache Test benötigt **keinen Browser** und ist **schneller**:

```bash
# Server muss laufen (in einem separaten Terminal):
gunicorn -b 0.0.0.0:8000 app:app

# Test starten:
python3 stress_test_simple.py
```

**Interaktive Auswahlmöglichkeiten:**
1. Rapid-Fire Test - Bombardiert Server mit Requests (60s)
2. Prüfungsmodus-Simulation - Simuliert 10 Prüfungsdurchläufe
3. Manueller Modus - Simuliert 20 manuelle Fehlerkonfigurationen
4. Concurrent Test - 5 parallele Threads (30s)
5. ALLES - Vollständiger Stresstest

### Option 2: GUI Stresstest mit Selenium

Simuliert echte Benutzer im Kiosk-Mode:

```bash
# Konfiguration anpassen (optional)
nano stress_test.py
# -> BASE_URL, ADMIN_CODE, PARALLEL_USERS, STRESS_TEST_DURATION

# Test starten
python3 stress_test.py
```

**Was wird getestet:**
- Parallele Browser-Sessions (Standard: 3)
- Prüfungsmodus (Start, Timer, Beenden)
- Manueller Modus (Fehlerauswahl, Zuschalten, Zurücksetzen)
- Admin-Panel (Login, Navigation)
- API-Endpunkte (parallel zu GUI-Tests)

## Test-Szenarien

### 1. Kiosk-Mode Simulation

```bash
# In stress_test.py den Kiosk-Mode aktivieren:
# Zeile 134: options.add_argument('--kiosk') # Kommentar entfernen
```

### 2. Headless-Betrieb (ohne sichtbares Fenster)

```bash
# In stress_test.py Headless aktivieren:
# Zeile 137: options.add_argument('--headless') # Kommentar entfernen
```

### 3. Maximale Last

```python
# In stress_test.py anpassen:
PARALLEL_USERS = 10  # Mehr parallele Browser
STRESS_TEST_DURATION = 600  # 10 Minuten
```

## Fehlerauswertung

### Fehler-Logs

Beide Tests erstellen JSON-Reports mit allen gefundenen Fehlern:

```bash
# GUI-Test:
cat stress_test_errors.json

# Simple-Test:
cat stress_test_simple_errors.json
```

### Report-Struktur

```json
{
  "test_duration": "0:05:23",
  "total_errors": 3,
  "total_warnings": 5,
  "errors": [
    {
      "timestamp": "2025-12-22T14:30:45",
      "category": "API_ERROR",
      "message": "HTTP 500 bei /api/relay_status",
      "details": {
        "status": 500,
        "response": "Internal Server Error..."
      }
    }
  ],
  "warnings": [...]
}
```

## Fehler-Kategorien

Die Tests erkennen folgende Fehlertypen:

| Kategorie | Beschreibung |
|-----------|--------------|
| `SELENIUM_SETUP` | WebDriver konnte nicht initialisiert werden |
| `NAVIGATION` | Seite konnte nicht geladen werden |
| `CLICK` | Element konnte nicht angeklickt werden |
| `INPUT` | Eingabefeld konnte nicht ausgefüllt werden |
| `API_ERROR` | HTTP-Fehler bei API-Request |
| `API_REQUEST` | Verbindungsfehler zu API |
| `TEST_EXECUTION` | Unerwarteter Fehler während Test |

## Performance-Metriken

### GUI-Test Output

```
Session 1: 23 Aktionen durchgeführt
Session 2: 19 Aktionen durchgeführt
Session 3: 21 Aktionen durchgeführt
API-Requests: 3421
Fehler: 0
Warnungen: 2
```

### Simple-Test Output

```
Gesamt-Requests: 1247
Erfolgreich: 1245
Fehler: 2
Erfolgsrate: 99.8%
```

## Typische Probleme & Lösungen

### Problem: "Server nicht erreichbar"

```bash
# Prüfe ob Gunicorn läuft:
ps aux | grep gunicorn

# Starte Server:
gunicorn -b 0.0.0.0:8000 app:app
```

### Problem: "chromedriver nicht gefunden"

```bash
# Installiere Chromium + Driver:
sudo apt-get install chromium-chromedriver

# Oder verwende WebDriver Manager:
pip3 install webdriver-manager
```

### Problem: "Zu viele parallele Connections"

```python
# Reduziere PARALLEL_USERS in stress_test.py:
PARALLEL_USERS = 2  # Weniger Browser-Sessions
```

### Problem: Display-Fehler im Kiosk-Mode

```bash
# Setze DISPLAY-Variable:
export DISPLAY=:0

# Oder verwende Headless-Mode (siehe oben)
```

## Erweiterte Konfiguration

### Custom Test-Szenarien erstellen

```python
# In stress_test.py eine neue Test-Methode hinzufügen:

def test_custom_scenario(self):
    """Dein eigener Test"""
    self.navigate_to(f"{BASE_URL}/deine_seite")
    self.click_element(By.ID, "dein_button")
    # ... weitere Aktionen

# Dann in run_random_tests hinzufügen:
test_functions = [
    self.test_prüfungsmodus,
    self.test_custom_scenario  # <-- neue Funktion
]
```

### Fehler-Injection testen

```python
# In simple-Test ungültige Daten senden:
tester.test_endpoint("POST", "/set_manual_errors", {
    "errors": {"invalid": "data"}
})
```

## Best Practices

1. **Immer zuerst Simple-Test ausführen**
   - Schneller und einfacher zu debuggen
   - Findet Backend-Probleme

2. **GUI-Tests nur für Integration**
   - Testen das Zusammenspiel Frontend/Backend
   - Finden UI-spezifische Bugs

3. **Schrittweise Last erhöhen**
   - Start mit 1-2 parallel Users
   - Erhöhe nur wenn stabil

4. **Logs überwachen**
   - `journalctl -u VDE-Messwand -f` (falls als Service)
   - Oder direkte Gunicorn-Ausgabe beobachten

5. **Nach Tests aufräumen**
   - Admin → Datenbank → Testdaten löschen
   - Relais zurücksetzen

## Automation

### Cronjob für regelmäßige Tests

```bash
# Crontab bearbeiten:
crontab -e

# Täglich um 2 Uhr Simple-Test ausführen:
0 2 * * * cd /home/vde/VDE-Messwand && python3 stress_test_simple.py << EOF
1
EOF
```

### CI/CD Integration

```bash
#!/bin/bash
# test_ci.sh

# Starte Server
gunicorn -b 0.0.0.0:8000 app:app &
SERVER_PID=$!
sleep 5

# Führe Tests aus
python3 stress_test_simple.py << EOF
5
EOF

# Prüfe Exit-Code
if [ $? -eq 0 ]; then
    echo "✅ Tests erfolgreich"
    kill $SERVER_PID
    exit 0
else
    echo "❌ Tests fehlgeschlagen"
    kill $SERVER_PID
    exit 1
fi
```

## Support

Bei Fragen oder Problemen:
- Überprüfe Logs: `stress_test_errors.json`
- Teste Server manuell: `curl http://localhost:8000`
- Prüfe Gunicorn-Output auf Exceptions
