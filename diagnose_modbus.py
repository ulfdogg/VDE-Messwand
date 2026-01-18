#!/usr/bin/env python3
"""
Modbus Diagnose-Tool
Testet verschiedene Konfigurationen
"""
import serial
import struct
import time

def calculate_crc16(data):
    """CRC-16 Modbus Berechnung"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 0x0001 else crc >> 1
    return struct.pack('<H', crc)

def test_modbus(port='/dev/ttyACM0', baudrate=9600, slave_id=1):
    """Testet Modbus-Kommunikation"""
    print(f"\n{'='*60}")
    print(f"Test: Port={port}, Baudrate={baudrate}, Slave ID={slave_id}")
    print(f"{'='*60}")

    try:
        # Öffne Serial-Port
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=1.0
        )

        time.sleep(0.1)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        # Test 1: Read Coils (FC01) - Relais-Status lesen
        print("\n📖 Test 1: Read Coils (FC01) - Lese Coil 0")
        frame = struct.pack('>BBHH', slave_id, 0x01, 0, 1)  # Slave, FC01, Start=0, Count=1
        frame += calculate_crc16(frame)

        print(f"   TX: {frame.hex()}")
        ser.write(frame)
        ser.flush()
        time.sleep(0.1)

        response = ser.read(100)
        print(f"   RX: {response.hex() if response else '(keine Antwort)'} ({len(response)} bytes)")

        if len(response) > 0:
            print("   ✅ Gerät antwortet!")
            ser.close()
            return True
        else:
            print("   ❌ Keine Antwort")

        # Test 2: Write Single Coil (FC05) - Relais einschalten
        print("\n✏️  Test 2: Write Single Coil (FC05) - Schalte Coil 0 EIN")
        ser.reset_input_buffer()
        frame = struct.pack('>BBH', slave_id, 0x05, 0) + struct.pack('>H', 0xFF00)
        frame += calculate_crc16(frame)

        print(f"   TX: {frame.hex()}")
        ser.write(frame)
        ser.flush()
        time.sleep(0.1)

        response = ser.read(100)
        print(f"   RX: {response.hex() if response else '(keine Antwort)'} ({len(response)} bytes)")

        if len(response) > 0:
            print("   ✅ Gerät antwortet!")
            ser.close()
            return True

        ser.close()
        return False

    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return False

# Hauptprogramm
print("🔍 Modbus RTU Diagnose-Tool")
print("="*60)

# Test verschiedene Konfigurationen
test_configs = [
    # (Slave ID, Baudrate)
    (1, 9600),
    (2, 9600),
    (1, 19200),
    (2, 19200),
    (1, 115200),
]

success = False
for slave_id, baudrate in test_configs:
    if test_modbus(slave_id=slave_id, baudrate=baudrate):
        print(f"\n🎉 ERFOLG mit Slave ID={slave_id}, Baudrate={baudrate}")
        success = True
        break
    time.sleep(0.5)

if not success:
    print("\n❌ Keine funktionierende Konfiguration gefunden!")
    print("\n💡 Überprüfen Sie:")
    print("   1. Ist das Modbus-Gerät eingeschaltet?")
    print("   2. Sind TX/RX richtig verbunden?")
    print("   3. Ist ein RS485-Adapter nötig und richtig angeschlossen?")
    print("   4. Ist die Masse (GND) verbunden?")
