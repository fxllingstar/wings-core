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
import time
import datetime
import os
import json
import shutil
import logging
import traceback
import sys
import hashlib
import secrets
from flask import Flask, request, jsonify, send_file, abort, send_from_directory, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from pathlib import Path
import bcrypt

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

SERVER_START_TIME = time.time()

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

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Helper: Save project metadata
def save_project_meta(project_id, data):
    path = os.path.join(STORAGE_DIR, project_id, "metadata.json")
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def load_server_config():
    if not os.path.exists(SERVER_CONFIG_FILE):
        return {}
    with open(SERVER_CONFIG_FILE, "r") as f:
        return json.load(f)

def save_server_config(config):
    with open(SERVER_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "alive", "message": "Wings-core Server is running!"}), 200

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

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    server_pass = data.get("server_password")

    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    server_cfg = load_server_config()
    users = load_users()

    # --- LEVEL 2: Global Server Password Logic ---
    if not server_cfg.get("global_password_hash"):
        # First person ever to login sets the server password!
        if not server_pass:
            return jsonify({"error": "First-time setup: Please provide a Server Access Password"}), 400
        server_cfg["global_password_hash"] = hash_password(server_pass)
        save_server_config(server_cfg)
    else:
        # FIXED: Use verify_password to check the server password
        if not verify_password(server_pass, server_cfg["global_password_hash"]):
            return jsonify({"error": "Invalid Server Access Password. You cannot access the data. HAHA"}), 403

    # --- LEVEL 1: Personal User Logic ---
    if username not in users:
        # Only create new user if they don't exist
        users[username] = hash_password(password)
        save_users(users)
    
    # Verify existing user password
    if not verify_password(password, users[username]):
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
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else ''
    meta['last_author'] = TOKENS.get(token, 'Unknown')
    meta['timestamp'] = datetime.datetime.now().isoformat()
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

# NEW: API endpoint for web dashboard to get server stats
@app.route('/api/stats', methods=['GET'])
def get_stats():
    storage = Path(STORAGE_DIR)
    total_projects = 0
    total_versions = 0
    total_size = 0
    
    try:
        for project_dir in storage.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                total_projects += 1
                meta = get_project_meta(project_dir.name)
                if meta:
                    total_versions += len(meta.get('versions', []))
                
                # Calculate size
                for file in project_dir.rglob('*'):
                    if file.is_file():
                        total_size += file.stat().st_size
    except FileNotFoundError:
        pass
    
    return jsonify({
        "total_projects": total_projects,
        "total_versions": total_versions,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "active_users": len(TOKENS),
        "start_time": SERVER_START_TIME  
    })

@app.route('/api/logs/server', methods=['GET'])
def get_server_logs():
    # Only allow admin or local checks for safety
    if not os.path.exists("wings_server.log"):
        return jsonify({"logs": "No logs found."})
    
    with open("wings_server.log", "r") as f:
        lines = f.readlines()
        return jsonify({"logs": lines[-100:]})


@app.route('/api/projects', methods=['GET'])
def get_projects():
    storage = Path(STORAGE_DIR)
    projects = []
    
    try:
        for project_dir in storage.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                meta = get_project_meta(project_dir.name)
                if meta:
                    projects.append({
                        "id": project_dir.name,
                        "latest_version": meta.get('latest_version', 'N/A'),
                        "version_count": len(meta.get('versions', [])),
                        "last_author": meta.get('last_author', 'Unknown'),
                        "timestamp": meta.get('timestamp', 'N/A')
                    })
    except FileNotFoundError:
        pass
    
    return jsonify({"projects": projects})

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/download/<project_id>/<filename>')
def download_web_file(project_id, filename):
    storage = Path(STORAGE_DIR).resolve()
    project_dir = (storage / project_id).resolve()
    target = (project_dir / filename).resolve()

    # Prevent path traversal on both levels
    if not project_dir.is_relative_to(storage):
        abort(400, description="Invalid project.")
    
    if not target.is_relative_to(project_dir):
        abort(400, description="Invalid filename.")

    if not target.is_file():
        abort(404, description=f"File '{filename}' not found in project '{project_id}'.")

    return send_from_directory(project_dir, filename, as_attachment=True)

if __name__ == '__main__':
    # Configure standard logging to a file
    logging.basicConfig(
        filename='wings_server.log',
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

    if not os.path.exists(STORAGE_DIR):
        os.mkdir(STORAGE_DIR)
    
    if not os.path.exists('templates'):
        os.mkdir('templates')
    
    if not os.path.exists('static'):
        os.mkdir('static')

    try:
        logging.info("Server starting...")
        app.run(debug=DEBUG, port=PORT, host='0.0.0.0')
    except Exception as e:
        # This block catches CRITICAL crashes that stop the server
        error_msg = traceback.format_exc()
        
        # 1. Log to the standard log
        logging.error("FATAL CRASH DETECTED:\n" + error_msg)
        
        # 2. Create a specific crash dump file for easy reading
        with open("crash.log", "w") as f:
            f.write(f"WINGS-CORE CRASH REPORT - {datetime.datetime.now()}\n")
            f.write("="*40 + "\n")
            f.write(error_msg)
            
        print("!! SERVER CRASHED !! Details saved to crash.log")
        sys.exit(1)
    
    app.run(debug=DEBUG, port=PORT, host='0.0.0.0')