#!/usr/bin/env python3
"""
VDE Messwand - Vereinfachter Stresstest (ohne Selenium)
Nur API/Backend-Tests für schnelles Testen
"""

import time
import random
import requests
import json
from datetime import datetime
from typing import Dict, Any
import concurrent.futures

BASE_URL = "http://localhost:8000"

class SimpleStressTester:
    """Einfacher Stresstest nur mit API-Calls"""

    def __init__(self):
        self.errors = []
        self.success_count = 0
        self.total_requests = 0

    def test_endpoint(self, method: str, endpoint: str, json_data: Dict = None, expect_ok: bool = True):
        """Teste einen einzelnen Endpoint"""
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=3)
            elif method == "POST":
                response = requests.post(url, json=json_data or {}, timeout=3)
            else:
                raise ValueError(f"Unbekannte Methode: {method}")

            self.total_requests += 1

            if expect_ok and response.status_code >= 400:
                self.errors.append({
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "error": "HTTP Error"
                })
                print(f"❌ {method} {endpoint} -> HTTP {response.status_code}")
                return False
            else:
                self.success_count += 1
                print(f"✅ {method} {endpoint} -> OK")
                return True

        except Exception as e:
            self.errors.append({
                "endpoint": endpoint,
                "error": str(e)
            })
            print(f"❌ {method} {endpoint} -> {e}")
            return False

    def run_rapid_fire_test(self, duration_seconds: int = 60):
        """Bombardiere Server mit Requests"""
        print(f"\n🔥 Starte Rapid-Fire Test ({duration_seconds}s)...\n")

        endpoints = [
            ("GET", "/api/relay_status"),
            ("GET", "/api/groups"),
            ("GET", "/api/stromkreise"),
            ("GET", "/api/kategorien"),
            ("GET", "/api/relais/config"),
            ("GET", "/api/training/config"),
            ("POST", "/reset_relays"),
        ]

        end_time = time.time() + duration_seconds
        while time.time() < end_time:
            method, endpoint = random.choice(endpoints)
            self.test_endpoint(method, endpoint)
            time.sleep(0.05)  # 50ms Pause = 20 req/s

    def simulate_exam_mode(self, num_exams: int = 10):
        """Simuliere mehrere Prüfungen"""
        print(f"\n📝 Simuliere {num_exams} Prüfungen...\n")

        for i in range(num_exams):
            exam_number = f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{i}"

            # Starte Prüfung
            success = self.test_endpoint("POST", "/start_exam", {
                "exam_number": exam_number
            })

            if success:
                # Warte kurz
                time.sleep(random.uniform(0.5, 2.0))

                # Beende Prüfung
                self.test_endpoint("POST", "/finish_exam", {
                    "exam_number": exam_number,
                    "duration": random.randint(60, 300)
                })

    def simulate_manual_mode(self, num_tests: int = 20):
        """Simuliere manuelle Fehlerauswahl"""
        print(f"\n🔧 Simuliere {num_tests} manuelle Fehlerkonfigurationen...\n")

        for i in range(num_tests):
            # Zufällige Relais-Auswahl
            num_errors = random.randint(1, 5)
            errors = {}

            for j in range(num_errors):
                stromkreis_key = f"stromkreis{j+1}"
                errors[stromkreis_key] = random.randint(0, 63)

            # Setze Fehler
            success = self.test_endpoint("POST", "/set_manual_errors", {"errors": errors})

            if success:
                time.sleep(0.5)
                # Reset
                self.test_endpoint("POST", "/reset_relays")

    def concurrent_test(self, num_workers: int = 5, duration: int = 30):
        """Teste mit mehreren parallelen Threads"""
        print(f"\n🚀 Starte {num_workers} parallele Test-Threads ({duration}s)...\n")

        def worker_task(worker_id: int):
            """Aufgabe für Worker"""
            endpoints = [
                ("GET", "/api/relay_status"),
                ("GET", "/api/groups"),
                ("POST", "/reset_relays"),
            ]

            end_time = time.time() + duration
            count = 0

            while time.time() < end_time:
                method, endpoint = random.choice(endpoints)
                self.test_endpoint(method, endpoint)
                count += 1
                time.sleep(random.uniform(0.1, 0.5))

            print(f"   Worker {worker_id}: {count} Requests")
            return count

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(num_workers)]
            results = [f.result() for f in futures]

        print(f"\n   Gesamt: {sum(results)} Requests von {num_workers} Workern")

    def print_summary(self):
        """Zeige Zusammenfassung"""
        print("\n" + "=" * 60)
        print("TEST ZUSAMMENFASSUNG")
        print("=" * 60)
        print(f"Gesamt-Requests: {self.total_requests}")
        print(f"Erfolgreich: {self.success_count}")
        print(f"Fehler: {len(self.errors)}")
        print(f"Erfolgsrate: {(self.success_count / max(self.total_requests, 1)) * 100:.1f}%")

        if self.errors:
            print(f"\n⚠️  FEHLER:")
            for error in self.errors[:10]:  # Zeige erste 10 Fehler
                print(f"  - {error}")

            if len(self.errors) > 10:
                print(f"  ... und {len(self.errors) - 10} weitere")

            # Speichere Fehler
            with open("stress_test_simple_errors.json", "w") as f:
                json.dump(self.errors, f, indent=2)
            print(f"\n💾 Fehler gespeichert: stress_test_simple_errors.json")
        else:
            print("\n✅ KEINE FEHLER!")

        print("=" * 60)

def main():
    """Hauptfunktion"""
    print("=" * 60)
    print("VDE MESSWAND - SIMPLE STRESSTEST")
    print("=" * 60)

    # Teste Server-Erreichbarkeit
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Server erreichbar (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ Server nicht erreichbar: {e}")
        print("   Starte Server mit: gunicorn -b 0.0.0.0:8000 app:app")
        return

    tester = SimpleStressTester()

    print("\nWähle Test-Modus:")
    print("1. Rapid-Fire Test (60s intensive Requests)")
    print("2. Prüfungsmodus-Simulation (10 Prüfungen)")
    print("3. Manueller Modus-Simulation (20 Tests)")
    print("4. Concurrent Test (5 parallele Threads, 30s)")
    print("5. ALLES (vollständiger Stresstest)")

    choice = input("\nEingabe (1-5): ").strip()

    if choice == "1":
        tester.run_rapid_fire_test(60)
    elif choice == "2":
        tester.simulate_exam_mode(10)
    elif choice == "3":
        tester.simulate_manual_mode(20)
    elif choice == "4":
        tester.concurrent_test(5, 30)
    elif choice == "5":
        print("\n🔥 VOLLSTÄNDIGER STRESSTEST 🔥\n")
        tester.run_rapid_fire_test(30)
        tester.simulate_exam_mode(5)
        tester.simulate_manual_mode(10)
        tester.concurrent_test(3, 30)
    else:
        print("❌ Ungültige Eingabe")
        return

    tester.print_summary()

if __name__ == "__main__":
    main()
