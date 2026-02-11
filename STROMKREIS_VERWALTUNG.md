# Stromkreis- und Kategorie-Verwaltung

## Übersicht

Die VDE Messwand unterstützt jetzt die **dynamische Verwaltung** von:
- ⚡ **Stromkreisen** (für den manuellen Modus)
- 🏷️ **Kategorien** (für Relais und Gruppen)

Keine hardcodierten Werte mehr in `config.py` - alles kann über die Oberfläche verwaltet werden!

## Neue Funktionen

### 1. Stromkreis-Verwaltung

**Admin-Panel → Stromkreise** (`/admin_stromkreise`)

Hier können Sie:
- ➕ **Neue Stromkreise erstellen** mit Namen und Relais-Bereich
- ✏️ **Stromkreise bearbeiten** (Name, Beschreibung, Relais-Zuordnung)
- 🗑️ **Stromkreise löschen** (außer die in config.py definierten)
- 📊 **Statistiken sehen** (Anzahl, zugeordnete Relais, etc.)

**Beispiel:**
- Name: "CEE 32A Steckdose"
- Beschreibung: "CEE Steckdose für Werkstatt"
- Start-Relais: 0
- Anzahl Relais: 10
- → Erstellt Stromkreis mit Relais 0-9

### 2. Kategorie-Verwaltung

**Kategorien** können über die API verwaltet werden:
- Standard-Kategorien: RISO, Zi, Zs, Drehfeld, RCD
- ➕ Custom-Kategorien über API hinzufügen
- 🗑️ Custom-Kategorien löschen (Standard-Kategorien bleiben)

### 3. Verbesserte Relais-Benennung

**Admin-Panel → Relais-Benennung** (`/admin_relay_names`)

Jetzt mit:
- 🏷️ **Kategorie-Dropdown** (dynamisch geladen)
- ⚡ **Stromkreis-Feld** (für Zuordnung)
- 📝 **Name-Feld** wie bisher

Alle drei Felder werden zusammen gespeichert!

### 4. Verbesserte Gruppen-Verwaltung

**Admin-Panel → Relais-Gruppen** (`/admin_groups`)

Jetzt mit:
- 🏷️ **Kategorie-Dropdown** (dynamisch geladen)
- ⚡ **Stromkreis-Feld**
- 📝 **Name und Beschreibung** wie bisher

## Datei-Struktur

Die Daten werden in JSON-Dateien gespeichert:

```
VDE-Messwand/
├── stromkreise.json       # Custom Stromkreise
├── kategorien.json        # Custom Kategorien
├── relay_groups.json      # Custom Relais-Gruppen (bereits vorhanden)
└── relay_names.json       # Relais-Namen mit Kategorie/Stromkreis (erweitert)
```

## API-Endpunkte

### Stromkreise

```
GET  /api/stromkreise              # Alle Stromkreise abrufen
POST /api/stromkreise/add          # Neuen Stromkreis erstellen
POST /api/stromkreise/update       # Stromkreis aktualisieren
POST /api/stromkreise/delete       # Stromkreis löschen
```

### Kategorien

```
GET  /api/kategorien               # Alle Kategorien abrufen
POST /api/kategorien/add           # Neue Kategorie hinzufügen
POST /api/kategorien/delete        # Kategorie löschen
```

## Datenstruktur

### Stromkreis (stromkreise.json)

```json
{
  "8": {
    "name": "CEE 32A",
    "description": "CEE Steckdose 32A für Werkstatt",
    "relays": [64, 65, 66, 67, 68, 69, 70, 71, 72, 73]
  }
}
```

### Relay-Namen (relay_names.json)

**Neue erweiterte Struktur:**

```json
{
  "0": {
    "name": "CEE L1",
    "category": "RISO",
    "stromkreis": "L1"
  },
  "1": {
    "name": "CEE L2",
    "category": "Zi",
    "stromkreis": "L2"
  }
}
```

**Alte Struktur (wird noch unterstützt):**

```json
{
  "0": "CEE L1",
  "1": "CEE L2"
}
```

### Kategorien (kategorien.json)

```json
[
  "Spannungsfall",
  "Erdung",
  "Custom Kategorie"
]
```

## Kompatibilität

- ✅ **Rückwärtskompatibel**: Alte `config.py` Einträge funktionieren weiterhin
- ✅ **Merge-Logik**: JSON-Dateien haben Vorrang vor config.py
- ✅ **Schutz**: Config.py-Einträge können in der UI nicht gelöscht werden (Badge: "In config.py definiert")

## Migration

### Bestehende Stromkreise in config.py

Die in `config.py` definierten Stromkreise (ID 1-7) bleiben bestehen und werden als "nicht editierbar" markiert.

Neue Stromkreise bekommen automatisch die nächste freie ID (ab 8).

### Bestehende Kategorien

Die 5 Standard-Kategorien bleiben immer verfügbar:
- RISO
- Zi
- Zs
- Drehfeld
- RCD

Zusätzliche Kategorien können über die API hinzugefügt werden.

## Verwendung im Code

### Stromkreise laden

```python
from stromkreis_manager import get_all_stromkreise

stromkreise = get_all_stromkreise()
# Enthält sowohl config.py als auch JSON-Einträge
```

### Kategorien laden

```python
from stromkreis_manager import get_all_kategorien

kategorien = get_all_kategorien()
# ['Drehfeld', 'RCD', 'RISO', 'Zi', 'Zs', ...]
```

### Relais-Namen mit Kategorie laden

```python
from group_manager import get_all_relay_names

relay_names = get_all_relay_names()
# {
#   0: {'name': 'CEE L1', 'category': 'RISO', 'stromkreis': 'L1'},
#   1: 'Alte Struktur (nur String)'
# }
```

## Nächste Schritte

Optional könnten folgende Features hinzugefügt werden:

1. **Import/Export**: CSV-Import für Bulk-Konfiguration
2. **Kategorien-UI**: Separate Admin-Seite für Kategorie-Verwaltung
3. **Vorlagen**: Vordefinierte Stromkreis-Templates
4. **Validierung**: Warnung bei Relais-Überschneidungen

## Neue Dateien

- `stromkreis_manager.py` - Backend für Stromkreis- und Kategorie-Verwaltung
- `templates/admin_stromkreise.html` - UI für Stromkreis-Verwaltung
- `STROMKREIS_VERWALTUNG.md` - Diese Dokumentation
