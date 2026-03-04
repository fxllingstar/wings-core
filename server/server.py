# wings-core
# Copyright (C) 2026 fxllingstar on GitHub
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.





import datetime
import os
import json
import shutil
import hashlib
import secrets
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load the variables from .env into the system
load_dotenv()


SERVER_CONFIG_FILE = "server_config.json"
ADMIN_TOKEN = os.getenv("WINGS_ADMIN_TOKEN")
PORT = int(os.getenv("WINGS_SERVER_PORT", 5000)) # 5000 is the fallback
DEBUG = os.getenv("DEBUG_MODE") == "True"
USERS_FILE = "users.json"
TOKENS = {}  



def require_auth():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return False

    if not auth_header.startswith("Bearer "):
        return False

    token = auth_header.split(" ")[1]

    return token in TOKENS
app = Flask(__name__)
STORAGE_DIR = "wings_storage"

# Helper: Load project metadata
def get_project_meta(project_id):
    path = os.path.join(STORAGE_DIR, project_id, "metadata.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    users = load_users()
    password_hash = hash_password(password)

    # If user doesn't exist → register automatically
    if username not in users:
        users[username] = password_hash
        save_users(users)
    else:
        # Validate password
        if users[username] != password_hash:
            return jsonify({"error": "Invalid password"}), 401

    # Generate token
    token = secrets.token_hex(32)
    TOKENS[token] = username

    return jsonify({"token": token}), 200


# Helper: Save project metadata
def save_project_meta(project_id, data):
    path = os.path.join(STORAGE_DIR, project_id, "metadata.json")
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "alive", "message": "Wings-core Server is running!"}), 200 #Yayy

@app.route('/init', methods=['POST'])
def init_project():
    project_id = request.json.get('project_id')
    project_path = os.path.join(STORAGE_DIR, project_id)
    
    if not os.path.exists(project_path):
        os.makedirs(project_path)
        # Initialize metadata
        save_project_meta(project_id, {
            "latest_version": "0.0",
            "versions": []
        })
        return jsonify({"message": "Project initialized on server."}), 201
    return jsonify({"message": "Project already exists."}), 200




def load_server_config():
    if not os.path.exists(SERVER_CONFIG_FILE):
        return {}
    with open(SERVER_CONFIG_FILE, "r") as f:
        return json.load(f)

def save_server_config(config):
    with open(SERVER_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    server_pass = data.get("server_password") # The new global lock

    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    server_cfg = load_server_config()
    users = load_users()
    pass_hash = hash_password(password)

    # --- LEVEL 2: Global Server Password Logic ---
    if not server_cfg.get("global_password_hash"):
        # First person ever to login sets the server password!
        if not server_pass:
            return jsonify({"error": "First-time setup: Please provide a Server Access Password"}), 400
        server_cfg["global_password_hash"] = hash_password(server_pass)
        save_server_config(server_cfg)
    else:
        # Verify the global lock
        if hash_password(server_pass) != server_cfg["global_password_hash"]:
            return jsonify({"error": "Invalid Server Access Password. You cannot access the data. HAHA"}), 403

    # --- LEVEL 1: Personal User Logic ---
    if username not in users:
        users[username] = pass_hash
        save_users(users)
    elif users[username] != pass_hash:
        return jsonify({"error": "Invalid personal password. NUH UH"}), 401

    # If we got here, both locks are open!
    token = secrets.token_hex(32)
    TOKENS[token] = username
    return jsonify({"token": token, "message": "Authenticated successfully! NICEE"}), 200






@app.route('/push', methods=['POST'])
def push():
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 403


    project_id = request.form['project_id']
    version = request.form['version']
    
    project_path = os.path.join(STORAGE_DIR, project_id)
    if not os.path.exists(project_path):
        return jsonify({"error": "Project does not exist"}), 404
        
    # --- 1. Save the Project Zip ---
    file = request.files['file']
    filename = secure_filename(f"{version}.zip")
    file.save(os.path.join(project_path, filename))
    
    # --- 2. Save the Log File (New!) ---
    if 'log' in request.files:
        log_file = request.files['log']
        log_filename = secure_filename(f"{version}.log")
        log_file.save(os.path.join(project_path, log_filename))
    
    # Update Metadata
    meta = get_project_meta(project_id)
    if version not in meta['versions']:
        meta['versions'].append(version)
    meta['latest_version'] = version
    meta['last_author'] = TOKENS.get(request.headers.get('Authorization'), 'Unknown')
    meta['timestamp'] = datetime.now().isoformat()
    save_project_meta(project_id, meta)

    
    save_project_meta(project_id, meta)

    
    return jsonify({"message": f"Version {version} pushed successfully."}), 200

@app.route('/status', methods=['GET'])
def status():
    project_id = request.args.get('project_id')
    meta = get_project_meta(project_id)
    if not meta:
        return jsonify({"error": "Project not found"}), 404
    return jsonify({"remote_version": meta['latest_version']}), 200

@app.route('/list', methods=['GET'])
def list_versions():
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 403

    project_id = request.args.get('project_id')
    meta = get_project_meta(project_id)
    if meta:
        return jsonify({"versions": meta['versions']}), 200
    return jsonify({"versions": []}), 404

@app.route('/logs', methods=['GET'])
def get_logs():
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 403

    project_id = request.args.get('project_id')
    version = request.args.get('version')
    
    meta = get_project_meta(project_id)
    if not meta:
        return "Project not found", 404
        
    # If no version specified or 'latest', get the newest one
    if not version or version == "latest":
        version = meta['latest_version']
        
    log_path = os.path.join(STORAGE_DIR, project_id, f"{version}.log")
    
    if os.path.exists(log_path):
        # We use mimetype="text/plain" so the CLI can read it easily as text 
        return send_file(log_path, mimetype="text/plain")
    else:
        return f"No log file found for version {version}", 404

@app.route('/pull', methods=['GET'])
def pull():
    if not require_auth():
        return jsonify({"error": "Unauthorized"}), 403


    project_id = request.args.get('project_id')
    version = request.args.get('version')
    
    meta = get_project_meta(project_id)
    
    # If no version specified, get latest
    if not version:
        version = meta['latest_version']
        
    file_path = os.path.join(STORAGE_DIR, project_id, f"{version}.zip")
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "Version not found"}), 404

if __name__ == '__main__':
    if not os.path.exists(STORAGE_DIR):
        os.mkdir(STORAGE_DIR)
    # Run on port 5000
    app.run(debug=True, port=5000)