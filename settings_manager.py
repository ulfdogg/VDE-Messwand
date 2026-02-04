"""
VDE Messwand - Einstellungs-Verwaltung
Ermöglicht das Ändern von Admin-Code und anderen Einstellungen
"""
import json
import os
from typing import Tuple

SETTINGS_FILE = 'settings.json'

def get_default_settings():
    """Gibt die Standard-Einstellungen zurück"""
    return {
        'admin_code': '1234',
        'wallbox_installed': False,  # Ob eine Wallbox vorhanden ist
        'wallbox_enabled': True      # Ob die Wallbox im Prüfmodus aktiv ist
    }

def load_settings():
    """Lädt Einstellungen aus JSON-Datei"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Sicherstellen, dass alle erforderlichen Keys existieren
                defaults = get_default_settings()
                for key, value in defaults.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except Exception as e:
            print(f"Fehler beim Laden der Einstellungen: {e}")
            return get_default_settings()
    else:
        # Erstelle Datei mit Standardwerten
        settings = get_default_settings()
        save_settings(settings)
        return settings

def save_settings(settings: dict) -> bool:
    """Speichert Einstellungen in JSON-Datei"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Fehler beim Speichern der Einstellungen: {e}")
        return False

def get_admin_code() -> str:
    """Gibt den aktuellen Admin-Code zurück"""
    settings = load_settings()
    return settings.get('admin_code', '1234')

def set_admin_code(new_code: str) -> Tuple[bool, str]:
    """
    Ändert den Admin-Code

    Args:
        new_code: Der neue Admin-Code

    Returns:
        Tuple[bool, str]: (Erfolg, Fehlermeldung)
    """
    # Validierung
    if not new_code:
        return False, "Code darf nicht leer sein"

    if len(new_code) < 4:
        return False, "Code muss mindestens 4 Zeichen lang sein"

    if len(new_code) > 20:
        return False, "Code darf maximal 20 Zeichen lang sein"

    # Nur Zahlen erlauben
    if not new_code.isdigit():
        return False, "Code darf nur aus Ziffern bestehen"

    # Einstellungen laden
    settings = load_settings()
    settings['admin_code'] = new_code

    # Speichern
    if save_settings(settings):
        return True, "Admin-Code erfolgreich geändert"
    else:
        return False, "Fehler beim Speichern des Codes"

def verify_admin_code(code: str) -> bool:
    """
    Überprüft ob der eingegebene Code korrekt ist

    Args:
        code: Der zu überprüfende Code

    Returns:
        bool: True wenn korrekt, False wenn falsch
    """
    current_code = get_admin_code()
    return code == current_code


def get_wallbox_installed() -> bool:
    """Gibt zurück ob eine Wallbox vorhanden/installiert ist"""
    settings = load_settings()
    return settings.get('wallbox_installed', False)


def set_wallbox_installed(installed: bool) -> Tuple[bool, str]:
    """
    Setzt ob eine Wallbox vorhanden ist

    Args:
        installed: True = Wallbox vorhanden, False = nicht vorhanden

    Returns:
        Tuple[bool, str]: (Erfolg, Nachricht)
    """
    settings = load_settings()
    settings['wallbox_installed'] = installed

    if save_settings(settings):
        status = "vorhanden" if installed else "nicht vorhanden"
        return True, f"Wallbox als {status} markiert"
    else:
        return False, "Fehler beim Speichern der Einstellung"


def get_wallbox_enabled() -> bool:
    """Gibt zurück ob der Wallbox-Stromkreis aktiviert ist"""
    settings = load_settings()
    return settings.get('wallbox_enabled', True)


def set_wallbox_enabled(enabled: bool) -> Tuple[bool, str]:
    """
    Aktiviert oder deaktiviert den Wallbox-Stromkreis

    Args:
        enabled: True = Wallbox aktiviert, False = deaktiviert

    Returns:
        Tuple[bool, str]: (Erfolg, Nachricht)
    """
    settings = load_settings()
    settings['wallbox_enabled'] = enabled

    if save_settings(settings):
        status = "aktiviert" if enabled else "deaktiviert"
        return True, f"Wallbox-Stromkreis {status}"
    else:
        return False, "Fehler beim Speichern der Einstellung"
