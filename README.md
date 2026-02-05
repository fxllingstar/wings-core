# wings-core ꒰ঌ ໒꒱

> Experimental self-hosted state sync & version system

**wings-core** is the foundation of a personal, self-reliant alternative to hosted code platforms. Instead of relying on GitHub or `git push`, this project introduces its own CLI, server, and protocol for pushing and pulling project state — fully under your control.

The goal is not to clone Git feature-for-feature, but to provide a **clean, understandable, and extensible** system for syncing project snapshots between machines and services.

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

---
## Project structure (planned)

```
wings-core/
├── cli/            # maksii command-line tool
├── server/         # server daemon
├── protocol/       # protocol specifications
├── docs/           # architecture & design docs
└── README.md
```

---

## Current status

🚧 **Early development / V1 planning**

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

**Maksimilian Seymen**
Creator & Head Dev <3

---

## License
TBD
