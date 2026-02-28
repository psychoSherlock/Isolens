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

Contains:

- **`vbox_controller.py`** — VBoxManage CLI wrapper for VM lifecycle (start, stop, snapshot, etc.)
- **`sandbox_orchestrator.py`** — HTTP + shared-folder orchestrator that coordinates a full analysis run:
  1. Copies the sample to `SandboxShare/` (VirtualBox shared folder)
  2. POSTs to the in-VM agent's `/api/execute` endpoint
  3. Polls `/api/status` until the agent finishes
  4. Retrieves the results zip from `SandboxShare/`
  5. Unpacks into `core/storage/reports/<analysis_id>/`

### `core/agent/`

Guest-side HTTP service (`isolens_agent.py`) running inside the sandbox VM. Uses only Python stdlib — no pip dependencies required. Exposes an HTTP API on the host-only network adapter for commands from the controller. Features a pluggable collector architecture:

- **SysmonCollector** — Exports Sysmon event logs (XML + text) via `wevtutil`
- **ProcmonCollector** — Collects Process Monitor CSV logs
- **NetworkCollector** — Gathers network captures via tshark
- **FakeNetCollector** — Collects FakeNet-NG logs and PCAPs
- **ScreenshotCollector** — Gathers screenshots taken during execution
- **TcpvconCollector** — Snapshots active TCP/UDP connections via `tcpvcon64`
- **HandleCollector** — Snapshots open file/registry handles via `handle64`

Execution flow: clears Sysmon → executes sample via `cmd /c start` (simulated double-click) → waits timeout → runs all collectors → packages results as zip → exports to `SandboxShare/`.

Communicates file transfers via VirtualBox Shared Folder (`SandboxShare/`).

### `core/modules/`

Functional processing layer for parsing logs, extracting IOCs, risk scoring, and parsing VBoxManage outputs.

### `core/observer/`

Monitoring layer that collects raw data from the host perspective (process tracking, network, etc.).

### `core/threatintelligence/`

AI-assisted layer that provides threat classification and natural language summaries.

### `core/storage/`

Persistent storage for databases, samples, logs, and reports.
