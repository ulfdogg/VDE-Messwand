"""
VDE Messwand - Modbus RTU Controller
"""
import struct
import time
from serial_handler import serial, SERIAL_AVAILABLE


class ModbusRTU:
    """Modbus RTU Kommunikation mit CRC-Prüfung und Retry-Logik"""
    
    def __init__(self, port, baudrate=9600, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.last_command_time = 0
        # Erhöhtes Intervall für stabilere Bus-Kommunikation (100ms)
        self.min_command_interval = 0.1
        self.connect()

    def connect(self):
        """Verbindung zur seriellen Schnittstelle herstellen"""
        global SERIAL_AVAILABLE
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
                print(f"✅ Real Modbus RTU connected on {self.port}")
                return True
            else:
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout
                )
                print(f"🔧 Dummy Modbus RTU mode on {self.port}")
                return True
        except Exception as e:
            print(f"❌ Error connecting to Modbus RTU: {e}")
            try:
                self.serial_conn = serial.Serial()
                print("🔧 Fallback to dummy mode")
                return True
            except:
                print("❌ Complete serial failure")
                return False

    def calculate_crc16(self, data):
        """CRC-16 Modbus Berechnung"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc >> 1) ^ 0xA001 if crc & 0x0001 else crc >> 1
        return struct.pack('<H', crc)

    def wait_for_command_interval(self):
        """Wartezeit zwischen Befehlen einhalten"""
        elapsed = time.time() - self.last_command_time
        if elapsed < self.min_command_interval:
            time.sleep(self.min_command_interval - elapsed)
        self.last_command_time = time.time()

    def send_command(self, slave_id, function_code, start_addr, data, retry_count=3):
        """Modbus-Befehl senden mit Retry-Logik"""
        for attempt in range(retry_count):
            try:
                if not self.serial_conn or not self.serial_conn.is_open:
                    self.connect()
                
                self.wait_for_command_interval()
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                
                # Frame zusammenbauen
                frame = struct.pack('>BBH', slave_id, function_code, start_addr) + data
                frame += self.calculate_crc16(frame)
                
                print(f"TX (Attempt {attempt + 1}): {frame.hex()}")
                
                # Senden
                bytes_written = self.serial_conn.write(frame)
                if bytes_written != len(frame):
                    print(f"Warning: Only {bytes_written} of {len(frame)} bytes written")
                
                self.serial_conn.flush()
                # Längere Wartezeit für Antwort (50ms statt 20ms)
                time.sleep(0.05)

                # Antwort empfangen
                response = bytearray()
                start_time = time.time()
                
                while len(response) < 8:
                    if time.time() - start_time > self.timeout:
                        print(f"Timeout waiting for response (got {len(response)} bytes)")
                        break
                    if self.serial_conn.in_waiting > 0:
                        response.extend(self.serial_conn.read(self.serial_conn.in_waiting))
                        time.sleep(0.01)
                    else:
                        time.sleep(0.01)
                
                print(f"RX (Attempt {attempt + 1}): {response.hex()} ({len(response)} bytes)")
                
                # CRC prüfen
                if len(response) >= 5:
                    received_crc = response[-2:]
                    calculated_crc = self.calculate_crc16(response[:-2])
                    if received_crc == calculated_crc:
                        print(f"✅ Command successful on attempt {attempt + 1}")
                        return True
                    else:
                        print(f"❌ CRC mismatch - Expected: {calculated_crc.hex()}, Got: {received_crc.hex()}")
                        if attempt < retry_count - 1:
                            time.sleep(0.15 * (attempt + 1))  # Längere Wartezeit zwischen Retries
                            continue
                else:
                    print(f"❌ Incomplete response")
                    if attempt < retry_count - 1:
                        time.sleep(0.15 * (attempt + 1))  # Längere Wartezeit zwischen Retries
                        continue
            
            except Exception as e:
                print(f"Modbus error (attempt {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(0.1 * (attempt + 1))
                    continue
        
        print(f"❌ Command failed after {retry_count} attempts")
        return False

    def write_single_coil(self, slave_id, coil_addr, state):
        """Einzelnes Relais schalten (FC05)"""
        value = 0xFF00 if state else 0x0000
        data = struct.pack('>H', value)
        return self.send_command(slave_id, 0x05, coil_addr, data)

    def write_multiple_coils(self, slave_id, start_addr, states):
        """Mehrere Relais gleichzeitig schalten (FC15)"""
        num_coils = len(states)
        byte_count = (num_coils + 7) // 8

        coil_bytes = []
        for i in range(byte_count):
            byte_val = 0
            for bit in range(8):
                coil_index = i * 8 + bit
                if coil_index < num_coils and states[coil_index]:
                    byte_val |= (1 << bit)
            coil_bytes.append(byte_val)

        data = struct.pack('>HB', num_coils, byte_count) + bytes(coil_bytes)
        return self.send_command(slave_id, 0x0F, start_addr, data)

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
                self.connect()

            self.wait_for_command_interval()
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()

            # Modbus FC01 (Read Coils) Frame erstellen
            frame = struct.pack('>BBHH', slave_id, 0x01, start_addr, num_coils)
            frame += self.calculate_crc16(frame)

            # Senden
            bytes_written = self.serial_conn.write(frame)
            if bytes_written != len(frame):
                print(f"Warning: Only {bytes_written} of {len(frame)} bytes written")

            self.serial_conn.flush()
            time.sleep(0.05)

            # Antwort lesen
            response = bytearray()
            start_time = time.time()
            min_response_size = 5

            while len(response) < min_response_size:
                if time.time() - start_time > self.timeout:
                    print(f"Timeout - nur {len(response)} bytes empfangen")
                    return None

                if self.serial_conn.in_waiting > 0:
                    response.extend(self.serial_conn.read(self.serial_conn.in_waiting))
                    time.sleep(0.01)
                else:
                    time.sleep(0.01)

            if len(response) < min_response_size:
                print(f"Antwort zu kurz: {len(response)} bytes")
                return None

            # Validierung
            if response[0] != slave_id:
                print(f"Falsche Slave ID: erwartet {slave_id}, bekommen {response[0]}")
                return None

            if response[1] != 0x01:
                if response[1] == 0x81:
                    error_code = response[2] if len(response) > 2 else 0
                    print(f"Modbus Fehler: Code {error_code}")
                return None

            # CRC prüfen
            received_crc = response[-2:]
            calculated_crc = self.calculate_crc16(response[:-2])

            if received_crc != calculated_crc:
                print(f"CRC Fehler")
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
            print(f"Fehler beim Lesen: {e}")
            return None

    def close(self):
        """Verbindung schließen"""
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
                print("Serial connection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")
