"""
VDE Messwand - Übungsmodus-Verwaltung
Konfiguration welche Relais bei welcher Übung/Kategorie geschaltet werden
"""
import json
import os

TRAINING_CONFIG_FILE = 'training_config.json'


def load_training_config():
    """
    Lädt Übungsmodus-Konfiguration aus JSON-Datei

    Returns:
        Dictionary mit Training-Konfiguration
        NEUE STRUKTUR:
        {
            "RISO": {
                "fluke": [2, 5, 9],
                "benning": [2, 5, 9]
            },
            "Zi": {
                "fluke": [10, 15, 20]
            }
        }
    """
    if os.path.exists(TRAINING_CONFIG_FILE):
        try:
            with open(TRAINING_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)

                # Prüfe ob alte Struktur (page → category)
                # Alte Struktur: Keys sind page_ids wie "fluke", "benning"
                # Neue Struktur: Keys sind Kategorien wie "RISO", "Zi"
                if config:
                    first_key = list(config.keys())[0]
                    # Wenn erster Key eine bekannte Seite ist, alte Struktur
                    if first_key in ['fluke', 'benning', 'gossen', 'general']:
                        print("⚠ Alte Training-Config Struktur erkannt, konvertiere...")
                        return convert_old_to_new_structure(config)

                return config
        except Exception as e:
            print(f"Error loading training config: {e}")
            return {}
    return {}


def convert_old_to_new_structure(old_config):
    """
    Konvertiert alte Struktur (page → category → relais)
    zu neuer Struktur (category → page → relais)

    Args:
        old_config: Alte Struktur

    Returns:
        Neue Struktur
    """
    new_config = {}

    for page_id, categories in old_config.items():
        for category, relais_list in categories.items():
            if category not in new_config:
                new_config[category] = {}
            new_config[category][page_id] = relais_list

    # Speichere neue Struktur
    save_training_config(new_config)
    print("✓ Training-Config erfolgreich konvertiert")

    return new_config


def save_training_config(config):
    """
    Speichert Übungsmodus-Konfiguration in JSON-Datei

    Args:
        config: Dictionary mit Training-Konfiguration

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        with open(TRAINING_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✓ Training config saved to {TRAINING_CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"Error saving training config: {e}")
        return False


def get_training_pages():
    """
    Gibt alle verfügbaren Übungsseiten zurück

    Returns:
        Liste von Dictionaries mit page_id und display_name
    """
    return [
        {'page_id': 'spannungsfrei', 'name': 'Spannungsfreie Messungen'},
        {'page_id': 'unter_spannung', 'name': 'Messungen unter Spannung'}
    ]


def get_relais_for_training(page_id, category):
    """
    Gibt die konfigurierten Relais für eine Kategorie und Übungsseite zurück

    Args:
        page_id: ID der Übungsseite (z.B. "fluke")
        category: Kategorie (z.B. "RISO")

    Returns:
        Liste von Relais-Nummern
    """
    config = load_training_config()

    # NEUE STRUKTUR: config[category][page_id]
    if category not in config:
        return []

    if page_id not in config[category]:
        return []

    return config[category][page_id]


def update_training_mapping(category, page_id, relais_list):
    """
    Aktualisiert die Relais-Zuordnung für eine Kategorie/Übungsseite
    NEUE SIGNATUR: category zuerst!

    Args:
        category: Kategorie (z.B. "RISO")
        page_id: ID der Übungsseite (z.B. "fluke")
        relais_list: Liste von Relais-Nummern [2, 5, 9]

    Returns:
        (success, message)
    """
    config = load_training_config()

    # Validiere page_id
    valid_pages = [p['page_id'] for p in get_training_pages()]
    if page_id not in valid_pages:
        return False, f"Ungültige Übungsseite: {page_id}"

    # Validiere Relais-Nummern
    if not isinstance(relais_list, list):
        return False, "Relais-Liste muss ein Array sein"

    for relay_num in relais_list:
        if not isinstance(relay_num, int) or not 0 <= relay_num <= 63:
            return False, f"Ungültige Relais-Nummer: {relay_num}"

    # NEUE STRUKTUR: config[category][page_id]
    # Erstelle Kategorie-Eintrag falls nicht vorhanden
    if category not in config:
        config[category] = {}

    # Setze oder lösche Seiten-Mapping
    if relais_list:
        config[category][page_id] = sorted(relais_list)
    else:
        # Leere Liste = Mapping löschen
        if page_id in config[category]:
            del config[category][page_id]

        # Wenn Kategorie leer, lösche sie
        if not config[category]:
            del config[category]

    if save_training_config(config):
        return True, f"Mapping für {category}/{page_id} aktualisiert"
    else:
        return False, "Fehler beim Speichern"


def delete_training_mapping(category, page_id):
    """
    Löscht die Relais-Zuordnung für eine Kategorie/Übungsseite

    Args:
        category: Kategorie
        page_id: ID der Übungsseite

    Returns:
        (success, message)
    """
    return update_training_mapping(category, page_id, [])


def get_all_mappings_for_category(category):
    """
    Gibt alle Seiten-Mappings für eine Kategorie zurück

    Args:
        category: Kategorie (z.B. "RISO")

    Returns:
        Dictionary {page_id: [relais]}
    """
    config = load_training_config()
    return config.get(category, {})


def get_all_mappings_for_page(page_id):
    """
    Gibt alle Kategorie-Mappings für eine Übungsseite zurück
    (Rückwärts-Suche in neuer Struktur)

    Args:
        page_id: ID der Übungsseite

    Returns:
        Dictionary {category: [relais]}
    """
    config = load_training_config()
    result = {}

    for category, pages in config.items():
        if page_id in pages:
            result[category] = pages[page_id]

    return result


def get_complete_training_config():
    """
    Gibt die komplette Übungsmodus-Konfiguration zurück
    NEUE STRUKTUR: category → pages

    Returns:
        Dictionary mit allen Kategorien und Seiten
    """
    return load_training_config()


def get_statistics():
    """
    Gibt Statistiken über die Übungsmodus-Konfiguration zurück

    Returns:
        Dictionary mit Statistiken
    """
    config = load_training_config()

    total_mappings = 0
    configured_categories = len(config)
    pages_used = set()

    # NEUE STRUKTUR: category → pages
    for category, pages in config.items():
        if pages:
            total_mappings += len(pages)
            pages_used.update(pages.keys())

    return {
        'total_categories': configured_categories,
        'total_pages': len(get_training_pages()),
        'configured_pages': len(pages_used),
        'total_mappings': total_mappings,
        'categories_list': sorted(config.keys())
    }


def import_from_relais_manager(category, page_id):
    """
    Importiert automatisch alle Relais einer Kategorie aus dem Relais-Manager

    Args:
        category: Kategorie
        page_id: ID der Übungsseite

    Returns:
        (success, message, relais_count)
    """
    try:
        from relais_manager import get_relais_by_category

        relais_list = get_relais_by_category(category)

        if not relais_list:
            return False, f"Keine Relais mit Kategorie '{category}' gefunden", 0

        success, message = update_training_mapping(category, page_id, relais_list)

        if success:
            return True, f"{len(relais_list)} Relais importiert", len(relais_list)
        else:
            return False, message, 0

    except ImportError:
        return False, "Relais-Manager nicht verfügbar", 0
    except Exception as e:
        return False, f"Fehler beim Import: {str(e)}", 0
