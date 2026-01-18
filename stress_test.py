#!/usr/bin/env python3
"""
VDE Messwand - GUI Stresstest mit Selenium
Simuliert Benutzerinteraktionen im Kiosk-Mode
"""

import time
import random
import json
import requests
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ==================== KONFIGURATION ====================

BASE_URL = "http://localhost:8000"
ADMIN_CODE = "1234"  # Passe an deine Einstellungen an
STRESS_TEST_DURATION = 300  # 5 Minuten
PARALLEL_USERS = 3  # Anzahl paralleler Browser-Sessions
ERROR_LOG_FILE = "stress_test_errors.json"

# ==================== FEHLER-LOGGING ====================

class ErrorLogger:
    """Sammelt und speichert alle Fehler während des Tests"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.start_time = datetime.now()

    def log_error(self, category: str, message: str, details: Dict[str, Any] = None):
        """Logge einen Fehler"""
        error = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "message": message,
            "details": details or {}
        }
        self.errors.append(error)
        print(f"❌ ERROR [{category}]: {message}")
        if details:
            print(f"   Details: {details}")

    def log_warning(self, category: str, message: str):
        """Logge eine Warnung"""
        warning = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "message": message
        }
        self.warnings.append(warning)
        print(f"⚠️  WARNING [{category}]: {message}")

    def save_report(self):
        """Speichere Fehlerreport als JSON"""
        report = {
            "test_duration": str(datetime.now() - self.start_time),
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings
        }

        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📊 Report gespeichert: {ERROR_LOG_FILE}")
        return report

# ==================== SELENIUM GUI TESTER ====================

class VDEGUITester:
    """Testet die GUI mit Selenium"""

    def __init__(self, session_id: int, error_logger: ErrorLogger):
        self.session_id = session_id
        self.logger = error_logger
        self.driver = None
        self.actions_performed = 0

    def setup_driver(self):
        """Initialisiere Chromium Driver für Pi"""
        try:
            options = webdriver.ChromeOptions()
            # Kiosk-Mode simulieren (optional auch ohne für normale Tests)
            # options.add_argument('--kiosk')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            # Für Headless-Betrieb (kein sichtbares Fenster):
            # options.add_argument('--headless')

            # Manuell ChromeDriver-Pfad setzen (für Raspberry Pi ARM)
            from selenium.webdriver.chrome.service import Service
            service = Service('/usr/bin/chromedriver')

            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_window_size(1024, 768)
            print(f"✅ Session {self.session_id}: Browser gestartet")
            return True

        except Exception as e:
            self.logger.log_error("SELENIUM_SETUP", f"Session {self.session_id}: Driver-Setup fehlgeschlagen", {
                "error": str(e)
            })
            return False

    def navigate_to(self, url: str, timeout: int = 10):
        """Navigiere zu URL"""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            return True
        except Exception as e:
            self.logger.log_error("NAVIGATION", f"Session {self.session_id}: Navigation zu {url} fehlgeschlagen", {
                "error": str(e)
            })
            return False

    def click_element(self, by: By, selector: str, timeout: int = 5):
        """Klicke auf Element"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )
            element.click()
            time.sleep(0.5)  # Kurze Pause nach Klick
            return True
        except Exception as e:
            self.logger.log_error("CLICK", f"Session {self.session_id}: Klick fehlgeschlagen", {
                "selector": selector,
                "error": str(e)
            })
            return False

    def fill_input(self, by: By, selector: str, value: str, timeout: int = 5):
        """Fülle Eingabefeld aus"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            element.clear()
            element.send_keys(value)
            return True
        except Exception as e:
            self.logger.log_error("INPUT", f"Session {self.session_id}: Eingabe fehlgeschlagen", {
                "selector": selector,
                "value": value,
                "error": str(e)
            })
            return False

    def test_prüfungsmodus(self):
        """Teste Prüfungsmodus-Flow"""
        print(f"🧪 Session {self.session_id}: Teste Prüfungsmodus...")

        # Navigiere zur Startseite
        if not self.navigate_to(f"{BASE_URL}/"):
            return False

        # Klicke auf Prüfungsmodus
        if not self.click_element(By.PARTIAL_LINK_TEXT, "Prüfungsmodus"):
            return False

        # Warte auf Exam-Seite
        time.sleep(1)

        # Prüfung starten
        if not self.click_element(By.ID, "startBtn"):
            return False

        # Warte kurz (simuliere Prüfungszeit)
        wait_time = random.randint(5, 15)
        print(f"   ⏱️  Warte {wait_time}s (simulierte Prüfungszeit)...")
        time.sleep(wait_time)

        # Prüfung beenden
        if not self.click_element(By.ID, "finishBtn"):
            return False

        print(f"✅ Session {self.session_id}: Prüfungsmodus erfolgreich")
        self.actions_performed += 1
        return True

    def test_manueller_modus(self):
        """Teste manuellen Modus"""
        print(f"🧪 Session {self.session_id}: Teste manuellen Modus...")

        if not self.navigate_to(f"{BASE_URL}/"):
            return False

        if not self.click_element(By.PARTIAL_LINK_TEXT, "Manuell"):
            return False

        time.sleep(1)

        # Wähle zufällige Fehler aus
        num_errors = random.randint(1, 5)
        print(f"   🎲 Wähle {num_errors} zufällige Fehler...")

        for i in range(1, num_errors + 1):
            try:
                select_element = self.driver.find_element(By.ID, f"stromkreis{i}")
                select = Select(select_element)

                # Überspringe erste Option (leer)
                if len(select.options) > 1:
                    random_option = random.randint(1, len(select.options) - 1)
                    select.select_by_index(random_option)
                    time.sleep(0.3)
            except Exception as e:
                self.logger.log_warning("SELECT", f"Stromkreis {i} konnte nicht ausgewählt werden")

        # Fehler zuschalten
        if not self.click_element(By.XPATH, "//button[contains(text(), 'Fehler zuschalten')]"):
            return False

        time.sleep(2)

        # Zurücksetzen
        if not self.click_element(By.XPATH, "//button[contains(text(), 'Zurücksetzen')]"):
            # Alert bestätigen
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
            except:
                pass
            return False

        print(f"✅ Session {self.session_id}: Manueller Modus erfolgreich")
        self.actions_performed += 1
        return True

    def test_admin_panel(self):
        """Teste Admin-Bereich (ohne destruktive Aktionen)"""
        print(f"🧪 Session {self.session_id}: Teste Admin-Panel...")

        if not self.navigate_to(f"{BASE_URL}/admin"):
            return False

        # Login
        if not self.fill_input(By.ID, "adminCode", ADMIN_CODE):
            return False

        if not self.click_element(By.XPATH, "//button[contains(text(), 'Login')]"):
            return False

        time.sleep(1)

        # Navigiere durch verschiedene Admin-Seiten
        admin_links = [
            ("Relais Status", "/relay_status"),
            ("Gruppen", "/admin_groups"),
            ("Relais-Namen", "/admin_relay_names"),
            ("Netzwerk", "/admin_network")
        ]

        for name, link in admin_links:
            try:
                self.navigate_to(f"{BASE_URL}{link}")
                time.sleep(1)
                print(f"   ✓ {name} geladen")
            except Exception as e:
                self.logger.log_warning("ADMIN_NAV", f"Konnte {name} nicht laden")

        print(f"✅ Session {self.session_id}: Admin-Panel erfolgreich")
        self.actions_performed += 1
        return True

    def run_random_tests(self, duration_seconds: int):
        """Führe zufällige Tests für bestimmte Zeit aus"""
        end_time = time.time() + duration_seconds
        test_functions = [
            self.test_prüfungsmodus,
            self.test_manueller_modus,
            self.test_admin_panel
        ]

        while time.time() < end_time:
            test_func = random.choice(test_functions)
            try:
                test_func()
            except Exception as e:
                self.logger.log_error("TEST_EXECUTION", f"Session {self.session_id}: Unerwarteter Fehler", {
                    "test": test_func.__name__,
                    "error": str(e)
                })

            # Pause zwischen Tests
            time.sleep(random.randint(1, 3))

        return self.actions_performed

    def cleanup(self):
        """Schließe Browser"""
        if self.driver:
            self.driver.quit()
            print(f"🔒 Session {self.session_id}: Browser geschlossen")

# ==================== API STRESS TEST ====================

class APIStressTester:
    """Stresstest für Backend-APIs"""

    def __init__(self, error_logger: ErrorLogger):
        self.logger = error_logger
        self.session = requests.Session()
        self.request_count = 0
        self.error_count = 0

    def api_request(self, method: str, endpoint: str, **kwargs):
        """Führe API-Request aus"""
        url = f"{BASE_URL}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=5, **kwargs)
            self.request_count += 1

            if response.status_code >= 400:
                self.logger.log_error("API_ERROR", f"HTTP {response.status_code} bei {endpoint}", {
                    "method": method,
                    "status": response.status_code,
                    "response": response.text[:200]
                })
                self.error_count += 1
                return None

            return response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text

        except Exception as e:
            self.logger.log_error("API_REQUEST", f"Request zu {endpoint} fehlgeschlagen", {
                "method": method,
                "error": str(e)
            })
            self.error_count += 1
            return None

    def test_relay_status(self):
        """Teste Relay-Status API"""
        return self.api_request("GET", "/api/relay_status")

    def test_groups_api(self):
        """Teste Groups API"""
        return self.api_request("GET", "/api/groups")

    def test_stromkreise_api(self):
        """Teste Stromkreise API"""
        return self.api_request("GET", "/api/stromkreise")

    def stress_test_apis(self, duration_seconds: int):
        """Bombardiere APIs mit Requests"""
        print(f"🔥 Starte API-Stresstest ({duration_seconds}s)...")

        end_time = time.time() + duration_seconds
        api_tests = [
            self.test_relay_status,
            self.test_groups_api,
            self.test_stromkreise_api
        ]

        while time.time() < end_time:
            for test_func in api_tests:
                test_func()
                time.sleep(0.1)  # Sehr kurze Pause für hohe Last

        print(f"📊 API-Test: {self.request_count} Requests, {self.error_count} Fehler")
        return self.request_count

# ==================== HAUPT-TESTRUNNER ====================

def run_stress_test():
    """Hauptfunktion für Stresstest"""
    print("=" * 60)
    print("VDE MESSWAND - GUI STRESSTEST")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Dauer: {STRESS_TEST_DURATION}s")
    print(f"Parallele Sessions: {PARALLEL_USERS}")
    print("=" * 60)

    error_logger = ErrorLogger()

    # Teste zuerst ob Server erreichbar ist
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Server erreichbar (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ Server nicht erreichbar: {e}")
        print("   Bitte starte den Server mit: gunicorn -b 0.0.0.0:8000 app:app")
        return

    print("\n🚀 Starte Stresstest...\n")

    # Parallele GUI-Tests
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_USERS + 1) as executor:
        # GUI-Tester
        gui_futures = []
        for i in range(PARALLEL_USERS):
            tester = VDEGUITester(i + 1, error_logger)
            if tester.setup_driver():
                future = executor.submit(tester.run_random_tests, STRESS_TEST_DURATION)
                gui_futures.append((tester, future))

        # API-Tester parallel
        api_tester = APIStressTester(error_logger)
        api_future = executor.submit(api_tester.stress_test_apis, STRESS_TEST_DURATION)

        # Warte auf Completion
        print(f"\n⏱️  Warte {STRESS_TEST_DURATION}s auf Test-Completion...\n")

        # Sammle Ergebnisse
        total_actions = 0
        for tester, future in gui_futures:
            try:
                actions = future.result()
                total_actions += actions
                print(f"Session {tester.session_id}: {actions} Aktionen durchgeführt")
            except Exception as e:
                error_logger.log_error("TEST_RESULT", f"Session fehlgeschlagen: {e}")
            finally:
                tester.cleanup()

        # API-Ergebnisse
        api_requests = api_future.result()

    # Report generieren
    print("\n" + "=" * 60)
    print("TEST ABGESCHLOSSEN")
    print("=" * 60)
    print(f"GUI-Aktionen: {total_actions}")
    print(f"API-Requests: {api_requests}")
    print(f"Fehler: {len(error_logger.errors)}")
    print(f"Warnungen: {len(error_logger.warnings)}")

    report = error_logger.save_report()

    if len(error_logger.errors) == 0:
        print("\n✅ ALLE TESTS ERFOLGREICH - Keine Fehler!")
    else:
        print(f"\n⚠️  {len(error_logger.errors)} FEHLER GEFUNDEN - Details in {ERROR_LOG_FILE}")

    print("=" * 60)

# ==================== MAIN ====================

if __name__ == "__main__":
    run_stress_test()
