from flask import Flask, render_template_string, jsonify
from flask_basicauth import BasicAuth
import os
import subprocess
import requests

NAS_MAC_ADDRESS = '<your-mac-address>'
NAS_IP = '<your-ip-address>'
USERNAME = '<your-username>'
PASSWORD = '<your-password>'

STATUS_CHECK_INTERVAL = 30000  # 30 seconds
IP_UPDATE_INTERVAL = 300000    # 5 minutes

app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = USERNAME
app.config['BASIC_AUTH_PASSWORD'] = PASSWORD

basic_auth = BasicAuth(app)

main_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Wake Nassy</title>
        <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='45' fill='%232196F3'/><path d='M50 30 L50 70 M30 50 L70 50' stroke='white' stroke-width='8' stroke-linecap='round'/></svg>">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            html, body {
                height: 100%;
                overflow: hidden;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                text-align: center;
                background-color: #f5f5f5;
                color: #333;
                display: flex;
                align-items: center;
                justify-content: center;
                -webkit-tap-highlight-color: transparent;
                padding: 0;
                margin: 0;
            }
            .card {
                background: white;
                padding: 1em;
                border-radius: 20px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                width: 90%;
                max-width: 400px;
                margin: 0;
            }
            h1 {
                font-size: 2em;
                margin: 0.3em 0;
                font-weight: 700;
                background: linear-gradient(45deg, #2196F3, #1976D2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .power-button {
                width: 90px;
                height: 90px;
                border-radius: 50%;
                background: #f0f0f0;
                border: none;
                cursor: pointer;
                position: relative;
                transition: all 0.3s ease;
                margin: 1em auto;
                display: flex;
                align-items: center;
                justify-content: center;
                -webkit-tap-highlight-color: transparent;
                touch-action: manipulation;
            }
            .power-button:hover {
                transform: scale(1.05);
            }
            .power-button:active {
                transform: scale(0.95);
            }
            .power-button i {
                font-size: 36px;
                color: #666;
                transition: color 0.3s ease;
            }
            .power-button.online {
                background: #e8f5e9;
                box-shadow: 0 0 20px rgba(76, 175, 80, 0.2);
            }
            .power-button.online i {
                color: #4caf50;
            }
            .power-button.offline {
                background: #ffebee;
                box-shadow: 0 0 20px rgba(244, 67, 54, 0.2);
            }
            .power-button.offline i {
                color: #f44336;
            }
            .power-button.waking {
                background: #fff3e0;
                box-shadow: 0 0 20px rgba(255, 152, 0, 0.2);
            }
            .power-button.waking i {
                color: #ff9800;
            }
            .message {
                margin-top: 1em;
                padding: 0.8em;
                border-radius: 12px;
                background: #e3f2fd;
                color: #1976d2;
                display: none;
                font-size: 1em;
            }
            .message.show {
                display: block;
                animation: fadeIn 0.5s ease-in;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @media (min-width: 768px) {
                .card {
                    padding: 1.5em;
                }
                h1 {
                    font-size: 2.5em;
                    margin: 0.5em 0;
                }
                .power-button {
                    width: 120px;
                    height: 120px;
                    margin: 1.5em auto;
                }
                .power-button i {
                    font-size: 48px;
                }
                .message {
                    font-size: 1.1em;
                    padding: 1em;
                }
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>NASSY</h1>
            <form action="/" method="post" id="wakeForm">
                <button type="submit" class="power-button" id="powerButton">
                    <i class="fas fa-power-off"></i>
                </button>
            </form>
            <div class="message" id="wakeMessage"></div>
            <div id="externalIp" style="margin-top: 1em; color: #666; font-size: 0.9em;"></div>
        </div>
        <script>
            function checkStatus() {
                fetch('/ping')
                    .then(response => response.json())
                    .then(data => {
                        const button = document.getElementById('powerButton');
                        const message = document.getElementById('wakeMessage');
                        if (data.status === 'online') {
                            button.classList.remove('offline', 'waking');
                            button.classList.add('online');
                            message.classList.remove('show');
                        } else {
                            button.classList.remove('online', 'waking');
                            button.classList.add('offline');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                    });
            }

            document.getElementById('wakeForm').addEventListener('submit', function(e) {
                e.preventDefault();
                const button = document.getElementById('powerButton');
                const message = document.getElementById('wakeMessage');
                
                // Check if server was already online before sending wake command
                const wasOnline = button.classList.contains('online');
                
                button.classList.remove('online', 'offline');
                button.classList.add('waking');
                
                fetch('/', {
                    method: 'POST',
                })
                .then(response => response.text())
                .then(html => {
                    // Only check status immediately if it was already online
                    if (wasOnline) {
                        checkStatus();
                    } else {
                        // Show message that server is starting
                        message.textContent = 'Server is starting up...';
                        message.classList.add('show');
                    }
                });
            });

            // Check status immediately and then every 30 seconds
            checkStatus();
            setInterval(checkStatus, {{ STATUS_CHECK_INTERVAL }});

            function updateExternalIp() {
                fetch('/external-ip')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('externalIp').textContent = `External IP: ${data.ip}`;
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('externalIp').textContent = 'Unable to fetch IP';
                    });
            }

            // Update external IP immediately and then every 5 minutes
            updateExternalIp();
            setInterval(updateExternalIp, {{ IP_UPDATE_INTERVAL }});
        </script>
    </body>
    </html>
'''

response_template = '''
'''

@app.route('/')
@basic_auth.required
def index():
    return render_template_string(main_template)

@app.route('/ping')
@basic_auth.required
def ping():
    try:
        result = subprocess.run(['ping', '-c', '1', '-W', '1', NAS_IP], 
                              capture_output=True, text=True)
        return jsonify({'status': 'online' if result.returncode == 0 else 'offline'})
    except Exception as e:
        return jsonify({'status': 'offline'})

@app.route('/', methods=['POST'])
@basic_auth.required
def wake():
    os.system(f"wakeonlan {NAS_MAC_ADDRESS}")
    return '', 200

@app.route('/external-ip')
@basic_auth.required
def get_external_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return jsonify({'ip': response.json()['ip']})
    except Exception as e:
        return jsonify({'ip': 'Unable to fetch IP'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

