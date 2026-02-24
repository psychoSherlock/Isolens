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

## 🛠 Scripts

The `scripts/` directory contains utility scripts for project maintenance:
- `sync_ai_docs.py`: Synchronizes the content of `AGENTS.md` (the source of truth) to all other AI instruction files (`GEMINI.md`, `AI-INSTRUCTIONS.md`, and `.github/copilot-instructions.md`). Run this after any update to `AGENTS.md`.

## 👥 Contributors

- [ATHUL PRAKASH NJ](https://github.com/psychoSherlock/)
- [AARON PAUL BIJU](https://github.com/aaronpaulbiju/)
- [ADITHI ASOK](https://github.com/kaalibindhi/)

Testing..