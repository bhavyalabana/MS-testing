from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import serial
import json
import platform
import serial.tools.list_ports
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import logging

app = Flask(__name__)
# Use environment variable for secret key
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
ENVIRONMENT = os.environ.get('FLASK_ENV', 'production')
PORT = int(os.environ.get('PORT', 5000))
REMOTE_SERIAL_SERVER = os.environ.get('REMOTE_SERIAL_SERVER')

# Configure users (use environment variables in production)
USERS = {
    os.environ.get('ADMIN_USERNAME', 'admin'): {
        'password': os.environ.get('ADMIN_PASSWORD', generate_password_hash('admin123'))
    }
}

class SerialManager:
    @staticmethod
    def is_cloud_environment():
        """Check if running in a cloud environment"""
        return ENVIRONMENT == 'production' and not REMOTE_SERIAL_SERVER

    @staticmethod
    def get_available_ports():
        """Get list of available serial ports based on environment"""
        if SerialManager.is_cloud_environment():
            logger.info("Running in cloud environment - no local serial ports available")
            return []
        
        try:
            return [port.device for port in serial.tools.list_ports.comports()]
        except Exception as e:
            logger.error(f"Error getting serial ports: {e}")
            return []

    @staticmethod
    def send_settings(port, baudrate, settings):
        """Send settings either locally or to remote serial server"""
        if SerialManager.is_cloud_environment():
            if REMOTE_SERIAL_SERVER:
                return SerialManager.send_to_remote_server(settings)
            return "Running in cloud environment - settings logged but not sent"

        try:
            with serial.Serial(
                port=port,
                baudrate=int(baudrate),
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1
            ) as ser:
                serial_data = json.dumps(settings) + '\n'
                ser.write(serial_data.encode())
                response = ser.readline().decode().strip()
                return response or "Settings sent successfully"
        except Exception as e:
            logger.error(f"Error sending settings: {e}")
            raise

    @staticmethod
    def send_to_remote_server(settings):
        """Send settings to a remote serial server"""
        try:
            import requests
            response = requests.post(REMOTE_SERIAL_SERVER, json=settings)
            response.raise_for_status()
            return response.json().get('message', 'Settings sent to remote server')
        except Exception as e:
            logger.error(f"Error sending to remote server: {e}")
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
            "isCloud": SerialManager.is_cloud_environment(),
            "hasRemoteServer": bool(REMOTE_SERIAL_SERVER)
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
                             username=session['username'],
                             is_cloud=SerialManager.is_cloud_environment(),
                             has_remote_server=bool(REMOTE_SERIAL_SERVER))
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
    logger.info(f"Available ports: {SerialManager.get_available_ports()}")
    app.run(host='0.0.0.0', port=PORT)
