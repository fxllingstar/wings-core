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
SERVER_URL = "http://127.0.0.1:5000"
CONFIG_DIR = ".wings"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
IGNORE_DIRS = {'.wings', '__pycache__', '.git'}

# --- App Info ---  Yes is tester is hard coded, sue me>:( 
try:
    APP_VERSION = importlib.metadata.version("wings_core")
except importlib.metadata.PackageNotFoundError:
    APP_VERSION = "0.1.5-dev"
    last_mod_time = os.path.getmtime(__file__)
LAST_UPDATED = datetime.fromtimestamp(last_mod_time).strftime('%m/%d/%Y')
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
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"{session_name}.log")
    
    # Configure logging ooh!
    logging.basicConfig(
        filename=log_file,
        filemode='w', # Overwrite for the current session
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    return logging.getLogger(), log_file



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
        print("Wings-core is already initialized here. HAHA")
        return

    cwd_name = os.path.basename(os.getcwd())
    project_id = input(f"Enter project identifier (default: {cwd_name}): ") or cwd_name
    
    # Register with server (yippee)
    try:
        payload = {"project_id": project_id}
        r = requests.post(f"{SERVER_URL}/init", json=payload,timeout=15)
        if r.status_code in [200, 201]:
            config = {
                "project_id": project_id,
                "local_version": "0.0",
                "server": SERVER_URL,
                "last_hash": calculate_hash()
            }
            save_config(config)
            print(f"Initialized empty wings-core project in {os.getcwd()} NICE!.")
            print(f"Project Identifier: {project_id}")
        else:
            print(f"Server error: {r.text}")
    except requests.exceptions.ConnectionError:
        print("Could not connect to wings-core server. Sad:( ")

def cmd_push(args):
    config = load_config()
    if not config:
        print("Not a wings-core project. Run 'wings-core init' first. nuh uh")
        return

    current_ver = config.get("local_version", "0.0")

    logger, log_path = get_logger("push_session")
    logger.info(f"Starting push process for project: {config['project_id']}")
    
    if args.version:
        new_version = args.version
    else:
        new_version = increment_version(current_ver)

    print(f"Pushing version {new_version}... is it working? Idk why are you asking me")
    
    zip_name = "temp_push_artifact.zip"
    zip_project(zip_name)

    try:
        with open(zip_name, 'rb') as f, open(log_path, 'rb') as l:
            files = {
                'file': f,
                'log': l  # Sending the log file to the server (maybe)
            }
            data = {'project_id': config['project_id'], 'version': new_version}
            
            logger.info(f"Uploading version {new_version} to {config['server']}...")
            r = requests.post(f"{config['server']}/push", data=data, files=files, timeout=30)
            
            # Log the response time
            logger.info(f"Server response received in {r.elapsed.total_seconds()}s")
            if r.elapsed.total_seconds() > 10:
                logger.warning("Server response time is quite long. Something might be wrong with the server or your connection. Server may be overloaded. :(")

        if r.status_code == 200:
            logger.info("Push confirmed successful by server.")
            # ... (save config logic) ...
        else:
            logger.error(f"Server rejected push: {r.text}")
             
    except Exception as e:
        logger.error(f"Critical failure during push: {e}")
    
    try:
        with open(zip_name, 'rb') as f:
            files = {'file': f}
            data = {'project_id': config['project_id'], 'version': new_version}
            r = requests.post(f"{config['server']}/push", data=data, files=files , timeout=30)
        
        if r.status_code == 200:
            config['local_version'] = new_version
            config['last_hash'] = calculate_hash()
            save_config(config)
            print(f"Successfully pushed version {new_version} YOOO LETS GOO")
        else:
            print(f"Failed to push: {r.text}, aw dang it :(")
            
    except Exception as e:
        print(f"Error during push: {e} sad:(")
    finally:
        if os.path.exists(zip_name):
            os.remove(zip_name)



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
            
        r = requests.get(f"{config['server']}/pull", params=params, stream=True, timeout=10)
        
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
        r = requests.get(f"{config['server']}/list", timeout=10, params={'project_id': config['project_id']})
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
        r = requests.get(f"{SERVER_URL}/ping", timeout=5)
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
            r = requests.post(f"{config['server']}/delete", json={'project_id': project_id}, timeout=15)
            if r.status_code == 200:
                print(f"✅ Server Response: {r.text}")
                print("Remote data wiped. You may want to run 'wings-core terminate' locally now. Adios!")
            else:
                print(f"❌ Failed: {r.text}")
        except Exception as e:
            print(f"❌ Could not connect to server: {e}")
    else:
        print("❌ Verification failed. Deletion aborted. Sadlyy")

# --- Main CLI Parser ---

def main():
    valid_commands = ['init', 'push', 'pull', 'status', 'list', 'verify', 'ping', 'config', 'qotd', 'terminate', 'delete-remote', 'logs', 'whoami']

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
    


    subparsers.add_parser('init')
    subparsers.add_parser('status')
    subparsers.add_parser('list')
    subparsers.add_parser('verify')
    subparsers.add_parser('ping')
    subparsers.add_parser('qotd', help="Get a dose of wisdom (Easter Egg)")
    subparsers.add_parser('terminate')
    subparsers.add_parser('delete-remote', help="Wipe project data from the server")
    subparsers.add_parser('whoami', help="Show current user and connection info")

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
    elif args.command == 'whoami': cmd_whoami(args)
    elif args.command == 'verify': cmd_verify(args)
    elif args.command == 'ping': cmd_ping(args)
    elif args.detailed_version: cmd_version(argparse.Namespace(detailed=True))
    elif args.command == 'qotd': cmd_qotd(args)
    elif args.command == 'logs': cmd_logs(args)
    elif args.command == 'terminate': cmd_terminate(args)
    elif args.command == 'delete-remote': cmd_delete_remote(args)
    else: parser.print_help()
    
#Run 
if __name__ == "__main__":
    main()