from flask import Flask, render_template, request, redirect, url_for
import random
import logging

app = Flask(__name__)

# Logger konfigurieren
logging.basicConfig(level=logging.DEBUG)

# Erwarteter Code
EXPECTED_CODE = "346"

# Fehlerdefinitionen und Widerstandswerte
resistor_values = {
    "Stromkreis 1 - Durchgängigkeit des Schutzleitersystems": {
        "Schutzleiter unterbrochen": "Unendlich (keine Verbindung)",
        "Hoher Übergangswiderstand": "47 Ω",
        "Schutzleiter nicht angeschlossen": "Unendlich (keine Verbindung)",
        "Schutzleiter mit Phase verbunden": "0 Ω (Kurzschluss)",
        "Korrosion im Schutzleiteranschluss": "82 Ω"
    },
    "Stromkreis 1 - Isolationswiderstandsmessung": {
        "Isolationswiderstand zu niedrig": "330 kΩ",
        "Fehlerhafter Isolationstest": "Unendlich (Messgerät Fehler)",
        "Kurzschluss zwischen L und N": "0 Ω",
        "Isolationsfehler bei PE": "560 kΩ",
        "Feuchtigkeitseinfluss": "1 MΩ"
    },
    # Weitere Stromkreise und Fehler wie angegeben
}

errors = {
    "Stromkreis 1 - Durchgängigkeit des Schutzleitersystems": [
        "Schutzleiter unterbrochen",
        "Hoher Übergangswiderstand",
        "Schutzleiter nicht angeschlossen",
        "Schutzleiter mit Phase verbunden",
        "Korrosion im Schutzleiteranschluss"
    ],
    "Stromkreis 1 - Isolationswiderstandsmessung": [
        "Isolationswiderstand zu niedrig",
        "Fehlerhafter Isolationstest",
        "Kurzschluss zwischen L und N",
        "Isolationsfehler bei PE",
        "Feuchtigkeitseinfluss"
    ],
    # Weitere Fehler wie angegeben
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

        # Verfügbare Stromkreise hallo
        available_categories = list(errors.keys())
        num_categories = min(len(available_categories), 3)  # Maximal 3 oder weniger, wenn nicht genug Kategorien

        if num_categories == 0:
            logging.error("Keine verfügbaren Kategorien für Fehler.")
            return render_template("home.html", error="Keine Fehlerkategorien verfügbar.")

        # Wähle 3 zufällige Kategorien aus, ohne Duplikate
        selected_categories = random.sample(available_categories, num_categories)

        selected_errors = {}
        for category in selected_categories:
            error = random.choice(errors[category])  # Zufälliger Fehler (nur 1 pro Kategorie)
            selected_errors[category] = {
                error: resistor_values[category].get(error, "Kein Wert verfügbar")
            }

        measurement_done = True  # Messung abgeschlossen
        logging.debug(f"Ausgewählte Fehler: {selected_errors}")

    return render_template("measurement.html", selected_errors=selected_errors)



@app.route("/reset", methods=["POST"])
def reset():
    global measurement_done, selected_errors
    measurement_done = False
    selected_errors = {}
    logging.debug("Messung zurückgesetzt.")
    return redirect(url_for("home"))

@app.route("/solutions", methods=["GET", "POST"])
def solutions():
    if request.method == "POST":
        code1 = request.form.get("code1", "")  # Standardwert ist eine leere Zeichenkette, wenn 'None'
        code2 = request.form.get("code2", "")  # Standardwert ist eine leere Zeichenkette, wenn 'None'
        code3 = request.form.get("code3", "")  # Standardwert ist eine leere Zeichenkette, wenn 'None'

        entered_code = code1 + code2 + code3
        logging.debug(f"Eingegebener Code: {entered_code}")

        if entered_code == EXPECTED_CODE:
            logging.debug("Code korrekt, zeige Fehler an.")
            return render_template("errors.html", errors=selected_errors)
        else:
            logging.debug("Ungültiger Code eingegeben.")
            return render_template("code_entry.html", error="Ungültiger Code!")

    return render_template("code_entry.html", error=None)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
