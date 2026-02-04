"""
VDE Messwand - Datenbank-Verwaltung
"""
import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH, EXAM_NUMBER_PREFIX


def init_db():
    """Initialisiert die Datenbank"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS examinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_number TEXT UNIQUE,
            active_relays TEXT,
            timestamp DATETIME,
            duration INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✓ Database initialized: {DATABASE_PATH}")


def generate_exam_number():
    """Generiert eine fortlaufende Prüfungsnummer"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT exam_number FROM examinations ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    
    if result:
        try:
            last_number = int(result[0].split('-')[-1])
            next_number = last_number + 1
        except:
            next_number = 1
    else:
        next_number = 1
    
    return f"{EXAM_NUMBER_PREFIX}-{next_number}"


def normalize_relay_list(relay_list):
    """
    Normalisiert eine Relais-Liste: Gruppen-Mitglieder werden zu Repräsentanten

    Args:
        relay_list: Liste von Relais-Nummern

    Returns:
        Normalisierte Liste (ohne Duplikate)
    """
    from config import RELAY_GROUPS

    normalized = []
    for relay in relay_list:
        # Finde Gruppe
        representative = relay
        for group_data in RELAY_GROUPS.values():
            if relay in group_data['relays']:
                representative = group_data['relays'][0]
                break

        if representative not in normalized:
            normalized.append(representative)

    return normalized


def get_relay_display_name(relay_num):
    """
    Gibt den Anzeigenamen für ein Relais zurück.
    Bei Gruppen wird der Gruppenname verwendet, sonst der Relais-Name.
    Wenn kein Name vergeben ist, wird "Relais X" zurückgegeben.

    Args:
        relay_num: Relais-Nummer (0-63)

    Returns:
        Anzeigename als String
    """
    from config import RELAY_GROUPS
    from group_manager import get_all_relay_names

    # Prüfe zuerst ob das Relais zu einer Gruppe gehört
    for group_data in RELAY_GROUPS.values():
        if relay_num in group_data['relays']:
            return group_data.get('name', f'Gruppe {relay_num}')

    # Sonst: Hole den Relais-Namen
    relay_names = get_all_relay_names()
    relay_data = relay_names.get(relay_num, {})

    if isinstance(relay_data, str):
        # Alte Struktur: nur String
        name = relay_data
    elif isinstance(relay_data, dict):
        # Neue Struktur: Dictionary
        name = relay_data.get('name', '')
    else:
        name = ''

    # Wenn Name vorhanden, verwende ihn, sonst "Relais X"
    if name and name.strip():
        return name.strip()
    else:
        return f'Relais {relay_num}'


def relay_list_to_names(relay_list):
    """
    Wandelt eine Liste von Relais-Nummern in eine Liste von Namen um.

    Args:
        relay_list: Liste von Relais-Nummern

    Returns:
        Liste von Anzeigenamen
    """
    return [get_relay_display_name(relay_num) for relay_num in relay_list]


def save_examination(exam_number, active_relays):
    """
    Speichert eine neue Prüfung in der Datenbank
    Normalisiert Relais-Gruppen automatisch und speichert Namen statt Nummern

    Args:
        exam_number: Prüfungsnummer
        active_relays: Liste der aktiven Relais (Nummern)

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        # Normalisiere Relais-Liste (Gruppen zusammenfassen)
        normalized_relays = normalize_relay_list(active_relays)

        # Wandle Nummern in Namen um
        relay_names = relay_list_to_names(normalized_relays)

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO examinations (exam_number, active_relays, timestamp, duration)
            VALUES (?, ?, ?, ?)
        ''', (exam_number, json.dumps(relay_names), datetime.now(), 0))
        conn.commit()
        conn.close()
        print(f"✓ Examination saved: {exam_number} with relays {relay_names}")
        return True
    except Exception as e:
        print(f"Error saving examination: {e}")
        return False


def update_examination_duration(exam_number, duration):
    """
    Aktualisiert die Dauer einer Prüfung
    
    Args:
        exam_number: Prüfungsnummer
        duration: Dauer in Sekunden
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE examinations SET duration = ? WHERE exam_number = ?',
            (duration, exam_number)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating examination duration: {e}")
        return False


def get_all_examinations():
    """
    Lädt alle Prüfungen aus der Datenbank
    
    Returns:
        Liste von Dictionaries mit Prüfungsdaten
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM examinations ORDER BY timestamp DESC')
    raw_examinations = cursor.fetchall()
    conn.close()
    
    examinations = []
    for exam in raw_examinations:
        exam_id, exam_number, active_relays_json, timestamp, duration = exam
        
        try:
            relay_list = json.loads(active_relays_json) if active_relays_json else []
        except:
            relay_list = []
        
        examinations.append({
            'id': exam_id,
            'exam_number': exam_number,
            'active_relays': relay_list,
            'timestamp': timestamp,
            'duration': duration,
            'is_completed': duration and duration > 0
        })
    
    return examinations


def get_examination_stats():
    """
    Berechnet Statistiken über alle Prüfungen
    
    Returns:
        Dictionary mit Statistiken
    """
    examinations = get_all_examinations()
    
    total = len(examinations)
    completed = sum(1 for e in examinations if e['is_completed'])
    incomplete = total - completed
    
    avg_duration = 0
    if completed > 0:
        total_duration = sum(e['duration'] for e in examinations if e['is_completed'])
        avg_duration = total_duration / completed
    
    return {
        'total': total,
        'completed': completed,
        'incomplete': incomplete,
        'avg_duration': avg_duration
    }


def clear_database():
    """
    Löscht alle Prüfungen aus der Datenbank
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM examinations')
        conn.commit()
        conn.close()
        print("✓ Database cleared")
        return True
    except Exception as e:
        print(f"Error clearing database: {e}")
        return False


def export_to_csv():
    """
    Exportiert alle Prüfungen als CSV-Daten

    Returns:
        Liste von Listen (CSV-Zeilen)
    """
    examinations = get_all_examinations()

    csv_data = [['Prüfungsnummer', 'Aktive_Fehler', 'Zeitstempel', 'Dauer_Sekunden', 'Status']]

    for exam in examinations:
        # active_relays enthält jetzt Namen (Strings) statt Nummern
        relays_str = ', '.join(str(r) for r in exam['active_relays'])
        status = 'Abgeschlossen' if exam['is_completed'] else 'Unterbrochen'

        csv_data.append([
            exam['exam_number'],
            relays_str,
            exam['timestamp'],
            exam['duration'] or 0,
            status
        ])

    return csv_data
