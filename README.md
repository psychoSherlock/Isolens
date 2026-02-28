# Isolens

Isolens Sandbox: Intelligent Dynamic Malware Analysis Sandbox (S6 Mini Project)

![diagram](https://github.com/user-attachments/assets/5d8e39c7-62d1-4694-967f-4b2fc27d2c57)
![diagram_iconed](https://github.com/user-attachments/assets/2803d955-8202-43c2-9eee-59a9521a7da4)

## 📌 Project Overview

IsoLens is a lightweight academic malware sandbox prototype designed to execute suspicious files inside an isolated environment and generate structured behavioral analysis reports.

## 🏗 Project Structure

The system is organized into modular components within the `core/` directory:

- **`core/interface/`**: User-facing UI for uploads and report visualization.
- **`core/gateway/`**: API entry point and request routing.
- **`core/controller/`**: Orchestration brain for VM/container lifecycle.
- **`core/agent/`**: Guest-side service for internal log and output collection.
- **`core/observer/`**: Host-side behavioral monitoring (network, process, etc).
- **`core/modules/`**: Data processing, IOC extraction, and risk scoring.
- **`core/threatintelligence/`**: AI-driven analysis and report augmentation.
- **`core/storage/`**: Persistent storage for samples, logs, and reports.

## 📚 Documentation

Detailed information can be found in the `docs/` folder:
- [**Architecture Overview**](docs/ARCHITECTURE.md): Technical breakdown of the modular system design and component responsibilities.
- [**Project Idea & Concept**](docs/IDEA.md): The core vision, problem statement, and proposed workflow for the automated sandbox.
- [**Sandbox VM Setup**](docs/SANDBOX_VM_SETUP.md): A comprehensive guide on setting up the isolated Windows 7 analysis environment.
- [**UI Components Plan**](docs/UI_COMPONENT_PLAN.md): Complete UI components Plan

## 🛠 Scripts

The `scripts/` directory contains utility scripts for project maintenance:
- `sync_ai_docs.py`: Synchronizes the content of `AGENTS.md` (the source of truth) to all other AI instruction files (`GEMINI.md`, `AI-INSTRUCTIONS.md`, and `.github/copilot-instructions.md`). Run this after any update to `AGENTS.md`.
## Frontend Interface

Below is the Material Themed Dashboard UI:

![Frontend Interface](docs/UI-design.png)

## 👥 Contributors

- [ATHUL PRAKASH NJ](https://github.com/psychoSherlock/)
- [AARON PAUL BIJU](https://github.com/aaronpaulbiju/)
- [ADITHI ASOK](https://github.com/kaalibindhi/)
- [IRFAN VS](https://github.com/Irfanvs/)

## UI Design Concepts

### 1. Scan Page
Main interface to upload files and start malware analysis.

![Scan Page](docs/UI/1.%20Scan%20Page.png)

---

### 2. Reports Page
Displays detailed malware analysis reports and risk levels.

![Reports Page](docs/UI/2.%20Reports%20Page.png)

---

### 3. Scan History Page
Shows previous scans and their statuses.

![Scan History Page](docs/UI/3.%20Scan%20History%20Page.png)

---

### 4. Sandbox Page
Displays VM status and sandbox controls.

![Sandbox Page](docs/UI/4.%20Sandbox%20Page.png)

---

### 5. Settings Page
Allows configuration of system and sandbox parameters.

![Settings Page](docs/UI/5.%20Settings%20Page.png)

---

### 6. Help & Support Page
Provides documentation, FAQ, and troubleshooting help.

![Help & Support Page](docs/UI/6.%20Help%20%26%20Support%20Page.png)
