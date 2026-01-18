"""
GPIO Monitor für Schließer-Überwachung
Überwacht einen Schließer-Kontakt an GPIO-Pins
Unterstützt Raspberry Pi 5 (gpiod) und ältere Modelle (RPi.GPIO)
"""
import time
import threading

# GPIO-Bibliothek importieren - versuche zuerst gpiod (Pi 5), dann RPi.GPIO
GPIO_BACKEND = None
GPIO_AVAILABLE = False

try:
    import gpiod
    GPIO_BACKEND = 'gpiod'
    GPIO_AVAILABLE = True
    print("✅ GPIO: Verwende gpiod (Raspberry Pi 5 kompatibel)")
except ImportError:
    try:
        import RPi.GPIO as GPIO
        GPIO_BACKEND = 'RPi.GPIO'
        GPIO_AVAILABLE = True
        print("✅ GPIO: Verwende RPi.GPIO (Raspberry Pi 1-4)")
    except (ImportError, RuntimeError):
        GPIO_AVAILABLE = False
        print("⚠️ Keine GPIO-Bibliothek verfügbar - Dummy-Modus aktiv")


class GPIOMonitor:
    """Überwacht GPIO-Pins für Schließer-Status"""

    def __init__(self, pin1=17, pin2=27, shutdown_timeout=120):
        """
        Initialisiert GPIO-Monitor

        Args:
            pin1: Erster GPIO-Pin (BCM-Nummerierung)
            pin2: Zweiter GPIO-Pin (BCM-Nummerierung)
            shutdown_timeout: Sekunden bis zum Shutdown bei aktivem Notaus (Standard: 120)
        """
        global GPIO_AVAILABLE

        self.pin1 = pin1
        self.pin2 = pin2
        self.is_active = False
        self.monitoring = False
        self.monitor_thread = None

        # GPIO-spezifische Attribute
        self.chip = None
        self.lines = None

        # Shutdown-Timer für Notaus
        self.shutdown_timeout = shutdown_timeout
        self.notaus_start_time = None  # Zeitpunkt wann Notaus aktiviert wurde
        self.shutdown_triggered = False

        if GPIO_AVAILABLE:
            try:
                if GPIO_BACKEND == 'gpiod':
                    self._init_gpiod()
                elif GPIO_BACKEND == 'RPi.GPIO':
                    self._init_rpi_gpio()

                print(f"✅ GPIO-Monitor initialisiert: Pin {self.pin1} und {self.pin2}")
                print(f"   Backend: {GPIO_BACKEND}")
                print(f"   Konfiguration: INPUT mit Pull-Up (LOW=geschlossen)")

                # Starte Überwachung
                self.start_monitoring()

            except Exception as e:
                print(f"❌ Fehler bei GPIO-Initialisierung: {e}")
                GPIO_AVAILABLE = False
        else:
            print("⚠️ GPIO-Monitor im Dummy-Modus")

    def _init_gpiod(self):
        """Initialisiert GPIO mit gpiod (Raspberry Pi 5)"""
        # Öffne GPIO-Chip (gpiochip4 ist ein Symlink zu gpiochip0 auf Pi 5)
        self.chip = gpiod.Chip('/dev/gpiochip4')

        # Versuche alte Verbindungen freizugeben falls vorhanden
        try:
            # Prüfe ob Pins bereits verwendet werden
            line_info1 = self.chip.get_line_info(self.pin1)
            line_info2 = self.chip.get_line_info(self.pin2)

            if line_info1.used or line_info2.used:
                print(f"⚠️ GPIO-Pins bereits belegt, werden freigegeben...")
                # Bei gpiod müssen wir warten bis der alte Request freigegeben wird
                # oder wir verwenden reconfigure=True
        except Exception as e:
            print(f"⚠️ Warnung beim Prüfen der Pin-Belegung: {e}")

        # Request Lines mit gpiod v2 API
        # Beide Pins als Tuple für gemeinsame LineSettings
        self.lines = self.chip.request_lines(
            consumer="gpio_monitor",
            config={(self.pin1, self.pin2): gpiod.LineSettings(
                direction=gpiod.line.Direction.INPUT,
                bias=gpiod.line.Bias.PULL_UP
            )}
        )

    def _init_rpi_gpio(self):
        """Initialisiert GPIO mit RPi.GPIO (Raspberry Pi 1-4)"""
        # GPIO-Modus setzen
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Pins als Input mit Pull-Up-Widerstand konfigurieren
        GPIO.setup(self.pin1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.pin2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read_status(self):
        """
        Liest aktuellen Schließer-Status

        Returns:
            bool: True wenn Schließer geschlossen (LOW Signal)
        """
        if not GPIO_AVAILABLE:
            return False  # Dummy-Modus: immer inaktiv

        try:
            if GPIO_BACKEND == 'gpiod':
                # gpiod: Lese Werte für beide Pins
                values = self.lines.get_values([self.pin1, self.pin2])
                # values ist eine Liste: [Value für pin1, Value für pin2]
                state1 = values[0]
                state2 = values[1]

                # Schließer ist geschlossen wenn Pin1 INACTIVE (LOW) ist
                # ACTIVE = 1 (HIGH), INACTIVE = 0 (LOW)
                # Pin2 wird ignoriert, nur Pin1 ist relevant
                closed = (state1 == gpiod.line.Value.INACTIVE)

            elif GPIO_BACKEND == 'RPi.GPIO':
                # RPi.GPIO: Lese nur Pin1
                state1 = GPIO.input(self.pin1)

                # Schließer ist geschlossen wenn Pin1 LOW ist
                # Pin2 wird ignoriert
                closed = (state1 == GPIO.LOW)
            else:
                closed = False

            return closed

        except Exception as e:
            print(f"❌ Fehler beim GPIO-Auslesen: {e}")
            return False

    def monitor_loop(self):
        """Kontinuierliche Überwachung in separatem Thread"""
        print("🔄 GPIO-Überwachung gestartet")

        last_state = None

        while self.monitoring:
            try:
                current_state = self.read_status()

                # Nur bei Zustandsänderung loggen
                if current_state != last_state:
                    self.is_active = current_state
                    if current_state:
                        print("🔴 WARNUNG: Schließer geschlossen (Notaus betätigt)")
                        # Starte Shutdown-Timer
                        self.notaus_start_time = time.time()
                        self.shutdown_triggered = False
                    else:
                        print("🟢 Schließer geöffnet (Normal)")
                        # Setze Timer zurück
                        self.notaus_start_time = None
                        self.shutdown_triggered = False
                    last_state = current_state

                # Prüfe Shutdown-Timer (wenn Notaus aktiv)
                if current_state and self.notaus_start_time and not self.shutdown_triggered:
                    elapsed = time.time() - self.notaus_start_time
                    remaining = self.shutdown_timeout - elapsed

                    # Warnungen bei 60 Sekunden und 30 Sekunden
                    if int(remaining) == 60 and int(elapsed) > 59:
                        print("⚠️ WARNUNG: System fährt in 60 Sekunden herunter!")
                    elif int(remaining) == 30 and int(elapsed) > 89:
                        print("⚠️ WARNUNG: System fährt in 30 Sekunden herunter!")
                    elif int(remaining) == 10 and int(elapsed) > 109:
                        print("⚠️ WARNUNG: System fährt in 10 Sekunden herunter!")

                    # Shutdown auslösen nach 2 Minuten
                    if elapsed >= self.shutdown_timeout:
                        self.shutdown_triggered = True
                        print("🔴 NOTAUS: 2 Minuten abgelaufen - System wird heruntergefahren!")
                        self._trigger_shutdown()

                time.sleep(0.1)  # 100ms Polling-Intervall

            except Exception as e:
                print(f"❌ Fehler in Monitor-Loop: {e}")
                time.sleep(1)

    def _trigger_shutdown(self):
        """Fährt das System herunter"""
        import subprocess
        try:
            print("💀 SHUTDOWN: Fahre System herunter...")
            # Verwende sudo shutdown (funktioniert wenn User in sudo-Gruppe ist)
            subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=False)
        except Exception as e:
            print(f"❌ Fehler beim Shutdown: {e}")
            print("   Hinweis: User muss in sudo-Gruppe sein oder NOPASSWD für shutdown haben")

    def start_monitoring(self):
        """Startet Hintergrund-Überwachung"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(
                target=self.monitor_loop,
                daemon=True
            )
            self.monitor_thread.start()

    def stop_monitoring(self):
        """Stoppt Hintergrund-Überwachung"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)

    def cleanup(self):
        """Räumt GPIO-Ressourcen auf"""
        self.stop_monitoring()

        if GPIO_AVAILABLE:
            try:
                if GPIO_BACKEND == 'gpiod':
                    if hasattr(self, 'lines') and self.lines:
                        self.lines.release()
                    if hasattr(self, 'chip') and self.chip:
                        self.chip.close()
                elif GPIO_BACKEND == 'RPi.GPIO':
                    GPIO.cleanup([self.pin1, self.pin2])

                print("✅ GPIO-Cleanup durchgeführt")
            except Exception as e:
                print(f"⚠️ GPIO-Cleanup Fehler: {e}")

    def get_status(self):
        """
        Gibt aktuellen Status zurück

        Returns:
            dict: Status-Informationen
        """
        status = {
            'active': self.is_active,
            'pin1': self.pin1,
            'pin2': self.pin2,
            'gpio_available': GPIO_AVAILABLE,
            'gpio_backend': GPIO_BACKEND,
            'monitoring': self.monitoring,
            'shutdown_pending': False,
            'shutdown_in_seconds': None
        }

        # Shutdown-Timer Info hinzufügen
        if self.is_active and self.notaus_start_time and not self.shutdown_triggered:
            elapsed = time.time() - self.notaus_start_time
            remaining = self.shutdown_timeout - elapsed
            status['shutdown_pending'] = True
            status['shutdown_in_seconds'] = int(remaining)

        return status


# Globale Instanz
gpio_monitor = None


def init_gpio_monitor(pin1=17, pin2=27, shutdown_timeout=120):
    """
    Initialisiert globalen GPIO-Monitor

    Args:
        pin1: Erster GPIO-Pin (Standard: 17)
        pin2: Zweiter GPIO-Pin (Standard: 27)
        shutdown_timeout: Sekunden bis zum Shutdown (Standard: 120)
    """
    global gpio_monitor

    if gpio_monitor is None:
        gpio_monitor = GPIOMonitor(pin1=pin1, pin2=pin2, shutdown_timeout=shutdown_timeout)

    return gpio_monitor


def get_gpio_status():
    """
    Gibt aktuellen GPIO-Status zurück

    Returns:
        dict: Status-Informationen
    """
    if gpio_monitor is None:
        return {
            'active': False,
            'gpio_available': False,
            'gpio_backend': None,
            'monitoring': False,
            'error': 'GPIO-Monitor nicht initialisiert'
        }

    return gpio_monitor.get_status()


def cleanup_gpio():
    """Cleanup-Funktion für GPIO"""
    global gpio_monitor

    if gpio_monitor is not None:
        gpio_monitor.cleanup()
        gpio_monitor = None
