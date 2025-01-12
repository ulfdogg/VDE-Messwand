from flask import Flask, render_template, request, redirect, url_for
import random
import logging
# import RPi.GPIO as GPIO  # GPIO-Bibliothek wird nicht verwendet, aber als Kommentar belassen

app = Flask(__name__)

# Logger konfigurieren
log_file = "error_log.txt"
logging.basicConfig(level=logging.DEBUG, filename=log_file, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# GPIO-Pins für 32 Relais
relay_pins = list(range(2, 34))  # GPIO-Pins von 2 bis 33

# GPIO.setup-Konfiguration auskommentiert
# GPIO.setmode(GPIO.BCM)
# for pin in relay_pins:
#     GPIO.setup(pin, GPIO.OUT)
#     GPIO.output(pin, GPIO.HIGH)

# Fehlerdefinitionen, Widerstandswerte und Zuordnung zu Relais
resistor_values = {
    # Lampe 1 (Stromkreis 1)
    "Hoher PE-Widerstand (Lampe 1)": "47 Ω",
    "N-PE-Isolationsfehler (Lampe 1)": "1.2 MΩ",
    "L-PE-Isolationsfehler (Lampe 1)": "820 kΩ",

    # Steckdose 1 (Stromkreis 2)
    "Hoher PE-Widerstand (Steckdose 1)": "47 Ω",
    "N-PE-Isolationsfehler (Steckdose 1)": "1 MΩ",
    "L-N-Isolationsfehler (Steckdose 1)": "2 MΩ",

    # Lampe 2 (Stromkreis 3)
    "Hoher PE-Widerstand (Lampe 2)": "100 Ω",
    "N-PE-Isolationsfehler (Lampe 2)": "1.5 MΩ",
    "L-PE-Isolationsfehler (Lampe 2)": "680 kΩ",

    # RCBO Steckdose (Stromkreis 4)
    "Hoher PE-Widerstand (RCBO Steckdose)": "56 Ω",
    "N-PE-Isolationsfehler (RCBO Steckdose)": "3 MΩ",
    "L-N-Isolationsfehler (RCBO Steckdose)": "1.8 MΩ",

    # CEE-Drehstrom (Stromkreis 5)
    "Hoher Übergangswiderstand (CEE)": "120 Ω",
    "L1-L2-Isolationsfehler (CEE)": "5 MΩ",
    "PE-Isolationsfehler (CEE)": "2.2 MΩ",

    # Perilex-Drehstrom (Stromkreis 6)
    "Hoher Übergangswiderstand (Perilex)": "82 Ω",
    "Drehfeld falsch (Perilex)": "Kein Widerstand, Phasen vertauscht",
    "PE-Isolationsfehler (Perilex)": "3.3 MΩ",
}

errors = list(resistor_values.keys())

# Zuordnung von Fehlern zu Relais
error_to_relay = {error: pin for error, pin in zip(errors, relay_pins)}

# Stromkreise und zugehörige Fehler
circuit_to_error_mapping = {
    "Stromkreis 1: Lampe 1": [
        "Hoher PE-Widerstand (Lampe 1)",
        "N-PE-Isolationsfehler (Lampe 1)",
        "L-PE-Isolationsfehler (Lampe 1)",
    ],
    "Stromkreis 2: Steckdose 1": [
        "Hoher PE-Widerstand (Steckdose 1)",
        "N-PE-Isolationsfehler (Steckdose 1)",
        "L-N-Isolationsfehler (Steckdose 1)",
    ],
    "Stromkreis 3: Lampe 2": [
        "Hoher PE-Widerstand (Lampe 2)",
        "N-PE-Isolationsfehler (Lampe 2)",
        "L-PE-Isolationsfehler (Lampe 2)",
    ],
    "Stromkreis 4: RCBO Steckdose": [
        "Hoher PE-Widerstand (RCBO Steckdose)",
        "N-PE-Isolationsfehler (RCBO Steckdose)",
        "L-N-Isolationsfehler (RCBO Steckdose)",
    ],
    "Stromkreis 5: CEE": [
        "Hoher Übergangswiderstand (CEE)",
        "L1-L2-Isolationsfehler (CEE)",
        "PE-Isolationsfehler (CEE)",
    ],
    "Stromkreis 6: Perilex": [
        "Hoher Übergangswiderstand (Perilex)",
        "Drehfeld falsch (Perilex)",
        "PE-Isolationsfehler (Perilex)",
    ],
}

# Globale Variablen
selected_errors = {}
measurement_done = False

@app.route("/")
def home():
    return render_template("home.html", measurement_done=measurement_done)

@app.route("/start", methods=["POST"])
def start():
    global measurement_done, selected_errors

    if not measurement_done:
        logging.debug("Starte Messung...")
        selected_errors = {}
        active_errors = []

        # Wähle zufällig bis zu 3 Fehler (maximal 1 Fehler pro Stromkreis)
        for circuit, error_list in circuit_to_error_mapping.items():
            if len(active_errors) >= 3:
                break
            error = random.choice(error_list)
            if error not in active_errors:
                active_errors.append(error)

        for error in active_errors:
            relay_pin = error_to_relay[error]
            # GPIO.output(relay_pin, GPIO.LOW)  # Relais einschalten (LOW = an) - Auskommentiert
            selected_errors[error] = {
                "error": error,
                "value": resistor_values[error],
                "relay_pin": relay_pin
            }
            logging.debug(f"Relais {relay_pin} für Fehler '{error}' aktiviert.")

        measurement_done = True
        logging.debug(f"Ausgewählte Fehler: {selected_errors}")

    return render_template("measurement.html", selected_errors=selected_errors)

@app.route("/reset", methods=["POST"])
def reset():
    global measurement_done, selected_errors

    # Alle Relais ausschalten - Auskommentiert
    # for pin in relay_pins:
    #     GPIO.output(pin, GPIO.HIGH)  # Relais ausschalten (HIGH = aus)

    logging.debug("Messung zurückgesetzt. Alle Relais ausgeschaltet.")

    measurement_done = False
    selected_errors = {}
    return redirect(url_for("home"))

@app.route("/solutions", methods=["GET", "POST"])
def solutions():
    if request.method == "POST":
        code1 = request.form.get("code1", "")
        code2 = request.form.get("code2", "")
        code3 = request.form.get("code3", "")

        if not code1 or not code2 or not code3:
            logging.debug("Nicht alle Felder wurden ausgefüllt.")
            return render_template("code_entry.html", error="Bitte alle Felder ausfüllen.")

        entered_code = code1 + code2 + code3
        logging.debug(f"Eingegebener Code: {entered_code}")

        if entered_code == "346":  # Erwarteter Code
            logging.debug("Code korrekt, zeige Fehler an.")
            return render_template("errors.html", errors=selected_errors)
        else:
            logging.debug("Ungültiger Code eingegeben.")
            return render_template("code_entry.html", error="Ungültiger Code!")

    return render_template("code_entry.html", error=None)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

