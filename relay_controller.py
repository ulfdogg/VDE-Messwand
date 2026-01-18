"""
VDE Messwand - Relay Controller
High-Level Relais-Steuerung
"""
import time
from modbus_controller import ModbusRTU
from config import SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT, MODBUS_MODULES


class RelayController:
    """High-Level Relais-Steuerung für 64 Relais auf 2 Modulen"""
    
    def __init__(self):
        self.active_relays = []
        self.modbus = ModbusRTU(SERIAL_PORT, BAUD_RATE, SERIAL_TIMEOUT)
        self.relay_states = {0: [False] * 32, 1: [False] * 32}

    def get_all_groups(self):
        """Lädt alle Gruppen (config.py + JSON-Datei)"""
        try:
            from group_manager import get_all_groups
            return get_all_groups()
        except Exception as e:
            print(f"Warning: Could not load groups from file: {e}")
            from config import RELAY_GROUPS
            return RELAY_GROUPS

    def get_relay_group(self, relay_num):
        """
        Prüft, ob ein Relais Teil einer Gruppe ist

        Args:
            relay_num: Relais-Nummer

        Returns:
            Tuple (group_name, relay_list) oder (None, [relay_num]) wenn keine Gruppe
        """
        # Lade aktuelle Gruppen (inkl. dynamische aus JSON)
        relay_groups = self.get_all_groups()

        for group_name, group_data in relay_groups.items():
            if relay_num in group_data['relays']:
                print(f"Relay {relay_num} is part of group '{group_name}' with relays {group_data['relays']}")
                return group_name, group_data['relays']
        return None, [relay_num]
    
    def normalize_relay_to_group_representative(self, relay_num):
        """
        Gibt den Gruppen-Repräsentanten zurück (immer das erste Relais der Gruppe)
        
        Args:
            relay_num: Beliebiges Relais
            
        Returns:
            Repräsentant der Gruppe oder relay_num selbst
        """
        group_name, relay_list = self.get_relay_group(relay_num)
        return relay_list[0]  # Immer das erste Relais als Repräsentant

    def get_module_info(self, relay_num):
        """
        Ermittelt Modul, lokale Adresse und Slave-ID für ein Relais
        
        Args:
            relay_num: Globale Relais-Nummer (0-63)
            
        Returns:
            (module_idx, local_relay, slave_id)
        """
        if relay_num < 32:
            return 0, relay_num, MODBUS_MODULES[0]['slave_id']
        else:
            return 1, relay_num - 32, MODBUS_MODULES[1]['slave_id']

    def set_relay(self, relay_num, state):
        """
        Schaltet ein einzelnes Relais (oder eine Gruppe, wenn es Teil einer ist)
        
        Args:
            relay_num: Globale Relais-Nummer (0-63)
            state: True = EIN, False = AUS
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            if not 0 <= relay_num <= 63:
                print(f"Invalid relay number: {relay_num}")
                return False
            
            # Prüfen ob Teil einer Gruppe
            group_name, relay_group = self.get_relay_group(relay_num)
            representative = relay_group[0]  # Erstes Relais ist Repräsentant
            
            success = True
            for relay in relay_group:
                module_idx, local_relay, slave_id = self.get_module_info(relay)
                self.relay_states[module_idx][local_relay] = state

                print(f"  Setting relay {relay} (Module {module_idx}, Local {local_relay}, Slave {slave_id}) to {state}")
                relay_success = self.modbus.write_single_coil(slave_id, local_relay, state)

                if not relay_success:
                    print(f"  ❌ Failed to set relay {relay}")
                    success = False
                else:
                    print(f"  ✅ Relay {relay} set successfully")

                # Längere Pause zwischen Gruppen-Relais für stabile Bus-Kommunikation
                time.sleep(0.1)  # 100ms Pause zwischen jedem Relais
            
            # Nur den Repräsentanten in active_relays tracken
            if success:
                if state and representative not in self.active_relays:
                    self.active_relays.append(representative)
                elif not state and representative in self.active_relays:
                    self.active_relays.remove(representative)
                
                if group_name:
                    print(f"✓ Relay group '{group_name}' ({relay_group}) set to {'ON' if state else 'OFF'}")
                else:
                    print(f"Relay {relay_num} set to {'ON' if state else 'OFF'}")
            
            return success
        
        except Exception as e:
            print(f"Error setting relay {relay_num}: {e}")
            return False

    def set_multiple_relays(self, relay_states_dict):
        """
        Schaltet mehrere Relais auf einmal
        
        Args:
            relay_states_dict: {relay_num: state, ...}
            
        Returns:
            (success_count, failed_relays)
        """
        success_count = 0
        failed_relays = []
        
        for relay_num, state in relay_states_dict.items():
            if self.set_relay(relay_num, state):
                success_count += 1
            else:
                failed_relays.append(relay_num)
            # Längere Pause zwischen verschiedenen Relais/Gruppen
            time.sleep(0.15)  # 150ms Pause zwischen Befehlen
        
        return success_count, failed_relays

    def reset_all_relays(self):
        """
        Setzt alle Relais auf beiden Modulen zurück

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            print("=" * 60)
            print("RESET ALL RELAYS - Starting...")
            print("=" * 60)

            success = True
            for module_idx in [0, 1]:
                slave_id = MODBUS_MODULES[module_idx]['slave_id']
                states = [False] * 32

                print(f"\nResetting Module {module_idx + 1} (Slave ID {slave_id})...")
                module_success = self.modbus.write_multiple_coils(slave_id, 0, states)

                if module_success:
                    self.relay_states[module_idx] = states.copy()
                    print(f"✅ Module {module_idx + 1} (Slave ID {slave_id}) reset successfully")
                else:
                    print(f"❌ Failed to reset module {module_idx + 1}")
                    success = False

                time.sleep(0.2)  # Längere Pause zwischen Modulen

            if success:
                self.active_relays = []
                print("\n" + "=" * 60)
                print("✅ All relays reset successfully")
                print("=" * 60)
                return True
            else:
                print("\n" + "=" * 60)
                print("❌ Reset failed for some modules")
                print("=" * 60)
                return False

        except Exception as e:
            print(f"❌ Error resetting relays: {e}")
            import traceback
            traceback.print_exc()
            return False

    def read_all_relay_status(self):
        """
        Liest den tatsächlichen Status aller 64 Relais von der Hardware aus

        Returns:
            Dictionary {relay_num: state} oder None bei Fehler
        """
        try:
            all_relays = {}

            # Beide Module auslesen
            for module_idx in [0, 1]:
                slave_id = MODBUS_MODULES[module_idx]['slave_id']

                # 32 Relais pro Modul lesen
                coils = self.modbus.read_coils(slave_id, 0, 32)

                if coils is None:
                    print(f"❌ Konnte Modul {module_idx + 1} nicht auslesen")
                    return None

                # Status in Dictionary speichern
                for local_relay, state in enumerate(coils):
                    global_relay = (module_idx * 32) + local_relay
                    all_relays[global_relay] = state

            return all_relays

        except Exception as e:
            print(f"❌ Fehler beim Lesen aller Relais: {e}")
            import traceback
            traceback.print_exc()
            return None

    def test_all_relays(self):
        """
        Testet alle 64 Relais nacheinander

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            print("Starting relay test...")
            for relay in range(64):
                print(f"Testing relay {relay}")

                if not self.set_relay(relay, True):
                    print(f"Failed to turn ON relay {relay}")
                    return False
                time.sleep(1.0)  # 1 Sekunde Pause nach Einschalten

                if not self.set_relay(relay, False):
                    print(f"Failed to turn OFF relay {relay}")
                    return False
                time.sleep(1.0)  # 1 Sekunde Pause nach Ausschalten

            print("Relay test completed successfully")
            return True

        except Exception as e:
            print(f"Error testing relays: {e}")
            return False

    def get_active_relays(self):
        """
        Gibt Liste der aktiven Relais zurück (Gruppen als Repräsentant)
        """
        return self.active_relays.copy()
    
    def get_active_relays_normalized(self):
        """
        Gibt normalisierte Liste zurück - alle Gruppen-Mitglieder werden zum Repräsentanten
        """
        normalized = []
        for relay in self.active_relays:
            representative = self.normalize_relay_to_group_representative(relay)
            if representative not in normalized:
                normalized.append(representative)
        return normalized

    def get_relay_state(self, relay_num):
        """
        Gibt den aktuellen Zustand eines Relais zurück
        
        Args:
            relay_num: Globale Relais-Nummer (0-63)
            
        Returns:
            True/False oder None bei ungültiger Nummer
        """
        if not 0 <= relay_num <= 63:
            return None
        
        module_idx, local_relay, _ = self.get_module_info(relay_num)
        return self.relay_states[module_idx][local_relay]

    def get_all_relay_states(self):
        """Gibt Dictionary aller Relais-Zustände zurück"""
        all_states = {}
        for i in range(64):
            all_states[i] = self.get_relay_state(i)
        return all_states
