# 📄 AI-INSTRUCTIONS.md

```markdown
# AI Development Instructions – IsoLens

## 📌 Project Overview

IsoLens is a lightweight academic malware sandbox prototype designed to execute suspicious files inside an isolated virtual machine and generate structured behavioral analysis reports.

The system is modular, extensible, and intentionally simple. It is not production-grade and should not be over-engineered.

The architecture is organized under the `core/` directory to maintain logical separation between system layers.

---

# 🏗 Project Structure
```

.
├── core/
│ ├── agent/
│ ├── controller/
│ ├── gateway/
│ ├── interface/
│ ├── modules/
│ ├── observer/
│ ├── storage/
│ │ ├── database/
│ │ ├── logs/
│ │ ├── reports/
│ │ └── samples/
│ └── threatintelligence/
├── docs/
│ ├── ARCHITECTURE.md
│ └── IDEA.md
├── SandboxShare/
├── README.md
├── LICENSE
└── CONTRIBUTING.md

```

---

# 📁 Component Responsibilities

## `core/interface/`
Handles all user-facing logic:
- File upload UI
- Report display
- Risk score visualization
- Screenshot rendering
- Next.js application (App Router) for the web interface
- Safe API JSON parsing (`parseApiResponse`) and proxy resilience for long-running analyses

No VM or analysis logic must exist here.

---

## `core/gateway/`
System entry layer:
- API endpoints
- Request validation
- Routes requests to controller
- Returns results to interface

Acts as the communication bridge between UI and system core.

---

## `core/controller/`
Central workflow coordinator:
- Restore VM snapshot
- Start / stop VM
- Inject file into VM
- Trigger execution
- Call observer
- Collect logs
- Call modules
- Call threatintelligence
- Store results
- **VBoxManage screenshot capture** during analysis execution

This is the orchestration brain of IsoLens.

---

## `core/modules/`
Functional processing layer.

Contains expandable submodules such as:
- Log parsing
- IOC extraction
- Risk scoring
- YARA rule generation
- Pattern detection utilities
- VBoxManage output parsing
- Procmon-to-API sequence translation (Procmon-to-LSTM bridge)
- LSTM sequential behavioral inference
- Network telemetry normalization and OS noise filtering (DNS & HTTP)
- Streaming threat intelligence feed ingestion (`build_threat_intel_db.py`)
- Deterministic network threat intelligence matching (`network_db_matcher.py`)
- Filesystem & registry behavioral normalization, sensitive target extraction, and MITRE mapping (`behavior_normalizer.py`)
- Static YARA pattern matching and capability detection (`yara_scanner.py`)
- GUI application window extraction, Tesseract OCR, and Laya System 1 threat triage (`gui_analyzer.py`)
- Multi-layer deterministic objective risk scoring and explainable breakdown (`risk_scorer.py`)


This layer converts raw monitoring data into structured findings.

This folder is intentionally named "modules" to allow future expansion without structural refactoring.

---

## `core/observer/`
Behavioral monitoring layer:
- Process tracking
- Network monitoring
- File system monitoring
- Registry observation
- Screenshot capture
- Sysmon log extraction

Each monitoring mechanism may exist as its own submodule.

This layer only collects data — it does not interpret it.

---

## `core/agent/`
Guest-side HTTP service (`isolens_agent.py`) that runs inside the sandbox VM.

- Single-file, stdlib-only Python script (no pip dependencies)
- HTTP API on the host-only network for receiving commands from the controller
- Pluggable collector architecture (Sysmon, Procmon, FakeNet, screenshots, handle, tcpvcon)
- Copies samples from VirtualBox shared folder, executes them via `schtasks /it` (interactive session), collects artifacts
- Active screenshot capture using PowerShell + System.Drawing (also captured from host via VBoxManage)
- Packages results as a zip and exports back to SandboxShare for host pickup
- Thread-safe: execution runs in background thread, HTTP stays responsive

API endpoints:
- `GET  /api/status`      — health check and agent state
- `GET  /api/collectors`   — list available collectors
- `GET  /api/artifacts`    — list collected artifact files
- `POST /api/execute`      — execute a sample `{"filename": "...", "timeout": 60, "screenshot_interval": 5}`
- `POST /api/collect`      — run collectors without executing
- `POST /api/cleanup`      — remove all artifacts
- `POST /api/shutdown`     — graceful shutdown

---

## `core/threatintelligence/`
AI-assisted intelligence layer:
- Natural language summaries
- Threat classification
- Risk scoring (0-100 scale with threat level mapping)
- Intelligence enrichment
- AI-driven report augmentation
- MITRE ATT&CK technique mapping
- IOC extraction and deduplication

AI calls route through an intelligent multi-tier cascade fallback router:
1. **Tier 1 (Primary)**: **NVIDIA NIM API** (`meta/llama-3.3-70b-instruct` via OpenAI-compatible endpoint `https://integrate.api.nvidia.com/v1`)
2. **Tier 2 (Fallback)**: **Google Gemini API** (`gemini-2.0-flash` via Generative Language API)
3. **Tier 3 (Fallback)**: **GitHub Copilot SDK** (`gpt-5-mini` local session)
4. **Tier 4 / Local Offline**: **Local / LAN Ollama Endpoint** (`llama3.1:8b` / `llama3.2:3b` at `http://10.42.0.88:11434` or `http://localhost:11434`)

### Multi-Agent Analysis Pipeline

The pipeline uses specialised per-tool agents that each receive minimal data (reducing token usage) and return structured JSON:

| Agent | Input | Purpose |
|---|---|---|
| `sysmon-analyzer` | Sysmon event summary | Detect process injection, LOLBin abuse, persistence |
| `procmon-analyzer` | Procmon summary JSON | Detect file/registry/process suspicious activity |
| `network-analyzer` | Network telemetry & IOCs | Deterministic local threat DB matching (C2, malware downloads, compromised IPs) — zero AI token consumption |
| `handle-analyzer` | Handle snapshot text | Detect mutex, sensitive file handles |
| `tcpvcon-analyzer` | TCPVcon CSV snapshot | Detect active malicious connections |
| `metadata-analyzer` | Execution metadata | Detect sandbox evasion, anomalies |
| `threat-summarizer` | All per-tool JSONs | Final risk score, classification, MITRE mapping |

### Files

- `ai_router.py` — Multi-provider AI router with automated 3-tier cascade (NVIDIA NIM → Gemini Flash → Copilot)
- `copilot_agents.py` — Per-tool analyst agents + threat-summarizer with JSON schema contracts
- `copilot_service.py` — Async Copilot SDK wrapper (gpt-5-mini enforced)
- `copilot_cli.py` — CLI for auth-status, list-agents, list-models, chat
- `threat_analyzer.py` — Pipeline orchestrator: loads report data → dispatches deterministic network DB lookups + AI tool agents → synthesizes via threat-summarizer → saves results

### Gateway Endpoints

- `POST /api/analysis/report/{id}/ai-analyze` — Run AI analysis pipeline
- `GET  /api/analysis/report/{id}/ai-report`  — Retrieve saved AI report
- `GET  /api/analysis/report/{id}/yara`       — Retrieve YARA static pattern detection findings
- `GET  /api/analysis/report/{id}/lstm`       — Retrieve BiLSTM sequential behavioral malice prediction
- `GET  /api/analysis/report/{id}/behavior`   — Retrieve normalized filesystem and registry behavioral findings
- `GET  /api/analysis/report/{id}/gui`        — Retrieve GUI screen OCR analysis and Laya threat triage
- `GET  /api/analysis/report/{id}/risk`       — Retrieve unified deterministic risk score and layer breakdown

This layer operates on structured findings from collector artifacts, not raw logs.

---

## `core/storage/`
Persistent storage layer.

### Subdirectories:

- `database/` → SQLite or structured data store (including `network_threat_intel.db` for offline IOC matching)
- `samples/` → Uploaded suspicious files
- `logs/` → Raw execution logs
- `reports/` → Final analysis outputs
- `yara_rules/` → Curated YARA detection rulesets for packers, evasion, and capabilities

No business logic must exist here.

---

# 🤖 AI Development Rules

These rules must always be followed when generating or modifying code.

---

## 1️⃣ Architecture Update Rule

When adding:
- New features
- New modules
- Workflow changes
- Structural modifications

The AI MUST:
- Update this `AI-INSTRUCTIONS.md` (Note: `AGENTS.md` is the source of truth, run `python3 scripts/sync_ai_docs.py` after updating)
- Update `docs/ARCHITECTURE.md` if needed
- Reflect changes in component responsibility sections

Never allow architecture drift.

---

## 1️⃣b Versioning Rule

- Do not version bump for every change. Only bump when the change is meaningful enough to warrant a new version.
- The `/version` endpoint is only updated when API behavior or API contracts change.
- For non-API changes that still warrant a release, do not bump the API version; instead, create a new commit and apply the appropriate version tag.

---

## 1️⃣c Documentation Sync Rule

When API endpoints are added, removed, or modified, `docs/curls.md` must be updated to match.

---

## 2️⃣ Mandatory Testing Policy

After ANY code change:

1. Ensure a `tests/` directory exists at project root.
2. Each test must be a standalone script.
3. Naming format:

```

TEST*{number}*{short_description}.py

```

Example:

```

TEST_01_controller_flow.py
TEST_02_log_parsing.py
TEST_03_risk_scoring.py

```

Each test script must:
- Run independently
- Print PASS or FAIL
- Print what the test is about
- Print the raw output produced by the test

Example:

```

[TEST_01_controller_flow] PASS
About: Controller dry-run builds correct VBoxManage command
Output:
{"cmd": ["VBoxManage", "startvm", "TestVM", "--type", "headless"], "returncode": 0, "stdout": "", "stderr": ""}

```

or

```

[TEST_02_log_parsing] FAIL
About: Network events parsed from sample log
Reason: No network events parsed
Output:
<raw parser output here>

```

---

## 3️⃣ Mandatory Test Execution Rule

After implementing a feature:

- Run all tests.
- If ANY test fails:
  - Fix the issue.
  - Re-run tests.
  - Repeat until all tests pass.

Never stop after a failed test.

---

## 4️⃣ Dependency Management

- Always update `requirements.txt` when new libraries are added.
- Prefer maintained and stable packages.
- Avoid deprecated APIs.
- Keep dependencies minimal.

---

## 5️⃣ Git Safety & Hygiene

Always ensure:

- Sensitive files are ignored.
- Large binaries are ignored.
- Logs are ignored.
- Databases are ignored.
- VM artifacts are ignored.
- `.env` files are ignored.

Ensure `.gitignore` includes:

```

core/storage/logs/
core/storage/samples/
core/storage/database/
_.vdi
_.iso
.env
**pycache**/

```

Never commit sensitive or large artifacts.

---

## 6️⃣ Separation of Concerns Rule

- No VM logic outside `controller/`
- No AI logic outside `threatintelligence/`
- No parsing logic outside `modules/`
- No monitoring logic outside `observer/`
- No storage logic outside `storage/`
- No UI logic outside `interface/`

Maintain clean boundaries.

---

## 7️⃣ Development Philosophy

IsoLens is:

- Academic
- Modular
- Lightweight
- Expandable
- Educational

Do not:
- Introduce microservices
- Add unnecessary abstraction
- Add heavy infrastructure
- Overcomplicate logic

Keep it readable and structured.

---

# 🔌 API Gateway Rules

- All API endpoints must be under `/api/`.
- VM identifiers must be passed in the request body for POST endpoints, not in the URL path.
- Request and response schemas must remain consistent and documented via models.
- Gateway routes must be organized into multiple modules (e.g., `system_routes.py`, `controller_routes.py`) and included in `app.py` via routers. Do not define all endpoints directly in `app.py`.
- Maintain `docs/curls.md` with short descriptions and curl examples for all endpoints.
- In `docs/curls.md`, use `dry_run=false` and `raise_on_error=true` in all examples.

# 📌 Final AI Checklist Before Completing Work

Before finalizing any change:

✔ Update AI-INSTRUCTIONS.md if architecture changed
✔ Update docs/ARCHITECTURE.md if needed
✔ Add isolated test scripts
✔ Run all tests
✔ Ensure all tests PASS
✔ Update requirements.txt if required
✔ Verify .gitignore safety

No exceptions.
```
