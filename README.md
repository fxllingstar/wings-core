# wings-core ꒰ঌ ໒꒱

> Experimental self-hosted state sync & version system

**wings-core** is the foundation of a personal, self-reliant alternative to hosted code platforms. Instead of relying on GitHub or `git push`, this project introduces its own CLI, server, and protocol for pushing and pulling project state — fully under your control.

The goal is not to clone Git feature-for-feature, but to provide a **clean, understandable, and extensible** system for syncing project snapshots between machines and services.

**!!IMPORTANT!!**

wings-core is licensed under the GNU Affero General Public License v3.0.
If you run a modified version of this software as a service, you must provide access to the source code of your modifications.
Read the License file here: https://github.com/fxllingstar/wings-core/blob/main/LICENSE

**ALSO IMPORTANT.**

CLI: Install via pip (or the release file).
Server: Clone the repo and run from the /server directory.

---

## What it does

At a high level, wings-core lets you:

* Push a project’s current state to a server you control
* Pull that state from anywhere else
* Track versions as immutable snapshots
* Verify integrity using hashes
* Integrate cleanly with other tools

Instead of:

```bash
git push
```

You use:

```bash
wings-core push
```
---

## What it is (and is not)

### ✅ It *is*

* A custom client–server sync system
* Snapshot-based versioning
* Designed for self-hosting
* Built to be understandable and hackable

### ❌ It is *not*

* A full Git replacement (yet)
* Focused on branching or merging
* Tied to any third-party platform

---

How to Use Wings-Core
Wings-Core is a self-hosted version control and sync tool. You host your own data, and you control the server.

1. Hosting Your Server (The Backend)
You need to have a server running to store your projects.

Using Docker (Recommended)
Clone this repository.

Run the server:
docker-compose up -d

Your server is now running on http://localhost:5000.

Using Python Directly

1. Navigate to the server folder.
2. Install dependencies: pip install -r requirements.txt
3. Start the server: python server.py


Using the CLI (The Frontend)
Once your server is up, you can use the wings-core tool to manage your files.

Installation

pip install .

Initial Setup

Go to your project folder and run:


# 1. Start a new project
wings-core init

# 2. Point to your personal server
wings-core set-server http://your-server-ip:5000

# 3. Log in (Default: admin / wings)
wings-core login


## Core components

### wings CLI

A command-line tool responsible for:

* Scanning project files
* Creating compressed snapshots
* Communicating with the server
* Reporting status in a machine-readable way

### wings server

A long-running service that:

* Receives push requests
* Stores versioned snapshots
* Serves pull requests
* Maintains simple metadata and indexes

The server acts as the single source of truth — no third-party services involved.


## Current status

🚧 **Getting ready for release.**

Initial goals for V1:

* Snapshot-based push & pull
* Version numbering
* Hash verification
* Token-based authentication

---

## Why this exists

This project exists to explore:

* How versioning systems work internally
* What Git *doesn’t* need to do for many workflows
* How far you can go by owning the entire stack

It is both a **learning project** and a **real system** intended for daily use.

---

## Author

**fxllingstar**
Creator & Head Dev <3

---

## License
AGPLv3
