// Global variables
let examTimer = null;
let examStartTime = null;
let currentExamNumber = null;

// Utility functions
function showMessage(message, type = 'success') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `status-message status-${type}`;
    messageDiv.textContent = message;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(messageDiv, container.firstChild);
        
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Exam mode functions
function startExam(examNumber) {
    currentExamNumber = examNumber;
    examStartTime = Date.now();
    
    fetch('/start_exam', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ exam_number: examNumber })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showMessage('Prüfung gestartet! Fehler wurden zugeschaltet.', 'success');
            startTimer();
            
            // Hide start button and show finish button
            const startBtn = document.getElementById('startBtn');
            const finishBtn = document.getElementById('finishBtn');
            const timerDisplay = document.getElementById('timerDisplay');
            
            if (startBtn) startBtn.style.display = 'none';
            if (finishBtn) finishBtn.style.display = 'inline-block';
            if (timerDisplay) timerDisplay.style.display = 'block';
        } else {
            showMessage('Fehler beim Starten der Prüfung!', 'error');
        }
    })
    .catch(error => {
        showMessage('Netzwerkfehler!', 'error');
        console.error('Error:', error);
    });
}

function startTimer() {
    let remainingTime = 20 * 60; // 20 minutes in seconds
    const timerElement = document.getElementById('timer');
    
    if (!timerElement) {
        console.error('Timer element not found!');
        return;
    }
    
    // Clear existing timer if any
    if (examTimer) {
        clearInterval(examTimer);
    }
    
    examTimer = setInterval(() => {
        timerElement.textContent = formatTime(remainingTime);
        remainingTime--;
        
        if (remainingTime < 0) {
            finishExam();
        }
    }, 1000);
}

function finishExam() {
    if (examTimer) {
        clearInterval(examTimer);
        examTimer = null;
    }
    
    const duration = examStartTime ? Math.floor((Date.now() - examStartTime) / 1000) : 0;
    
    fetch('/finish_exam', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            exam_number: currentExamNumber,
            duration: duration
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showMessage('Prüfung beendet! Alle Relais wurden zurückgesetzt.', 'success');

            // Format duration
            const minutes = Math.floor(duration / 60);
            const seconds = duration % 60;
            const durationText = `${minutes}:${seconds.toString().padStart(2, '0')}`;

            // Show completion message
            const container = document.querySelector('.container');
            if (container) {
                container.innerHTML = `
                    <div class="glass-card">
                        <h1>✅ Prüfung beendet</h1>

                        <div style="background: rgba(76, 175, 80, 0.1); border: 2px solid rgba(76, 175, 80, 0.3); border-radius: 15px; padding: 30px; margin: 30px 0;">
                            <p style="text-align: center; font-size: 1.3rem; margin: 10px 0; color: #4caf50;">
                                <strong>Prüfungsnummer:</strong>
                            </p>
                            <p style="text-align: center; font-size: 2.5rem; font-weight: bold; margin: 10px 0; color: #4caf50;">
                                ${currentExamNumber}
                            </p>
                            <p style="text-align: center; font-size: 1.1rem; margin: 20px 0; opacity: 0.9;">
                                Dauer: ${durationText} Min
                            </p>
                        </div>

                        <p style="text-align: center; font-size: 1.2rem; margin: 20px 0;">
                            Die Prüfung wurde erfolgreich abgeschlossen.
                        </p>

                        <div class="spinner"></div>

                        <p style="text-align: center; margin-top: 20px; opacity: 0.8;">
                            Weiterleitung zur Startseite in <span id="countdown">3</span> Sekunden...
                        </p>
                    </div>
                `;

                // Countdown
                let countdown = 3;
                const countdownEl = document.getElementById('countdown');
                const countdownInterval = setInterval(() => {
                    countdown--;
                    if (countdownEl) {
                        countdownEl.textContent = countdown;
                    }
                    if (countdown <= 0) {
                        clearInterval(countdownInterval);
                    }
                }, 1000);

                // Redirect after 3 seconds
                setTimeout(() => {
                    window.location.href = '/';
                }, 3000);
            }
        } else {
            showMessage('Fehler beim Beenden der Prüfung!', 'error');
        }
    })
    .catch(error => {
        showMessage('Netzwerkfehler!', 'error');
        console.error('Error:', error);
    });
}

// Test mode functions
function runTest() {
    const runBtn = document.getElementById('runTestBtn');
    if (!runBtn) {
        console.error('Run test button not found!');
        return;
    }
    
    runBtn.disabled = true;
    runBtn.textContent = 'Test läuft...';
    
    showMessage('Relais-Test gestartet...', 'success');
    
    fetch('/run_test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showMessage('Relais-Test erfolgreich abgeschlossen!', 'success');
        } else {
            showMessage(`Fehler beim Test: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        showMessage('Netzwerkfehler!', 'error');
        console.error('Error:', error);
    })
    .finally(() => {
        runBtn.disabled = false;
        runBtn.textContent = 'Test Starten';
    });
}

// Admin functions
function adminLogin() {
    const codeInput = document.getElementById('adminCode');
    if (!codeInput) {
        console.error('Admin code input not found!');
        return;
    }
    
    const code = codeInput.value;
    if (!code) {
        showMessage('Bitte Code eingeben!', 'error');
        return;
    }
    
    fetch('/admin_login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: code })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            window.location.href = '/admin_panel';
        } else {
            showMessage('Falscher Code!', 'error');
            codeInput.value = '';
        }
    })
    .catch(error => {
        showMessage('Netzwerkfehler!', 'error');
        console.error('Error:', error);
    });
}

function clearDatabase() {
    if (confirm('Sind Sie sicher, dass Sie die gesamte Datenbank löschen möchten?')) {
        fetch('/clear_database', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showMessage('Datenbank wurde geleert!', 'success');
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                showMessage('Fehler beim Leeren der Datenbank!', 'error');
            }
        })
        .catch(error => {
            showMessage('Netzwerkfehler!', 'error');
            console.error('Error:', error);
        });
    }
}

function connectWifi() {
    const ssidInput = document.getElementById('wifiSSID');
    const passwordInput = document.getElementById('wifiPassword');
    
    if (!ssidInput || !passwordInput) {
        console.error('WiFi input fields not found!');
        return;
    }
    
    const ssid = ssidInput.value;
    const password = passwordInput.value;
    
    if (!ssid) {
        showMessage('Bitte SSID eingeben!', 'error');
        return;
    }
    
    fetch('/connect_wifi', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ssid: ssid, password: password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showMessage('WLAN-Verbindung wird hergestellt...', 'success');
        } else {
            showMessage(`Fehler bei WLAN-Verbindung: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        showMessage('Netzwerkfehler!', 'error');
        console.error('Error:', error);
    });
}

function shutdownSystem() {
    if (confirm('System wirklich herunterfahren?')) {
        fetch('/shutdown_system', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showMessage('System wird heruntergefahren...', 'success');
                
                // Show shutdown message
                document.body.innerHTML = `
                    <div class="container">
                        <div class="glass-card">
                            <h1>System wird heruntergefahren</h1>
                            <div class="spinner"></div>
                            <p style="text-align: center; margin-top: 20px;">
                                Bitte warten Sie, bis das System vollständig heruntergefahren ist.
                            </p>
                        </div>
                    </div>
                `;
            } else {
                showMessage(`Fehler beim Herunterfahren: ${data.error}`, 'error');
            }
        })
        .catch(error => {
            showMessage('Netzwerkfehler!', 'error');
            console.error('Error:', error);
        });
    }
}

// Debug function for manual mode
function debugLog(message) {
    console.log('DEBUG:', message);
    const debugOutput = document.getElementById('debug-output');
    if (debugOutput) {
        const timestamp = new Date().toLocaleTimeString();
        debugOutput.innerHTML = `${timestamp}: ${message}<br>${debugOutput.innerHTML}`;
    }
}

function setManualErrors() {
    const errors = {};
    let activeCount = 0;
    const selectedErrors = [];

    for (let i = 1; i <= 7; i++) {
        const element = document.getElementById('stromkreis' + i);
        if (element && element.value !== '') {
            const relayId = parseInt(element.value);
            if (!isNaN(relayId) && relayId > 0) {
                errors['stromkreis' + i] = relayId;
                activeCount++;
                const selectedOption = element.options[element.selectedIndex];
                if (selectedOption) {
                    selectedErrors.push(`Stromkreis ${i}: ${selectedOption.text} (Relais ${relayId})`);
                }
            }
        }
    }

    if (activeCount === 0) {
        alert('⚠ Keine Fehler ausgewählt!');
        return;
    }

    debugLog(`Setting ${activeCount} manual errors: ${JSON.stringify(errors)}`);

    fetch('/set_manual_errors', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({errors: errors})
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        debugLog(`Response: ${JSON.stringify(data)}`);
        if (data.success) {
            alert(`✅ ${data.activated_count} Fehler erfolgreich zugeschaltet!\nAktive Relais: ${data.active_relays.join(', ')}`);
            updateStatusDisplay();
        } else {
            alert(`❌ Fehler beim Zuschalten: ${data.error || 'Unbekannter Fehler'}`);
        }
    })
    .catch(error => {
        debugLog(`Error: ${error}`);
        alert('🚫 Verbindungsfehler: ' + error);
    });
}

function updateStatusDisplay() {
    const statusText = document.getElementById('status-text');
    if (!statusText) {
        console.warn('Status text element not found');
        return;
    }
    
    const activeErrors = [];
    
    for (let i = 1; i <= 7; i++) {
        const selectEl = document.getElementById('stromkreis' + i);
        if (selectEl && selectEl.value !== '') {
            const relayId = parseInt(selectEl.value);
            const selectedOption = selectEl.options[selectEl.selectedIndex];
            if (selectedOption && !isNaN(relayId)) {
                const errorName = selectedOption.text.split(' (')[0];
                activeErrors.push(`Stromkreis ${i}: ${errorName} (Relais ${relayId})`);
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

function resetRelays() {
    if (!confirm('🔄 Alle Relais zurücksetzen?\n\nDies deaktiviert alle aktiven Fehler.')) {
        return;
    }

    debugLog('Resetting relays...');

    fetch('/reset_relays', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        debugLog('Reset response: ' + JSON.stringify(data));
        
        // Reset all select elements
        for (let i = 1; i <= 7; i++) {
            const selectElement = document.getElementById('stromkreis' + i);
            const descriptionDiv = document.getElementById('description' + i);
            if (selectElement) {
                selectElement.value = '';
            }
            if (descriptionDiv) {
                descriptionDiv.innerHTML = '<em>Kein Fehler ausgewählt</em>';
            }
        }
        
        updateStatusDisplay();
        
        if (data.success) {
            alert('✅ Alle Relais zurückgesetzt!');
        } else {
            alert(`⚠ Reset teilweise erfolgreich: ${data.message || 'Unbekannter Status'}`);
        }
    })
    .catch(error => {
        debugLog('Reset error: ' + error);
        alert('🚫 Verbindungsfehler beim Reset!');
    });
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Add touch-friendly interactions
    const buttons = document.querySelectorAll('.btn, .menu-item');
    buttons.forEach(button => {
        button.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.95)';
        });
        
        button.addEventListener('touchend', function() {
            this.style.transform = '';
        });
        
        // Also handle mouse events for desktop
        button.addEventListener('mousedown', function() {
            this.style.transform = 'scale(0.95)';
        });
        
        button.addEventListener('mouseup', function() {
            this.style.transform = '';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });
    
    // Handle Enter key for admin login
    const adminCodeInput = document.getElementById('adminCode');
    if (adminCodeInput) {
        adminCodeInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                adminLogin();
            }
        });
    }
    
    // Initialize status display if elements exist
    const statusText = document.getElementById('status-text');
    if (statusText) {
        updateStatusDisplay();
    }
    
    // Add change listeners to select elements for real-time status updates
    for (let i = 1; i <= 7; i++) {
        const selectElement = document.getElementById('stromkreis' + i);
        if (selectElement) {
            selectElement.addEventListener('change', updateStatusDisplay);
        }
    }
    
    console.log('Initialization complete');
});
