wings-core Protocol Specification
Version: 0.1.0

Last Updated: 4/2/2026

Status: Stable / Prototype

1. Overview
wings-core is a lightweight, self-hosted state synchronization and version control system. It utilizes a Client-Server architecture over HTTP/HTTPS to manage project snapshots.

2. API Endpoints (Server-Side)
The server acts as a RESTful API. All endpoints are expected to be reachable via SERVER_URL.

Endpoint, Method, Purpose, Parameters
/ping, GET, Connectivity check, None
/init, POST, Project registration, project_id (JSON)
/push, POST, Upload new snapshot, "project_id, version, file (Multipart)"
/pull, GET, Download snapshot, "project_id, version (Optional)"
/status, GET, Fetch remote version,project_id
/list, GET ,List all versions, project_id

3. Versioning Logic
wings-core follows a specific base-10 minor increment logic:
Minor Increment: Each standard push increases the version by 0.1 (e.g., 1.0 1.1).
Rollover: When the minor version reaches .10, it automatically converts to the next major version (e.g., 1.9 -> 2.0).Manual Overwrite: Users can specify a version (e.g., 1.0.1) which the server will store as a unique entry in the metadata.json.

4. CLI Command Reference
The following commands are implemented in the wings-core executable:

Utility Commands
wings-core: Functional check ("Hello! This is maksii-core").

wings-core -version: Simple version string.

wings-core --version: Detailed version, update date, and tester status.

wings-core --help: Display command list.

wings-core ping: Check server connectivity.

State Management
wings-core init: Initializes local .wings metadata and links to the remote server.

wings-core push: Zips the current project, increments the version, and uploads.

wings-core push -v "x.x": Pushes current state with a forced version number.

wings-core pull: Downloads the latest remote version and extracts it locally.

wings-core pull -v "x.x": Downloads a specific historical version.

wings-core status: Compares local version/hashes against remote metadata.

Debug & Integrity
wings-core list: Shows all versions currently stored on the server.

wings-core verify: Compares current file hashes against the last known local sync hash.

Local File Structure
When initialized, a project will contain a hidden .wings directory:

project-root/
├── .wings/
│   └── config.json      Stores project_id, server_url, and local_version
├── [your_files]
└── ...

Server Storage Structure
The server organizes files by project identifier:



wings_storage/
├── [project_id]/
│   ├── metadata.json    # JSON list of versions and the "latest" pointer
│   ├── 0.1.zip          # Snapshot artifacts
│   └── 0.2.zip