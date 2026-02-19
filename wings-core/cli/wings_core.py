#Imports
import difflib
import argparse
from logging import config
import sys
import os
import json
import requests
import shutil
import hashlib
import importlib.metadata
from datetime import datetime



# --- Configuration ---
SERVER_URL = "http://127.0.0.1:5000"
CONFIG_DIR = ".wings"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
IGNORE_DIRS = {'.wings', '__pycache__', '.git'}

# --- App Info --- 
try:
    APP_VERSION = importlib.metadata.version("wings_core")
except importlib.metadata.PackageNotFoundError:
    APP_VERSION = "0.1.5-dev"
    last_mod_time = os.path.getmtime(__file__)
LAST_UPDATED = datetime.datetime.fromtimestamp(last_mod_time).strftime('%m/%d/%Y')
IS_TESTER = True  
IS_USER = False
#
#True for yay false for nay :)

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
    #Hopefully -_-
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
    
    # Register with server (yippee)
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
    
    # Very basic file count difference logic for demo (this is going to crash soon lol)
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
            print("Pong! Server is reachable.") #Awh:(
        else:
            print(f"Server responded with {r.status_code}")
    except:
        print("Ping failed. Server is unreachable.")

def cmd_terminate(args):
    config = load_config()
    if not config:
        print("This project is currently not tracked by wings-core.")
        return

    print(f"⚠️  WARNING: You are about to terminate tracking for project: {config['project_id']}")
    print("This will delete all metadata. You will NOT be able to push or pull anymore unless you re-initialize.")
    confirm = input("Are you absolutely sure? (y/n): ").lower()

if confirm == 'y':
    try:
        if os.path.exists(CONFIG_DIR):
            shutil.rmtree(CONFIG_DIR)
            print(f"✅ Success: Tracking terminated. '{config['project_id']}' is now just a regular folder.")
        else:
            print("No metadata folder found, but config was loaded. Clean-up may be required.")
    except Exception as e:
        print(f"❌ Error during termination: {e}")
else:

    print("\n🛡️  Termination aborted. Your project is still being tracked.")
    print("Nothing was deleted.")






def cmd_qotd(args):

    api_key = "T5IPGazplSNa0zshSzXLA54AunEpBaXdGpwaK2pK" 
    url = "https://api.api-ninjas.com/v2/quoteoftheday"
    
    print("Fetching today's message from the oracle...")
    
    try:
     
        response = requests.get(url, headers={'X-Api-Key': api_key}, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            quote_obj = data[0] if isinstance(data, list) else data
            
            quote = quote_obj.get('quote')
            author = quote_obj.get('author')
            
            if quote:
                print("\n" + "═" * 50)
                print(f"  TODAY'S WISDOM")
                print("─" * 50)
                print(f"  \"{quote}\"")
                print(f"\n  — {author}")
                print("═" * 50 + "\n")
            else:
                print("The oracle is resting. No quote found in the response. awh:(")
                
        elif response.status_code == 401:
            print("❌ Error: Invalid API Key. Please verify your key in wings_core.py.")
        else:
            print(f"❌ Oracle is unavailable. (Status: {response.status_code})")
            
    except Exception as e:
        print(f"❌ The connection to the oracle was lost: {e}")



# --- Main CLI Parser ---

def main():
    valid_commands = ['init', 'push', 'pull', 'status', 'list', 'verify', 'ping', 'config', 'QOTD', 'terminate']

    if len(sys.argv) > 1:
        user_input = sys.argv[1]
        
        if not user_input.startswith('-') and user_input not in valid_commands:
            matches = difflib.get_close_matches(user_input, valid_commands, n=1, cutoff=0.6)
            
            if matches:
                closest = matches[0]
                # The Safety Prompt
                choice = input(f"❓ Unrecognized command '{user_input}'. Did you mean '{closest}'? (y/N): ").lower()
                
                if choice == 'y':
                    sys.argv[1] = closest
                else:
                    print("Operation cancelled.")
                    return # Exit the program early
            else:
                print(f"❌ '{user_input}' is not a valid wings-core command. Type 'wings-core --help' for a list.")
                return
            
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
    subparsers.add_parser('QOTD', help="Get a dose of wisdom (Easter Egg)")
    subparsers.add_parser('terminate')
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
    elif args.command == 'qotd': cmd_qotd(args)
    elif args.command == 'terminate': cmd_terminate(args)
    else: parser.print_help()
    
#Run 
if __name__ == "__main__":
    main()