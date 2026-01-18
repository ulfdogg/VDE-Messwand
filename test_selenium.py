#!/usr/bin/env python3
"""
Schneller Selenium-Test um zu prüfen ob ChromeDriver funktioniert
"""

import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

print("=" * 60)
print("SELENIUM / CHROMEDRIVER TEST")
print("=" * 60)

# Setze DISPLAY
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'
    print(f"✓ DISPLAY gesetzt auf :0")

print(f"✓ DISPLAY: {os.environ.get('DISPLAY')}")

# Teste ChromeDriver
try:
    print("\n🔧 Initialisiere Chrome WebDriver...")

    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Kein Kiosk-Mode für Test
    # options.add_argument('--headless')  # Auskommentiert = sichtbar

    # Manuell ChromeDriver-Pfad setzen (für Raspberry Pi ARM)
    from selenium.webdriver.chrome.service import Service
    service = Service('/usr/bin/chromedriver')

    driver = webdriver.Chrome(service=service, options=options)

    print("✅ ChromeDriver erfolgreich gestartet!")

    # Teste mit lokalem Server
    url = "http://10.100.72.191:8000"
    print(f"\n🌐 Lade {url}...")

    driver.get(url)
    time.sleep(2)

    print(f"✅ Seite geladen!")
    print(f"   Titel: {driver.title}")

    # Screenshot machen
    screenshot_path = "/home/vde/vde-messwand/selenium_test.png"
    driver.save_screenshot(screenshot_path)
    print(f"📸 Screenshot gespeichert: {screenshot_path}")

    # Warte 3 Sekunden damit du es siehst
    print("\n⏱️  Warte 3 Sekunden...")
    time.sleep(3)

    # Schließe Browser
    driver.quit()
    print("\n✅ TEST ERFOLGREICH!")

except Exception as e:
    print(f"\n❌ FEHLER: {e}")
    print("\nTroubleshooting:")
    print("1. Ist ChromeDriver installiert?")
    print("   which chromedriver")
    print("2. Läuft der Server?")
    print("   curl http://10.100.72.191:8000")
    print("3. Ist DISPLAY gesetzt?")
    print("   echo $DISPLAY")
    import traceback
    traceback.print_exc()

print("=" * 60)
