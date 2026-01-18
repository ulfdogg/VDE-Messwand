"""
VDE Messwand - Hauptanwendung
"""
from flask import Flask, render_template, request, jsonify, Response, send_file
from jinja2 import FileSystemLoader
import subprocess
import io
import csv
import time
from datetime import datetime

# Import eigener Module
from config import *
from database import *
from relay_controller import RelayController
from exam_utils import *
from group_manager import *
from settings_manager import *
from stromkreis_manager import *
from relais_manager import *
from training_manager import *
from relais_templates import *
from relais_excel import *
from network_manager import (
    is_hotspot_active, toggle_hotspot, get_wifi_networks,
    connect_to_wifi, get_current_connection, get_network_info,
    get_ethernet_info
)
from gpio_monitor import init_gpio_monitor, get_gpio_status, cleanup_gpio

# Flask App initialisieren
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.jinja_loader = FileSystemLoader('templates', encoding='utf-8')

# Logging-Filter für GPIO-Status API
import logging
class NoGPIOStatusFilter(logging.Filter):
    def filter(self, record):
        # Filtere /api/gpio/status Requests heraus
        return '/api/gpio/status' not in record.getMessage()

# Füge Filter zu Werkzeug-Logger hinzu
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addFilter(NoGPIOStatusFilter())

# Globale Instanzen
relay_controller = RelayController()
exam_active = False

# GPIO-Monitor initialisieren (Standard: GPIO 17 und 27)
# Kann in config.py angepasst werden
gpio_monitor_instance = None


# ==================== HAUPT-ROUTEN ====================

@app.route('/')
def index():
    """Startseite"""
    return render_template('index.html')


# ==================== PRÜFUNGSMODUS ====================

@app.route('/exam_mode')
def exam_mode():
    """Prüfungsmodus-Seite"""
    exam_number = generate_exam_number()
    return render_template('exam_mode.html', exam_number=exam_number)


@app.route('/start_exam', methods=['POST'])
def start_exam():
    """Startet eine neue Prüfung mit zufälligen Fehlern"""
    global exam_active
    
    exam_number = request.json.get('exam_number')
    selected_relays = select_random_relays()
    
    # Relais aktivieren (Gruppen werden automatisch zusammen geschaltet)
    for relay_id in selected_relays:
        relay_controller.set_relay(relay_id, True)
    
    # In Datenbank speichern (wird automatisch normalisiert)
    save_examination(exam_number, selected_relays)
    
    exam_active = True
    return jsonify({
        'success': True,
        'selected_errors': selected_relays,
        'exam_number': exam_number
    })


@app.route('/finish_exam', methods=['POST'])
def finish_exam():
    """Beendet eine Prüfung"""
    global exam_active
    
    exam_number = request.json.get('exam_number')
    duration = request.json.get('duration', 0)
    
    relay_controller.reset_all_relays()
    update_examination_duration(exam_number, duration)
    
    exam_active = False
    return jsonify({'success': True})


# ==================== MANUELLER MODUS ====================

@app.route('/manual_mode')
def manual_mode():
    """Manuelle Fehlerauswahl"""
    # Lade neue Relais-Konfiguration und dynamische Stromkreise
    relais_config = get_all_relais_config()
    groups = get_groups_overview()
    stromkreise = get_all_stromkreise()

    # Erstelle erweiterte Stromkreis-Info mit Relais
    stromkreise_with_names = {}

    for sk_id, sk_data in stromkreise.items():
        relay_options = []

        # Finde alle Relais mit diesem Stromkreis
        relais_in_stromkreis = []
        for relay_num in range(64):
            relay_data = relais_config.get(relay_num, {})
            if relay_data.get('stromkreis') == sk_data['name']:
                relais_in_stromkreis.append(relay_num)

        # Gruppiere nach Gruppen-Nummer
        processed_groups = set()

        for relay_num in sorted(relais_in_stromkreis):
            relay_data = relais_config.get(relay_num, {})
            group_num = relay_data.get('group_number', 0)

            if group_num > 0:
                # Ist in Gruppe
                if group_num not in processed_groups:
                    processed_groups.add(group_num)
                    group_info = groups.get(group_num, {})
                    relay_options.append({
                        'number': relay_num,
                        'name': relay_data.get('name', f'Gruppe {group_num}'),
                        'is_group': True,
                        'group_relays': group_info.get('relays', [relay_num])
                    })
            else:
                # Einzelnes Relais
                relay_options.append({
                    'number': relay_num,
                    'name': relay_data.get('name', f'Relais {relay_num}'),
                    'is_group': False
                })

        stromkreise_with_names[sk_id] = {
            'name': sk_data['name'],
            'description': sk_data.get('description', ''),
            'relays': relay_options
        }

    return render_template('manual_mode_pi.html',
                         stromkreise=stromkreise_with_names)


@app.route('/manual_mode_pi')
def manual_mode_pi():
    """Manuelle Fehlerauswahl (Pi-Version)"""
    # Lade neue Relais-Konfiguration und dynamische Stromkreise
    relais_config = get_all_relais_config()
    groups = get_groups_overview()
    stromkreise = get_all_stromkreise()

    # Erstelle erweiterte Stromkreis-Info mit Relais
    stromkreise_with_names = {}

    for sk_id, sk_data in stromkreise.items():
        relay_options = []

        # Finde alle Relais mit diesem Stromkreis
        relais_in_stromkreis = []
        for relay_num in range(64):
            relay_data = relais_config.get(relay_num, {})
            if relay_data.get('stromkreis') == sk_data['name']:
                relais_in_stromkreis.append(relay_num)

        # Gruppiere nach Gruppen-Nummer
        processed_groups = set()

        for relay_num in sorted(relais_in_stromkreis):
            relay_data = relais_config.get(relay_num, {})
            group_num = relay_data.get('group_number', 0)

            if group_num > 0:
                # Ist in Gruppe
                if group_num not in processed_groups:
                    processed_groups.add(group_num)
                    group_info = groups.get(group_num, {})
                    relay_options.append({
                        'number': relay_num,
                        'name': relay_data.get('name', f'Gruppe {group_num}'),
                        'is_group': True,
                        'group_relays': group_info.get('relays', [relay_num])
                    })
            else:
                # Einzelnes Relais
                relay_options.append({
                    'number': relay_num,
                    'name': relay_data.get('name', f'Relais {relay_num}'),
                    'is_group': False
                })

        stromkreise_with_names[sk_id] = {
            'name': sk_data['name'],
            'description': sk_data.get('description', ''),
            'relays': relay_options
        }

    return render_template('manual_mode_pi.html',
                         stromkreise=stromkreise_with_names)


@app.route('/set_manual_errors', methods=['POST'])
def set_manual_errors():
    """Setzt manuell ausgewählte Fehler"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'Keine Daten erhalten'})
        
        errors = data.get('errors', {})
        if not errors:
            return jsonify({'success': False, 'error': 'Keine Fehler ausgewählt'})
        
        # Alle Relais zurücksetzen
        relay_controller.reset_all_relays()
        
        # Sammle nur eindeutige Repräsentanten (bei Gruppen)
        unique_relays = set()
        for stromkreis_key, relay_id in errors.items():
            try:
                relay_id = int(relay_id)
                if 0 <= relay_id <= 63:
                    # Normalisiere zu Gruppen-Repräsentant
                    representative = relay_controller.normalize_relay_to_group_representative(relay_id)
                    unique_relays.add(representative)
            except ValueError:
                pass
        
        activated_count = 0
        activated_relays = []
        failed_relays = []
        
        # Aktiviere eindeutige Relais/Gruppen
        for relay_id in unique_relays:
            if relay_controller.set_relay(relay_id, True):
                activated_count += 1
                activated_relays.append(relay_id)
                print(f"✅ Relay/Group {relay_id} activated")
            else:
                failed_relays.append(relay_id)
                print(f"❌ Failed to activate relay {relay_id}")
        
        return jsonify({
            'success': activated_count > 0,
            'activated_count': activated_count,
            'active_relays': activated_relays,
            'failed_relays': failed_relays,
            'message': f'{activated_count} Fehler zugeschaltet' + 
                      (f', {len(failed_relays)} fehlgeschlagen' if failed_relays else '')
        })
    
    except Exception as e:
        print(f"ERROR in set_manual_errors: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'})


@app.route('/reset_relays', methods=['POST'])
def reset_relays():
    """Setzt alle Relais zurück"""
    try:
        success = relay_controller.reset_all_relays()
        return jsonify({
            'success': success,
            'message': 'Alle Relais zurückgesetzt',
            'active_relays': relay_controller.active_relays
        })
    except Exception as e:
        print(f"ERROR in reset_relays: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/relay_status')
def relay_status_page():
    """Relay Status Monitor Seite"""
    return render_template('relay_status.html')


@app.route('/api/relay_status', methods=['GET'])
def api_relay_status():
    """API Endpoint zum Auslesen aller Relay-Status"""
    try:
        relay_status = relay_controller.read_all_relay_status()

        if relay_status is None:
            return jsonify({
                'success': False,
                'error': 'Konnte Relais-Status nicht auslesen'
            })

        # Zähle aktive Relais
        active_count = sum(1 for state in relay_status.values() if state)
        active_relays = [num for num, state in relay_status.items() if state]

        return jsonify({
            'success': True,
            'relays': relay_status,
            'active_count': active_count,
            'total_count': len(relay_status),
            'active_relays': active_relays
        })
    except Exception as e:
        print(f"ERROR in api_relay_status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })


# ==================== TESTMODUS ====================

@app.route('/test_mode')
def test_mode():
    """Testmodus-Seite"""
    return render_template('test_mode.html')


@app.route('/run_test', methods=['POST'])
def run_test():
    """Führt einen vollständigen Relais-Test durch"""
    try:
        success = relay_controller.test_all_relays()
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/run_test_stream')
def run_test_stream():
    """Führt Relais-Test mit Live-Updates via Server-Sent Events durch"""
    def generate():
        try:
            yield f"data: {json.dumps({'type': 'start', 'total': 64})}\n\n"

            failed_relays = []

            for relay in range(64):
                # Relais einschalten
                yield f"data: {json.dumps({'type': 'testing', 'relay': relay, 'action': 'on'})}\n\n"

                if not relay_controller.set_relay(relay, True):
                    failed_relays.append({'relay': relay, 'error': 'Konnte nicht einschalten'})
                    yield f"data: {json.dumps({'type': 'error', 'relay': relay, 'error': 'Einschalten fehlgeschlagen'})}\n\n"
                    continue

                time.sleep(1.0)

                # Modbus-Readback prüfen ob Relais AN ist
                status = relay_controller.read_all_relay_status()
                modbus_ok = status and status.get(relay, False) == True

                yield f"data: {json.dumps({'type': 'status', 'relay': relay, 'modbus_ok': modbus_ok, 'state': 'on'})}\n\n"

                if not modbus_ok:
                    failed_relays.append({'relay': relay, 'error': 'Modbus: Relais nicht AN'})

                time.sleep(1.5)  # Grüne Anzeige länger sichtbar

                # Relais ausschalten
                yield f"data: {json.dumps({'type': 'testing', 'relay': relay, 'action': 'off'})}\n\n"

                if not relay_controller.set_relay(relay, False):
                    failed_relays.append({'relay': relay, 'error': 'Konnte nicht ausschalten'})

                time.sleep(0.5)

                # Modbus-Readback prüfen ob ALLE Relais AUS sind
                status = relay_controller.read_all_relay_status()
                any_on = False
                active_relays = []
                if status:
                    for r, state in status.items():
                        if state:
                            any_on = True
                            active_relays.append(r)

                all_off_ok = not any_on
                yield f"data: {json.dumps({'type': 'all_off', 'modbus_ok': all_off_ok, 'active_relays': active_relays})}\n\n"

                if not all_off_ok:
                    failed_relays.append({'relay': relay, 'error': f'Modbus: Relais noch aktiv: {active_relays}'})

                time.sleep(1.5)  # Blaue Anzeige länger sichtbar

                # Fortschritt
                yield f"data: {json.dumps({'type': 'progress', 'relay': relay, 'done': relay + 1, 'total': 64})}\n\n"

            # Test abgeschlossen
            yield f"data: {json.dumps({'type': 'complete', 'success': len(failed_relays) == 0, 'failed': failed_relays})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/test_single_relay/<int:relay_id>')
def test_single_relay(relay_id):
    """Testet ein einzelnes Relais"""
    try:
        relay_controller.reset_all_relays()
        success = relay_controller.set_relay(relay_id, True)
        time.sleep(0.5)
        relay_controller.set_relay(relay_id, False)
        return jsonify({'success': success, 'relay_id': relay_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== ÜBUNGSMODUS ====================

@app.route('/training_mode')
def training_mode():
    """Übungsmodus-Hauptseite"""
    return render_template('training_mode.html')


@app.route('/training/general')
def training_general():
    """Allgemeine VDE-Anleitung"""
    return render_template('training_general_new.html')


@app.route('/training/fluke')
def training_fluke():
    """Fluke Übungen"""
    return render_template('training_fluke_new.html')


@app.route('/training/benning')
def training_benning():
    """Benning Übungen"""
    return render_template('training_benning_new.html')


@app.route('/training/gossen')
def training_gossen():
    """Gossen-Metrawatt Übungen"""
    return render_template('training_gossen_new.html')


# ==================== ADMIN-BEREICH ====================

@app.route('/admin')
def admin():
    """Admin-Login"""
    return render_template('admin_login.html')


@app.route('/admin_login', methods=['POST'])
def admin_login():
    """Admin-Login Validierung"""
    code = request.json.get('code')
    # Verwende den Code aus settings.json, falls vorhanden
    is_valid = verify_admin_code(code)
    return jsonify({'success': is_valid})


@app.route('/admin_panel')
def admin_panel():
    """Admin-Übersicht"""
    return render_template('admin_panel.html')


# ==================== GRUPPEN-VERWALTUNG ====================

@app.route('/admin_groups')
def admin_groups():
    """Gruppen-Verwaltung GUI"""
    stats = get_group_statistics()
    available_relays = sorted(get_available_relays())
    kategorien = get_all_kategorien()

    return render_template('admin_groups.html',
                         groups=stats['groups'],
                         total_groups=stats['total_groups'],
                         grouped_relays=stats['total_grouped_relays'],
                         available_relays=available_relays,
                         kategorien=kategorien)


@app.route('/admin_relay_names')
def admin_relay_names():
    """Relais-Benennungs GUI"""
    all_names = get_all_relay_names()
    groups = get_all_groups()
    stromkreise = get_all_stromkreise()
    kategorien = get_all_kategorien()

    # Gruppiere Relais nach Stromkreisen für bessere Übersicht
    relay_info = []
    for i in range(64):
        # Prüfe ob in Gruppe
        in_group = None
        for group_id, group_data in groups.items():
            if i in group_data['relays']:
                in_group = group_data['name']
                break

        # Finde Stromkreis
        stromkreis_name = None
        for sk_data in stromkreise.values():
            if i in sk_data['relays']:
                stromkreis_name = sk_data['name']
                break

        # Hole vollständige Relais-Daten (Name, Kategorie, Stromkreis)
        relay_data = all_names.get(i, {})
        if isinstance(relay_data, str):
            # Alte Struktur: nur String
            relay_name = relay_data
            category = ''
            stromkreis_info = ''
        elif isinstance(relay_data, dict):
            # Neue Struktur: Dictionary mit name, category, stromkreis
            relay_name = relay_data.get('name', '')
            category = relay_data.get('category', '')
            stromkreis_info = relay_data.get('stromkreis', '')
        else:
            relay_name = ''
            category = ''
            stromkreis_info = ''

        relay_info.append({
            'number': i,
            'name': relay_name,
            'category': category,
            'stromkreis': stromkreis_info or stromkreis_name,
            'group': in_group,
            'editable': in_group is None
        })

    return render_template('admin_relay_names.html',
                         relay_info=relay_info,
                         stromkreise=stromkreise,
                         kategorien=kategorien)


@app.route('/api/groups', methods=['GET'])
def api_get_groups():
    """API: Alle Gruppen abrufen"""
    stats = get_group_statistics()
    return jsonify({
        'success': True,
        'groups': stats['groups'],
        'statistics': {
            'total_groups': stats['total_groups'],
            'grouped_relays': stats['total_grouped_relays'],
            'available_relays': stats['available_relays']
        }
    })


@app.route('/api/relay_names', methods=['GET'])
def api_get_relay_names():
    """API: Alle Relais-Namen abrufen"""
    names = get_all_relay_names()
    return jsonify({
        'success': True,
        'relay_names': names
    })


@app.route('/api/relay_names/set', methods=['POST'])
def api_set_relay_name():
    """API: Einzelnen Relais-Namen setzen"""
    data = request.json
    relay_num = data.get('relay_num')
    name = data.get('name', '')
    
    try:
        relay_num = int(relay_num)
    except:
        return jsonify({'success': False, 'message': 'Ungültige Relais-Nummer'})
    
    success, message = set_relay_name(relay_num, name)
    
    if success:
        reload_relay_config()
    
    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/relay_names/bulk', methods=['POST'])
def api_bulk_set_relay_names():
    """API: Mehrere Relais-Namen auf einmal setzen"""
    data = request.json
    # Unterstütze alte 'names' und neue 'relay_data' Struktur
    relay_data_dict = data.get('relay_data', data.get('names', {}))

    success, message, failed = bulk_set_relay_names(relay_data_dict)

    if success:
        reload_relay_config()

    return jsonify({
        'success': success,
        'message': message,
        'failed': failed
    })


@app.route('/api/groups/available_relays', methods=['GET'])
def api_get_available_relays():
    """API: Verfügbare (nicht gruppierte) Relais"""
    available = sorted(get_available_relays())
    return jsonify({
        'success': True,
        'available_relays': available
    })


@app.route('/api/groups/add', methods=['POST'])
def api_add_group():
    """API: Neue Gruppe erstellen"""
    data = request.json

    group_id = data.get('group_id', '').strip()
    name = data.get('name', '').strip()
    relays = data.get('relays', [])
    description = data.get('description', '').strip()
    category = data.get('category', '').strip()
    stromkreis = data.get('stromkreis', '').strip()

    success, message = add_group(group_id, name, relays, description, category, stromkreis)

    # Bei Erfolg: Gruppen in config neu laden
    if success:
        reload_relay_config()

    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/groups/update', methods=['POST'])
def api_update_group():
    """API: Gruppe aktualisieren"""
    data = request.json

    group_id = data.get('group_id', '').strip()
    name = data.get('name', '').strip()
    relays = data.get('relays', [])
    description = data.get('description', '').strip()
    category = data.get('category', '').strip()
    stromkreis = data.get('stromkreis', '').strip()

    success, message = update_group(group_id, name, relays, description, category, stromkreis)

    if success:
        reload_relay_config()

    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/groups/delete', methods=['POST'])
def api_delete_group():
    """API: Gruppe löschen"""
    data = request.json
    group_id = data.get('group_id', '')

    success, message = delete_group(group_id)

    if success:
        reload_relay_config()

    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/relays/by_category/<category>', methods=['GET'])
def api_get_relays_by_category(category):
    """API: Relais und Gruppen nach Kategorie abrufen"""
    from group_manager import get_relays_by_category

    result = get_relays_by_category(category)

    return jsonify({
        'success': True,
        'category': category,
        'relays': result['relays'],
        'groups': result['groups']
    })


@app.route('/api/relays/activate_category', methods=['POST'])
def api_activate_category():
    """API: Alle Relais einer Kategorie aktivieren (nach Stromkreis gruppiert)"""
    from group_manager import get_relays_by_category

    data = request.json
    category = data.get('category', '')

    if not category:
        return jsonify({'success': False, 'message': 'Kategorie fehlt'})

    try:
        result = get_relays_by_category(category)

        # Sammle alle Relais, die aktiviert werden sollen
        relays_to_activate = []

        # Gruppiere nach Stromkreis
        stromkreise = {}

        # Einzelne Relais hinzufügen
        for relay_info in result['relays']:
            sk = relay_info['stromkreis'] or 'default'
            if sk not in stromkreise:
                stromkreise[sk] = []
            stromkreise[sk].append({
                'relay_num': relay_info['relay_num'],
                'name': relay_info['name']
            })

        # Gruppen hinzufügen
        for group_info in result['groups']:
            sk = group_info['stromkreis'] or 'default'
            if sk not in stromkreise:
                stromkreise[sk] = []
            stromkreise[sk].append({
                'group': group_info['name'],
                'relays': group_info['relays']
            })

        # Aktiviere die Relais (nur unterschiedliche Stromkreise gleichzeitig)
        activated = []
        for sk, items in stromkreise.items():
            for item in items:
                if 'relay_num' in item:
                    # Einzelnes Relais
                    relay_controller.set_relay(item['relay_num'], True)
                    activated.append(f"Relais {item['relay_num']} ({item['name']})")
                elif 'group' in item:
                    # Gruppe
                    for relay_num in item['relays']:
                        relay_controller.set_relay(relay_num, True)
                    activated.append(f"Gruppe {item['group']}")

        return jsonify({
            'success': True,
            'message': f"{len(activated)} Relais/Gruppen aktiviert",
            'activated': activated,
            'stromkreise': list(stromkreise.keys())
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        })


def reload_relay_config():
    """Lädt RELAY_GROUPS und RELAY_NAMES aus Dateien neu"""
    global RELAY_GROUPS
    try:
        # Update config mit neuen Daten
        import config
        config.RELAY_GROUPS = get_all_groups()
        config.RELAY_NAMES = get_all_relay_names()
        config.STROMKREISE = get_all_stromkreise()

        print("✓ Relay configuration reloaded")
        return True
    except Exception as e:
        print(f"Error reloading config: {e}")
        return False


# ==================== STROMKREIS-VERWALTUNG ====================

@app.route('/admin_stromkreise')
def admin_stromkreise():
    """Stromkreis-Verwaltung GUI (alte Seite)"""
    stats = get_stromkreis_statistics()

    return render_template('admin_stromkreise.html',
                         stromkreise=stats['stromkreise'],
                         stats=stats)


@app.route('/admin_config')
def admin_config():
    """Konfigurationsseite (Stromkreise + Kategorien in Tabs)"""
    stromkreise = get_all_stromkreise()
    kategorien = get_all_kategorien()

    return render_template('admin_config.html',
                         stromkreise=stromkreise,
                         kategorien=kategorien)


@app.route('/api/stromkreise', methods=['GET'])
def api_get_stromkreise():
    """API: Alle Stromkreise abrufen"""
    stats = get_stromkreis_statistics()
    return jsonify({
        'success': True,
        'stromkreise': stats['stromkreise'],
        'statistics': {
            'total_stromkreise': stats['total_stromkreise'],
            'unique_covered_relays': stats['unique_covered_relays'],
            'uncovered_relays': stats['uncovered_relays']
        }
    })


@app.route('/api/stromkreise/add', methods=['POST'])
def api_add_stromkreis():
    """API: Neuen Stromkreis erstellen"""
    data = request.json

    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    relay_start = data.get('relay_start', 0)
    relay_count = data.get('relay_count', 10)

    try:
        relay_start = int(relay_start)
        relay_count = int(relay_count)
    except:
        return jsonify({'success': False, 'message': 'Ungültige Relais-Werte'})

    success, message, stromkreis_id = add_stromkreis(name, description, relay_start, relay_count)

    # Bei Erfolg: Config neu laden
    if success:
        reload_relay_config()

    return jsonify({
        'success': success,
        'message': message,
        'stromkreis_id': stromkreis_id
    })


@app.route('/api/stromkreise/update', methods=['POST'])
def api_update_stromkreis():
    """API: Stromkreis aktualisieren"""
    data = request.json

    stromkreis_id = data.get('stromkreis_id')
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    relay_start = data.get('relay_start', 0)
    relay_count = data.get('relay_count', 10)

    try:
        relay_start = int(relay_start)
        relay_count = int(relay_count)
    except:
        return jsonify({'success': False, 'message': 'Ungültige Relais-Werte'})

    success, message = update_stromkreis(stromkreis_id, name, description, relay_start, relay_count)

    if success:
        reload_relay_config()

    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/stromkreise/delete', methods=['POST'])
def api_delete_stromkreis():
    """API: Stromkreis löschen"""
    data = request.json
    stromkreis_id = data.get('stromkreis_id')

    success, message = delete_stromkreis(stromkreis_id)

    if success:
        reload_relay_config()

    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/kategorien', methods=['GET'])
def api_get_kategorien():
    """API: Alle Kategorien abrufen"""
    kategorien = get_all_kategorien()
    return jsonify({
        'success': True,
        'kategorien': kategorien
    })


@app.route('/api/kategorien/add', methods=['POST'])
def api_add_kategorie():
    """API: Neue Kategorie hinzufügen"""
    data = request.json
    name = data.get('name', '').strip()

    success, message = add_kategorie(name)

    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/kategorien/delete', methods=['POST'])
def api_delete_kategorie():
    """API: Kategorie löschen"""
    data = request.json
    name = data.get('name', '')

    success, message = delete_kategorie(name)

    return jsonify({
        'success': success,
        'message': message
    })


# ==================== RELAIS-VERWALTUNG (NEUE MODULARE VERSION) ====================

@app.route('/admin_relais')
def admin_relais():
    """Neue modulare Relais-Verwaltungsseite"""
    relais_config = get_all_relais_config()
    stats = get_relais_statistics()
    kategorien = get_all_kategorien()
    stromkreise = get_all_stromkreise()

    return render_template('admin_relais.html',
                         relais_config=relais_config,
                         stats=stats,
                         kategorien=kategorien,
                         stromkreise=stromkreise)


@app.route('/api/relais/config', methods=['GET'])
def api_get_relais_config():
    """API: Alle Relais-Konfigurationen abrufen"""
    config = get_all_relais_config()
    return jsonify({
        'success': True,
        'relais_config': config
    })


@app.route('/api/relais/statistics', methods=['GET'])
def api_get_relais_statistics():
    """API: Statistiken über Relais-Konfiguration"""
    stats = get_relais_statistics()
    return jsonify({
        'success': True,
        'statistics': stats
    })


@app.route('/api/relais/update', methods=['POST'])
def api_update_relais():
    """API: Einzelnes Relais aktualisieren"""
    data = request.json

    relay_num = data.get('relay_num')
    group_number = data.get('group_number', 0)
    name = data.get('name', '')
    category = data.get('category', '')
    stromkreis = data.get('stromkreis', '')

    try:
        relay_num = int(relay_num)
        group_number = int(group_number)
    except:
        return jsonify({'success': False, 'message': 'Ungültige Eingabe'})

    success, message = update_relay_config(relay_num, group_number, name, category, stromkreis)

    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/relais/bulk_update', methods=['POST'])
def api_bulk_update_relais():
    """API: Mehrere Relais auf einmal aktualisieren"""
    data = request.json
    updates = data.get('updates', {})

    result = bulk_update_relais(updates)

    return jsonify({
        'success': result['success'],
        'message': result['message'],
        'failed_count': result['failed_count']
    })


@app.route('/api/relais/groups', methods=['GET'])
def api_get_relais_groups():
    """API: Übersicht über alle Gruppen"""
    groups = get_groups_overview()

    return jsonify({
        'success': True,
        'groups': groups
    })


@app.route('/api/relais/by_category/<category>', methods=['GET'])
def api_get_relais_by_category_new(category):
    """API: Relais einer Kategorie abrufen"""
    relais_list = get_relais_by_category(category)

    return jsonify({
        'success': True,
        'category': category,
        'relais': relais_list
    })


# ==================== RELAIS-VORLAGEN ====================

@app.route('/api/relais/templates', methods=['GET'])
def api_get_templates():
    """API: Verfügbare Vorlagen abrufen"""
    templates = get_available_templates()

    return jsonify({
        'success': True,
        'templates': templates
    })


@app.route('/api/relais/template/<template_id>', methods=['GET'])
def api_get_template_info(template_id):
    """API: Detaillierte Informationen zu einer Vorlage"""
    template_info = get_template_info(template_id)

    if template_info:
        return jsonify({
            'success': True,
            'template': template_info
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Vorlage nicht gefunden'
        }), 404


@app.route('/api/relais/apply_template', methods=['POST'])
def api_apply_template():
    """API: Vorlage anwenden"""
    try:
        data = request.json
        template_id = data.get('template_id')
        start_relay = data.get('start_relay')
        group_offset = data.get('group_offset', 0)

        if not template_id:
            return jsonify({
                'success': False,
                'message': 'Keine Vorlage ausgewählt'
            }), 400

        # Vorlage anwenden
        template_config = apply_template(template_id, start_relay, group_offset)

        if not template_config:
            return jsonify({
                'success': False,
                'message': 'Vorlage konnte nicht geladen werden'
            }), 404

        # Bulk-Update durchführen
        result = bulk_update_relais(template_config)

        if result['success']:
            return jsonify({
                'success': True,
                'message': f"Vorlage '{template_id}' erfolgreich angewendet",
                'applied_relais': list(template_config.keys()),
                'count': len(template_config)
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', 'Fehler beim Anwenden der Vorlage')
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        }), 500


# ==================== EXCEL IMPORT/EXPORT ====================

@app.route('/api/relais/excel/template/empty', methods=['GET'])
def api_download_empty_template():
    """API: Leere Excel-Vorlage herunterladen"""
    try:
        excel_file = create_excel_template(include_current_config=False)

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='VDE_Messwand_Relais_Vorlage_Leer.xlsx'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler beim Erstellen der Vorlage: {str(e)}'
        }), 500


@app.route('/api/relais/excel/template/current', methods=['GET'])
def api_download_current_config():
    """API: Excel-Vorlage mit aktueller Konfiguration herunterladen"""
    try:
        excel_file = create_excel_template(include_current_config=True)

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='VDE_Messwand_Relais_Aktuell.xlsx'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler beim Erstellen der Datei: {str(e)}'
        }), 500


@app.route('/api/relais/excel/template/predefined', methods=['GET'])
def api_get_predefined_templates():
    """API: Liste vordefinierter Excel-Vorlagen"""
    templates = get_predefined_templates()

    # Nur Metadaten zurückgeben, keine Config
    template_list = [{
        'id': t['id'],
        'name': t['name'],
        'description': t['description']
    } for t in templates]

    return jsonify({
        'success': True,
        'templates': template_list
    })


@app.route('/api/relais/excel/template/predefined/<template_id>', methods=['GET'])
def api_download_predefined_template(template_id):
    """API: Vordefinierte Excel-Vorlage herunterladen"""
    try:
        excel_file = create_predefined_template_excel(template_id)

        if not excel_file:
            return jsonify({
                'success': False,
                'message': 'Vorlage nicht gefunden'
            }), 404

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'VDE_Messwand_{template_id}.xlsx'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler beim Erstellen der Vorlage: {str(e)}'
        }), 500


@app.route('/api/relais/excel/import', methods=['POST'])
def api_import_excel():
    """API: Excel-Datei importieren"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Keine Datei hochgeladen'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Keine Datei ausgewählt'
            }), 400

        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({
                'success': False,
                'message': 'Nur Excel-Dateien (.xlsx, .xls) sind erlaubt'
            }), 400

        # Importiere Daten
        result = import_from_excel(file.stream)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler beim Importieren: {str(e)}'
        }), 500


# ==================== ÜBUNGSMODUS-VERWALTUNG ====================

@app.route('/admin_training')
def admin_training():
    """Übungsmodus-Admin-Seite - NEUE Kategorie-basierte Ansicht"""
    training_config = get_complete_training_config()
    training_pages = get_training_pages()
    kategorien = get_all_kategorien()
    stats = get_statistics()
    relais_config = get_all_relais_config()

    return render_template('admin_training_new.html',
                         training_config=training_config,
                         training_pages=training_pages,
                         kategorien=kategorien,
                         stats=stats,
                         relais_config=relais_config)


@app.route('/api/training/config', methods=['GET'])
def api_get_training_config():
    """API: Komplette Training-Konfiguration abrufen"""
    config = get_complete_training_config()

    return jsonify({
        'success': True,
        'training_config': config
    })


@app.route('/api/training/pages', methods=['GET'])
def api_get_training_pages():
    """API: Verfügbare Übungsseiten"""
    pages = get_training_pages()

    return jsonify({
        'success': True,
        'pages': pages
    })


@app.route('/api/training/<page_id>/<category>', methods=['GET'])
def api_get_training_relais(page_id, category):
    """API: Relais für Übungsseite/Kategorie abrufen"""
    relais_list = get_relais_for_training(page_id, category)

    return jsonify({
        'success': True,
        'page_id': page_id,
        'category': category,
        'relais': relais_list
    })


@app.route('/api/training/update', methods=['POST'])
def api_update_training_mapping():
    """API: Mapping für Kategorie/Übungsseite aktualisieren"""
    data = request.json

    category = data.get('category', '')
    page_id = data.get('page_id', '')
    relais_list = data.get('relais_list', [])

    success, message = update_training_mapping(category, page_id, relais_list)

    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/training/delete', methods=['POST'])
def api_delete_training_mapping():
    """API: Mapping löschen"""
    data = request.json

    category = data.get('category', '')
    page_id = data.get('page_id', '')

    success, message = delete_training_mapping(category, page_id)

    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/training/import_from_category', methods=['POST'])
def api_import_training_from_category():
    """API: Auto-Import aus Relais-Manager"""
    data = request.json

    category = data.get('category', '')
    page_id = data.get('page_id', '')

    success, message, count = import_from_relais_manager(category, page_id)

    return jsonify({
        'success': success,
        'message': message,
        'imported_count': count
    })


@app.route('/api/training/statistics', methods=['GET'])
def api_get_training_statistics():
    """API: Statistiken über Training-Config"""
    stats = get_statistics()

    return jsonify({
        'success': True,
        'statistics': stats
    })


@app.route('/api/training/activate', methods=['POST'])
def api_activate_training():
    """API: Aktiviert Relais für Übungsseite/Kategorie"""
    data = request.json

    page_id = data.get('page_id', '')
    category = data.get('category', '')

    # Hole konfigurierte Relais
    relais_list = get_relais_for_training(page_id, category)

    if not relais_list:
        return jsonify({
            'success': False,
            'message': f'Keine Relais für {page_id}/{category} konfiguriert'
        })

    try:
        # Alle Relais zurücksetzen
        relay_controller.reset_all_relays()

        # Aktiviere konfigurierte Relais (mit Gruppen-Normalisierung)
        activated = []
        for relay_num in relais_list:
            # Normalisiere zu Gruppen-Repräsentant
            representative = normalize_relay_to_representative(relay_num)

            if relay_controller.set_relay(representative, True):
                activated.append(relay_num)

        return jsonify({
            'success': True,
            'message': f'{len(activated)} Relais aktiviert',
            'activated_relais': activated
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        })


@app.route('/admin_database')
def admin_database():
    """Datenbank-Verwaltung"""
    from group_manager import get_all_relay_names, get_all_groups
    
    examinations = get_all_examinations()
    stats = get_examination_stats()
    relay_names = get_all_relay_names()
    groups = get_all_groups()
    
    # Formatiere Daten für Template mit Namen
    formatted_exams = []
    for exam in examinations:
        formatted_date, formatted_time = format_timestamp(exam['timestamp'])
        
        # Erstelle lesbare Relais-Beschreibungen
        relay_descriptions = []
        for relay_num in exam['active_relays']:
            # Prüfe ob in Gruppe
            group_name = None
            for group_data in groups.values():
                if relay_num in group_data['relays']:
                    group_name = group_data['name']
                    break
            
            if group_name:
                relay_descriptions.append({
                    'number': relay_num,
                    'name': group_name,
                    'is_group': True
                })
            elif relay_num in relay_names:
                relay_descriptions.append({
                    'number': relay_num,
                    'name': relay_names[relay_num],
                    'is_group': False
                })
            else:
                relay_descriptions.append({
                    'number': relay_num,
                    'name': f"Relais {relay_num}",
                    'is_group': False
                })
        
        formatted_exams.append({
            'id': exam['id'],
            'exam_number': exam['exam_number'],
            'relay_list': exam['active_relays'],
            'relay_descriptions': relay_descriptions,
            'formatted_date': formatted_date,
            'formatted_time': formatted_time,
            'formatted_duration': format_duration(exam['duration']),
            'is_completed': exam['is_completed']
        })
    
    return render_template('admin_database.html',
                         examinations=formatted_exams,
                         completed_count=stats['completed'],
                         incomplete_count=stats['incomplete'])


@app.route('/clear_database', methods=['POST'])
def clear_database_route():
    """Löscht alle Prüfungsdaten"""
    success = clear_database()
    return jsonify({'success': success})


@app.route('/export_database')
def export_database():
    """Exportiert Datenbank als CSV"""
    try:
        csv_data = export_to_csv()
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerows(csv_data)
        
        csv_content = output.getvalue()
        output.close()
        
        filename = f"vde_pruefungen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(csv_content, mimetype='text/csv',
                       headers={'Content-Disposition': f'attachment; filename={filename}'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/admin_network')
def admin_network():
    """Netzwerk-Informationen"""
    try:
        ifconfig_result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        network_info = ifconfig_result.stdout
        hostname = subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip()

        # Hotspot-Status
        hotspot_active = is_hotspot_active()
        current_connection = get_current_connection()
        net_info = get_network_info()
        eth_info = get_ethernet_info()

        return render_template('admin_network.html',
                             network_info=network_info,
                             hostname=hostname,
                             hotspot_active=hotspot_active,
                             current_connection=current_connection,
                             net_info=net_info,
                             eth_info=eth_info)
    except Exception as e:
        return render_template('admin_network.html',
                             network_info=f"Error: {e}",
                             hostname="Unknown",
                             hotspot_active=False,
                             current_connection=[],
                             net_info={},
                             eth_info=None)


@app.route('/api/network/hotspot/toggle', methods=['POST'])
def api_toggle_hotspot():
    """API: WiFi-Hotspot ein/ausschalten"""
    try:
        success, message = toggle_hotspot()
        return jsonify({
            'success': success,
            'message': message,
            'hotspot_active': is_hotspot_active()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        })


@app.route('/api/network/wifi/scan', methods=['GET'])
def api_scan_wifi():
    """API: WiFi-Netzwerke scannen"""
    try:
        networks = get_wifi_networks()
        return jsonify({
            'success': True,
            'networks': networks
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        })


@app.route('/api/network/wifi/connect', methods=['POST'])
def api_connect_wifi():
    """API: Mit WiFi-Netzwerk verbinden"""
    try:
        data = request.json
        ssid = data.get('ssid', '')
        password = data.get('password', '')

        if not ssid:
            return jsonify({
                'success': False,
                'message': 'SSID fehlt'
            })

        success, message = connect_to_wifi(ssid, password)
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        })


@app.route('/api/network/status', methods=['GET'])
def api_network_status():
    """API: Netzwerk-Status abrufen"""
    try:
        hotspot_active = is_hotspot_active()
        current_connection = get_current_connection()
        net_info = get_network_info()

        return jsonify({
            'success': True,
            'hotspot_active': hotspot_active,
            'current_connection': current_connection,
            'network_info': net_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        })


# ==================== GPIO-MONITOR (SCHLIESSEN) ====================

@app.route('/api/gpio/status', methods=['GET'])
def api_gpio_status():
    """API: GPIO-Schließer-Status abrufen (ohne Logging)"""
    try:
        status = get_gpio_status()
        return jsonify({
            'success': True,
            'gpio_status': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        })


@app.route('/admin_settings')
def admin_settings():
    """Admin-Einstellungen"""
    current_code = get_admin_code()
    # Zeige nur die Länge und verberge die Ziffern
    masked_code = '*' * len(current_code)
    return render_template('admin_settings.html', current_code=masked_code)


@app.route('/api/settings/change_code', methods=['POST'])
def api_change_admin_code():
    """API: Admin-Code ändern"""
    data = request.json
    current_code = data.get('current_code', '')
    new_code = data.get('new_code', '')

    # Überprüfe aktuellen Code
    if not verify_admin_code(current_code):
        return jsonify({
            'success': False,
            'message': 'Aktueller Code ist falsch'
        })

    # Setze neuen Code
    success, message = set_admin_code(new_code)

    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/shutdown_system', methods=['POST'])
def shutdown_system():
    """Fährt das System herunter"""
    try:
        relay_controller.reset_all_relays()
        subprocess.Popen(['sudo', 'shutdown', '-h', '+1'])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== DEBUG/STATUS ====================

@app.route('/debug_status')
def debug_status():
    """Debug-Informationen"""
    from serial_handler import SERIAL_AVAILABLE
    
    return jsonify({
        'serial_available': SERIAL_AVAILABLE,
        'active_relays': relay_controller.active_relays,
        'relay_states_module_0': relay_controller.relay_states[0][:10],
        'relay_states_module_1': relay_controller.relay_states[1][:10],
        'stromkreise': {k: v['name'] for k, v in STROMKREISE.items()},
        'modbus_modules': MODBUS_MODULES
    })


# ==================== APP START ====================

def initialize_app(skip_gpio_check=False):
    """Initialisiert die App einmalig"""
    init_db()

    # Lade dynamische Gruppen und Namen beim Start
    import config
    config.RELAY_GROUPS = get_all_groups()
    config.RELAY_NAMES = get_all_relay_names()

    # Initialisiere GPIO-Monitor
    import os
    gpio_pin1 = getattr(config, 'GPIO_MONITOR_PIN1', 17)
    gpio_pin2 = getattr(config, 'GPIO_MONITOR_PIN2', 27)
    gpio_shutdown_timeout = getattr(config, 'GPIO_SHUTDOWN_TIMEOUT', 120)

    # Bei Flask dev server: nur im Reloader
    # Bei Gunicorn: skip_gpio_check=True (wird vom Hook aufgerufen)
    if skip_gpio_check or os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not DEBUG:
        init_gpio_monitor(pin1=gpio_pin1, pin2=gpio_pin2, shutdown_timeout=gpio_shutdown_timeout)
    else:
        print("⏭️ GPIO-Monitor wird im Reloader-Prozess übersprungen")

    from serial_handler import SERIAL_AVAILABLE

    print("=" * 60)
    print("VDE Messwand - Modulare Version")
    print("=" * 60)
    print(f"Serial Port: {SERIAL_PORT}")
    print(f"Baud Rate: {BAUD_RATE}")
    print(f"Serial Status: {'✅ Hardware Ready' if SERIAL_AVAILABLE else '🔧 Dummy Mode'}")
    print(f"\nGPIO-Monitor: Pin {gpio_pin1} und {gpio_pin2}")
    print(f"Warnung: 'Notaus betätigt' bei geschlossenem Schließer")
    print(f"\nRelais: 0-63 (64 Stück)")
    print(f"Relais-Gruppen: {len(config.RELAY_GROUPS)} definiert")
    print(f"Benannte Relais: {len(config.RELAY_NAMES)} definiert")
    print(f"Stromkreise für UI-Gruppierung:")
    for sk_num, sk_data in STROMKREISE.items():
        print(f"  {sk_num}. {sk_data['name']}: Relais {sk_data['relays'][0]}-{sk_data['relays'][-1]}")
    print("=" * 60)

    try:
        app.run(host=HOST, port=PORT, debug=DEBUG)
    finally:
        # Cleanup beim Beenden
        cleanup_gpio()


# ==================== GUNICORN HOOKS ====================

def on_starting(server):
    """Gunicorn Hook: Wird beim Start des Master-Prozesses aufgerufen (vor den Workern)"""
    print("🚀 Gunicorn Master-Prozess: Initialisiere App...")
    initialize_app(skip_gpio_check=True)
    print("✅ App-Initialisierung abgeschlossen")


if __name__ == '__main__':
    initialize_app()