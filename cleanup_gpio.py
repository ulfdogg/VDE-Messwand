#!/usr/bin/env python3
"""
GPIO Cleanup Script
Gibt alle GPIO-Pins frei, die vom gpio_monitor belegt sind
"""
import sys

try:
    import gpiod

    # Öffne Chip
    chip = gpiod.Chip('/dev/gpiochip4')

    # Prüfe alle Pins
    freed_pins = []
    for pin_num in range(28):  # GPIO 0-27
        try:
            line_info = chip.get_line_info(pin_num)
            if line_info.used and line_info.consumer == "gpio_monitor":
                freed_pins.append(pin_num)
                print(f"Pin {pin_num} von gpio_monitor belegt")
        except Exception:
            pass

    chip.close()

    if freed_pins:
        print(f"\n⚠️ Folgende Pins waren belegt: {freed_pins}")
        print("Diese werden beim nächsten Request automatisch neu angefordert.")
        print("\nBitte beenden Sie alle laufenden app.py Prozesse mit Strg+C")
        print("und starten Sie die Anwendung neu.")
    else:
        print("✅ Keine GPIO-Pins von gpio_monitor belegt")

except ImportError:
    print("❌ gpiod nicht verfügbar")
    sys.exit(1)
except Exception as e:
    print(f"❌ Fehler: {e}")
    sys.exit(1)
