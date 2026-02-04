import os
import json
import shutil
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
STORAGE_DIR = "wings_storage"

# Helper: Load project metadata
def get_project_meta(project_id):
    path = os.path.join(STORAGE_DIR, project_id, "metadata.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

# Helper: Save project metadata
def save_project_meta(project_id, data):
    path = os.path.join(STORAGE_DIR, project_id, "metadata.json")
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "alive", "message": "Wings Server is running"}), 200

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

@app.route('/push', methods=['POST'])
def push():
    project_id = request.form['project_id']
    version = request.form['version']
    
    # Save the file
    project_path = os.path.join(STORAGE_DIR, project_id)
    if not os.path.exists(project_path):
        return jsonify({"error": "Project does not exist"}), 404
        
    file = request.files['file']
    filename = secure_filename(f"{version}.zip")
    save_path = os.path.join(project_path, filename)
    file.save(save_path)
    
    # Update Metadata
    meta = get_project_meta(project_id)
    if version not in meta['versions']:
        meta['versions'].append(version)
    meta['latest_version'] = version
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
    project_id = request.args.get('project_id')
    meta = get_project_meta(project_id)
    if meta:
        return jsonify({"versions": meta['versions']}), 200
    return jsonify({"versions": []}), 404

@app.route('/pull', methods=['GET'])
def pull():
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