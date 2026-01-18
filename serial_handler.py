"""
VDE Messwand - Serial/PySerial Handler
Robuste Import-Lösung mit Dummy-Fallback
"""

serial = None
SERIAL_AVAILABLE = False


def import_serial():
    """Versucht pyserial zu importieren, erstellt bei Bedarf Dummy"""
    global serial, SERIAL_AVAILABLE
    try:
        import serial as pyserial
        if hasattr(pyserial, 'Serial') and hasattr(pyserial, 'EIGHTBITS'):
            serial = pyserial
            SERIAL_AVAILABLE = True
            print(f"✓ pyserial successfully imported, version: {getattr(serial, 'VERSION', 'unknown')}")
            return True
    except Exception as e:
        print(f"Direct import failed: {e}")
    
    print("⚠ Creating dummy serial interface for testing")
    create_dummy_serial()
    return False


def create_dummy_serial():
    """Erstellt eine Dummy-Serial-Klasse für Tests ohne Hardware"""
    global serial, SERIAL_AVAILABLE
    
    class DummySerial:
        VERSION = "DUMMY-1.0"
        EIGHTBITS = 8
        PARITY_NONE = 'N'
        STOPBITS_TWO = 2
        SerialTimeoutException = Exception
        
        class Serial:
            def __init__(self, port=None, baudrate=9600, **kwargs):
                print(f"🔧 DummySerial: Simulating connection to {port} at {baudrate} baud")
                self.port = port
                self.baudrate = baudrate
                self.is_open = True
                self.in_waiting = 0
            
            def write(self, data):
                return len(data) if data else 0
            
            def read(self, size):
                return b'\x01\x05\x00\x00\xFF\x00\x8C\x3A'[:size]
            
            def flush(self):
                pass
            
            def reset_input_buffer(self):
                pass
            
            def reset_output_buffer(self):
                pass
            
            def close(self):
                self.is_open = False
    
    serial = DummySerial()
    SERIAL_AVAILABLE = False


# Automatischer Import beim Modul-Load
import_serial()
