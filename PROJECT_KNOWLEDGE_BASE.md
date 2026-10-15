# IsoLens: Comprehensive Project Knowledge Base & AI Specification

> **Purpose of this Document:** This document serves as an exhaustive, definitive technical reference designed for autonomous AI agents, security researchers, and developers. It details every architectural layer, technology stack component, virtualization and guest control mechanism, multi-agent AI pipeline, API contract, and operational workflow in the **IsoLens** project.

---

## 1. Executive Summary & Academic Context

* **Project Title:** ISOLENS: Intelligent Dynamic Malware Analysis Sandbox
* **Academic Level:** S6 Mini Project (2025–2026), B.Tech in Computer Science & Engineering (Cyber Security)
* **Institution:** Muthoot Institute of Technology and Science (MITS), affiliated with APJ Abdul Kalam Technological University (KTU), Kerala, India.
* **Core Team:**
  * Athul Prakash N J (`MUT23CC022`)
  * Aaron Paul Biju (`MUT23CC002`)
  * Adithi Asok (`MUT23CC006`)
  * Irfan V S (`MUT23CC035`)
* **Core Problem Statement:** Commercial malware sandboxes (e.g., Cuckoo, Any.Run, Hybrid Analysis, Joe Sandbox) are often resource-heavy, complex to deploy in air-gapped or classroom environments, or closed-source/expensive. IsoLens was engineered as a modular, lightweight, educational automated sandbox that executes suspicious binaries within an isolated virtual machine, captures multi-dimensional telemetry, and uses a specialized multi-agent AI pipeline to generate structured threat intelligence with MITRE ATT&CK mappings.

---

## 2. High-Level System Architecture & End-to-End Workflow

IsoLens is architected under the `core/` directory to enforce strict separation of concerns across system layers:

```
                                    ┌────────────────────────┐
                                    │ Next.js Web Interface  │
                                    │ (React 19 / Tailwind)  │
                                    │ Port: 3000             │
                                    └───────────┬────────────┘
                                                │ Proxied HTTP (/api/*)
                                                ▼
                                    ┌────────────────────────┐
                                    │ FastAPI API Gateway    │
                                    │ (Uvicorn / Port: 6969) │
                                    └───────────┬────────────┘
                                                │
                       ┌────────────────────────┼────────────────────────┐
                       │                        │                        │
                       ▼                        ▼                        ▼
       ┌────────────────────────┐   ┌────────────────────────┐   ┌────────────────────────┐
       │   Sandbox Controller   │   │  Threat Intelligence   │   │    Storage Manager     │
       │  (VBoxManage Wrapper)  │   │   Multi-Agent Copilot  │   │  (Samples, Reports,    │
       │ (sandbox_orchestrator) │   │     (gpt-5-mini)       │   │    Logs, Artifacts)    │
       └───────────┬────────────┘   └────────────────────────┘   └────────────────────────┘
                   │
      ┌────────────┴────────────┐
      │ Host-Only Net (9090)    │ Shared Folder (SandboxShare)
      ▼                         ▼
┌────────────────────────────────────────────────────────┐
│ VirtualBox Sandbox VM ("WindowsSandbox")               │
│ IP: 192.168.56.105 (Port 9090)                         │
│ ┌────────────────────────────────────────────────────┐ │
│ │ isolens_agent.py (In-Guest HTTP Server, Stdlib)    │ │
│ ├────────────────────────────────────────────────────┤ │
│ │ Telemetry Collectors:                              │ │
│ │  • Sysmon (wevtutil XML ETW capture)               │ │
│ │  • Procmon (PML to CSV backing filter)             │ │
│ │  • Screenshots (PowerShell System.Drawing)         │ │
│ │  • Tcpvcon (CLI active socket snapshot)            │ │
│ │  • Handle (Sysinternals handle enumeration)        │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

### Complete End-to-End Execution Sequence

1. **Submission:** User uploads a suspicious binary (`.exe`, `.dll`, `.bat`, etc.) and selects analysis parameters (execution timeout: 10–300s, default 60s; screenshot interval: 2–30s, default 5s).
2. **Archival & Shared Staging:** The gateway stores the original sample into `core/storage/samples/<analysis_id>_<filename>` and copies it to the host-side VirtualBox shared directory `SandboxShare/<filename>`.
3. **Execution Command:** The host orchestrator issues an HTTP `POST /api/execute` request to the in-VM agent at `http://192.168.56.105:9090`.
4. **Guest Initialization & Execution:**
   * Agent clears prior artifacts and cleans Sysmon logs (`wevtutil cl Microsoft-Windows-Sysmon/Operational`) to ensure a zero baseline.
   * Agent launches background collectors: starts `Procmon.exe` with a backing PML file, starts `tshark.exe` on interface 1.
   * Agent launches the sample in an interactive user session via `schtasks /it` (Windows Task Scheduler interactive switch) so GUI windows appear on the desktop and can be captured visually (falling back to `cmd /c start`).
   * Agent starts in-guest periodic screenshot capture via PowerShell + `System.Drawing`.
5. **Parallel Host Observation:**
   * While the agent runs, the host orchestrator starts a concurrent background thread invoking `VBoxManage controlvm WindowsSandbox screenshotpng` every N seconds to capture display frames independently from the host hypervisor side.
6. **Telemetry Collection & Export:**
   * After the timeout period elapses, the guest agent terminates active logging (stops `tshark`, terminates `Procmon`, flushes buffers).
   * It runs all collector plugins: parses Sysmon ETW XML, converts Procmon PML to CSV and summarizes interesting operations, parses PCAP for DNS/HTTP/TCP streams, gathers open handles via `handle64`, and snapshots active sockets via `tcpvcon64`.
   * The agent bundles all JSON summaries, screenshots, and raw logs into a ZIP archive (`results_<samplename>_<timestamp>.zip`) and copies it directly into the mapped shared drive `Z:\` (`SandboxShare/`).
7. **Extraction & Manifest Generation:**
   * Host orchestrator detects the agent status changing to `idle`, retrieves the ZIP from `SandboxShare/`, unpacks it into `core/storage/reports/<analysis_id>/`, merges host screenshots, and writes `analysis_manifest.json`.
8. **Multi-Agent AI Analysis:**
   * The user or system triggers `POST /api/analysis/report/<id>/ai-analyze`.
   * The orchestrator reads all tool outputs and parallel-dispatches them to 6 domain-specific AI agents using GitHub Copilot SDK (`gpt-5-mini`), then synthesizes everything through a master `threat-summarizer` agent into an executive threat intelligence report.
9. **Visualization & PDF Export:**
   * Results (processes, files, registry keys, network connections, screenshots, AI risk score, MITRE ATT&CK techniques, remediation actions) are displayed in the Next.js dashboard and can be exported as a professional PDF report.

---

## 3. Technology Stack & Programming Language Inventory

### Languages Used Across the Repository
* **Python (3.8+ compatible, 3.13 tested):**
  * `core/gateway/`: FastAPI REST Gateway and Pydantic schemas.
  * `core/controller/`: VBoxManage subprocess orchestration and HTTP orchestrator.
  * `core/agent/isolens_agent.py`: Guest HTTP daemon (strict Python standard library, zero dependencies).
  * `core/threatintelligence/`: Multi-agent pipeline via `github-copilot-sdk`.
  * `core/modules/`: VBoxManage text parsers and IOC extractors.
  * `tests/`: Isolated verification test scripts.
* **TypeScript & JavaScript (Node.js 18+):**
  * `core/interface/`: Next.js 16 (App Router), React 19, Tailwind CSS.
  * Client API layer (`src/lib/api.ts`) and PDF report generator (`src/lib/pdf.ts`).
* **C# (.NET Framework 4.0 / 4.8):**
  * `SandboxShare/malware_emulator.cs`: Compiled using `csc.exe` to generate `malware_emulator.exe` for benchmarking sandbox detection.
* **PowerShell:**
  * Guest-side screenshot acquisition (`System.Windows.Forms` + `System.Drawing`).
  * VM provisioning and OpenSSH automation (`SandboxShare/setup_win10.ps1`, `check_vm_status.ps1`).
* **Windows Batch (`.bat`):**
  * `SandboxShare/start_agent.bat`: Boots the guest agent, maps drive `Z:`, and runs Python.
  * `SandboxShare/build_emulator.bat`: Compiles the C# emulator.
* **Bash Shell:**
  * `run.sh`: Service launcher and pre-flight validation.
* **LaTeX:**
  * `Miniproject_Report/`: Formal academic report for KTU university submission.

### Host Dependencies (`requirements.txt`)
* `fastapi==0.111.0`: High-performance asynchronous API framework.
* `uvicorn==0.30.1`: ASGI web server for FastAPI.
* `httpx==0.27.0`: Async HTTP client.
* `github-copilot-sdk==0.1.29`: Official Python SDK for GitHub Copilot agent sessions.

### Interface Dependencies (`core/interface/package.json`)
* `next: 16.1.6`, `react: 19.2.3`, `react-dom: 19.2.3`
* `tailwindcss: 3.4.4`, `postcss: 8.5.6`
* `jspdf: 4.2.0`, `jspdf-autotable: 5.0.7` (PDF report compilation)
* `react-icons: 5.5.0`, `axios: 1.13.5`

---

## 4. Virtual Machine Architecture & Control Plane

### Virtual Machine Configuration Details
* **Hypervisor:** Oracle VM VirtualBox (controlled purely via CLI `VBoxManage`).
* **Default VM Name:** `WindowsSandbox` (legacy docs reference `Windows 7 Sandbox`; live production environment utilizes Windows 10 Home Build 19045 / AtlasOS for enhanced Sysmon 15 compatibility and lower telemetry overhead).
* **Virtual Hardware Allocation:**
  * RAM: 2048 MB – 3072 MB (typically 3 GB).
  * Processors: 2 vCPUs.
  * Disk: 25–40 GB dynamically allocated VDI.
  * Graphics: VBoxSVGA with 128 MB VRAM.
  * Guest Additions: Installed (enables bidirectional clipboard, folder mounting, and `guestproperty` queries).

### Network Topology & Isolation Model
To prevent accidental worm propagation or malware exfiltration onto the host LAN or internet:
1. **Adapter 1 (Host-Only Network):**
   * Interface: `vboxnet0` (typically `192.168.56.0/24`).
   * Host IP: `192.168.56.1`
   * Guest IP: `192.168.56.105`
   * Purpose: Dedicated channel for host-to-guest HTTP API communication on port `9090`.
2. **Adapter 2 / 3 (Optional / Simulated):**
   * Bridged or NAT adapter (can be disabled during untrusted runs).
   * FakeNet-NG / INetSim can be engaged to mock DNS and internet services locally.
3. **File Exchange Mechanism:**
   * VirtualBox Shared Folder named `SandboxShare`.
   * Host Path: `<project_root>/SandboxShare/`
   * Guest Path: Mapped to `Z:\` (`\\VBOXSVR\SandboxShare`).
   * Permissions: Full read/write for sample transfer and results retrieval.

### Hypervisor Controller (`core/controller/vbox_controller.py`)
Encapsulates `VBoxManage` CLI execution with structured error handling and dry-run simulation:
* `list_vms()` / `list_running_vms()`
* `show_vm_info(vm, machinereadable=True)`: Parsed by `core/modules/vbox_output_parser.py`.
* `start_vm(vm, headless=True/False)`
* `poweroff_vm(vm)`, `savestate_vm(vm)`, `pause_vm(vm)`, `resume_vm(vm)`, `reset_vm(vm)`, `shutdown_vm(vm)`
* `snapshot_take(vm, name)`, `snapshot_restore(vm, name)`, `snapshot_restore_current(vm)`
* `get_vm_ip_addresses(vm)`: Queries `/VirtualBox/GuestInfo/Net/*` via Guest Additions.
* `screenshot_vm(vm, output_path)`: Uses `controlvm <vm> screenshotpng <path>` to capture raw PNG display frames directly from hypervisor memory.

---

## 5. In-Guest Agent Architecture (`core/agent/isolens_agent.py`)

The guest agent is a standalone **1,580+ line single-file Python script** specifically designed to operate inside hostile environments without requiring `pip`, C compilers, or third-party packages.

### Critical Engineering Design Decisions
1. **Zero External Dependencies:** Built 100% on Python standard library (`http.server`, `socketserver`, `subprocess`, `xml.etree.ElementTree`, `csv`, `zipfile`, `threading`).
2. **`_NoFQDNHTTPServer` (DNS Hang Prevention):**
   * *Problem:* Standard Python `HTTPServer` invokes `socket.getfqdn()` during `server_bind()`. In isolated sandbox environments with no DNS resolution, this causes reverse-lookup timeouts of 30–60 seconds or permanent thread hangs.
   * *Solution:* A custom subclass overrides `server_bind` to bind directly to `0.0.0.0` without invoking FQDN resolution.
3. **Interactive Session Launch via `schtasks /it`:**
   * *Problem:* Executing processes from an agent running as a service or background process places them in Session 0 (non-interactive). Windows displays, message boxes, and ransom notes are invisible to desktop screen-grabbers.
   * *Solution:* The agent schedules a one-shot task using `schtasks /create /tn IsoLensExec /tr "cmd /c start ... " /it /f` and triggers it via `schtasks /run`. This executes the malware directly inside the active user's interactive desktop session.
4. **Thread-Safe State Machine:**
   * States: `idle` → `executing` → `collecting` → `error`.
   * Execution occurs on a detached worker thread so HTTP status polling remains responsive even during heavy system load.

### Pluggable Collector Subsystem

| Collector | Execution Method & Target | Output File & Extraction Detail |
|---|---|---|
| **SysmonCollector** | `wevtutil qe Microsoft-Windows-Sysmon/Operational /f:xml` | `sysmon_summary.json`: Filters events by process tree. Extracts PID lineage, parent/child relationships (EID 1), outbound connections (EID 3), unsigned DLL loads (EID 7), sensitive file creates (EID 11/15), persistence registry keys (EID 12/13/14), and DNS queries (EID 22). |
| **ProcmonCollector** | Starts `Procmon64.exe /BackingFile procmon.pml`. At collection, calls `/Terminate`, converts PML to CSV via `/SaveAs procmon.csv`, kills process. | `procmon_summary.json`: Parses CSV rows. Filters noise from background Windows processes to focus on sample PID activity: notable file modifications (`Write`, `Delete`, `Create`), registry writes (`SetValue`, `CreateKey`), and process creations. |
| **ScreenshotCollector** | Background thread invoking PowerShell snippet with `System.Windows.Forms` & `System.Drawing`. | Periodic PNG captures saved in `artifacts/screenshots/screenshot_XXX_timestamp.png`. Captures popup alerts, GUI ransom notes, and command prompt windows. |
| **TcpvconCollector** | Executes `C:\IsoLens\tools\tcpvcon64.exe -accepteula -a -c`. | `tcpvcon_snapshot.csv`: Instantaneous snapshot of all active/listening TCP and UDP endpoints, filtered for sample process ownership. |
| **HandleCollector** | Executes `C:\IsoLens\tools\handle64.exe -accepteula -p <sample>`. | `handle_snapshot.txt`: Enumerates open mutexes (e.g. single-instance markers), named pipes, sensitive registry keys, and file locks. |

---

## 6. Multi-Agent AI Threat Intelligence Pipeline (`core/threatintelligence/`)

IsoLens implements a specialized **hierarchical multi-agent AI architecture** using the official `github-copilot-sdk`.

### Design Rationale: Per-Tool Specialized Analysts
Rather than sending entire megabytes of raw execution logs to a single monolithic LLM prompt (which triggers token context overflows, high inference latency, and hallucinated findings), IsoLens shards telemetry across specialized analyst agents:

```
Raw Telemetry Artifacts
  ├── Sysmon XML/JSON   ─────────► [ sysmon-analyzer ]    ─► Structured JSON Verdict
  ├── Procmon CSV/JSON  ─────────► [ procmon-analyzer ]   ─► Structured JSON Verdict
  ├── Network PCAP/JSON ─────────► [ network-analyzer ]   ─► Structured JSON Verdict
  ├── Open Handles      ─────────► [ handle-analyzer ]    ─► Structured JSON Verdict
  ├── Active Sockets    ─────────► [ tcpvcon-analyzer ]   ─► Structured JSON Verdict
  └── Exec Metadata     ─────────► [ metadata-analyzer ]  ─► Structured JSON Verdict
                                           │
                                           ▼ (Consolidated JSON Inputs)
                                ┌──────────────────────┐
                                │  threat-summarizer   │
                                └──────────┬───────────┘
                                           ▼
                                 Final Threat Report:
                           • Consolidated Risk Score (0-100)
                           • Threat Level (Critical/High/Med/Low)
                           • Malware Family & Platform Classification
                           • MITRE ATT&CK Technique Mappings
                           • Deduplicated IOC Catalog
                           • Actionable Remediation Steps
```

### Model Enforcement: `gpt-5-mini`
All agents are strictly pinned to the `gpt-5-mini` model in `core/threatintelligence/copilot_service.py` (`REQUIRED_MODEL = "gpt-5-mini"`). This ensures:
1. Low latency: Full 7-agent pipeline completes in ~25–35 seconds.
2. Low token footprint: Tool inputs are capped at ~6,000 characters per tool payload.
3. Strict JSON conformance: Enforced with programmatic validation and fallback extractors (`_clean_json_response`).

### Agent Profiles & Schema Contract

#### Per-Tool Analyst JSON Schema:
```json
{
  "tool": "sysmon|procmon|network|handle|tcpvcon|metadata",
  "verdict": "malicious|suspicious|benign|inconclusive",
  "confidence": 85,
  "findings": [
    {
      "severity": "high|medium|low",
      "indicator": "Spawned powershell.exe with encoded command",
      "description": "Suspicious LOLBin execution for defense evasion"
    }
  ],
  "iocs": [
    {
      "type": "process|file|registry|network|dns|url|mutex|hash",
      "value": "powershell.exe -enc ..."
    }
  ],
  "summary": "Brief synthesis of findings."
}
```

#### Final Threat Summarizer Output Schema:
* **`risk_score`**: Normalized integer between 0 and 100.
  * 0–15: Benign / Clean
  * 16–35: Low Risk / Potentially Unwanted Program (PUP)
  * 36–60: Medium Risk / Confirmed Suspicious Behavior
  * 61–80: High Risk / Active Malicious Capabilities
  * 81–100: Critical / Destructive or Exfiltrating Malware
* **`classification`**: `malware_type` (ransomware, trojan, infostealer, worm, backdoor, etc.), `malware_family`, `platform`.
* **`mitre_attack`**: Array of matched tactics and techniques with IDs (e.g., `T1059.001 - PowerShell`, `T1547.001 - Registry Run Keys`).
* **`recommendations`**: Prioritized containment and remediation steps.

---

## 7. API Gateway Complete Specification (`core/gateway/`)

The gateway runs on **port 6969** (`http://0.0.0.0:6969`) powered by FastAPI and Uvicorn. CORS is enabled globally for local frontends.

### Route Modules

#### 1. System Endpoints (`system_routes.py`)
* `GET /api/ping`: Returns `{"status": "ok", "data": {"message": "pong"}}`.
* `GET /api/version`: Returns current gateway API version string.

#### 2. Virtual Machine Management (`controller_routes.py`)
* `GET /api/vms`: Lists all VirtualBox VMs registered on host.
* `GET /api/vms/running`: Lists currently running VMs.
* `GET /api/vms/ip?vm=<name>`: Enumerates IP addresses via Guest Additions properties.
* `POST /api/vms/info`: Returns parsed hardware and state details (`memory_mb`, `cpus`, `vram_mb`, `chipset`, `graphics_controller`, `vrde`, `network`).
* `POST /api/vms/start`: Powers on VM (`{"vm": "WindowsSandbox", "headless": true}`).
* `POST /api/vms/poweroff`: Immediate VM power off.
* `POST /api/vms/savestate`, `pause`, `resume`, `reset`, `shutdown`: Hypervisor execution control.
* `POST /api/vms/snapshot/take`: Creates named snapshot.
* `POST /api/vms/snapshot/restore`: Restores named snapshot.
* `POST /api/vms/snapshot/restore-current`: Reverts VM to the current active snapshot.
* `GET /api/vms/screen?vm=<name>`: Captures an immediate live PNG screenshot from the hypervisor display and serves with `Cache-Control: no-cache`.

#### 3. Sandbox Analysis Pipeline (`analysis_routes.py`)
* `POST /api/analysis/submit`: Multipart file upload (`file`, `timeout`, `screenshot_interval`). Triggers full asynchronous orchestration run.
* `GET /api/analysis/status`: Returns state of current or most recent analysis run.
* `POST /api/analysis/check-vm`: Verifies guest agent reachability (`192.168.56.105:9090`), checks collector availability, and confirms host shared folder access.
* `POST /api/analysis/cleanup`: Instructs guest agent to purge temporary artifacts.
* `GET /api/analysis/agent/status`, `/collectors`, `/artifacts`: Reverse-proxy endpoints querying guest agent health and collectors.
* `GET /api/analysis/report/{id}/screenshots`: Lists screenshot filenames for an analysis.
* `GET /api/analysis/report/{id}/file/{path}`: Serves individual artifacts (logs, images, summaries) with directory traversal protection.
* `GET /api/analysis/reports/list`: Enumerate all historical analyses that have a valid `analysis_manifest.json`.
* `DELETE /api/analysis/reports/clear`: Deletes all historical report folders and temporary shared archives.
* `GET /api/analysis/report/{id}/data`: Aggregates all JSON summaries, handle logs, TCPVcon tables, and screenshot lists into one combined payload for frontend rendering.
* `POST /api/analysis/report/{id}/ai-analyze`: Dispatches collector data to the multi-agent AI pipeline.
* `GET /api/analysis/report/{id}/ai-report`: Retrieves stored `ai_report.json`.
* `GET /api/analysis/report/{id}/ai-progress`: Returns real-time agent execution progress (`progress.json`).

---

## 8. Frontend Web Dashboard (`core/interface/`)

The web interface is a responsive Material-themed Next.js 16 application running on **port 3000**.

### Routing & Architecture
* **API Proxying:** `next.config.ts` defines rewrites routing `/api/:path*` to `http://localhost:6969/api/:path*`, allowing browser components to use relative URLs and avoid CORS issues.
* **Layout Structure (`layout.tsx`):** Persistent Left Sidebar (`Sidebar.tsx`) and Top Navigation Header (`Header.tsx`) with dark mode aesthetics and violet accent highlights.
* **Core Application Routes:**
  1. `/scan` (`src/app/scan/page.tsx`): Main upload portal. Supports drag-and-drop file upload, timeout slider, and screenshot interval configuration. Provides live status polling during execution.
  2. `/reports` (`src/app/reports/page.tsx`): Comprehensive analysis view. Displays:
     * High-level threat level badges and risk score meter.
     * Tabbed telemetry viewers: Sysmon Process Tree, File System Operations, Registry Modifications, Network Traffic & DNS, Open Handles, Active Sockets.
     * Screenshot Gallery: Visual carousel of VM displays captured during analysis.
     * AI Intelligence Tab: Interactive multi-agent pipeline status, executive summary, MITRE ATT&CK technique breakdown, deduplicated IOC table, and remediation advice.
     * Export Action: Direct PDF download generated via `jspdf` and `jspdf-autotable`.
  3. `/scan-history` (`src/app/scan-history/page.tsx`): Historical scan table displaying past analyses, sample hashes, verdicts, and date stamps.
  4. `/settings` (`src/app/settings/page.tsx`): System diagnostics and configuration. Displays gateway version, VM status, live hypervisor display preview, and agent reachability checks.
  5. `/help-support` (`src/app/help-support/page.tsx`): Troubleshooting guide, Sysinternals tool documentation, and FAQ.
  *(Note: A standalone `/sandbox` page existed in early prototypes but was cleanly consolidated into `/settings` and `/scan` in commit `4f50954` to eliminate UI redundancy).*

---

## 9. Malware Simulation & Validation Assets

To test and benchmark the sandbox without deploying live zero-day weaponized exploits, the repository includes customized malware emulators:

### 1. C# Malware Emulator (`SandboxShare/malware_emulator.cs`)
Simulates 56 distinct malicious behaviors across 6 operational phases:
* **Phase 1 (Filesystem):** Drops fake PE stub (`dropped_payload.bin`), writes hidden C2 config (`.hidden_c2_config.dat`), enumerates sensitive directories (`Desktop`, `Documents`, `System32\config`), drops batch scripts, and copies self as `svchost_update.exe`.
* **Phase 2 (Registry):** Writes `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` persistence keys.
* **Phase 3 (Network):** Performs DNS resolutions, HTTP GET requests, raw TCP socket connections, and UDP beacons.
* **Phase 4 (Process Spawning):** Spawns reconnaissance utilities (`whoami`, `ipconfig`, `netstat`, `systeminfo`, `tasklist`, `net user`, `arp`, `route`, `wmic`).
* **Phase 5 (Evasion):** Executes VM artifact detection, hypervisor keyword scanning, and uptime checks.
* **Phase 6 (Exfiltration):** Base64-encodes simulated credentials and performs HTTP POST transmission.

### 2. Empirical Benchmark Results (`docs/RESULTS.md`)
Tested across 50 diverse malware samples in an isolated environment:
* **Detection Accuracy:** 94% (47 of 50 samples detected and classified correctly).
* **Breakdown by Category:** Trojans (100%), Spyware (100%), Worms (100%), Ransomware (91.7%), Backdoors (80%).
* **True Positive Rate:** 94% (+38% improvement over static signature analysis alone).
* **False Positive Rate:** 4% (-67% reduction compared to static analysis).
* **Average Total Analysis Time:** 3 minutes 45 seconds (including VM run + multi-agent AI).

---

## 10. Current Status, Environment Nuances, & Troubleshooting Guide

### Python Runtime & Virtual Environment Notice
* **Host Operating System:** Linux (Kali Linux `6.18.x-amd64`).
* **System Python vs. Venv Python:**
  * System `/usr/bin/python3` is currently Python 3.14 on this Kali environment.
  * The project virtual environment (`.venv/`) was initially bootstrapped with **Python 3.13** (`.venv/lib/python3.13/site-packages`).
  * If executing scripts manually outside `./run.sh`, ensure you invoke `python3.13` with `PYTHONPATH=.venv/lib/python3.13/site-packages` or execute `.venv/bin/python` directly to ensure `fastapi`, `uvicorn`, and `github-copilot-sdk` (`copilot`) are loaded correctly.

### Standalone Test Suite (`tests/`)
IsoLens strictly adheres to an isolated test-driven methodology with numbered standalone scripts:
* `TEST_06_vbox_output_parser.py`: Tests parsing of `VBoxManage` machinereadable stdout.
* `TEST_07_agent_core.py`: Tests agent collector loading and JSON serialization.
* `TEST_08_openssh_script_exists.py`: Verifies SSH deployment scripts.
* `TEST_09_vm_ip.py`: Validates Guest Additions IP parsing.
* `TEST_10_interface_config.py`: Verifies Next.js rewrite rules.
* `TEST_11_orchestrator.py` & `TEST_11_reports_page_structure.py`: Validates orchestrator lifecycle.
* `TEST_12_agent_integrity.py` & `TEST_12_analysis_routes_imports.py`: Validates agent imports.
* `TEST_13_screenshot_features.py`: Tests periodic screenshot capture mechanisms.
* `TEST_16_threatintel_copilot_setup.py`: Verifies Copilot SDK setup.
* `TEST_17_threat_agent_catalog.py`: Verifies all 7 Copilot prompt schemas.
* `TEST_18_threat_analyzer_structure.py`: Validates report loading logic.
* `TEST_19_ai_analysis_api_wiring.py`: Validates AI analysis endpoints on FastAPI router.
*(Note: `TEST_14` and `TEST_15` check for legacy `src/app/sandbox/page.tsx` which was consolidated into other routes in commit `4f50954`).*

### How to Run the Platform
1. **Start Full Stack:**
   ```bash
   ./run.sh
   ```
   * Starts FastAPI Gateway on `http://localhost:6969` (logs to `gateway.log`).
   * Starts Next.js interface on `http://localhost:3000` (logs to `interface.log`).
   * Checks agent connectivity to `192.168.56.105:9090`.
2. **Stop Full Stack:**
   ```bash
   ./run.sh stop
   ```
3. **Guest Agent Boot inside VM:**
   * Double-click `SandboxShare\start_agent.bat` or run:
     ```cmd
     python C:\IsoLens\agent\isolens_agent.py --host 0.0.0.0 --port 9090 --share Z: --workdir C:\IsoLens
     ```

---

## 11. Quick Summary Matrix for Autonomous AIs

| Dimension | Specification |
|---|---|
| **Architecture Paradigm** | Modular host controller + in-VM lightweight agent + multi-agent AI |
| **Backend Framework** | FastAPI 0.111.0 / Uvicorn (Port 6969) |
| **Frontend Framework** | Next.js 16.1.6 / React 19.2.3 / Tailwind CSS (Port 3000) |
| **Virtualization** | Oracle VirtualBox via CLI `VBoxManage` |
| **Default VM Name & IP** | `WindowsSandbox` @ `192.168.56.105:9090` (Host-Only Network) |
| **File Sharing Bridge** | VirtualBox Shared Folder `SandboxShare` ↔ Guest `Z:\` |
| **In-Guest Agent** | `core/agent/isolens_agent.py` (Python stdlib only, no pip required) |
| **Interactive Launch** | `schtasks /it` inside active user GUI session |
| **In-Guest Collectors** | Sysmon (ETW XML), Procmon (CSV), tshark (PCAP), Screenshot (PowerShell), Tcpvcon, Handle |
| **AI Framework & Model** | `github-copilot-sdk` pinned strictly to `gpt-5-mini` |
| **AI Agent Topology** | 6 Per-Tool Analysts + 1 Consolidated Threat Summarizer |
| **AI Output Contract** | Strict JSON with Risk Score (0-100), MITRE ATT&CK, IOCs, and Remediation |
| **Source of Truth Rule** | `AGENTS.md` is canonical; synchronized via `scripts/sync_ai_docs.py` |

---
*End of Knowledge Base Reference Document.*
