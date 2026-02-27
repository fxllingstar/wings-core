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


#Imports
import difflib
import getpass
import argparse
import zipfile
import logging
import sys
import os
import json
import requests
import shutil
import hashlib
import importlib.metadata
from datetime import datetime



# --- Configuration --- ooh shiny
DEFAULT_SERVER = "http://127.0.0.1:5000"  # Fallback if no server is set
CONFIG_DIR = ".wings"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
IGNORE_DIRS = {'.wings', '__pycache__', '.git', 'node_modules', '.venv'} # Added a few more common ignores

def get_active_server():
    """Returns the server URL from config, or the default if not found."""
    config = load_config()
    if config and config.get('server'):
        return config.get('server').rstrip('/')
    return DEFAULT_SERVER
# --- App Info ---  Yes is tester is hard coded, sue me>:( 
try:
    # Note: Use the name as defined in your setup.py (usually 'wings-core')
    APP_VERSION = importlib.metadata.version("wings-core")
except importlib.metadata.PackageNotFoundError:
    APP_VERSION = "1.0.0-release" # Fallback version if not installed properly

if getattr(sys, 'frozen', False):
    # If running as an EXE, get the time of the EXE file itself
    last_mod_time = os.path.getmtime(sys.executable)
else:
    # If running as a script, get the time of the .py file
    try:
        last_mod_time = os.path.getmtime(__file__)
    except FileNotFoundError:
        last_mod_time = 0 # Fallback

LAST_UPDATED = datetime.fromtimestamp(last_mod_time).strftime('%m/%d/%Y')

IS_TESTER = False
IS_USER = True
#
#True for yay false for nay :)
def get_auth_headers(config):
    token = config.get("token")
    if not token:
        raise PermissionError("Not authenticated. Run init first.")
    return {"Authorization": f"Bearer {token}"}

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
    warned = False

    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for name in files:
            filepath = os.path.join(root, name)
            try:
                with open(filepath, "rb") as f:
                    while chunk := f.read(4096):
                        sha.update(chunk)
            except OSError as e:
                if not warned:
                    print("⚠ Warning: Some files could not be read during hashing.")
                    warned = True

    return sha.hexdigest()

def zip_project(output_filename):
    """Zips the current directory excluding IGNORE_DIRS."""
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Filter ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, '.')
                zipf.write(filepath, arcname)

    return output_filename

def get_logger(session_name="wings"):
    log_dir = os.path.join(CONFIG_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{session_name}.log")

    logger = logging.getLogger(session_name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger, log_file


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
        print("Wings-core is already initialized here. HAHAHA")
        return

    cwd_name = os.path.basename(os.getcwd())
    project_id = input(f"Enter project identifier (default: {cwd_name}): ") or cwd_name

    print("🔐 Authentication Required")
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    try:
        # Step 1: Login
        login_response = requests.post(
            f"{get_active_server()}/login",
            json={"username": username, "password": password},
            timeout=10
        )

        if login_response.status_code != 200:
            print("❌ Authentication failed.")
            return

        token = login_response.json().get("token")
        if not token:
            print("❌ Invalid login response.")
            return

        # Step 2: Register project
        r = requests.post(
            f"{get_active_server()}/init",
            json={"project_id": project_id},
            timeout=15
        )

        if r.status_code in [200, 201]:
            config = {
                "project_id": project_id,
                "local_version": "0.0",
                "server": get_active_server(),
                "last_hash": calculate_hash(),
                "token": token
            }

            save_config(config)

            print(f" Project initialized and authenticated. YAYYY")
            print(f"Project Identifier: {project_id}")

        else:
            print(f"Server error: {r.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e} AWH:(")

def get_auth_headers(config, require_auth=False):
    token = config.get('token')

    if require_auth and not token:
        raise PermissionError("You are not logged in. Run 'wings-core login' first.")

    if token:
        return {"Authorization": f"Bearer {token}"}

    return {}


def cmd_push(args):
    config = load_config()
    
    if not config:
        print("❌ Not a wings-core project.")
        return

    current_ver = config.get("local_version", "0.0")
    new_version = args.version if args.version else increment_version(current_ver)

    logger, log_path = get_logger("push_session")

    logger.info("==== PUSH SESSION STARTED ====")
    logger.info(f"Project ID: {config['project_id']}")
    logger.info(f"Local Version: {current_ver}")
    logger.info(f"New Version: {new_version}")
    logger.info(f"Server: {config['server']}")
    logger.info(f"User: {getpass.getuser()}")

    zip_name = "temp_push_artifact.zip"

    try:
        logger.info("Zipping project...")
        zip_project(zip_name)
        logger.info("Zip completed successfully.")

        logger.info("Calculating hash...")
        current_hash = calculate_hash()
        logger.info(f"Current Hash: {current_hash}")

        try:
             headers = get_auth_headers(config)
        except PermissionError as e:
            print(f"❌ {e}")
            logger.error("Push aborted: user not authenticated.")
            return

        logger.info("Opening files for upload...")

        with open(zip_name, 'rb') as f:
            files = {
                'file': (f"{new_version}.zip", f)
            }
            data = {
                'project_id': config['project_id'],
                'version': new_version
            }

            logger.info("Sending POST request to server...")
            r = requests.post(
                f"{config['server']}/push",
                data=data,
                files=files,
                headers=headers,
                timeout=30
            )

        logger.info(f"Server Response Code: {r.status_code}")
        logger.info(f"Server Response Text: {r.text}")

        if r.status_code == 200:
            config['local_version'] = new_version
            config['last_hash'] = current_hash
            save_config(config)

            logger.info("Push successful. Config updated.")
            print(f"✅ Successfully pushed version {new_version}!")
        elif r.status_code == 403:
            logger.warning("Server rejected authentication (403).")
            print("❌ Unauthorized! Please run 'wings-core login' first.")
        else:
            logger.error("Push failed.")
            print(f"❌ Failed to push: {r.text}")

    except Exception as e:
        logger.exception("Exception occurred during push.")
        print(f"❌ Error during push: {e}")

    finally:
        if os.path.exists(zip_name):
            os.remove(zip_name)
            logger.info("Temporary zip file removed.")

        logger.info("==== PUSH SESSION ENDED ====")
        logging.shutdown()


def cmd_whoami(args):
    config = load_config()
    current_user = getpass.getuser()
    
    # 1. Identity Header
    print("\n" + "═" * 30)
    print(f"WINGS-CORE IDENTITY")
    print("═" * 30)
    
    # 2. User Info
    print(f"Current User   : {current_user}")
    
    # 3. Connection Info
    if config:
        print(f"Connected To   : {config.get('server', 'Not set')}")
        print(f"Project ID     : {config.get('project_id', 'None')}")
        
        # 4. Token Status (Future-proofed)
        token = config.get('token')
        if token:
            # We hide the full token for security, showing only the first 4 chars
            masked_token = f"{token[:4]}****" 
            print(f"Token Status   : ✅ Active ({masked_token})")
        else:
            print(f"Token Status   : ❌ No Token (Not Authenticated)")
    else:
        print(f"Server Status  : ⚠️  Not in a wings project folder.")
        print(f"Token Status   : N/A")
    
    print("═" * 30 + "\n")



def cmd_logs(args):
    config = load_config()
    if not config:
        print("❌ Not a wings-core project.")
        return

    version = args.version or "latest"
    print(f"📂 Fetching logs for {config['project_id']} (Version: {version})...")

    try:
        params = {'project_id': config['project_id'], 'version': version}
        r = requests.get(f"{config['server']}/logs", params=params, timeout=10)

        if r.status_code == 200:
            print("\n--- SERVER LOG START ---")
            print(r.text)
            print("--- SERVER LOG END ---\n")
        else:
            print(f"❌ Could not find logs for this version: {r.text}")
    except Exception as e:
        print(f"❌ Error fetching logs: {e}")



def cmd_pull(args):
    config = load_config()
    if not config:
        print("Not a wings-core project. INIT FIRST HUMAN >:(")
        return
    
    current_hash = calculate_hash()
    if current_hash != config.get('last_hash'):
        print("❌ Pull aborted: You have local changes.")
        print("Run 'wings-core push' or restore your files before pulling. Safety First!")
        return

    project_id = config['project_id']
    target_version = args.version 
    
    print(f"Pulling {'latest' if not target_version else target_version}...")
    
    try:
        params = {'project_id': project_id}
        if target_version:
            params['version'] = target_version
            
        try:
            headers = get_auth_headers(config, require_auth=True)
        except PermissionError as e:
            print(f"❌ {e}")
            return

        r = requests.post(f"{config['server']}/delete", 
                         json={'project_id': project_id}, 
                         headers=headers, 
                         timeout=15)
        
        if r.status_code != 200:
            print(f"Failed to delete project: {r.text}")
            return
        
        r = requests.get(f"{config['server']}/pull", params=params, headers=headers, stream=True, timeout=10)
        
        if r.status_code == 200:
            zip_name = "temp_pull.zip"
            with open(zip_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            shutil.unpack_archive(zip_name, '.')
            os.remove(zip_name)
            
            status_r = requests.get(f"{config['server']}/status", timeout=10, params={'project_id': project_id})
            if status_r.status_code == 200:
                remote_ver = status_r.json()['remote_version']
                config['local_version'] = target_version if target_version else remote_ver
                config['last_hash'] = calculate_hash()
                save_config(config)
            
            print("Pull complete. OOHH SHINY NEW FILES")
        else:
            print(f"Failed to pull: {r.text}, Awh:( no shiny new files")
    except Exception as e:
        print(f"Error: {e}")

def cmd_status(args):
    config = load_config()
    if not config:
        print("Not a wings-core project. INIT FIRST >:(")
        return
    
    # Check remote
    try:
        r = requests.get(
            f"{config['server']}/status", 
            params={'project_id': config['project_id']}, 
            timeout=10
        )
        remote_ver = r.json().get('remote_version', 'Unknown')
    except (requests.exceptions.RequestException, ValueError):
        remote_ver = "Unreachable"

    # Check sync status
    local_ver = config.get('local_version', '0.0')
    current_hash = calculate_hash()
    
    file_count = 0
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        file_count += len(files)
    
    sync_status = "Synced"
    if local_ver != remote_ver:
        sync_status = "Out of sync (Version mismatch) something is not right here :("
    elif current_hash != config.get('last_hash'):
        sync_status = "Out of sync (Local changes) Something is not right here too :("

    print(f"Project: {config['project_id']}")
    print(f"Local version: {local_ver}")
    print(f"Remote version: {remote_ver}")
    print(f"Status: {sync_status}")
    print(f"Total Files: {file_count}")


def cmd_list(args):
    config = load_config()
    if not config:
        print("Not a wings-core project. INIT FIRSTTTT!")
        return
    
    try:
        try:
            headers = get_auth_headers(config, require_auth=True)
        except PermissionError as e:
            print(f"❌ {e}")
            return
        
        r = requests.get(f"{config['server']}/list", 
                         params={'project_id': config['project_id']}, 
                         headers=headers, 
                         timeout=15)
        if r.status_code == 200:
            versions = r.json().get('versions', [])
            print("Available versions on server:")
            for v in versions:
                print(f" - {v}")
        else:
            print("Could not fetch list. :(")
    except requests.exceptions.RequestException:
        print("Server unreachable. Awh dang it :(")

def cmd_verify(args):
    config = load_config()
    if not config:
        print("Not a wings-core project.")
        return
    
    current = calculate_hash()
    stored = config.get('last_hash')
    
    if current == stored:
        print("Integrity Verified: Local state matches last known snapshot. Yippee!")
    else:
        print("Integrity Warning: Local files have changed since last operation. Pay attention plz >:(")

def cmd_ping(args):
    try:
        r = requests.get(f"{get_active_server()}/ping", timeout=5)
        if r.status_code == 200:
            print("Pong! Server is reachable.") #Awh:(
        else:
            print(f"Server responded with {r.status_code}")
    except requests.exceptions.RequestException:
        print("Ping failed. Server is unreachable.")

def cmd_terminate(args):
    config = load_config()
    if not config:
        print("This project is currently not tracked by wings-core. Nuh uh")
        return

    print(f"⚠️  WARNING: You are about to terminate tracking for project: {config['project_id']}")
    print("This will delete all metadata. You will NOT be able to push or pull anymore unless you re-initialize. READ. >:(")
    confirm = input("Are you absolutely sure? (y/n): ").lower()

    if confirm == 'y':
        try:
            if os.path.exists(CONFIG_DIR):
                shutil.rmtree(CONFIG_DIR)
                print(f"✅ Success: Tracking terminated. '{config['project_id']}' is now just a regular folder. Byee, wings-core is outa heree")
            else:
                print("No metadata folder found, but config was loaded. Clean-up may be required. BRING THE VACUUM CLEANERR")
        except Exception as e:
            print(f"❌ Error during termination: {e} Wings-core did not leave :)")
    else:
        print("\n🛡️  Termination aborted. Your project is still being tracked.")
        print("Nothing was deleted. YAY!")

def cmd_login(args):
    config = load_config()
    if not config:
        print("❌ Please run 'wings-core init' first.")
        return

    print("🔑 Wings-Core Authentication")
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    try:
        r = requests.post(
            f"{config['server']}/login",
            json={"username": username, "password": password},
            timeout=10
        )

        if r.status_code == 200:
            try:
                data = r.json()
            except ValueError:
                print("❌ Server returned invalid JSON.")
                return

            token = data.get('token')

            if not token:
                print("❌ Login failed: No token received.")
                return

            config['token'] = token
            save_config(config)
            print("✅ Login successful! Token saved securely.")

        else:
            try:
                error = r.json().get('error', r.text)
            except ValueError:
                error = r.text

            print(f"❌ Login failed: {error}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to authentication server: {e}")

def cmd_set_server(args):
    config = load_config()
    if not config:
        print("❌ Not a wings-core project.")
        return

    new_url = args.url.strip().rstrip("/")
    if not new_url.startswith(("http://", "https://")):
        print("❌ Invalid URL. Use http:// or https://")
        return

    print(f"📡 Verifying server at {new_url}...")
    try:
        # We try to hit the /ping endpoint we made earlier
        r = requests.get(f"{new_url}/ping", timeout=5)
        if r.status_code == 200 and "wings" in r.text.lower():
            config['server'] = new_url
            save_config(config)
            print(f"✅ Success! Server address updated to {new_url}")
        else:
            print("⚠️  Warning: The server responded, but it doesn't look like a Wings server.")
            confirm = input("Save anyway? (y/N): ").lower()
            if confirm == 'y':
                config['server'] = new_url
                save_config(config)
                print("✅ Address saved.")
    except Exception:
        print("❌ Could not reach the server. Is it running?")
        print("Address NOT changed.")

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

def cmd_delete_remote(args):
    config = load_config()
    if not config:
        print("❌ Not a wings-core project.")
        return

    project_id = config['project_id']
    
    # Extra-strength confirmation
    print(f"💣 CRITICAL WARNING: This will permanently delete ALL versions of '{project_id}' from the server.")
    print("This action CANNOT be undone. BOOM")
    
    # Verification challenge
    verify = input(f"Type the project name '{project_id}' to confirm deletion: ")
    
    if verify == project_id:
        try:
            headers = get_auth_headers(config, require_auth=True)
            r = requests.post(f"{config['server']}/delete", 
                             json={'project_id': project_id}, 
                             headers=headers, 
                             timeout=15)
            
            if r.status_code == 200:
                print(f"✅ Server Response: {r.text}")
                print("Remote data wiped. You may want to run 'wings-core terminate' locally now. Adios!")
            else:
                print(f"❌ Failed: {r.text}")
        except PermissionError as e:
            print(f"❌ {e}")
        except Exception as e:
            print(f"❌ Could not connect to server: {e}")
    else:
        print("❌ Verification failed. Deletion aborted. Sadlyy")

# --- Main CLI Parser ---

def main():
    valid_commands = ['init', 'push', 'pull', 'status', 'list', 'verify', 'ping', 'config', 'qotd', 'terminate', 'delete-remote', 'logs', 'whoami', 'login', 'set-server']

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
    logs_parser = subparsers.add_parser('logs', help="Fetch process logs from the server")
    logs_parser.add_argument('-v', '--version', dest='version', help="Fetch logs for a specific version")
    pull_parser = subparsers.add_parser('pull')
    pull_parser.add_argument('-v', dest='version', help="Specify version manually")
    

    server_parser = subparsers.add_parser('set-server', help="Change the server URL for this project")
    server_parser.add_argument('url', help="The new server URL (e.g., http://1.2.3.4:5000)")
    subparsers.add_parser('init')
    subparsers.add_parser('status')
    subparsers.add_parser('login', help="Authenticate with the server")
    subparsers.add_parser('list')
    subparsers.add_parser('verify')
    subparsers.add_parser('ping')
    subparsers.add_parser('qotd', help="Get a dose of wisdom (Easter Egg)")
    subparsers.add_parser('terminate')
    subparsers.add_parser('delete-remote', help="Wipe project data from the server")
    subparsers.add_parser('whoami', help="Show current user and connection info")


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
    elif args.command == 'whoami': cmd_whoami(args)
    elif args.command == 'set-server': cmd_set_server(args)
    elif args.command == 'verify': cmd_verify(args)
    elif args.command == 'ping': cmd_ping(args)
    elif args.command == 'login': cmd_login(args)
    elif args.detailed_version: cmd_version(argparse.Namespace(detailed=True))
    elif args.command == 'qotd': cmd_qotd(args)
    elif args.command == 'logs': cmd_logs(args)
    elif args.command == 'terminate': cmd_terminate(args)
    elif args.command == 'delete-remote': cmd_delete_remote(args)
    else: parser.print_help()
    

#Run 
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Operation cancelled by user. Exiting...")
        if os.path.exists("temp_push_artifact.zip"):
            os.remove("temp_push_artifact.zip")
        sys.exit(0)