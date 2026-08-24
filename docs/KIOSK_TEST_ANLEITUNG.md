# 🖥️ VDE Messwand - Kiosk Test Anleitung

## Was macht dieser Test?

Der Kiosk-Test **öffnet einen Browser direkt auf dem Pi-Display** und simuliert einen echten Benutzer, der am Terminal steht und die Anwendung bedient.

**Du siehst ALLES live auf dem Display**, genau als würdest du selbst dort stehen!

## 🚀 Schnellstart

```bash
./START_KIOSK_TEST.sh
```

Das war's! Der Rest ist selbsterklärend.

## 📋 Voraussetzungen

### 1. Server muss laufen

```bash
# Server starten auf korrekter IP:
gunicorn -b 10.100.72.191:8000 app:app

# Oder im Hintergrund:
gunicorn -b 10.100.72.191:8000 app:app --daemon
```

### 2. Chromium WebDriver installiert

```bash
sudo apt-get update
sudo apt-get install chromium-browser chromium-chromedriver
```

### 3. Selenium installiert

```bash
pip3 install selenium
```

## 🎬 Zwei Test-Modi

### 1️⃣ Visual Test (`stress_test_visual.py`)

**Was passiert:**
- Browser öffnet sich **VOLLBILD** auf dem Pi-Display
- Führt automatisch Test-Szenarien durch
- Macht **Screenshots** von jedem Schritt
- Läuft durch: Prüfungsmodus, Manueller Modus, Admin

**Perfekt für:**
- Debug und Fehlersuche
- Screenshots für Dokumentation
- Visuelle Überprüfung der UI

**Starten:**
```bash
python3 stress_test_visual.py
# Wähle Option 3 (Beide Modi)
```

**Screenshots werden gespeichert in:**
```
stress_test_screenshots/
  └── 20251222_143022/
      ├── 001_session1_step01_startseite.png
      ├── 002_session1_step02_before_menu_click.png
      └── ...
```

---

### 2️⃣ Kiosk Simulator (`kiosk_simulator.py`)

**Was passiert:**
- Browser öffnet sich **VOLLBILD** (echter Kiosk-Mode)
- Simuliert **realistisches Benutzerverhalten**:
  - Wartezeiten 2-5 Sekunden (wie echter Mensch)
  - Liest Bildschirm
  - Wählt zufällige Optionen
  - Macht Pausen zwischen Aktionen

**3 Szenarien:**
1. **Prüfungsmodus** - Benutzer macht eine Prüfung
2. **Manueller Modus** - Benutzer wählt Fehler aus
3. **Admin-Bereich** - Admin schaut sich Status an

**Perfekt für:**
- Realistische Stresstests
- Benutzerverhalten simulieren
- Langzeit-Tests (Continuous Mode)

**Starten:**
```bash
python3 kiosk_simulator.py
```

**Modi:**
- **Option 1-3:** Einzelnes Szenario (einmalig)
- **Option 4:** Alle Szenarien nacheinander
- **Option 5:** Continuous (5 Minuten Endlos-Loop)
- **Option 6:** Extended (30 Minuten Stresstest)

---

## 🎯 Was du auf dem Display siehst

### Beispiel: Prüfungsmodus

```
┌─────────────────────────────────────────┐
│  🖥️  PI-DISPLAY (VOLLBILD)            │
├─────────────────────────────────────────┤
│                                         │
│  Browser öffnet sich automatisch...     │
│                                         │
│  1. Startseite wird geladen             │
│     ↓                                   │
│  2. Klick auf "Prüfungsmodus"          │
│     ↓                                   │
│  3. Prüfungsnummer wird angezeigt       │
│     ↓                                   │
│  4. Klick auf "Prüfung Starten"        │
│     ↓                                   │
│  5. Timer läuft... (20:00, 19:59...)   │
│     ↓                                   │
│  6. Nach 10-20 Sekunden: Klick auf      │
│     "Prüfung Beenden"                   │
│     ↓                                   │
│  7. Ergebnis-Seite mit Prüfungsnummer   │
│     ↓                                   │
│  8. Zurück zur Startseite               │
│                                         │
└─────────────────────────────────────────┘
```

Du siehst **alles live** - jeder Klick, jede Navigation, jeden Formular-Eintrag!

---

## ⚙️ Anpassungen

### IP-Adresse ändern

Falls sich deine IP ändert:

```bash
# In beiden Dateien anpassen:
nano stress_test_visual.py
# Zeile 19: BASE_URL = "http://DEINE_IP:8000"

nano kiosk_simulator.py
# Zeile 15: BASE_URL = "http://DEINE_IP:8000"
```

### Wartezeiten anpassen

In [kiosk_simulator.py](kiosk_simulator.py:21-23):

```python
REALISTIC_DELAYS = True  # False = schneller
MIN_DELAY = 2  # Kürzer = schneller
MAX_DELAY = 5  # Kürzer = schneller
```

### Admin-Code ändern

In [kiosk_simulator.py](kiosk_simulator.py:16):

```python
ADMIN_CODE = "1234"  # Dein Code
```

### Vollbild deaktivieren (für Tests)

In [stress_test_visual.py](stress_test_visual.py:23):

```python
FULLSCREEN = False  # Normales Fenster statt Vollbild
```

In [kiosk_simulator.py](kiosk_simulator.py:18):

```python
FULLSCREEN = False  # Normales Fenster statt Vollbild
```

---

## 🐛 Troubleshooting

### Problem: "Browser startet nicht"

```bash
# Prüfe ob chromium-chromedriver installiert ist:
which chromedriver

# Falls nicht:
sudo apt-get install chromium-chromedriver

# Prüfe Chromium:
chromium-browser --version
```

### Problem: "Display not found"

```bash
# Prüfe DISPLAY-Variable:
echo $DISPLAY

# Sollte ausgeben: :0

# Falls leer, setze manuell:
export DISPLAY=:0
```

### Problem: "Server nicht erreichbar"

```bash
# Prüfe ob Server läuft:
curl http://10.100.72.191:8000

# Prüfe Gunicorn:
ps aux | grep gunicorn

# Starte Server neu:
pkill gunicorn
gunicorn -b 10.100.72.191:8000 app:app
```

### Problem: "Browser bleibt hängen"

```bash
# Beende alle Chrome-Prozesse:
pkill chromium
pkill chrome

# Starte Test neu:
./START_KIOSK_TEST.sh
```

### Problem: "Permission denied"

```bash
# Mache Scripts ausführbar:
chmod +x START_KIOSK_TEST.sh
chmod +x stress_test_visual.py
chmod +x kiosk_simulator.py
```

---

## 📊 Continuous Mode (Langzeit-Test)

Der Continuous Mode simuliert **echten Kiosk-Betrieb** über längere Zeit:

```bash
python3 kiosk_simulator.py
# Wähle Option 6 (30 Minuten)
```

**Was passiert:**
- Endlos-Loop von zufälligen Szenarien
- 5-15 Sekunden Pause zwischen "Benutzern"
- Läuft 30 Minuten (oder Ctrl+C zum Abbrechen)
- Findet Race-Conditions und Memory-Leaks

**Output:**
```
🔄 Zyklus 1
🎲 Zufälliges Szenario: Prüfungsmodus
✅ Prüfungsmodus-Szenario abgeschlossen!
💤 Pause zwischen Benutzern (8s)...

🔄 Zyklus 2
🎲 Zufälliges Szenario: Manueller Modus
✅ Manueller Modus-Szenario abgeschlossen!
💤 Pause zwischen Benutzern (12s)...

...
```

---

## 🎥 Screenshots automatisch anschauen

Nach Visual Test:

```bash
# Öffne Screenshot-Ordner:
cd stress_test_screenshots

# Liste alle Sessions:
ls -la

# Öffne neueste Session:
cd $(ls -t | head -1)

# Zeige alle Screenshots als Slideshow (Raspberry Pi):
feh --slideshow-delay 2 *.png

# Oder einzeln anschauen:
feh 001_session1_step01_startseite.png
```

---

## 💡 Best Practices

### 1. Teste zuerst mit einzelnem Szenario

```bash
python3 kiosk_simulator.py
# Wähle Option 1 (nur Prüfungsmodus)
```

### 2. Dann vollständiger Test

```bash
python3 kiosk_simulator.py
# Wähle Option 4 (alle Szenarien)
```

### 3. Langzeit-Test über Nacht

```bash
# Starte 30-Minuten Test im Hintergrund:
nohup python3 kiosk_simulator.py << EOF > kiosk_test.log 2>&1 &
6
EOF

# Überwache Log:
tail -f kiosk_test.log
```

### 4. Screenshots für Dokumentation

```bash
python3 stress_test_visual.py
# → Screenshots in stress_test_screenshots/
# → Perfekt für Bug-Reports oder Handbücher
```

---

## 🔒 Browser beenden

Falls Browser hängen bleibt:

```bash
# Alle Chrome-Prozesse beenden:
pkill -9 chromium

# Oder sanfter:
pkill chromium-browse
```

---

## 📈 Performance-Monitoring

Während der Test läuft:

```bash
# In separatem Terminal: CPU/RAM überwachen
htop

# Oder speziell Gunicorn:
ps aux | grep gunicorn

# Netzwerk-Traffic:
iftop -i wlan0  # oder eth0
```

---

## ✅ Zusammenfassung

| Was | Befehl | Dauer | Sichtbar |
|-----|--------|-------|----------|
| Quick-Start | `./START_KIOSK_TEST.sh` | Interaktiv | ✅ Ja |
| Visual Test | `python3 stress_test_visual.py` | 2-5 Min | ✅ Ja + Screenshots |
| Kiosk Single | `python3 kiosk_simulator.py` (Option 1-3) | 1-2 Min | ✅ Ja |
| Kiosk All | `python3 kiosk_simulator.py` (Option 4) | 3-5 Min | ✅ Ja |
| Continuous | `python3 kiosk_simulator.py` (Option 5) | 5 Min | ✅ Ja |
| Extended | `python3 kiosk_simulator.py` (Option 6) | 30 Min | ✅ Ja |

---

## 🎯 Empfehlung

**Für dich (Display-Sichtbarkeit):**

```bash
./START_KIOSK_TEST.sh
# Wähle Option 2 (Kiosk Simulator)
# Wähle Option 4 (Alle Szenarien)
```

Das gibt dir die **beste Demo** - du siehst alles live auf dem Display, genau wie ein echter Benutzer!

**Viel Erfolg! 🚀**
