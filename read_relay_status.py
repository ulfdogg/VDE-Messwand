#!/usr/bin/env python3
"""
VDE Messwand - Relay Status Reader
Liest den aktuellen Status aller 64 Relais aus
"""
import struct
import time
import sys
from serial_handler import serial, SERIAL_AVAILABLE
from config import SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT, MODBUS_MODULES


class ModbusReader:
    """Modbus RTU Reader für Relais-Status"""

    def __init__(self, port, baudrate=9600, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.connect()

    def connect(self):
        """Verbindung zur seriellen Schnittstelle herstellen"""
        try:
            if SERIAL_AVAILABLE and hasattr(serial, 'Serial'):
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_TWO,
                    timeout=self.timeout,
                    write_timeout=self.timeout,
                    inter_byte_timeout=0.1
                )
                time.sleep(0.1)
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                print(f"✅ Verbunden mit {self.port}")
                return True
            else:
                print("❌ Serial nicht verfügbar - Dummy-Modus")
                return False
        except Exception as e:
            print(f"❌ Fehler beim Verbinden: {e}")
            return False

    def calculate_crc16(self, data):
        """CRC-16 Modbus Berechnung"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc >> 1) ^ 0xA001 if crc & 0x0001 else crc >> 1
        return struct.pack('<H', crc)

    def read_coils(self, slave_id, start_addr, num_coils):
        """
        Liest Coil-Status (FC01 - Read Coils)

        Args:
            slave_id: Modbus Slave ID
            start_addr: Start-Adresse
            num_coils: Anzahl zu lesender Coils

        Returns:
            Liste mit Boolean-Werten oder None bei Fehler
        """
        try:
            if not self.serial_conn or not self.serial_conn.is_open:
                print("❌ Keine Verbindung")
                return None

            # Modbus FC01 (Read Coils) Frame erstellen
            frame = struct.pack('>BBHH', slave_id, 0x01, start_addr, num_coils)
            frame += self.calculate_crc16(frame)

            # Senden
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            self.serial_conn.write(frame)
            self.serial_conn.flush()

            # Warten auf Antwort
            time.sleep(0.1)

            # Antwort lesen
            response = bytearray()
            start_time = time.time()

            # Minimale Antwort: Slave(1) + FC(1) + ByteCount(1) + Data(min 1) + CRC(2) = 6 bytes
            min_response_size = 5

            while len(response) < min_response_size:
                if time.time() - start_time > self.timeout:
                    print(f"⏱️ Timeout - nur {len(response)} bytes empfangen")
                    break

                if self.serial_conn.in_waiting > 0:
                    response.extend(self.serial_conn.read(self.serial_conn.in_waiting))
                    time.sleep(0.01)
                else:
                    time.sleep(0.01)

            if len(response) < min_response_size:
                print(f"❌ Antwort zu kurz: {len(response)} bytes")
                return None

            # Antwort validieren
            if response[0] != slave_id:
                print(f"❌ Falsche Slave ID: erwartet {slave_id}, bekommen {response[0]}")
                return None

            if response[1] != 0x01:
                if response[1] == 0x81:  # Error response
                    error_code = response[2] if len(response) > 2 else 0
                    print(f"❌ Modbus Fehler: Code {error_code}")
                else:
                    print(f"❌ Falsche Funktion: erwartet 0x01, bekommen {response[1]:02x}")
                return None

            # CRC prüfen
            received_crc = response[-2:]
            calculated_crc = self.calculate_crc16(response[:-2])

            if received_crc != calculated_crc:
                print(f"❌ CRC Fehler - Erwartet: {calculated_crc.hex()}, Bekommen: {received_crc.hex()}")
                return None

            # Daten extrahieren
            byte_count = response[2]
            coil_data = response[3:3+byte_count]

            # Bits in Boolean-Liste umwandeln
            coils = []
            for byte_idx, byte_val in enumerate(coil_data):
                for bit_idx in range(8):
                    if len(coils) < num_coils:
                        coils.append(bool(byte_val & (1 << bit_idx)))

            return coils[:num_coils]

        except Exception as e:
            print(f"❌ Fehler beim Lesen: {e}")
            return None

    def close(self):
        """Verbindung schließen"""
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
        except Exception as e:
            print(f"Fehler beim Schließen: {e}")


def read_all_relays():
    """Liest alle 64 Relais-Status aus"""
    print("=" * 60)
    print("VDE Messwand - Relay Status Reader")
    print("=" * 60)
    print()

    reader = ModbusReader(SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT)

    all_relays = {}

    # Beide Module auslesen
    for module_idx, module in enumerate(MODBUS_MODULES):
        slave_id = module['slave_id']
        print(f"\n📦 Modul {module_idx + 1} (Slave ID: {slave_id})")
        print("-" * 60)

        # 32 Relais pro Modul lesen (Adresse 0-31)
        coils = reader.read_coils(slave_id, 0, 32)

        if coils is None:
            print(f"❌ Konnte Modul {module_idx + 1} nicht auslesen")
            continue

        # Relais-Status anzeigen
        on_count = 0
        off_count = 0

        for local_relay, state in enumerate(coils):
            global_relay = (module_idx * 32) + local_relay
            all_relays[global_relay] = state

            status = "🟢 EIN " if state else "⚫ AUS"
            print(f"  Relais {global_relay:2d} (Modul {module_idx + 1}, Lokal {local_relay:2d}): {status}")

            if state:
                on_count += 1
            else:
                off_count += 1

        print(f"\n  Zusammenfassung Modul {module_idx + 1}: {on_count} EIN, {off_count} AUS")

    # Gesamtübersicht
    print("\n" + "=" * 60)
    total_on = sum(1 for state in all_relays.values() if state)
    total_off = sum(1 for state in all_relays.values() if not state)
    print(f"GESAMT: {total_on} Relais EIN, {total_off} Relais AUS von {len(all_relays)}")

    # Aktive Relais auflisten
    if total_on > 0:
        active_relays = [num for num, state in all_relays.items() if state]
        print(f"\nAktive Relais: {', '.join(map(str, active_relays))}")

    print("=" * 60)

    reader.close()
    return all_relays


if __name__ == "__main__":
    try:
        read_all_relays()
    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
