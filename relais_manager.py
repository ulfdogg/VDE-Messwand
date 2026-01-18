"""
VDE Messwand - Modulare Relais-Verwaltung
Nummer-basierte Gruppierung mit Kategorie und Stromkreis
"""
import json
import os

RELAIS_CONFIG_FILE = 'relais_config.json'


def load_relais_config():
    """
    Lädt Relais-Konfiguration aus JSON-Datei

    Returns:
        Dictionary mit Relais-Konfiguration {relay_num: {group_number, name, category, stromkreis}}
    """
    if os.path.exists(RELAIS_CONFIG_FILE):
        try:
            with open(RELAIS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading relais config: {e}")
            return {}
    return {}


def save_relais_config(config):
    """
    Speichert Relais-Konfiguration in JSON-Datei

    Args:
        config: Dictionary mit Relais-Konfiguration

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        with open(RELAIS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✓ Relais config saved to {RELAIS_CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"Error saving relais config: {e}")
        return False


def get_relais_by_group_number(group_number):
    """
    Gibt alle Relais einer Gruppen-Nummer zurück

    Args:
        group_number: Gruppen-Nummer (0 = keine Gruppe, 1-99 = Gruppe)

    Returns:
        Liste von Relais-Nummern in dieser Gruppe
    """
    config = load_relais_config()
    relais_in_group = []

    for relay_num_str, relay_data in config.items():
        if relay_data.get('group_number') == group_number:
            relais_in_group.append(int(relay_num_str))

    return sorted(relais_in_group)


def get_groups_overview():
    """
    Gibt eine Übersicht über alle Gruppen zurück

    Returns:
        Dictionary {group_number: {name, relays, category, stromkreis}}
    """
    config = load_relais_config()
    groups = {}

    for relay_num_str, relay_data in config.items():
        group_num = relay_data.get('group_number', 0)

        if group_num > 0:  # 0 = keine Gruppe
            if group_num not in groups:
                groups[group_num] = {
                    'name': relay_data.get('name', f'Gruppe {group_num}'),
                    'relays': [],
                    'category': relay_data.get('category', ''),
                    'stromkreis': relay_data.get('stromkreis', '')
                }
            groups[group_num]['relays'].append(int(relay_num_str))

    # Sortiere Relais in jeder Gruppe
    for group_data in groups.values():
        group_data['relays'].sort()

    return groups


def update_relay_config(relay_num, group_number=0, name='', category='', stromkreis=''):
    """
    Aktualisiert die Konfiguration eines einzelnen Relais

    Args:
        relay_num: Relais-Nummer (0-63)
        group_number: Gruppen-Nummer (0 = keine Gruppe, 1-99 = Gruppe)
        name: Name/Beschreibung
        category: Kategorie
        stromkreis: Stromkreis

    Returns:
        (success, message)
    """
    if not 0 <= relay_num <= 63:
        return False, "Ungültige Relais-Nummer"

    if not 0 <= group_number <= 99:
        return False, "Ungültige Gruppen-Nummer (0-99)"

    config = load_relais_config()

    # Konvertiere zu String für JSON-Keys
    relay_key = str(relay_num)

    # Erstelle oder aktualisiere Eintrag
    config[relay_key] = {
        'group_number': group_number,
        'name': name.strip(),
        'category': category.strip(),
        'stromkreis': stromkreis.strip()
    }

    # Wenn alle Felder leer und group_number = 0, lösche den Eintrag
    if (group_number == 0 and not name.strip() and
        not category.strip() and not stromkreis.strip()):
        if relay_key in config:
            del config[relay_key]

    if save_relais_config(config):
        return True, f"Relais {relay_num} erfolgreich aktualisiert"
    else:
        return False, "Fehler beim Speichern"


def bulk_update_relais(updates):
    """
    Aktualisiert mehrere Relais auf einmal

    Args:
        updates: Dictionary {relay_num: {group_number, name, category, stromkreis}, ...}

    Returns:
        Dictionary mit success, message und failed_count
    """
    config = load_relais_config()
    failed = 0
    success_count = 0

    for relay_num, data in updates.items():
        try:
            relay_num = int(relay_num)
            if not 0 <= relay_num <= 63:
                failed += 1
                continue

            group_number = data.get('group_number', 0)
            name = data.get('name', '')
            category = data.get('category', '')
            stromkreis = data.get('stromkreis', '')

            relay_key = str(relay_num)


            # Update oder erstelle Eintrag
            config[relay_key] = {
                'group_number': int(group_number),
                'name': name.strip(),
                'category': category.strip(),
                'stromkreis': stromkreis.strip()
            }

            # Leere Einträge löschen
            if (int(group_number) == 0 and not name.strip() and
                not category.strip() and not stromkreis.strip()):
                if relay_key in config:
                    del config[relay_key]

            success_count += 1

        except Exception as e:
            print(f"Error updating relay {relay_num}: {e}")
            failed += 1

    if save_relais_config(config):
        return {
            'success': True,
            'message': f"{success_count} Relais aktualisiert",
            'failed_count': failed
        }
    else:
        return {
            'success': False,
            'message': "Fehler beim Speichern",
            'failed_count': failed
        }


def get_all_relais_config():
    """
    Gibt die komplette Relais-Konfiguration zurück (alle 64 Relais)

    Returns:
        Dictionary mit allen 64 Relais und ihren Konfigurationen
    """
    config = load_relais_config()
    full_config = {}

    for i in range(64):
        relay_key = str(i)
        if relay_key in config:
            full_config[i] = config[relay_key]
        else:
            # Standardwerte für nicht konfigurierte Relais
            full_config[i] = {
                'group_number': 0,
                'name': '',
                'category': '',
                'stromkreis': ''
            }

    return full_config


def get_relais_by_category(category):
    """
    Gibt alle Relais einer bestimmten Kategorie zurück

    Args:
        category: Kategorie-Name

    Returns:
        Liste von Relais-Nummern
    """
    config = load_relais_config()
    relais_list = []

    for relay_num_str, relay_data in config.items():
        if relay_data.get('category', '') == category:
            relais_list.append(int(relay_num_str))

    return sorted(relais_list)


def get_relais_by_stromkreis(stromkreis):
    """
    Gibt alle Relais eines bestimmten Stromkreises zurück

    Args:
        stromkreis: Stromkreis-Name

    Returns:
        Liste von Relais-Nummern
    """
    config = load_relais_config()
    relais_list = []

    for relay_num_str, relay_data in config.items():
        if relay_data.get('stromkreis', '') == stromkreis:
            relais_list.append(int(relay_num_str))

    return sorted(relais_list)


def get_representative_relais_for_groups():
    """
    Gibt für jede Gruppe das kleinste Relais zurück (Repräsentant)

    Returns:
        Dictionary {group_number: representative_relay_num}
    """
    groups = get_groups_overview()
    representatives = {}

    for group_num, group_data in groups.items():
        if group_data['relays']:
            representatives[group_num] = min(group_data['relays'])

    return representatives


def normalize_relay_to_representative(relay_num):
    """
    Gibt den Repräsentanten einer Gruppe zurück (kleinste Relais-Nummer)
    Wenn Relais nicht in Gruppe, gibt die ursprüngliche Nummer zurück

    Args:
        relay_num: Relais-Nummer

    Returns:
        Repräsentant-Relais-Nummer
    """
    config = load_relais_config()
    relay_key = str(relay_num)

    if relay_key not in config:
        return relay_num

    group_number = config[relay_key].get('group_number', 0)

    if group_number == 0:
        # Keine Gruppe
        return relay_num

    # Finde kleinstes Relais in der Gruppe
    group_relais = get_relais_by_group_number(group_number)
    if group_relais:
        return min(group_relais)

    return relay_num


def get_relais_statistics():
    """
    Gibt Statistiken über die Relais-Konfiguration zurück

    Returns:
        Dictionary mit Statistiken
    """
    config = load_relais_config()
    groups = get_groups_overview()

    configured_count = len(config)
    grouped_count = sum(len(g['relays']) for g in groups.values())
    named_count = sum(1 for r in config.values() if r.get('name', '').strip())
    categorized_count = sum(1 for r in config.values() if r.get('category', '').strip())

    return {
        'total_relais': 64,
        'configured_relais': configured_count,
        'grouped_relais': grouped_count,
        'named_relais': named_count,
        'categorized_relais': categorized_count,
        'total_groups': len(groups),
        'unconfigured_relais': 64 - configured_count
    }
