// Touch-optimierte Fehlerauswahl und Statusanzeige für Pi

// speichert aktuelle Auswahl pro Stromkreis
const selectedErrorsPi = {};

document.addEventListener('DOMContentLoaded', function() {
    // Fehlerbutton-Logik für alle Stromkreise
    for (let i = 1; i <= 7; i++) {
        const gruppe = document.getElementById('fehlergruppe' + i);
        if (gruppe) {
            const buttons = gruppe.querySelectorAll('.fehler-btn');
            buttons.forEach(btn => {
                btn.addEventListener('click', function() {
                    // Auswahl aktualisieren
                    buttons.forEach(b => b.classList.remove('selected'));
                    btn.classList.add('selected');
                    selectedErrorsPi[i] = btn.dataset.relay || '';
                    // Fehlerbeschreibung anzeigen
                    const descDiv = document.getElementById('description' + i);
                    if (!btn.dataset.relay) {
                        descDiv.innerHTML = '<em>Kein Fehler ausgewählt</em>';
                    } else {
                        descDiv.innerHTML = btn.title ? btn.title : btn.textContent;
                    }
                    updateStatusDisplayPi();
                });
            });
            // Default: erster Button (Kein Fehler) auswählen
            buttons[0].classList.add('selected');
        }
    }
    updateStatusDisplayPi();
});

function setManualErrorsPi() {
    const errors = {};
    let activeCount = 0;
    let activeRelays = [];
    for (let i = 1; i <= 7; i++) {
        const relay = selectedErrorsPi[i];
        if (relay && relay !== '') {
            errors['stromkreis' + i] = parseInt(relay);
            activeRelays.push(relay);
            activeCount++;
        }
    }
    if (activeCount === 0) {
        alert('⚠ Keine Fehler ausgewählt!');
        return;
    }
    const requestBody = JSON.stringify({errors: errors});
    fetch('/set_manual_errors', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: requestBody
    })
    .then(resp => resp.json())
    .then(data => {
        if (data.success) {
            alert(`✅ ${data.activated_count} Fehler erfolgreich zugeschaltet!\nAktive Relais: ${data.active_relays.join(', ')}`);
            updateStatusDisplayPi();
        } else {
            alert(`❌ Fehler beim Zuschalten: ${data.error || 'Unbekannter Fehler'}`);
        }
    })
    .catch(error => {
        alert('🚫 Verbindungsfehler: ' + error);
    });
}

function resetRelaysPi() {
    if (!confirm('🔄 Alle Relais zurücksetzen?\n\nDies deaktiviert alle aktiven Fehler.')) {
        return;
    }
    fetch('/reset_relays', {method: 'POST'})
    .then(resp => resp.json())
    .then(data => {
        for (let i = 1; i <= 7; i++) {
            selectedErrorsPi[i] = '';
            const gruppe = document.getElementById('fehlergruppe' + i);
            if (gruppe) {
                gruppe.querySelectorAll('.fehler-btn').forEach((btn, idx) => {
                    btn.classList.remove('selected');
                    if (idx === 0) btn.classList.add('selected');
                });
            }
            const descDiv = document.getElementById('description' + i);
            if (descDiv) descDiv.innerHTML = '<em>Kein Fehler ausgewählt</em>';
        }
        updateStatusDisplayPi();
        alert('✅ Alle Relais zurückgesetzt!');
    })
    .catch(error => {
        alert('🚫 Verbindungsfehler beim Reset!');
    });
}

function updateStatusDisplayPi() {
    const statusText = document.getElementById('status-text');
    const activeErrors = [];
    for (let i = 1; i <= 7; i++) {
        const gruppe = document.getElementById('fehlergruppe' + i);
        if (gruppe) {
            const selectedBtn = gruppe.querySelector('.fehler-btn.selected');
            if (selectedBtn && selectedBtn.dataset.relay) {
                activeErrors.push(`Stromkreis ${i}: ${selectedBtn.textContent.trim()} (Relais ${selectedBtn.dataset.relay})`);
            }
        }
    }
    if (activeErrors.length === 0) {
        statusText.textContent = 'Keine Fehler aktiv';
        statusText.style.color = '#4CAF50';
    } else {
        statusText.innerHTML = `<strong>${activeErrors.length} Fehler ausgewählt:</strong><br>• ` + activeErrors.join('<br>• ');
        statusText.style.color = '#ff9800';
    }
}
