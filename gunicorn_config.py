"""
Gunicorn Konfiguration für VDE Messwand
"""
import multiprocessing

# Server Socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker Processes
workers = 4
worker_class = 'sync'
worker_connections = 1000
timeout = 300
keepalive = 2

# Logging
accesslog = '-'  # Stdout
errorlog = '-'   # Stdout
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process Naming
proc_name = 'vde-messwand'

# Server Hooks
def on_starting(server):
    """
    Hook: Wird beim Start des Master-Prozesses aufgerufen (vor den Workern)
    Hier initialisieren wir den GPIO-Monitor einmalig
    """
    print("🚀 Gunicorn Master-Prozess startet...")

    # Importiere und initialisiere die App
    from app import initialize_app
    initialize_app(skip_gpio_check=True)

    print("✅ GPIO-Monitor im Master-Prozess initialisiert")
    print("   Worker-Prozesse werden jetzt gestartet...")


def on_exit(server):
    """Hook: Wird beim Beenden des Master-Prozesses aufgerufen"""
    print("🛑 Gunicorn Master-Prozess wird beendet...")

    # GPIO Cleanup
    from app import cleanup_gpio
    cleanup_gpio()

    print("✅ Cleanup abgeschlossen")
