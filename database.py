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


def save_examination(exam_number, active_relays):
    """
    Speichert eine neue Prüfung in der Datenbank
    Normalisiert Relais-Gruppen automatisch
    
    Args:
        exam_number: Prüfungsnummer
        active_relays: Liste der aktiven Relais
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        # Normalisiere Relais-Liste (Gruppen zusammenfassen)
        normalized_relays = normalize_relay_list(active_relays)
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO examinations (exam_number, active_relays, timestamp, duration)
            VALUES (?, ?, ?, ?)
        ''', (exam_number, json.dumps(normalized_relays), datetime.now(), 0))
        conn.commit()
        conn.close()
        print(f"✓ Examination saved: {exam_number} with relays {normalized_relays}")
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
    
    csv_data = [['Prüfungsnummer', 'Relais_IDs', 'Zeitstempel', 'Dauer_Sekunden', 'Status']]
    
    for exam in examinations:
        relays_str = ', '.join(map(str, exam['active_relays']))
        status = 'Abgeschlossen' if exam['is_completed'] else 'Unterbrochen'
        
        csv_data.append([
            exam['exam_number'],
            relays_str,
            exam['timestamp'],
            exam['duration'] or 0,
            status
        ])
    
    return csv_data
