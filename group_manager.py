"""
VDE Messwand - Relais-Gruppen und Relais-Namen Verwaltung
Backend-Funktionen für dynamische Gruppenverwaltung und Benennung
"""
import json
import os
from config import DATABASE_PATH

GROUPS_FILE = 'relay_groups.json'
RELAY_NAMES_FILE = 'relay_names.json'


def load_groups_from_file():
    """
    Lädt Gruppen aus JSON-Datei
    
    Returns:
        Dictionary mit Gruppen
    """
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading groups: {e}")
            return {}
    return {}


def save_groups_to_file(groups):
    """
    Speichert Gruppen in JSON-Datei
    
    Args:
        groups: Dictionary mit Gruppen
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        with open(GROUPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(groups, f, indent=2, ensure_ascii=False)
        print(f"✓ Groups saved to {GROUPS_FILE}")
        return True
    except Exception as e:
        print(f"Error saving groups: {e}")
        return False


def load_relay_names_from_file():
    """
    Lädt Relais-Namen aus JSON-Datei

    Returns:
        Dictionary mit Relais-Daten {relay_num: {name, category, stromkreis}}
    """
    if os.path.exists(RELAY_NAMES_FILE):
        try:
            with open(RELAY_NAMES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Konvertiere String-Keys zu Integer und normalisiere Datenstruktur
                result = {}
                for k, v in data.items():
                    relay_num = int(k)
                    # Unterstütze alte Struktur (nur String) und neue (Objekt)
                    if isinstance(v, str):
                        result[relay_num] = {'name': v, 'category': '', 'stromkreis': ''}
                    elif isinstance(v, dict):
                        result[relay_num] = {
                            'name': v.get('name', ''),
                            'category': v.get('category', ''),
                            'stromkreis': v.get('stromkreis', '')
                        }
                return result
        except Exception as e:
            print(f"Error loading relay names: {e}")
            return {}
    return {}


def save_relay_names_to_file(relay_names):
    """
    Speichert Relais-Namen in JSON-Datei

    Args:
        relay_names: Dictionary mit Relais-Daten {relay_num: {name, category, stromkreis}}

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        with open(RELAY_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(relay_names, f, indent=2, ensure_ascii=False)
        print(f"✓ Relay names saved to {RELAY_NAMES_FILE}")
        return True
    except Exception as e:
        print(f"Error saving relay names: {e}")
        return False


def get_all_relay_names():
    """
    Gibt alle Relais-Namen zurück (config.py + JSON)
    
    Returns:
        Dictionary mit allen Relais-Namen
    """
    from config import RELAY_NAMES
    
    file_names = load_relay_names_from_file()
    
    # Merge: File-Namen haben Vorrang
    all_names = RELAY_NAMES.copy()
    all_names.update(file_names)
    
    return all_names


def set_relay_name(relay_num, name):
    """
    Setzt oder ändert den Namen eines Relais
    
    Args:
        relay_num: Relais-Nummer (0-63)
        name: Neuer Name (leer = löschen)
        
    Returns:
        (success, message)
    """
    if not 0 <= relay_num <= 63:
        return False, f"Ungültige Relais-Nummer: {relay_num}"
    
    # Prüfe ob Relais in Gruppe ist
    groups = get_all_groups()
    for group_data in groups.values():
        if relay_num in group_data['relays']:
            return False, f"Relais {relay_num} ist Teil der Gruppe '{group_data['name']}'. Gruppen können nicht einzeln benannt werden."
    
    relay_names = load_relay_names_from_file()
    
    if name and name.strip():
        relay_names[relay_num] = name.strip()
        success = save_relay_names_to_file(relay_names)
        if success:
            return True, f"Relais {relay_num} wurde benannt als '{name}'"
        else:
            return False, "Fehler beim Speichern"
    else:
        # Name löschen
        if relay_num in relay_names:
            del relay_names[relay_num]
            success = save_relay_names_to_file(relay_names)
            if success:
                return True, f"Name für Relais {relay_num} wurde gelöscht"
            else:
                return False, "Fehler beim Speichern"
        else:
            return True, "Kein Name gesetzt"


def bulk_set_relay_names(relay_data_dict):
    """
    Setzt mehrere Relais-Namen mit Kategorien auf einmal

    Args:
        relay_data_dict: Dictionary {relay_num: {name, category, stromkreis}, ...}

    Returns:
        (success, message, failed_relays)
    """
    relay_names = load_relay_names_from_file()
    failed = []
    success_count = 0

    for relay_num, data in relay_data_dict.items():
        try:
            relay_num = int(relay_num)
            if not 0 <= relay_num <= 63:
                failed.append((relay_num, "Ungültige Nummer"))
                continue

            # Prüfe Gruppe
            groups = get_all_groups()
            is_grouped = False
            for group_data in groups.values():
                if relay_num in group_data['relays']:
                    is_grouped = True
                    break

            if is_grouped:
                failed.append((relay_num, "Teil einer Gruppe"))
                continue

            # Extrahiere Daten (unterstütze auch alte Struktur mit nur String)
            if isinstance(data, str):
                name = data
                category = ''
                stromkreis = ''
            else:
                name = data.get('name', '')
                category = data.get('category', '')
                stromkreis = data.get('stromkreis', '')

            if name and name.strip():
                relay_names[relay_num] = {
                    'name': name.strip(),
                    'category': category,
                    'stromkreis': stromkreis
                }
                success_count += 1
            elif relay_num in relay_names:
                del relay_names[relay_num]
                success_count += 1

        except Exception as e:
            failed.append((relay_num, str(e)))

    if success_count > 0:
        if save_relay_names_to_file(relay_names):
            return True, f"{success_count} Relais benannt", failed
        else:
            return False, "Fehler beim Speichern", failed

    return False, "Keine Änderungen", failed


def get_all_groups():
    """
    Gibt alle definierten Gruppen zurück
    
    Returns:
        Dictionary mit allen Gruppen
    """
    # Kombiniere Gruppen aus config.py und JSON-Datei
    from config import RELAY_GROUPS
    
    file_groups = load_groups_from_file()
    
    # Merge: File-Gruppen haben Vorrang
    all_groups = RELAY_GROUPS.copy()
    all_groups.update(file_groups)
    
    return all_groups


def add_group(group_id, name, relays, description='', category='', stromkreis=''):
    """
    Fügt eine neue Gruppe hinzu

    Args:
        group_id: Eindeutige ID für die Gruppe
        name: Anzeigename
        relays: Liste von Relais-Nummern
        description: Optional Beschreibung
        category: Optional Kategorie (RISO, Zi, Zs, Drehfeld, RCD)
        stromkreis: Optional Stromkreis-Zuordnung (z.B. L1, L2, L3)

    Returns:
        (success, message)
    """
    if not group_id or not name or not relays:
        return False, "Gruppe-ID, Name und Relais müssen angegeben werden"

    if not isinstance(relays, list) or len(relays) < 2:
        return False, "Eine Gruppe muss mindestens 2 Relais enthalten"

    # Prüfe ob Relais-Nummern gültig sind
    for relay in relays:
        if not isinstance(relay, int) or relay < 0 or relay > 63:
            return False, f"Ungültige Relais-Nummer: {relay}"

    # Prüfe auf Überschneidungen mit existierenden Gruppen
    existing_groups = get_all_groups()
    for existing_id, existing_data in existing_groups.items():
        if existing_id == group_id:
            continue  # Bei Update ignorieren

        overlap = set(relays) & set(existing_data['relays'])
        if overlap:
            return False, f"Relais {overlap} sind bereits in Gruppe '{existing_data['name']}'"

    # Lade bestehende File-Gruppen
    groups = load_groups_from_file()

    # Füge neue Gruppe hinzu
    groups[group_id] = {
        'name': name,
        'relays': sorted(relays),
        'description': description,
        'category': category,
        'stromkreis': stromkreis
    }

    # Speichern
    if save_groups_to_file(groups):
        return True, f"Gruppe '{name}' erfolgreich erstellt"
    else:
        return False, "Fehler beim Speichern"


def update_group(group_id, name, relays, description='', category='', stromkreis=''):
    """
    Aktualisiert eine existierende Gruppe

    Args:
        group_id: ID der zu aktualisierenden Gruppe
        name: Neuer Name
        relays: Neue Relais-Liste
        description: Neue Beschreibung
        category: Optional Kategorie (RISO, Zi, Zs, Drehfeld, RCD)
        stromkreis: Optional Stromkreis-Zuordnung (z.B. L1, L2, L3)

    Returns:
        (success, message)
    """
    groups = load_groups_from_file()

    if group_id not in groups:
        # Prüfe ob in config.py definiert
        from config import RELAY_GROUPS
        if group_id in RELAY_GROUPS:
            return False, "Gruppen aus config.py können nicht bearbeitet werden"
        return False, "Gruppe nicht gefunden"

    # Validierung wie bei add_group
    if not isinstance(relays, list) or len(relays) < 2:
        return False, "Eine Gruppe muss mindestens 2 Relais enthalten"

    for relay in relays:
        if not isinstance(relay, int) or relay < 0 or relay > 63:
            return False, f"Ungültige Relais-Nummer: {relay}"

    # Prüfe Überschneidungen (außer mit sich selbst)
    all_groups = get_all_groups()
    for existing_id, existing_data in all_groups.items():
        if existing_id == group_id:
            continue

        overlap = set(relays) & set(existing_data['relays'])
        if overlap:
            return False, f"Relais {overlap} sind bereits in Gruppe '{existing_data['name']}'"

    # Update
    groups[group_id] = {
        'name': name,
        'relays': sorted(relays),
        'description': description,
        'category': category,
        'stromkreis': stromkreis
    }

    if save_groups_to_file(groups):
        return True, f"Gruppe '{name}' erfolgreich aktualisiert"
    else:
        return False, "Fehler beim Speichern"


def delete_group(group_id):
    """
    Löscht eine Gruppe
    
    Args:
        group_id: ID der zu löschenden Gruppe
        
    Returns:
        (success, message)
    """
    groups = load_groups_from_file()
    
    if group_id not in groups:
        from config import RELAY_GROUPS
        if group_id in RELAY_GROUPS:
            return False, "Gruppen aus config.py können nicht gelöscht werden"
        return False, "Gruppe nicht gefunden"
    
    group_name = groups[group_id]['name']
    del groups[group_id]
    
    if save_groups_to_file(groups):
        return True, f"Gruppe '{group_name}' erfolgreich gelöscht"
    else:
        return False, "Fehler beim Speichern"


def get_available_relays():
    """
    Gibt Liste der verfügbaren (nicht gruppierten) Relais zurück
    
    Returns:
        Set von Relais-Nummern
    """
    all_relays = set(range(64))
    grouped_relays = set()
    
    groups = get_all_groups()
    for group_data in groups.values():
        grouped_relays.update(group_data['relays'])
    
    return all_relays - grouped_relays


def get_group_statistics():
    """
    Gibt Statistiken über Gruppen zurück

    Returns:
        Dictionary mit Statistiken
    """
    groups = get_all_groups()
    grouped_relays = set()

    for group_data in groups.values():
        grouped_relays.update(group_data['relays'])

    return {
        'total_groups': len(groups),
        'total_grouped_relays': len(grouped_relays),
        'available_relays': 64 - len(grouped_relays),
        'groups': groups
    }


def get_relays_by_category(category):
    """
    Gibt alle Relais und Gruppen einer bestimmten Kategorie zurück

    Args:
        category: Kategorie (RISO, Zi, Zs, Drehfeld, RCD)

    Returns:
        Dictionary mit 'relays' (einzelne Relais) und 'groups' (Gruppen)
    """
    result = {
        'relays': [],  # Liste von {relay_num, name, stromkreis}
        'groups': []   # Liste von {group_id, name, relays, stromkreis}
    }

    # Einzelne Relais mit dieser Kategorie
    relay_names = load_relay_names_from_file()
    for relay_num, data in relay_names.items():
        if data.get('category') == category:
            result['relays'].append({
                'relay_num': relay_num,
                'name': data.get('name', f'Relais {relay_num}'),
                'stromkreis': data.get('stromkreis', '')
            })

    # Gruppen mit dieser Kategorie
    groups = get_all_groups()
    for group_id, group_data in groups.items():
        if group_data.get('category') == category:
            result['groups'].append({
                'group_id': group_id,
                'name': group_data['name'],
                'relays': group_data['relays'],
                'stromkreis': group_data.get('stromkreis', '')
            })

    return result