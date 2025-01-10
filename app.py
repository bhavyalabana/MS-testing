from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import platform
import os
import requests
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS  # Add this import




# Near the top of your app.py, after importing Flas
LOCAL_CLIENT_URL = os.environ.get('LOCAL_CLIENT_URL', 'http://localhost:5001')

app = Flask(__name__)
CORS(app)  # Enable CORS for the Flask app
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
ENVIRONMENT = os.environ.get('FLASK_ENV', 'production')
PORT = int(os.environ.get('PORT', 5000))
LOCAL_CLIENT_URL = os.environ.get('LOCAL_CLIENT_URL', 'http://localhost:5001')

# Configure users
USERS = {
    os.environ.get('ADMIN_USERNAME', 'admin'): {
        'password': os.environ.get('ADMIN_PASSWORD', generate_password_hash('admin123'))
    }
}

class SerialManager:
    @staticmethod
    def get_available_ports():
        """Get list of available serial ports from local client"""
        try:
            response = requests.get('http://localhost:5001/ports')
            print(f"Response from local client: {response.json()}")  # Debug print
            return response.json().get('ports', [])
        except requests.exceptions.ConnectionError:
            print("Could not connect to local client")
            return []
        except Exception as e:
            print(f"Error getting ports: {str(e)}")
            return []

    @staticmethod
    def send_settings(port, baudrate, settings):
        """Send settings to local client"""
        try:
            response = requests.post(f"{LOCAL_CLIENT_URL}/send", json={
                'port': port,
                'baudrate': baudrate,
                'settings': settings
            })
            response.raise_for_status()
            return response.json().get('response', 'Settings sent successfully')
        except Exception as e:
            logger.error(f"Error sending settings: {e}")
            raise

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and check_password_hash(USERS[username]['password'], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/get_ports')
@login_required
def get_ports():
    """API endpoint to get available ports"""
    try:
        ports = SerialManager.get_available_ports()
        return jsonify({
            "ports": ports,
            "isCloud": True,
            "hasRemoteServer": True
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
@login_required
def index():
    try:
        return render_template('index.html', 
                             os_type=platform.system(),
                             available_ports=SerialManager.get_available_ports(),
                             username=session['username'])
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return str(e), 500

@app.route('/submit_settings', methods=['POST'])
@login_required
def submit_settings():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No settings provided"}), 400

        network_settings = {
            key: data[key] for key in ['vlan_id', 'ip_address', 'subnet_mask', 'gateway']
            if key in data and data[key]
        }

        if not network_settings:
            return jsonify({"status": "error", "message": "No network settings provided"}), 400

        response = SerialManager.send_settings(
            data.get('port'),
            data.get('baudrate', 9600),
            network_settings
        )

        return jsonify({"status": "success", "response": response})

    except Exception as e:
        logger.error(f"Error submitting settings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Starting application in {ENVIRONMENT} environment")
    app.run(host='0.0.0.0', port=PORT)
