#!/usr/bin/env python3
"""
VDE Messwand - Visual Stresstest mit Screenshots
Macht Screenshots von jedem Test-Schritt für visuelle Analyse
"""

import time
import random
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# ==================== KONFIGURATION ====================

BASE_URL = "http://10.100.72.191:8000"
ADMIN_CODE = "1234"
SCREENSHOT_DIR = "stress_test_screenshots"
HEADLESS = False  # True = unsichtbar, False = Browser sichtbar
FULLSCREEN = True  # True = Vollbild wie im Kiosk-Mode

# ==================== SCREENSHOT MANAGER ====================

class ScreenshotManager:
    """Verwaltet Screenshots für visuelle Analyse"""

    def __init__(self):
        self.screenshot_dir = Path(SCREENSHOT_DIR)
        self.screenshot_dir.mkdir(exist_ok=True)
        self.screenshot_count = 0

        # Erstelle Session-Ordner
        self.session_dir = self.screenshot_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir.mkdir(exist_ok=True)

        print(f"📸 Screenshots werden gespeichert in: {self.session_dir}")

    def take_screenshot(self, driver, name: str, session_id: int = 0):
        """Mache Screenshot"""
        self.screenshot_count += 1
        filename = f"{self.screenshot_count:03d}_session{session_id}_{name}.png"
        filepath = self.session_dir / filename

        try:
            driver.save_screenshot(str(filepath))
            print(f"  📸 Screenshot: {filename}")
            return str(filepath)
        except Exception as e:
            print(f"  ❌ Screenshot fehlgeschlagen: {e}")
            return None

# ==================== VISUAL TESTER ====================

class VisualGUITester:
    """GUI-Tester mit Screenshot-Funktion"""

    def __init__(self, session_id: int, screenshot_manager: ScreenshotManager):
        self.session_id = session_id
        self.screenshots = screenshot_manager
        self.driver = None
        self.step = 0

    def setup_driver(self):
        """Initialisiere Browser"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # Kiosk-Mode Simulation
            if FULLSCREEN:
                options.add_argument('--start-maximized')
                options.add_argument('--kiosk')  # Echter Kiosk-Mode!
                print(f"🖥️  Session {self.session_id}: KIOSK-MODE (Vollbild)")

            if HEADLESS:
                options.add_argument('--headless')
                print(f"🔇 Session {self.session_id}: Headless-Mode")
            else:
                print(f"👁️  Session {self.session_id}: Sichtbarer Browser")

            # Manuell ChromeDriver-Pfad setzen (für Raspberry Pi ARM)
            from selenium.webdriver.chrome.service import Service
            service = Service('/usr/bin/chromedriver')

            self.driver = webdriver.Chrome(service=service, options=options)

            if not FULLSCREEN:
                # Platziere Fenster nebeneinander (für 3 Sessions)
                window_width = 1920 // 3  # Bei Full-HD
                window_x = (self.session_id - 1) * window_width
                self.driver.set_window_position(window_x, 0)
                self.driver.set_window_size(window_width, 1080)

            return True
        except Exception as e:
            print(f"❌ Session {self.session_id}: Setup fehlgeschlagen: {e}")
            return False

    def screenshot(self, name: str):
        """Mache Screenshot vom aktuellen Zustand"""
        self.step += 1
        return self.screenshots.take_screenshot(
            self.driver,
            f"step{self.step:02d}_{name}",
            self.session_id
        )

    def navigate_and_capture(self, url: str, name: str):
        """Navigiere und mache Screenshot"""
        print(f"📍 Session {self.session_id}: {name}")
        self.driver.get(url)
        time.sleep(1)
        self.screenshot(name)

    def click_and_capture(self, by: By, selector: str, name: str, timeout: int = 5):
        """Klicke und mache Screenshot"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )

            # Screenshot VOR Klick
            self.screenshot(f"before_{name}")

            element.click()
            time.sleep(0.5)

            # Screenshot NACH Klick
            self.screenshot(f"after_{name}")

            return True
        except Exception as e:
            print(f"  ❌ Klick fehlgeschlagen: {e}")
            self.screenshot(f"error_{name}")
            return False

    def test_prüfungsmodus_visual(self):
        """Teste Prüfungsmodus mit Screenshots"""
        print(f"\n🧪 Session {self.session_id}: Prüfungsmodus (VISUELL)\n")

        # 1. Startseite
        self.navigate_and_capture(f"{BASE_URL}/", "01_startseite")

        # 2. Klick auf Prüfungsmodus
        self.click_and_capture(By.PARTIAL_LINK_TEXT, "Prüfungsmodus", "02_menu_click")

        # 3. Prüfungsseite
        time.sleep(1)
        self.screenshot("03_exam_page")

        # 4. Prüfung starten
        self.click_and_capture(By.ID, "startBtn", "04_start_exam")

        # 5. Während der Prüfung (Timer läuft)
        time.sleep(3)
        self.screenshot("05_exam_running")

        # 6. Noch ein Screenshot nach 5 Sekunden
        time.sleep(5)
        self.screenshot("06_exam_timer")

        # 7. Prüfung beenden
        self.click_and_capture(By.ID, "finishBtn", "07_finish_exam")

        # 8. Ergebnis-Seite
        time.sleep(2)
        self.screenshot("08_exam_result")

        print(f"✅ Session {self.session_id}: Prüfungsmodus abgeschlossen\n")

    def test_manueller_modus_visual(self):
        """Teste Manuellen Modus mit Screenshots"""
        print(f"\n🧪 Session {self.session_id}: Manueller Modus (VISUELL)\n")

        # 1. Startseite
        self.navigate_and_capture(f"{BASE_URL}/", "01_startseite")

        # 2. Klick auf Manuell
        self.click_and_capture(By.PARTIAL_LINK_TEXT, "Manuell", "02_manual_click")

        # 3. Manuelle Seite
        time.sleep(1)
        self.screenshot("03_manual_page")

        # 4. Wähle Fehler aus
        num_errors = random.randint(2, 4)
        for i in range(1, num_errors + 1):
            try:
                select_element = self.driver.find_element(By.ID, f"stromkreis{i}")
                select = Select(select_element)

                if len(select.options) > 1:
                    random_option = random.randint(1, len(select.options) - 1)
                    select.select_by_index(random_option)
                    time.sleep(0.5)
                    self.screenshot(f"04_select_error_{i}")
            except:
                pass

        # 5. Fehler zuschalten
        self.click_and_capture(
            By.XPATH,
            "//button[contains(text(), 'Fehler zuschalten')]",
            "05_activate_errors"
        )

        # 6. Status nach Aktivierung
        time.sleep(2)
        self.screenshot("06_errors_active")

        # 7. Zurücksetzen (mit Alert)
        self.screenshot("07_before_reset")

        try:
            reset_btn = self.driver.find_element(
                By.XPATH,
                "//button[contains(text(), 'Zurücksetzen')]"
            )
            reset_btn.click()
            time.sleep(0.5)

            # Alert-Screenshot (falls möglich)
            try:
                alert = self.driver.switch_to.alert
                self.screenshot("08_reset_alert")
                alert.accept()
            except:
                pass

            time.sleep(1)
            self.screenshot("09_after_reset")
        except Exception as e:
            print(f"  ⚠️  Reset nicht möglich: {e}")

        print(f"✅ Session {self.session_id}: Manueller Modus abgeschlossen\n")

    def cleanup(self):
        """Schließe Browser"""
        if self.driver:
            self.screenshot("99_final_state")
            self.driver.quit()

# ==================== MAIN ====================

def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("VDE MESSWAND - VISUAL STRESSTEST")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Headless: {'Ja (unsichtbar)' if HEADLESS else 'Nein (sichtbar)'}")
    print("=" * 60)

    screenshot_mgr = ScreenshotManager()

    print("\nWähle Test:")
    print("1. Prüfungsmodus (1 Session mit Screenshots)")
    print("2. Manueller Modus (1 Session mit Screenshots)")
    print("3. Beide Modi (1 Session, nacheinander)")
    print("4. 3 parallele Sessions (Demo für Multi-User)")

    choice = input("\nEingabe (1-4): ").strip()

    if choice == "1":
        tester = VisualGUITester(1, screenshot_mgr)
        if tester.setup_driver():
            tester.test_prüfungsmodus_visual()
            input("\n⏸️  Drücke ENTER um Browser zu schließen...")
            tester.cleanup()

    elif choice == "2":
        tester = VisualGUITester(1, screenshot_mgr)
        if tester.setup_driver():
            tester.test_manueller_modus_visual()
            input("\n⏸️  Drücke ENTER um Browser zu schließen...")
            tester.cleanup()

    elif choice == "3":
        tester = VisualGUITester(1, screenshot_mgr)
        if tester.setup_driver():
            tester.test_prüfungsmodus_visual()
            time.sleep(2)
            tester.test_manueller_modus_visual()
            input("\n⏸️  Drücke ENTER um Browser zu schließen...")
            tester.cleanup()

    elif choice == "4":
        print("\n🚀 Starte 3 parallele Browser-Sessions...")
        print("   (Fenster werden nebeneinander platziert)\n")

        testers = []
        for i in range(3):
            tester = VisualGUITester(i + 1, screenshot_mgr)
            if tester.setup_driver():
                testers.append(tester)

        # Alle testen gleichzeitig Prüfungsmodus
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(t.test_prüfungsmodus_visual)
                for t in testers
            ]
            concurrent.futures.wait(futures)

        input("\n⏸️  Drücke ENTER um alle Browser zu schließen...")
        for tester in testers:
            tester.cleanup()

    else:
        print("❌ Ungültige Eingabe")
        return

    print("\n" + "=" * 60)
    print(f"✅ FERTIG! Screenshots in: {screenshot_mgr.session_dir}")
    print("=" * 60)

    # Zeige Screenshot-Übersicht
    screenshots = list(screenshot_mgr.session_dir.glob("*.png"))
    print(f"\n📸 {len(screenshots)} Screenshots erstellt:")
    for screenshot in sorted(screenshots)[:10]:
        print(f"   - {screenshot.name}")
    if len(screenshots) > 10:
        print(f"   ... und {len(screenshots) - 10} weitere")

if __name__ == "__main__":
    main()
