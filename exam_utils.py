"""
VDE Messwand - Prüfungs-Hilfsfunktionen
"""
import random
from config import DEFAULT_EXAM_RELAY_COUNT
from relais_manager import get_all_relais_config, get_groups_overview
from stromkreis_manager import get_all_stromkreise
from settings_manager import get_wallbox_enabled


def get_effective_relay_list():
    """
    Erstellt eine Liste aller wählbaren Relais/Gruppen
    Gruppen werden als ein Element behandelt

    Returns:
        Liste von Relais-Nummern oder Gruppen-IDs
    """
    groups = get_groups_overview()
    all_relays = set(range(64))
    grouped_relays = set()
    effective_list = []

    # Gruppen zuerst erfassen
    for group_num, group_data in groups.items():
        grouped_relays.update(group_data['relays'])
        # Verwende das erste Relais der Gruppe als Repräsentant
        effective_list.append(min(group_data['relays']))

    # Einzelne Relais (die nicht in Gruppen sind)
    for relay in all_relays - grouped_relays:
        effective_list.append(relay)

    return effective_list


def select_random_relays(count=None):
    """
    Wählt zufällige Relais aus verschiedenen Stromkreisen
    Berücksichtigt Relais-Gruppen automatisch
    Ignoriert Wallbox-Stromkreis wenn in Einstellungen deaktiviert

    Args:
        count: Anzahl der zu wählenden Relais (Standard: aus config)

    Returns:
        Liste der ausgewählten Relais-Nummern
    """
    if count is None:
        count = DEFAULT_EXAM_RELAY_COUNT

    try:
        relais_config = get_all_relais_config()
        groups = get_groups_overview()
        stromkreise = get_all_stromkreise()
        wallbox_enabled = get_wallbox_enabled()

        # Erstelle Mapping: Stromkreis -> Relais
        stromkreis_to_relais = {}
        for sk_id, sk_data in stromkreise.items():
            # Überspringe Wallbox-Stromkreis wenn deaktiviert
            if not wallbox_enabled and sk_data['name'] == 'Wallbox':
                continue

            # Finde alle Relais mit diesem Stromkreis
            relais_list = []
            for relay_num in range(64):
                relay_data = relais_config.get(relay_num, {})
                if relay_data.get('stromkreis') == sk_data['name']:
                    relais_list.append(relay_num)

            if relais_list:
                stromkreis_to_relais[sk_id] = {
                    'name': sk_data['name'],
                    'relays': relais_list
                }

        available_stromkreise = list(stromkreis_to_relais.values())

        if len(available_stromkreise) < count:
            count = len(available_stromkreise)

        if count == 0:
            # Fallback: Wähle aus allen konfigurierten Relais
            effective_list = get_effective_relay_list()
            return random.sample(effective_list, min(3, len(effective_list)))

        selected_stromkreise = random.sample(available_stromkreise, count)
        selected_relays = []

        for stromkreis in selected_stromkreise:
            # Wähle aus effektiven Relais (Gruppen werden als eines gezählt)
            effective_relays = []
            grouped = set()

            # Sammle gruppierte Relais in diesem Stromkreis
            for group_num, group_data in groups.items():
                group_in_stromkreis = [r for r in group_data['relays'] if r in stromkreis['relays']]
                if group_in_stromkreis:
                    effective_relays.append(min(group_data['relays']))  # Repräsentant
                    grouped.update(group_data['relays'])

            # Sammle einzelne Relais
            for relay in stromkreis['relays']:
                if relay not in grouped:
                    effective_relays.append(relay)

            if effective_relays:
                relay = random.choice(effective_relays)
                selected_relays.append(relay)

        return selected_relays

    except Exception as e:
        print(f"Error selecting random relays: {e}")
        effective_list = get_effective_relay_list()
        return random.sample(effective_list, min(count, len(effective_list)))


def get_stromkreis_for_relay(relay_num):
    """
    Findet den Stromkreis für ein bestimmtes Relais

    Args:
        relay_num: Relais-Nummer (0-63)

    Returns:
        Dictionary mit Stromkreis-Info oder None
    """
    relais_config = get_all_relais_config()
    relay_data = relais_config.get(relay_num, {})
    stromkreis_name = relay_data.get('stromkreis')

    if stromkreis_name:
        stromkreise = get_all_stromkreise()
        for sk_id, sk_data in stromkreise.items():
            if sk_data['name'] == stromkreis_name:
                return {
                    'number': sk_id,
                    'name': sk_data['name'],
                    'description': sk_data.get('description', '')
                }

    return None


def get_relay_description(relay_num):
    """
    Gibt eine Beschreibung für ein Relais zurück
    Berücksichtigt auch Gruppen

    Args:
        relay_num: Relais-Nummer (0-63)

    Returns:
        String mit Beschreibung
    """
    relais_config = get_all_relais_config()
    groups = get_groups_overview()

    relay_data = relais_config.get(relay_num, {})
    group_num = relay_data.get('group_number', 0)

    # Prüfe ob Teil einer Gruppe
    if group_num > 0 and group_num in groups:
        group_data = groups[group_num]
        return f"{relay_data.get('name', f'Gruppe {group_num}')} (Relais {', '.join(map(str, group_data['relays']))})"

    # Verwende konfigurierten Namen
    if relay_data.get('name'):
        return relay_data['name']

    # Sonst Stromkreis-basierte Beschreibung
    stromkreis = get_stromkreis_for_relay(relay_num)
    if stromkreis:
        return f"{stromkreis['name']} - Relais {relay_num}"

    return f"Relais {relay_num}"


def format_duration(seconds):
    """
    Formatiert eine Dauer in Sekunden als lesbaren String
    
    Args:
        seconds: Dauer in Sekunden
        
    Returns:
        Formatierter String (z.B. "5m 23s")
    """
    if not seconds or seconds <= 0:
        return "0s"
    
    minutes = seconds // 60
    secs = seconds % 60
    
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def format_timestamp(timestamp_str):
    """
    Formatiert einen Zeitstempel für die Anzeige
    
    Args:
        timestamp_str: Zeitstempel als String
        
    Returns:
        Tuple (date, time) als formatierte Strings
    """
    from datetime import datetime
    
    try:
        if timestamp_str:
            if 'T' in str(timestamp_str):
                dt = datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(str(timestamp_str), '%Y-%m-%d %H:%M:%S.%f')
            
            formatted_date = dt.strftime('%d.%m.%Y')
            formatted_time = dt.strftime('%H:%M:%S')
            return formatted_date, formatted_time
        else:
            return 'Unbekannt', ''
    
    except:
        date_part = str(timestamp_str).split(' ')[0] if timestamp_str else 'Unbekannt'
        time_part = str(timestamp_str).split(' ')[1] if timestamp_str and ' ' in str(timestamp_str) else ''
        return date_part, time_part


def validate_relay_selection(relay_numbers):
    """
    Validiert eine Liste von Relais-Nummern
    
    Args:
        relay_numbers: Liste von Relais-Nummern
        
    Returns:
        Tuple (valid_relays, invalid_relays)
    """
    valid = []
    invalid = []
    
    for relay in relay_numbers:
        try:
            relay_int = int(relay)
            if 0 <= relay_int <= 63:
                valid.append(relay_int)
            else:
                invalid.append(relay)
        except (ValueError, TypeError):
            invalid.append(relay)
    
    return valid, invalid
