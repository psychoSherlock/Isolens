# IsoLens Architecture

## Overview

IsoLens is a modular malware sandbox. The architecture is divided into several layers within the `core/` directory.

## Component Responsibilities

### `core/interface/`

Handles all user-facing logic, including file uploads and report visualization. Implemented as a Next.js (App Router) web interface.

### `core/gateway/`

The system entry layer that routes API requests to the controller.

### `core/controller/`

The orchestration brain that coordinates the VM lifecycle and analysis workflow, including VirtualBox control via VBoxManage.

### `core/agent/`

Guest-side HTTP service (`isolens_agent.py`) running inside the sandbox VM. Uses only Python stdlib — no pip dependencies required. Exposes an HTTP API on the host-only network adapter for commands from the controller. Features a pluggable collector architecture for Sysmon events, Procmon CSV, network captures, and screenshots. Communicates file transfers via VirtualBox Shared Folder (`SandboxShare/`).

### `core/modules/`

Functional processing layer for parsing logs, extracting IOCs, risk scoring, and parsing VBoxManage outputs.

### `core/observer/`

Monitoring layer that collects raw data from the host perspective (process tracking, network, etc.).

### `core/threatintelligence/`

AI-assisted layer that provides threat classification and natural language summaries.

### `core/storage/`

Persistent storage for databases, samples, logs, and reports.
