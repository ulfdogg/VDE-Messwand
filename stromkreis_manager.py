"""
VDE Messwand - Stromkreis-Verwaltung
Backend-Funktionen für dynamische Stromkreis-Verwaltung
"""
import json
import os

STROMKREISE_FILE = 'stromkreise.json'
KATEGORIEN_FILE = 'kategorien.json'


def load_stromkreise_from_file():
    """
    Lädt Stromkreise aus JSON-Datei

    Returns:
        Dictionary mit Stromkreisen (int-Keys)
    """
    if os.path.exists(STROMKREISE_FILE):
        try:
            with open(STROMKREISE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # String-Keys aus JSON zu int konvertieren
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"Error loading stromkreise: {e}")
            return {}
    return {}


def save_stromkreise_to_file(stromkreise):
    """
    Speichert Stromkreise in JSON-Datei

    Args:
        stromkreise: Dictionary mit Stromkreisen

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        with open(STROMKREISE_FILE, 'w', encoding='utf-8') as f:
            json.dump(stromkreise, f, indent=2, ensure_ascii=False)
        print(f"✓ Stromkreise saved to {STROMKREISE_FILE}")
        return True
    except Exception as e:
        print(f"Error saving stromkreise: {e}")
        return False


def get_all_stromkreise():
    """
    Gibt alle definierten Stromkreise zurück (aus stromkreise.json)

    Returns:
        Dictionary mit allen Stromkreisen
    """
    return load_stromkreise_from_file()


def add_stromkreis(name, description=''):
    """
    Fügt einen neuen Stromkreis hinzu

    Args:
        name: Name des Stromkreises
        description: Beschreibung

    Returns:
        (success, message, stromkreis_id)
    """
    if not name or not name.strip():
        return False, "Name darf nicht leer sein", None

    # Lade bestehende File-Stromkreise
    stromkreise = load_stromkreise_from_file()

    # Prüfe ob Name bereits vergeben
    for sk_data in stromkreise.values():
        if sk_data['name'].strip().lower() == name.strip().lower():
            return False, f"Stromkreis '{name}' existiert bereits", None

    # Finde nächste freie ID
    existing_ids = set(stromkreise.keys())

    new_id = 1
    while new_id in existing_ids:
        new_id += 1

    # Füge neuen Stromkreis hinzu
    stromkreise[new_id] = {
        'name': name.strip(),
        'description': description.strip()
    }

    # Speichern
    if save_stromkreise_to_file(stromkreise):
        return True, f"Stromkreis '{name}' erfolgreich erstellt", new_id
    else:
        return False, "Fehler beim Speichern", None


def update_stromkreis(stromkreis_id, name, description=''):
    """
    Aktualisiert einen existierenden Stromkreis

    Args:
        stromkreis_id: ID des zu aktualisierenden Stromkreises
        name: Neuer Name
        description: Neue Beschreibung

    Returns:
        (success, message)
    """
    stromkreise = load_stromkreise_from_file()

    try:
        stromkreis_id = int(stromkreis_id)
    except:
        return False, "Ungültige Stromkreis-ID"

    if stromkreis_id not in stromkreise:
        return False, "Stromkreis nicht gefunden"

    if not name or not name.strip():
        return False, "Name darf nicht leer sein"

    # Update (relays-Feld beibehalten falls vorhanden, für Rückwärtskompatibilität)
    stromkreise[stromkreis_id] = {
        'name': name.strip(),
        'description': description.strip()
    }

    if save_stromkreise_to_file(stromkreise):
        return True, f"Stromkreis '{name}' erfolgreich aktualisiert"
    else:
        return False, "Fehler beim Speichern"


def delete_stromkreis(stromkreis_id):
    """
    Löscht einen Stromkreis

    Args:
        stromkreis_id: ID des zu löschenden Stromkreises

    Returns:
        (success, message)
    """
    stromkreise = load_stromkreise_from_file()

    try:
        stromkreis_id = int(stromkreis_id)
    except:
        return False, "Ungültige Stromkreis-ID"

    if stromkreis_id not in stromkreise:
        return False, "Stromkreis nicht gefunden"

    stromkreis_name = stromkreise[stromkreis_id]['name']
    del stromkreise[stromkreis_id]

    if save_stromkreise_to_file(stromkreise):
        return True, f"Stromkreis '{stromkreis_name}' erfolgreich gelöscht"
    else:
        return False, "Fehler beim Speichern"


def get_stromkreis_statistics():
    """
    Gibt Statistiken über Stromkreise zurück

    Returns:
        Dictionary mit Statistiken
    """
    stromkreise = get_all_stromkreise()
    total_relays = 0
    covered_relays = set()

    for sk_data in stromkreise.values():
        relays = sk_data.get('relays', [])
        total_relays += len(relays)
        covered_relays.update(relays)

    return {
        'total_stromkreise': len(stromkreise),
        'total_relay_assignments': total_relays,
        'unique_covered_relays': len(covered_relays),
        'uncovered_relays': 64 - len(covered_relays),
        'stromkreise': stromkreise
    }


# ==================== KATEGORIEN-VERWALTUNG ====================

def load_kategorien_from_file():
    """
    Lädt Kategorien aus JSON-Datei

    Returns:
        Liste von Kategorien
    """
    if os.path.exists(KATEGORIEN_FILE):
        try:
            with open(KATEGORIEN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading kategorien: {e}")
            return []
    return []


def save_kategorien_to_file(kategorien):
    """
    Speichert Kategorien in JSON-Datei

    Args:
        kategorien: Liste von Kategorien

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        with open(KATEGORIEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(kategorien, f, indent=2, ensure_ascii=False)
        print(f"✓ Kategorien saved to {KATEGORIEN_FILE}")
        return True
    except Exception as e:
        print(f"Error saving kategorien: {e}")
        return False


def get_all_kategorien():
    """
    Gibt alle verfügbaren Kategorien zurück (aus kategorien.json)

    Returns:
        Liste von Kategorien
    """
    kategorien = load_kategorien_from_file()
    kategorien.sort()
    return kategorien


def add_kategorie(name):
    """
    Fügt eine neue Kategorie hinzu

    Args:
        name: Name der Kategorie

    Returns:
        (success, message)
    """
    if not name or not name.strip():
        return False, "Name darf nicht leer sein"

    name = name.strip()

    # Prüfe ob bereits vorhanden
    all_kategorien = get_all_kategorien()
    if name in all_kategorien:
        return False, f"Kategorie '{name}' existiert bereits"

    # Lade custom kategorien
    kategorien = load_kategorien_from_file()
    kategorien.append(name)

    if save_kategorien_to_file(kategorien):
        return True, f"Kategorie '{name}' erfolgreich erstellt"
    else:
        return False, "Fehler beim Speichern"


def delete_kategorie(name):
    """
    Löscht eine Kategorie

    Args:
        name: Name der zu löschenden Kategorie

    Returns:
        (success, message)
    """
    kategorien = load_kategorien_from_file()

    if name not in kategorien:
        return False, "Kategorie nicht gefunden"

    kategorien.remove(name)

    if save_kategorien_to_file(kategorien):
        return True, f"Kategorie '{name}' erfolgreich gelöscht"
    else:
        return False, "Fehler beim Speichern"
