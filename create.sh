#!/bin/bash

# Überprüfen, ob das Verzeichnis leer ist
current_dir=$(pwd)

# Überprüfen, ob das Verzeichnis leer ist
if [ "$(ls -A $current_dir)" ]; then
    echo "Verzeichnis ist nicht leer, keine Dateien werden erstellt."
else
    echo "Das Verzeichnis ist leer, Dateien werden erstellt..."
fi

# Erstellen der Unterordner und Dateien
mkdir -p $current_dir/templates
mkdir -p $current_dir/static/css
mkdir -p $current_dir/static/images

# Erstellen von Beispiel-Dateien

# home.html
cat <<EOL > $current_dir/templates/home.html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Start der Messung</title>
</head>
<body>
    <h1>Start der Messung</h1>
    <form action="/start" method="POST">
        <button type="submit">Start</button>
    </form>
</body>
</html>
EOL

# styles.css
cat <<EOL > $current_dir/static/css/styles.css
/* Haupt-Stylesheet */
body {
    font-family: Arial, sans-serif;
    background-color: #3e0e0e;
    color: white;
    margin: 0;
    padding: 20px;
}
h1 {
    color: #d32f2f;
}
button {
    background-color: #d32f2f;
    color: white;
    border: none;
    padding: 10px 20px;
    font-size: 16px;
    cursor: pointer;
}
button:hover {
    background-color: #c62828;
}
.error {
    color: #ff1744;
}
EOL

# review_ready.html
cat <<EOL > $current_dir/templates/review_ready.html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Messung abgeschlossen</title>
</head>
<body>
    <h1>Messung abgeschlossen</h1>
    <form action="/solutions" method="POST">
        <button type="submit">Fertig</button>
    </form>
</body>
</html>
EOL

# code_entry.html
cat <<EOL > $current_dir/templates/code_entry.html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Eingabe</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>
<body>
    <div class="container">
        <h1>Bitte Code eingeben</h1>
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}
        <form action="/solutions" method="post">
            <input id="code-input" type="password" name="code" placeholder="Code" readonly required>
            <div class="numpad">
                {% for num in range(1, 10) %}
                    <button type="button" class="num-button" onclick="addNumber('{{ num }}')">{{ num }}</button>
                {% endfor %}
                <button type="button" class="num-button" onclick="deleteNumber()">←</button>
                <button type="button" class="num-button" onclick="addNumber('0')">0</button>
                <button type="submit">✓</button>
            </div>
        </form>
    </div>
    <script>
        const codeInput = document.getElementById('code-input');
        
        function addNumber(num) {
            codeInput.value += num;
        }
        
        function deleteNumber() {
            codeInput.value = codeInput.value.slice(0, -1);
        }
    </script>
</body>
</html>
EOL

# solutions.html
cat <<EOL > $current_dir/templates/errors.html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fehlerbehebung</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>
<body>
    <h1>Fehlerbehebung</h1>
    <div class="errors-list">
        <ul>
            {% for category, error in errors.items() %}
                <li>{{ category }}: {{ error }}</li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
EOL

# Erfolgreiche Erstellung
echo "Dateien und Ordner wurden erfolgreich erstellt."

exit 0
