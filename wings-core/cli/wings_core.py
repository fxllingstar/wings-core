import argparse
import sys
import os
import json
import requests
import shutil
import hashlib
from datetime import datetime

# --- Configuration ---
SERVER_URL = "http://127.0.0.1:5000"
CONFIG_DIR = ".wings"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
IGNORE_DIRS = {'.wings', '__pycache__', '.git'}

# --- App Info ---
APP_VERSION = "0.1.0"
LAST_UPDATED = "4/2/2026"
IS_TESTER = True  # Set to True for "Yay", False for "Nay"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(data):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def calculate_hash():
    """Calculates a simple hash of the current directory state for verification."""
    sha = hashlib.sha256()
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for name in files:
            filepath = os.path.join(root, name)
            try:
                with open(filepath, "rb") as f:
                    while chunk := f.read(4096):
                        sha.update(chunk)
            except OSError:
                pass
    return sha.hexdigest()

def zip_project(output_filename):
    """Zips the current directory excluding .wings folder."""
    # We use a temporary logic to avoid zipping the .wings folder recursively
    # For simplicity in this script, we assume standard usage. 
    # A robust solution would manually write files to zipfile to exclude .wings
    shutil.make_archive(output_filename.replace('.zip', ''), 'zip', '.')
    return output_filename

def increment_version(current_ver):
    """Handles logic: 1.0 -> 1.1 ... 1.9 -> 2.0"""
    try:
        major, minor = map(int, current_ver.split('.'))
        minor += 1
        if minor >= 10:
            major += 1
            minor = 0
        return f"{major}.{minor}"
    except ValueError:
        return current_ver # Fallback if version string is custom

# --- Commands ---

def cmd_hello():
    print("Hello! This is wings-core.")

def cmd_version(args):
    if args.detailed:
        tester = "Yay" if IS_TESTER else "Nay"
        print(f"Version {APP_VERSION}, Last updated : {LAST_UPDATED}, Tester version : {tester}")
    else:
        print(f"Version: {APP_VERSION}")

def cmd_init(args):
    if os.path.exists(CONFIG_FILE):
        print("Wings-core is already initialized here.")
        return

    cwd_name = os.path.basename(os.getcwd())
    project_id = input(f"Enter project identifier (default: {cwd_name}): ") or cwd_name
    
    # Register with server
    try:
        payload = {"project_id": project_id}
        r = requests.post(f"{SERVER_URL}/init", json=payload)
        if r.status_code in [200, 201]:
            config = {
                "project_id": project_id,
                "local_version": "0.0",
                "server": SERVER_URL,
                "last_hash": calculate_hash()
            }
            save_config(config)
            print(f"Initialized empty wings-core project in {os.getcwd()}")
            print(f"Project Identifier: {project_id}")
        else:
            print(f"Server error: {r.text}")
    except requests.exceptions.ConnectionError:
        print("Could not connect to wings-core server.")

def cmd_push(args):
    config = load_config()
    if not config:
        print("Not a wings-core project. Run 'wings-core init' first.")
        return

    current_ver = config.get("local_version", "0.0")
    
    if args.version:
        new_version = args.version
    else:
        new_version = increment_version(current_ver)

    print(f"Pushing version {new_version}...")
    
    zip_name = "temp_push_artifact.zip"
    zip_project(zip_name)
    
    try:
        with open(zip_name, 'rb') as f:
            files = {'file': f}
            data = {'project_id': config['project_id'], 'version': new_version}
            r = requests.post(f"{config['server']}/push", data=data, files=files)
        
        if r.status_code == 200:
            config['local_version'] = new_version
            config['last_hash'] = calculate_hash()
            save_config(config)
            print(f"Successfully pushed version {new_version}")
        else:
            print(f"Failed to push: {r.text}")
            
    except Exception as e:
        print(f"Error during push: {e}")
    finally:
        if os.path.exists(zip_name):
            os.remove(zip_name)

def cmd_pull(args):
    config = load_config()
    if not config:
        print("Not a wings-core project.")
        return

    project_id = config['project_id']
    target_version = args.version 
    
    print(f"Pulling {'latest' if not target_version else target_version}...")
    
    try:
        params = {'project_id': project_id}
        if target_version:
            params['version'] = target_version
            
        r = requests.get(f"{config['server']}/pull", params=params, stream=True)
        
        if r.status_code == 200:
            zip_name = "temp_pull.zip"
            with open(zip_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            shutil.unpack_archive(zip_name, '.')
            os.remove(zip_name)
            
            status_r = requests.get(f"{config['server']}/status", params={'project_id': project_id})
            if status_r.status_code == 200:
                 remote_ver = status_r.json()['remote_version']
                 config['local_version'] = target_version if target_version else remote_ver
                 config['last_hash'] = calculate_hash()
                 save_config(config)
            
            print("Pull complete.")
        else:
            print(f"Failed to pull: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

def cmd_status(args):
    config = load_config()
    if not config:
        print("Not a wings-core project.")
        return
    
    # Check remote
    try:
        r = requests.get(f"{config['server']}/status", params={'project_id': config['project_id']})
        remote_ver = r.json().get('remote_version', 'Unknown')
    except:
        remote_ver = "Unreachable"

    # Check sync status
    local_ver = config['local_version']
    current_hash = calculate_hash()
    
    # Very basic file count difference logic for demo
    file_count = sum(len(files) for _, _, files in os.walk('.') if '.wings' not in _[0])
    
    sync_status = "Synced"
    if local_ver != remote_ver:
        sync_status = "Out of sync (Version mismatch)"
    elif current_hash != config.get('last_hash'):
        sync_status = "Out of sync (Local changes)"

    print(f"Project: {config['project_id']}")
    print(f"Local version: {local_ver}")
    print(f"Remote version: {remote_ver}")
    print(f"Status: {sync_status}")
    print(f"Total Files: {file_count}")

def cmd_list(args):
    config = load_config()
    if not config:
        print("Not a wings-core project.")
        return
    
    try:
        r = requests.get(f"{config['server']}/list", params={'project_id': config['project_id']})
        if r.status_code == 200:
            versions = r.json().get('versions', [])
            print("Available versions on server:")
            for v in versions:
                print(f" - {v}")
        else:
            print("Could not fetch list.")
    except:
        print("Server unreachable.")

def cmd_verify(args):
    config = load_config()
    if not config:
        print("Not a wings-core project.")
        return
    
    current = calculate_hash()
    stored = config.get('last_hash')
    
    if current == stored:
        print("Integrity Verified: Local state matches last known snapshot.")
    else:
        print("Integrity Warning: Local files have changed since last operation.")

def cmd_ping(args):
    try:
        r = requests.get(f"{SERVER_URL}/ping", timeout=2)
        if r.status_code == 200:
            print("Pong! Server is reachable.")
        else:
            print(f"Server responded with {r.status_code}")
    except:
        print("Ping failed. Server is unreachable.")

# --- Main CLI Parser ---

def main():
    parser = argparse.ArgumentParser(description="Wings Core VCS", add_help=False)
    
    # Global flags
    parser.add_argument('-version', action='store_true', help="Simple version")
    parser.add_argument('--version', dest='detailed_version', action='store_true', help="Detailed version")
    parser.add_argument('--help', action='help', help="Show help")
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Subcommands
    push_parser = subparsers.add_parser('push')
    push_parser.add_argument('-v', dest='version', help="Specify version manually")
    
    pull_parser = subparsers.add_parser('pull')
    pull_parser.add_argument('-v', dest='version', help="Specify version manually")
    
    subparsers.add_parser('init')
    subparsers.add_parser('status')
    subparsers.add_parser('list')
    subparsers.add_parser('verify')
    subparsers.add_parser('ping')

    # Parse only known args to handle the "wings-core" (no args) case manually
    if len(sys.argv) == 1:
        cmd_hello()
        return

    # Handle odd flag naming conventions requested (wings-core -version)
    if '-version' in sys.argv:
        cmd_version(argparse.Namespace(detailed=False))
        return
    if '--version' in sys.argv:
        cmd_version(argparse.Namespace(detailed=True))
        return

    args = parser.parse_args()

    if args.command == 'init': cmd_init(args)
    elif args.command == 'push': cmd_push(args)
    elif args.command == 'pull': cmd_pull(args)
    elif args.command == 'status': cmd_status(args)
    elif args.command == 'list': cmd_list(args)
    elif args.command == 'verify': cmd_verify(args)
    elif args.command == 'ping': cmd_ping(args)
    elif args.detailed_version: cmd_version(argparse.Namespace(detailed=True))
    else: parser.print_help()

if __name__ == "__main__":
    main()