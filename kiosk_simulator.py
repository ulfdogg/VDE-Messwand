#!/usr/bin/env python3
"""
VDE Messwand - Kiosk Simulator
Simuliert einen echten Benutzer am Kiosk-Terminal
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import os

# ==================== KONFIGURATION ====================

BASE_URL = "http://10.100.72.191:8000"
ADMIN_CODE = "1234"

# Kiosk-Display Einstellungen (für Raspberry Pi)
DISPLAY = ":0"  # Standard X Display
FULLSCREEN = True

# Benutzer-Simulation Einstellungen
REALISTIC_DELAYS = True  # Realistische Wartezeiten wie echter Benutzer
MIN_DELAY = 2  # Minimum Sekunden zwischen Aktionen
MAX_DELAY = 5  # Maximum Sekunden zwischen Aktionen

# ==================== REALISTISCHE BENUTZER-SIMULATION ====================

class KioskUser:
    """Simuliert einen echten Benutzer am Kiosk"""

    def __init__(self):
        self.driver = None
        self.action_count = 0

    def human_delay(self, min_sec=None, max_sec=None):
        """Wartet wie ein echter Mensch"""
        if REALISTIC_DELAYS:
            min_sec = min_sec or MIN_DELAY
            max_sec = max_sec or MAX_DELAY
            delay = random.uniform(min_sec, max_sec)
            print(f"   ⏱️  Warte {delay:.1f}s (wie echter Benutzer)...")
            time.sleep(delay)
        else:
            time.sleep(0.5)

    def setup_kiosk_browser(self):
        """Startet Browser im Kiosk-Mode"""
        print("\n🖥️  Starte Kiosk-Browser...")

        try:
            # Setze DISPLAY für Pi
            os.environ['DISPLAY'] = DISPLAY

            options = webdriver.ChromeOptions()

            # Kiosk-Mode Optionen
            if FULLSCREEN:
                options.add_argument('--kiosk')  # Vollbild, keine Browser-UI
                options.add_argument('--start-maximized')

            # Pi-spezifische Optionen
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-extensions')

            # Touch-Screen optimiert
            options.add_argument('--touch-events=enabled')

            # Auto-Login deaktivieren
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)

            # Manuell ChromeDriver-Pfad setzen (für Raspberry Pi ARM)
            from selenium.webdriver.chrome.service import Service
            service = Service('/usr/bin/chromedriver')

            self.driver = webdriver.Chrome(service=service, options=options)

            print("✅ Browser gestartet im Kiosk-Mode!")
            return True

        except Exception as e:
            print(f"❌ Fehler beim Starten: {e}")
            print("\nTroubleshooting:")
            print("  1. Ist chromium-chromedriver installiert?")
            print("     sudo apt-get install chromium-chromedriver")
            print("  2. Läuft das X-Display?")
            print("     echo $DISPLAY")
            print("  3. Ist der Server erreichbar?")
            print(f"     curl {BASE_URL}")
            return False

    def touch_click(self, by: By, selector: str, description: str, timeout: int = 10):
        """Simuliert Touch-Klick (mit Finger auf Display)"""
        try:
            print(f"👆 Klicke auf: {description}")

            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )

            # Kurze Pause (Benutzer muss Element finden)
            time.sleep(random.uniform(0.5, 1.5))

            element.click()
            self.action_count += 1

            return True

        except TimeoutException:
            print(f"   ❌ Element nicht gefunden: {description}")
            return False
        except Exception as e:
            print(f"   ❌ Klick fehlgeschlagen: {e}")
            return False

    def touch_select(self, select_id: str, description: str):
        """Wählt Option aus Dropdown (Touch-optimiert)"""
        try:
            print(f"📋 Wähle aus: {description}")

            select_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, select_id))
            )

            select = Select(select_element)

            # Benutzer überlegt kurz
            time.sleep(random.uniform(1, 2))

            # Wähle zufällige Option (nicht die erste = leer)
            if len(select.options) > 1:
                option_index = random.randint(1, len(select.options) - 1)
                select.select_by_index(option_index)

                selected_text = select.options[option_index].text
                print(f"   ✓ Ausgewählt: {selected_text}")

                self.action_count += 1
                return True

            return False

        except Exception as e:
            print(f"   ❌ Auswahl fehlgeschlagen: {e}")
            return False

    def scenario_prüfungsmodus(self):
        """Szenario: Benutzer macht eine Prüfung"""
        print("\n" + "=" * 60)
        print("🧪 SZENARIO: Prüfungsmodus")
        print("=" * 60)

        # 1. Startseite laden
        print("\n📍 Lade Startseite...")
        self.driver.get(BASE_URL)
        self.human_delay(2, 4)  # Benutzer liest Optionen

        # 2. Klick auf Prüfungsmodus
        if not self.touch_click(By.PARTIAL_LINK_TEXT, "Prüfungsmodus", "Prüfungsmodus Button"):
            return False

        self.human_delay(1, 2)  # Prüfungsseite lädt

        # 3. Prüfungsnummer anschauen
        print("👀 Benutzer liest Prüfungsnummer...")
        self.human_delay(2, 3)

        # 4. Prüfung starten
        if not self.touch_click(By.ID, "startBtn", "Prüfung Starten Button"):
            return False

        print("✅ Prüfung gestartet! Timer läuft...")

        # 5. Prüfung durchführen (simuliert)
        exam_duration = random.randint(10, 20)
        print(f"⏱️  Simuliere Prüfungsdurchführung ({exam_duration}s)...")

        for i in range(exam_duration):
            time.sleep(1)
            if i % 5 == 0:
                print(f"   ... {i}s vergangen (Benutzer sucht Fehler) ...")

        # 6. Prüfung beenden
        print("\n✋ Benutzer beendet Prüfung...")
        if not self.touch_click(By.ID, "finishBtn", "Prüfung Beenden Button"):
            # Vielleicht hat Timer bereits abgelaufen
            print("   ℹ️  Prüfung bereits beendet oder Button nicht gefunden")

        self.human_delay(2, 4)  # Benutzer liest Ergebnis

        print("\n✅ Prüfungsmodus-Szenario abgeschlossen!")
        return True

    def scenario_manueller_modus(self):
        """Szenario: Benutzer wählt manuell Fehler aus"""
        print("\n" + "=" * 60)
        print("🔧 SZENARIO: Manueller Modus")
        print("=" * 60)

        # 1. Zur Startseite
        print("\n📍 Zurück zur Startseite...")
        self.driver.get(BASE_URL)
        self.human_delay(1, 2)

        # 2. Klick auf Manuell
        if not self.touch_click(By.PARTIAL_LINK_TEXT, "Manuell", "Manueller Modus Button"):
            return False

        self.human_delay(2, 3)  # Benutzer sieht sich Optionen an

        # 3. Wähle Fehler aus verschiedenen Stromkreisen
        print("\n🎯 Benutzer wählt Fehler aus...")

        num_errors = random.randint(2, 4)
        print(f"   Ziel: {num_errors} Fehler auswählen")

        selected = 0
        for i in range(1, 8):  # Bis zu 7 Stromkreise
            if selected >= num_errors:
                break

            # Nicht jeden Stromkreis nutzen (realistisch)
            if random.random() < 0.6:  # 60% Chance
                if self.touch_select(f"stromkreis{i}", f"Stromkreis {i}"):
                    selected += 1
                    self.human_delay(1, 2)  # Nachdenken zwischen Auswahlen

        if selected == 0:
            print("   ⚠️  Keine Fehler ausgewählt!")
            return False

        print(f"   ✓ {selected} Fehler ausgewählt")

        # 4. Fehler zuschalten
        print("\n⚡ Schalte Fehler zu...")
        self.human_delay(1, 2)  # Benutzer prüft Auswahl nochmal

        if not self.touch_click(
            By.XPATH,
            "//button[contains(text(), 'Fehler zuschalten')]",
            "Fehler Zuschalten Button"
        ):
            return False

        self.human_delay(2, 4)  # Benutzer wartet auf Bestätigung

        # 5. Optional: Fehler zurücksetzen
        if random.random() < 0.7:  # 70% Chance
            print("\n🔄 Setze Fehler zurück...")
            self.human_delay(1, 2)

            if self.touch_click(
                By.XPATH,
                "//button[contains(text(), 'Zurücksetzen')]",
                "Zurücksetzen Button"
            ):
                # Bestätige Alert
                try:
                    time.sleep(0.5)
                    alert = self.driver.switch_to.alert
                    print("   ✓ Bestätige Zurücksetzen-Dialog...")
                    alert.accept()
                except:
                    pass

                self.human_delay(1, 2)

        print("\n✅ Manueller Modus-Szenario abgeschlossen!")
        return True

    def scenario_admin_bereich(self):
        """Szenario: Admin schaut sich Status an"""
        print("\n" + "=" * 60)
        print("👨‍💼 SZENARIO: Admin-Bereich")
        print("=" * 60)

        # 1. Zur Startseite
        print("\n📍 Zur Startseite...")
        self.driver.get(BASE_URL)
        self.human_delay(1, 2)

        # 2. Klick auf Admin
        if not self.touch_click(By.PARTIAL_LINK_TEXT, "Admin", "Admin Button"):
            return False

        self.human_delay(1, 2)

        # 3. Admin-Code eingeben
        print("🔐 Gebe Admin-Code ein...")

        try:
            code_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "adminCode"))
            )

            # Simuliere langsames Tippen (Touch-Tastatur)
            for digit in ADMIN_CODE:
                time.sleep(random.uniform(0.3, 0.7))
                code_input.send_keys(digit)

            self.human_delay(0.5, 1)

            # Login
            if not self.touch_click(
                By.XPATH,
                "//button[contains(text(), 'Login')]",
                "Login Button"
            ):
                return False

            self.human_delay(2, 3)

            # 4. Relais-Status anschauen
            print("\n📊 Schaue Relais-Status an...")
            self.driver.get(f"{BASE_URL}/relay_status")
            self.human_delay(3, 5)  # Admin studiert Status

            # 5. Zurück zur Startseite
            print("\n🏠 Zurück zur Startseite...")
            self.driver.get(BASE_URL)
            self.human_delay(1, 2)

            print("\n✅ Admin-Szenario abgeschlossen!")
            return True

        except Exception as e:
            print(f"   ❌ Admin-Login fehlgeschlagen: {e}")
            return False

    def continuous_simulation(self, duration_minutes: int = 5):
        """Endlos-Simulation wie echter Kiosk-Betrieb"""
        print("\n" + "=" * 60)
        print(f"🔄 CONTINUOUS KIOSK SIMULATION ({duration_minutes} Minuten)")
        print("=" * 60)

        end_time = time.time() + (duration_minutes * 60)
        cycle = 0

        scenarios = [
            ("Prüfungsmodus", self.scenario_prüfungsmodus),
            ("Manueller Modus", self.scenario_manueller_modus),
            ("Admin-Bereich", self.scenario_admin_bereich),
        ]

        while time.time() < end_time:
            cycle += 1
            print(f"\n{'=' * 60}")
            print(f"🔄 Zyklus {cycle}")
            print(f"{'=' * 60}")

            # Wähle zufälliges Szenario
            scenario_name, scenario_func = random.choice(scenarios)
            print(f"🎲 Zufälliges Szenario: {scenario_name}")

            try:
                scenario_func()
            except Exception as e:
                print(f"❌ Fehler im Szenario: {e}")

            # Pause zwischen Szenarien
            pause = random.randint(5, 15)
            print(f"\n💤 Pause zwischen Benutzern ({pause}s)...")
            time.sleep(pause)

        print("\n" + "=" * 60)
        print("✅ Continuous Simulation abgeschlossen!")
        print(f"📊 Gesamt-Aktionen: {self.action_count}")
        print("=" * 60)

    def cleanup(self):
        """Beende Browser"""
        if self.driver:
            print("\n🔒 Schließe Browser...")
            self.driver.quit()

# ==================== MAIN ====================

def main():
    print("=" * 60)
    print("VDE MESSWAND - KIOSK SIMULATOR")
    print("=" * 60)
    print(f"Display: {DISPLAY}")
    print(f"Server: {BASE_URL}")
    print(f"Vollbild: {FULLSCREEN}")
    print("=" * 60)

    # Initialisiere Kiosk-Benutzer
    user = KioskUser()

    if not user.setup_kiosk_browser():
        print("\n❌ Browser-Setup fehlgeschlagen!")
        return

    print("\n📋 Wähle Simulation:")
    print("1. Prüfungsmodus (einmalig)")
    print("2. Manueller Modus (einmalig)")
    print("3. Admin-Bereich (einmalig)")
    print("4. Alle Szenarien nacheinander")
    print("5. Continuous (5 Minuten Endlos-Betrieb)")
    print("6. Continuous Extended (30 Minuten Stresstest)")

    choice = input("\nEingabe (1-6): ").strip()

    try:
        if choice == "1":
            user.scenario_prüfungsmodus()
            input("\n⏸️  Drücke ENTER um zu beenden...")

        elif choice == "2":
            user.scenario_manueller_modus()
            input("\n⏸️  Drücke ENTER um zu beenden...")

        elif choice == "3":
            user.scenario_admin_bereich()
            input("\n⏸️  Drücke ENTER um zu beenden...")

        elif choice == "4":
            user.scenario_prüfungsmodus()
            time.sleep(3)
            user.scenario_manueller_modus()
            time.sleep(3)
            user.scenario_admin_bereich()
            input("\n⏸️  Drücke ENTER um zu beenden...")

        elif choice == "5":
            user.continuous_simulation(duration_minutes=5)

        elif choice == "6":
            user.continuous_simulation(duration_minutes=30)

        else:
            print("❌ Ungültige Eingabe")

    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation abgebrochen (Ctrl+C)")

    finally:
        user.cleanup()

    print("\n✅ Kiosk-Simulation beendet!")
    print(f"📊 Gesamt-Aktionen: {user.action_count}")

if __name__ == "__main__":
    main()
