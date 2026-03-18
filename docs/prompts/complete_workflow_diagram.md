# IsoLens Complete Project Workflow - Image Generation Prompt

## 🎨 Design Theme Summary

**CRITICAL STYLING REQUIREMENTS:**
- ✅ **WHITE BACKGROUND** - Clean, professional, print-friendly theme
- ✅ **LINE-FOCUSED DESIGN** - Beautiful arrows and flow lines are the primary visual elements
- ✅ **MINIMAL ICONS** - Only 5-10 strategic icons (browser, server, VM, AI, database), all with text labels
- ✅ **LABEL EVERYTHING** - Every box, arrow, icon, step, and section must have clear text
- ✅ **HIGH CONTRAST** - Black text and lines on white background for readability
- ✅ **SUBTLE COLORS** - Light gray boxes for layers; subtle tints only for VM (light red) and AI (light blue) zones

---

## Design Requirements

Create a **comprehensive, visually stunning end-to-end workflow diagram** that illustrates the complete IsoLens Malware Sandbox system from user upload to final threat intelligence report. This is an academic mini-project, so the diagram should be impressive, detailed, and showcase the sophisticated multi-layer architecture and AI-powered analysis pipeline.

---

## Visual Style Guidelines

- **Style**: Modern, professional system architecture diagram with **white/light background theme**
- **Color Scheme**: 
  - **Minimalist, line-focused approach**: White background with black lines and text
  - Use **subtle light gray boxes** for grouping layers/phases (instead of colored swimlanes)
  - **Minimal accent colors**: 
    - Light red/pink tint ONLY for the isolated VM execution zone (security emphasis)
    - Light blue/purple tint ONLY for AI analysis components (innovation highlight)
    - All other areas: white background with gray borders
  - **No gradients or heavy shadows** - clean, professional, print-friendly
  - High contrast black text on white background
- **Layout**: Left-to-right or top-to-bottom flow showing chronological progression
- **Visual Elements**: 
  - **EMPHASIS ON LINES AND ARROWS** - these are the primary visual elements
  - Use different arrow styles (solid, dashed, dotted) to show different flow types
  - **All arrows must be clearly labeled** with what they represent
  - Minimal strategic icons (5-10 total: browser, server, VM, AI, database) - **all labeled with text**
  - Use simple rectangular boxes with clean borders for components
  - Number all steps clearly (1, 2, 3...) within the flow
  - Use standard flowchart symbols (diamond for decisions, etc.)
- **Typography**: Bold headers for phases, clear labels on arrows, readable step descriptions
- **Emphasis**: Make the AI multi-agent analysis pipeline particularly prominent with detailed arrow flows showing data movement

---

## Complete Workflow - End-to-End Process

### **PHASE 0: SYSTEM INITIALIZATION** (Background - shown at top)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM STARTUP & PREREQUISITES                        │
└─────────────────────────────────────────────────────────────────────────┘

[HOST SYSTEM]
├── Ubuntu/Linux Host OS
├── VirtualBox Installed
├── Python 3.8+ with venv
├── Node.js 18+
└── run.sh launcher script

         ↓ ./run.sh
         ↓

[SERVICE STARTUP]
├── FastAPI Gateway       → Port 6969 (uvicorn)
├── Next.js Interface     → Port 3000 (next dev)
└── VirtualBox VM Ready
    ├── Windows 7 Sandbox
    ├── Host-only Network: 192.168.56.105
    ├── IsoLens Agent v1.3.0 running on port 9090
    ├── Shared Folder: \\VBOXSVR\SandboxShare
    └── Pre-installed Tools:
        ├── Sysmon
        ├── Process Monitor
        ├── FakeNet-NG
        ├── Handle64
        ├── TCPVcon64
        └── PowerShell (screenshots)

✓ System Ready for Analysis
```

---

### **PHASE 1: USER INTERACTION** (UI Layer)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                             │
│                    (Next.js 16.1.6 - Port 3000)                         │
└─────────────────────────────────────────────────────────────────────────┘

STEP 1: User Opens Web Interface
        ↓
        http://localhost:3000
        ↓
        [IsoLens Dashboard - Material Design]
        ├── Scan Page (Active)
        ├── Reports Page
        ├── Scan History
        ├── Sandbox Status
        ├── Settings
        └── Help & Support

STEP 2: User Navigates to Scan Page
        ↓
        [File Upload Interface]
        ├── Drag & Drop Zone
        ├── File Browser Button
        ├── Configuration Options:
        │   ├── Analysis Timeout (10-300 sec) [Default: 60s]
        │   └── Screenshot Interval (seconds) [Default: 5s]
        └── "Start Analysis" Button

STEP 3: User Selects Malware Sample
        ↓
        [File Selected]
        ├── Filename: suspicious_file.exe
        ├── Size: 2.4 MB
        ├── Type: PE32 executable
        └── SHA256: <calculated client-side>

STEP 4: User Configures Analysis
        ↓
        [Settings]
        ├── Timeout: 120 seconds
        └── Screenshot Interval: 5 seconds

STEP 5: User Clicks "Start Analysis"
        ↓
        [Upload Progress Bar]
        └── Uploading to gateway...
```

---

### **PHASE 2: API GATEWAY PROCESSING** (Backend Entry)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY LAYER                                │
│                     (FastAPI - Port 6969)                               │
└─────────────────────────────────────────────────────────────────────────┘

STEP 6: Gateway Receives Upload
        ↓
        POST /api/analysis/submit
        ├── Headers: multipart/form-data
        ├── Body:
        │   ├── file: suspicious_file.exe
        │   ├── timeout: 120
        │   └── screenshot_interval: 5
        └── Request ID: <generated UUID>

STEP 7: Validation & Pre-processing
        ↓
        [Security Checks]
        ├── File size < 100MB? ✓
        ├── Timeout in range (10-300)? ✓
        ├── Is another analysis running? → Check
        │   └── If YES: Return 409 Conflict
        │   └── If NO: Proceed ✓
        └── Generate analysis_id: a1b2c3d4-e5f6-...

STEP 8: Save Sample to Storage
        ↓
        [File System Write]
        └── core/storage/samples/suspicious_file.exe
            ├── Calculate SHA256 hash
            ├── Store metadata (size, type, timestamp)
            └── Mark as "pending"

STEP 9: Invoke Sandbox Orchestrator
        ↓
        [Internal API Call]
        └── orchestrator.run_analysis(
                sample_path="...",
                timeout=120,
                screenshot_interval=5
            )
```

---

### **PHASE 3: ORCHESTRATION & VM CONTROL** (Controller Layer)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SANDBOX ORCHESTRATION LAYER                           │
│                     (Python - controller/)                              │
└─────────────────────────────────────────────────────────────────────────┘

STEP 10: Orchestrator Initializes
         ↓
         [SandboxOrchestrator]
         ├── Create AnalysisResult object
         │   ├── analysis_id: a1b2c3d4...
         │   ├── sample_name: suspicious_file.exe
         │   ├── status: "pending" → "running"
         │   └── started_at: 2026-03-18T17:42:00Z
         └── Agent Config:
             ├── VM: WindowsSandbox
             ├── Host: 192.168.56.105:9090
             └── Timeout: 15s (HTTP)

STEP 11: VM Preparation (Optional)
         ↓
         [VBoxController - VBoxManage CLI]
         ├── Check VM Status: VBoxManage showvminfo WindowsSandbox
         ├── If Powered Off: VBoxManage startvm WindowsSandbox --type headless
         ├── Wait for boot (check agent /api/status)
         └── Optional: Restore clean snapshot
             └── VBoxManage snapshot WindowsSandbox restore "CleanState"

STEP 12: Copy Sample to Shared Folder
         ↓
         [File Transfer - Host Side]
         └── SandboxShare/ (VirtualBox Shared Folder)
             ├── Source: core/storage/samples/suspicious_file.exe
             ├── Destination: SandboxShare/suspicious_file.exe
             └── File is now accessible to VM at \\VBOXSVR\SandboxShare

STEP 13: Command Agent to Execute
         ↓
         [HTTP Request to VM Agent]
         POST http://192.168.56.105:9090/api/execute
         Body: {
             "filename": "suspicious_file.exe",
             "timeout": 120,
             "screenshot_interval": 5
         }
         ↓
         [Agent Response]
         {
             "status": "ok",
             "data": {
                 "message": "Execution started in background thread",
                 "analysis_id": "a1b2c3d4...",
                 "sample": "suspicious_file.exe"
             }
         }

STEP 14: Poll Agent Status
         ↓
         [Polling Loop - Every 5 seconds]
         └── GET http://192.168.56.105:9090/api/status
             ├── While status == "executing" or "collecting": Continue polling
             ├── Max poll time: timeout + 60 seconds
             └── When status == "idle": Proceed to retrieval
```

---

### **PHASE 4: SANDBOX EXECUTION** (Inside Isolated VM)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ISOLATED SANDBOX ENVIRONMENT                          │
│              (Windows 7 VM - Host-Only Network)                         │
│                    IsoLens Agent v1.3.0                                 │
└─────────────────────────────────────────────────────────────────────────┘

STEP 15: Agent Receives Execute Command
         ↓
         [IsoLens Agent - isolens_agent.py]
         ├── Spawn background thread for execution
         ├── Main HTTP server stays responsive
         └── Change status: "idle" → "executing"

STEP 16: Agent Copies Sample Locally
         ↓
         [File Transfer - Guest Side]
         └── \\VBOXSVR\SandboxShare\suspicious_file.exe
             ↓ Copy
             C:\IsoLens\samples\suspicious_file.exe

STEP 17: Pre-Execution Setup
         ↓
         [Environment Preparation]
         ├── Clear Sysmon Event Log
         │   └── wevtutil clear-log Microsoft-Windows-Sysmon/Operational
         ├── Start Process Monitor (if configured)
         ├── Start FakeNet-NG (if configured)
         └── Record pre-execution baseline

STEP 18: Execute Malware Sample
         ↓
         [CRITICAL: Malware Execution in Isolated Environment]
         
         Method: Interactive Session Execution
         └── schtasks /create /tn "IsoLensExec" /tr "C:\IsoLens\samples\suspicious_file.exe" /sc once /st NOW /it
             ↓
             [Malware Running in User Context]
             ├── Process spawns
             ├── DLLs loaded
             ├── Network connections attempted
             ├── Files created/modified
             ├── Registry keys modified
             └── Child processes spawned

         [Parallel: Screenshot Capture]
         └── Every 5 seconds:
             PowerShell + System.Drawing → screenshot_NNNN.png
             └── Saved to C:\IsoLens\artifacts\screenshots\

STEP 19: Behavioral Monitoring (Passive)
         ↓
         [Background Monitoring - 120 seconds]
         ├── Sysmon logs events in real-time
         ├── Process Monitor records file/registry/process activity
         ├── FakeNet-NG intercepts network traffic
         ├── Windows logs API calls
         └── [Timer Running: 120s countdown]

         Time Elapsed: 0s ... 30s ... 60s ... 90s ... 120s ✓

STEP 20: Timeout Reached - Stop Execution
         ↓
         [Execution Window Closed]
         ├── Timeout: 120 seconds elapsed
         └── Change status: "executing" → "collecting"
```

---

### **PHASE 5: ARTIFACT COLLECTION** (Inside VM)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      ARTIFACT COLLECTION PHASE                           │
│                    (Agent Collector Plugins)                            │
└─────────────────────────────────────────────────────────────────────────┘

STEP 21: Run All Collectors in Sequence
         ↓
         [7 Pluggable Collectors Execute]

         ┌──────────────────────────────────────┐
         │  1. SysmonCollector                   │
         ├───────────────────────────────────────┤
         │  Export Sysmon Event Log              │
         │  └── wevtutil query-events ...        │
         │      ├── sysmon_events.xml (raw)      │
         │      ├── sysmon_events.txt (readable) │
         │      └── sysmon_summary.json (parsed) │
         └──────────────────────────────────────┘

         ┌──────────────────────────────────────┐
         │  2. ProcmonCollector                  │
         ├───────────────────────────────────────┤
         │  Export Process Monitor Logs          │
         │  └── procmon /terminate               │
         │      └── procmon.csv                  │
         │      └── procmon_summary.json         │
         └──────────────────────────────────────┘

         ┌──────────────────────────────────────┐
         │  3. NetworkCollector                  │
         ├───────────────────────────────────────┤
         │  Capture Network Traffic              │
         │  └── tshark dump                      │
         │      └── capture.pcap                 │
         │      └── network_summary.json         │
         └──────────────────────────────────────┘

         ┌──────────────────────────────────────┐
         │  4. FakeNetCollector                  │
         ├───────────────────────────────────────┤
         │  Collect Fake Network Responses       │
         │  └── FakeNet-NG logs                  │
         │      ├── fakenet.log                  │
         │      └── fakenet.pcap                 │
         └──────────────────────────────────────┘

         ┌──────────────────────────────────────┐
         │  5. ScreenshotCollector               │
         ├───────────────────────────────────────┤
         │  Gather All Screenshots               │
         │  └── C:\IsoLens\artifacts\screenshots │
         │      ├── screenshot_0000.png          │
         │      ├── screenshot_0001.png          │
         │      └── ... (24 screenshots @ 5s)    │
         └──────────────────────────────────────┘

         ┌──────────────────────────────────────┐
         │  6. HandleCollector                   │
         ├───────────────────────────────────────┤
         │  Snapshot Open Handles                │
         │  └── handle64.exe -accepteula         │
         │      └── handle_snapshot.txt          │
         │          ├── File handles             │
         │          ├── Mutex handles            │
         │          └── Registry handles         │
         └──────────────────────────────────────┘

         ┌──────────────────────────────────────┐
         │  7. TcpvconCollector                  │
         ├───────────────────────────────────────┤
         │  Snapshot Active Connections          │
         │  └── tcpvcon64.exe -accepteula -c     │
         │      └── tcpvcon_snapshot.csv         │
         │          ├── TCP connections          │
         │          ├── UDP connections          │
         │          └── Process associations     │
         └──────────────────────────────────────┘

STEP 22: Package All Artifacts
         ↓
         [Zip Archive Creation]
         └── C:\IsoLens\artifacts\results_a1b2c3d4.zip
             ├── sysmon/ (3 files)
             ├── procmon/ (2 files)
             ├── network/ (2 files)
             ├── fakenet/ (2 files)
             ├── screenshots/ (24 PNG files)
             ├── handle/ (1 file)
             ├── tcpvcon/ (1 file)
             └── metadata.json
                 ├── analysis_id
                 ├── sample_name
                 ├── start_time
                 ├── end_time
                 ├── timeout
                 ├── exit_code
                 └── collector_stats

STEP 23: Export to Shared Folder
         ↓
         [File Transfer Back to Host]
         └── Copy: C:\IsoLens\artifacts\results_a1b2c3d4.zip
             → \\VBOXSVR\SandboxShare\results_a1b2c3d4.zip

STEP 24: Agent Returns to Idle
         ↓
         [Agent Status Update]
         └── status: "collecting" → "idle"
         └── current_sample: None
         └── execution_count: +1
```

---

### **PHASE 6: RESULT RETRIEVAL** (Back to Host)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      HOST RESULT RETRIEVAL                               │
│                    (Orchestrator Continues)                             │
└─────────────────────────────────────────────────────────────────────────┘

STEP 25: Orchestrator Detects Completion
         ↓
         [Polling Loop Completes]
         └── GET /api/status returns "idle" ✓

STEP 26: Retrieve Results Zip
         ↓
         [File System Read]
         └── SandboxShare/results_a1b2c3d4.zip
             ↓ Copy to host storage
             core/storage/reports/a1b2c3d4/agent_package.zip

STEP 27: Unpack Artifacts
         ↓
         [Zip Extraction]
         └── core/storage/reports/a1b2c3d4/
             ├── artifacts/
             │   ├── sysmon/
             │   │   ├── sysmon_events.xml
             │   │   ├── sysmon_events.txt
             │   │   └── sysmon_summary.json
             │   ├── procmon/
             │   │   ├── procmon.csv
             │   │   └── procmon_summary.json
             │   ├── network/
             │   │   ├── capture.pcap
             │   │   └── network_summary.json
             │   ├── fakenet/
             │   │   ├── fakenet.log
             │   │   └── fakenet.pcap
             │   ├── screenshots/
             │   │   └── *.png (24 files)
             │   ├── handle/
             │   │   └── handle_snapshot.txt
             │   ├── tcpvcon/
             │   │   └── tcpvcon_snapshot.csv
             │   └── metadata.json
             └── analysis_summary.json

STEP 28: Update Analysis Status
         ↓
         [AnalysisResult Update]
         ├── status: "running" → "complete"
         ├── completed_at: 2026-03-18T17:44:30Z
         ├── sysmon_events: 247 (from metadata)
         ├── files_collected: [list of 35 files]
         └── report_dir: "core/storage/reports/a1b2c3d4"

STEP 29: Return Response to Gateway
         ↓
         [Gateway Returns to UI]
         └── Response: {
                 "status": "ok",
                 "data": {
                     "analysis_id": "a1b2c3d4...",
                     "status": "complete",
                     "report_url": "/api/analysis/report/a1b2c3d4"
                 }
             }
```

---

### **PHASE 7: INITIAL REPORT DISPLAY** (Basic Analysis)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      INITIAL REPORT DISPLAY                              │
│                    (UI - Reports Page)                                  │
└─────────────────────────────────────────────────────────────────────────┘

STEP 30: UI Receives Completion Notification
         ↓
         [Next.js Frontend]
         └── Analysis Complete! View Report →

STEP 31: User Navigates to Reports Page
         ↓
         GET /api/analysis/report/a1b2c3d4
         ↓
         [Report Data Loaded]
         └── Basic Analysis Results:
             ├── Sample Name: suspicious_file.exe
             ├── Analysis ID: a1b2c3d4...
             ├── Status: Complete ✓
             ├── Duration: 2m 30s
             ├── Sysmon Events: 247
             ├── Files Collected: 35
             ├── Screenshots: 24
             └── [AI Analysis Not Yet Run]

STEP 32: Display Basic Findings
         ↓
         [Report Sections]
         ├── 📊 Execution Summary
         │   ├── Timeout: 120 seconds
         │   ├── Exit Code: 0
         │   └── Execution Time: 120s
         ├── 📁 Collected Artifacts
         │   ├── Sysmon (3 files, 1.2 MB)
         │   ├── Procmon (2 files, 5.8 MB)
         │   ├── Network (2 files, 856 KB)
         │   ├── Screenshots (24 files, 4.2 MB)
         │   └── Other (5 files, 312 KB)
         ├── 📸 Screenshots Gallery
         │   └── [Thumbnail grid - 24 images]
         └── 🔍 Raw Logs
             └── [Download links for each artifact]
```

---

### **PHASE 8: AI ANALYSIS PIPELINE** (Advanced Threat Intelligence)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  AI-POWERED THREAT ANALYSIS PIPELINE                     │
│            (GitHub Copilot SDK - gpt-5-mini Model)                      │
└─────────────────────────────────────────────────────────────────────────┘

STEP 33: User Triggers AI Analysis
         ↓
         [UI Action]
         └── Button: "Run AI Threat Analysis" →
         POST /api/analysis/report/a1b2c3d4/ai-analyze

STEP 34: Gateway Invokes ThreatAnalyzer
         ↓
         [Async Job Spawned]
         └── threat_analyzer.analyze_report(
                 analysis_id="a1b2c3d4",
                 report_dir="core/storage/reports/a1b2c3d4"
             )

STEP 35: Load Artifact Summaries
         ↓
         [ThreatAnalyzer Initialization]
         ├── Read metadata.json
         ├── Load sysmon_summary.json (truncate to 6000 chars)
         ├── Load procmon_summary.json (truncate to 6000 chars)
         ├── Load network_summary.json (truncate to 6000 chars)
         ├── Load handle_snapshot.txt (truncate to 6000 chars)
         └── Load tcpvcon_snapshot.csv (truncate to 6000 chars)

STEP 36: Dispatch to Per-Tool AI Agents (PARALLEL)
         ↓
         [Multi-Agent Analysis - 6 Agents Running Concurrently]

         ╔═══════════════════════════════════════════════════════════════╗
         ║                    AGENT 1: sysmon-analyzer                    ║
         ╠═══════════════════════════════════════════════════════════════╣
         ║  Input: sysmon_summary.json                                    ║
         ║  Model: gpt-5-mini                                            ║
         ║  Prompt: "Analyze Sysmon events for process injection,        ║
         ║           lateral movement, LOLBin abuse, persistence..."     ║
         ║  ↓                                                             ║
         ║  Output: sysmon_analysis.json                                 ║
         ║  {                                                             ║
         ║    "verdict": "malicious",                                    ║
         ║    "confidence": 87,                                          ║
         ║    "findings": [                                              ║
         ║      {                                                         ║
         ║        "type": "process_injection",                           ║
         ║        "severity": "high",                                    ║
         ║        "description": "Detected CreateRemoteThread...",       ║
         ║        "evidence": "EventID 8, PID 1234 → PID 5678"          ║
         ║      }                                                         ║
         ║    ],                                                          ║
         ║    "iocs": [                                                   ║
         ║      {"type": "process", "value": "powershell.exe -enc..."}  ║
         ║    ]                                                           ║
         ║  }                                                             ║
         ╚═══════════════════════════════════════════════════════════════╝

         ╔═══════════════════════════════════════════════════════════════╗
         ║                   AGENT 2: procmon-analyzer                    ║
         ╠═══════════════════════════════════════════════════════════════╣
         ║  Input: procmon_summary.json                                   ║
         ║  Model: gpt-5-mini                                            ║
         ║  Focus: File drops, registry persistence, data exfiltration   ║
         ║  ↓                                                             ║
         ║  Output: procmon_analysis.json                                ║
         ║  {                                                             ║
         ║    "verdict": "malicious",                                    ║
         ║    "confidence": 92,                                          ║
         ║    "findings": [                                              ║
         ║      {                                                         ║
         ║        "type": "registry_persistence",                        ║
         ║        "severity": "critical",                                ║
         ║        "description": "Added Run key for persistence",        ║
         ║        "evidence": "HKCU\\Software\\Microsoft\\..."           ║
         ║      }                                                         ║
         ║    ]                                                           ║
         ║  }                                                             ║
         ╚═══════════════════════════════════════════════════════════════╝

         ╔═══════════════════════════════════════════════════════════════╗
         ║                   AGENT 3: network-analyzer                    ║
         ╠═══════════════════════════════════════════════════════════════╣
         ║  Input: network_summary.json                                   ║
         ║  Model: gpt-5-mini                                            ║
         ║  Focus: C2 communication, beaconing, data exfiltration        ║
         ║  ↓                                                             ║
         ║  Output: network_analysis.json                                ║
         ║  {                                                             ║
         ║    "verdict": "suspicious",                                   ║
         ║    "confidence": 78,                                          ║
         ║    "findings": [                                              ║
         ║      {                                                         ║
         ║        "type": "c2_communication",                            ║
         ║        "severity": "high",                                    ║
         ║        "description": "Suspicious HTTPS beaconing...",        ║
         ║        "evidence": "192.168.1.100:443 every 60s"             ║
         ║      }                                                         ║
         ║    ],                                                          ║
         ║    "iocs": [                                                   ║
         ║      {"type": "ip", "value": "192.168.1.100"}                ║
         ║    ]                                                           ║
         ║  }                                                             ║
         ╚═══════════════════════════════════════════════════════════════╝

         ╔═══════════════════════════════════════════════════════════════╗
         ║                   AGENT 4: handle-analyzer                     ║
         ╠═══════════════════════════════════════════════════════════════╣
         ║  Input: handle_snapshot.txt                                    ║
         ║  Model: gpt-5-mini                                            ║
         ║  Focus: Suspicious mutex, sensitive file access               ║
         ║  ↓                                                             ║
         ║  Output: handle_analysis.json                                 ║
         ║  {                                                             ║
         ║    "verdict": "suspicious",                                   ║
         ║    "confidence": 65,                                          ║
         ║    "findings": [                                              ║
         ║      {                                                         ║
         ║        "type": "mutex_detection",                             ║
         ║        "severity": "medium",                                  ║
         ║        "description": "Mutex for single-instance check",      ║
         ║        "evidence": "Global\\MalwareMutex2024"                 ║
         ║      }                                                         ║
         ║    ]                                                           ║
         ║  }                                                             ║
         ╚═══════════════════════════════════════════════════════════════╝

         ╔═══════════════════════════════════════════════════════════════╗
         ║                  AGENT 5: tcpvcon-analyzer                     ║
         ╠═══════════════════════════════════════════════════════════════╣
         ║  Input: tcpvcon_snapshot.csv                                   ║
         ║  Model: gpt-5-mini                                            ║
         ║  Focus: Active malicious connections                          ║
         ║  ↓                                                             ║
         ║  Output: tcpvcon_analysis.json                                ║
         ║  {                                                             ║
         ║    "verdict": "malicious",                                    ║
         ║    "confidence": 82,                                          ║
         ║    "findings": [                                              ║
         ║      {                                                         ║
         ║        "type": "suspicious_connection",                       ║
         ║        "severity": "high",                                    ║
         ║        "description": "Established connection to known C2",   ║
         ║        "evidence": "suspicious_file.exe → 203.0.113.42:8080" ║
         ║      }                                                         ║
         ║    ]                                                           ║
         ║  }                                                             ║
         ╚═══════════════════════════════════════════════════════════════╝

         ╔═══════════════════════════════════════════════════════════════╗
         ║                  AGENT 6: metadata-analyzer                    ║
         ╠═══════════════════════════════════════════════════════════════╣
         ║  Input: metadata.json                                          ║
         ║  Model: gpt-5-mini                                            ║
         ║  Focus: Sandbox evasion, execution anomalies                  ║
         ║  ↓                                                             ║
         ║  Output: metadata_analysis.json                               ║
         ║  {                                                             ║
         ║    "verdict": "suspicious",                                   ║
         ║    "confidence": 71,                                          ║
         ║    "findings": [                                              ║
         ║      {                                                         ║
         ║        "type": "time_check",                                  ║
         ║        "severity": "low",                                     ║
         ║        "description": "Possible VM detection attempt",        ║
         ║        "evidence": "Sleep delay before execution"             ║
         ║      }                                                         ║
         ║    ]                                                           ║
         ║  }                                                             ║
         ╚═══════════════════════════════════════════════════════════════╝

         [All 6 agents complete in parallel - Total time: ~15-30 seconds]

STEP 37: Collect Per-Tool Results
         ↓
         [ThreatAnalyzer Aggregates]
         └── tool_results = [
                 sysmon_analysis.json,
                 procmon_analysis.json,
                 network_analysis.json,
                 handle_analysis.json,
                 tcpvcon_analysis.json,
                 metadata_analysis.json
             ]

STEP 38: Feed to Threat Summarizer Agent
         ↓
         ╔═══════════════════════════════════════════════════════════════╗
         ║              AGENT 7: threat-summarizer (FINAL)                ║
         ╠═══════════════════════════════════════════════════════════════╣
         ║  Input: All 6 per-tool JSON results                            ║
         ║  Model: gpt-5-mini                                            ║
         ║  Task: Synthesize final threat assessment                     ║
         ║  ↓                                                             ║
         ║  Processing:                                                   ║
         ║  ├── Calculate overall risk score (0-100)                     ║
         ║  ├── Determine threat level (none/low/medium/high/critical)   ║
         ║  ├── Classify malware type and family                         ║
         ║  ├── Map to MITRE ATT&CK techniques                           ║
         ║  ├── Deduplicate IOCs across tools                            ║
         ║  ├── Generate executive summary                               ║
         ║  └── Provide remediation recommendations                      ║
         ║  ↓                                                             ║
         ║  Output: threat_report.json                                   ║
         ║  {                                                             ║
         ║    "risk_score": 87,                                          ║
         ║    "threat_level": "high",                                    ║
         ║    "malware_type": "trojan",                                  ║
         ║    "malware_family": "Generic Backdoor",                      ║
         ║    "platform": "Windows",                                     ║
         ║    "classification_confidence": 85,                           ║
         ║    "executive_summary": "This sample exhibits high-risk...",  ║
         ║    "key_findings": [                                          ║
         ║      {                                                         ║
         ║        "category": "Persistence",                             ║
         ║        "severity": "critical",                                ║
         ║        "description": "Registry Run key modification"         ║
         ║      },                                                        ║
         ║      {                                                         ║
         ║        "category": "Command & Control",                       ║
         ║        "severity": "high",                                    ║
         ║        "description": "HTTPS beaconing to 192.168.1.100"     ║
         ║      }                                                         ║
         ║    ],                                                          ║
         ║    "iocs": [                                                   ║
         ║      {"type": "ip", "value": "192.168.1.100", "context":...},║
         ║      {"type": "registry", "value": "HKCU\\...Run", ...},     ║
         ║      {"type": "mutex", "value": "Global\\MalwareMutex2024"}  ║
         ║    ],                                                          ║
         ║    "mitre_attack": [                                          ║
         ║      {                                                         ║
         ║        "technique_id": "T1055",                               ║
         ║        "technique_name": "Process Injection",                 ║
         ║        "tactic": "Defense Evasion",                           ║
         ║        "description": "Detected CreateRemoteThread..."        ║
         ║      },                                                        ║
         ║      {                                                         ║
         ║        "technique_id": "T1547.001",                           ║
         ║        "technique_name": "Registry Run Keys",                 ║
         ║        "tactic": "Persistence",                               ║
         ║        "description": "Registry modification for autostart"   ║
         ║      },                                                        ║
         ║      {                                                         ║
         ║        "technique_id": "T1071.001",                           ║
         ║        "technique_name": "Web Protocols (HTTPS)",             ║
         ║        "tactic": "Command and Control",                       ║
         ║        "description": "HTTPS C2 communication"                ║
         ║      }                                                         ║
         ║    ],                                                          ║
         ║    "recommendations": [                                        ║
         ║      {                                                         ║
         ║        "priority": "critical",                                ║
         ║        "action": "Block IP 192.168.1.100 at firewall",       ║
         ║        "rationale": "Active C2 communication detected"        ║
         ║      },                                                        ║
         ║      {                                                         ║
         ║        "priority": "high",                                    ║
         ║        "action": "Remove registry Run key persistence",       ║
         ║        "rationale": "Ensures malware won't survive reboot"    ║
         ║      }                                                         ║
         ║    ]                                                           ║
         ║  }                                                             ║
         ╚═══════════════════════════════════════════════════════════════╝

STEP 39: Save AI Analysis Results
         ↓
         [File System Write]
         └── core/storage/reports/a1b2c3d4/ai_analysis/
             ├── tool_results/
             │   ├── sysmon_analysis.json
             │   ├── procmon_analysis.json
             │   ├── network_analysis.json
             │   ├── handle_analysis.json
             │   ├── tcpvcon_analysis.json
             │   └── metadata_analysis.json
             ├── threat_report.json (FINAL)
             └── full_analysis_log.txt

STEP 40: Update AI Analysis Status
         ↓
         [ThreatAnalysisReport]
         ├── status: "running" → "complete"
         ├── completed_at: 2026-03-18T17:45:15Z
         └── Duration: 45 seconds (AI analysis)
```

---

### **PHASE 9: ENHANCED REPORT DISPLAY** (Final Results)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     COMPREHENSIVE THREAT REPORT                          │
│                    (UI - Enhanced Reports Page)                         │
└─────────────────────────────────────────────────────────────────────────┘

STEP 41: UI Fetches AI Report
         ↓
         GET /api/analysis/report/a1b2c3d4/ai-report
         ↓
         [Complete Threat Intelligence Loaded]

STEP 42: Display Risk Assessment Dashboard
         ↓
         [Top Section - Risk Overview]
         ┌─────────────────────────────────────────────────────────────┐
         │  🚨 RISK SCORE: 87/100                                       │
         │  ⚠️  THREAT LEVEL: HIGH                                      │
         │  🦠 CLASSIFICATION: Trojan / Generic Backdoor                │
         │  💻 PLATFORM: Windows                                        │
         │  ✓  CONFIDENCE: 85%                                          │
         └─────────────────────────────────────────────────────────────┘

STEP 43: Display Executive Summary
         ↓
         [Executive Summary Card]
         └── "This sample exhibits high-risk behavior indicative of a
              trojan with backdoor capabilities. Key findings include
              process injection, registry persistence, and C2 communication
              over HTTPS. Immediate containment recommended."

STEP 44: Display Key Findings
         ↓
         [Findings Table]
         ├── Persistence (Critical): Registry Run key modification
         ├── Defense Evasion (High): Process injection detected
         ├── Command & Control (High): HTTPS beaconing to 192.168.1.100
         └── Execution (Medium): Suspicious PowerShell usage

STEP 45: Display IOCs (Indicators of Compromise)
         ↓
         [IOC List - Searchable/Filterable]
         ├── IP: 192.168.1.100 (C2 Server)
         ├── Registry: HKCU\Software\Microsoft\Windows\CurrentVersion\Run
         ├── Mutex: Global\MalwareMutex2024
         ├── File: C:\Users\Admin\AppData\Roaming\backdoor.exe
         └── Hash: <SHA256 of dropped file>

STEP 46: Display MITRE ATT&CK Mapping
         ↓
         [MITRE ATT&CK Matrix]
         └── Interactive matrix showing:
             ├── T1055 - Process Injection (Defense Evasion)
             ├── T1547.001 - Registry Run Keys (Persistence)
             └── T1071.001 - Web Protocols (Command and Control)

STEP 47: Display Recommendations
         ↓
         [Action Items - Priority Sorted]
         ├── 🔴 CRITICAL: Block IP 192.168.1.100 at firewall
         ├── 🟠 HIGH: Remove registry persistence mechanism
         ├── 🟡 MEDIUM: Scan for additional compromised systems
         └── 🟢 LOW: Update endpoint detection signatures

STEP 48: Display Raw Artifacts (Optional)
         ↓
         [Collapsible Sections]
         ├── 📊 Per-Tool Analysis Details
         │   ├── Sysmon (87% malicious, 12 findings)
         │   ├── Procmon (92% malicious, 8 findings)
         │   └── ... (6 tool results)
         ├── 📸 Screenshot Timeline (24 images)
         ├── 📁 Download Artifacts (35 files)
         └── 📄 View Raw Logs (XML, CSV, PCAP)
```

---

### **PHASE 10: EXPORT & ARCHIVAL** (Optional)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     EXPORT & ARCHIVAL OPTIONS                            │
└─────────────────────────────────────────────────────────────────────────┘

STEP 49: User Export Options
         ↓
         [Export Menu]
         ├── 📄 Export as PDF Report
         ├── 📊 Export as JSON (API-friendly)
         ├── 📝 Export as Markdown
         ├── 📦 Download Full Archive (all artifacts)
         └── 🔗 Share Report Link (read-only)

STEP 50: Historical Analysis Storage
         ↓
         [Database Record - Future]
         └── analyses table:
             ├── analysis_id: a1b2c3d4...
             ├── sample_sha256: <hash>
             ├── risk_score: 87
             ├── threat_level: high
             ├── created_at: 2026-03-18T17:42:00Z
             └── report_path: /reports/a1b2c3d4
```

---

## System State Diagram

Show the overall system state machine:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM STATE MACHINE                              │
└─────────────────────────────────────────────────────────────────────────┘

     [IDLE]
       ↓
   (User uploads sample)
       ↓
   [PENDING]
       ↓
   (Orchestrator starts)
       ↓
   [RUNNING]
       ├→ [VM_STARTING] → [VM_READY] ─┐
       ├→ [SAMPLE_COPYING] ───────────┤
       ├→ [EXECUTING] ────────────────┤
       │   ├→ Timeout reached         │
       │   └→ Sample exits early       │
       ├→ [COLLECTING] ───────────────┤
       └→ [PACKAGING] ────────────────┘
       ↓
   [RETRIEVING]
       ↓
   [COMPLETE] ←──────────────┐
       ↓                       │
   (Optional: AI analysis)     │
       ↓                       │
   [AI_ANALYZING]             │
       ├→ Per-tool agents      │
       └→ Summarizer agent     │
       ↓                       │
   [AI_COMPLETE] ─────────────┘
       ↓
   [ARCHIVED]

Error Paths:
   Any stage → [FAILED]
       ↓
   (Error logged, user notified)
       ↓
   [IDLE] (Ready for next analysis)
```

---

## Technology Stack Summary (Show as Icons)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TECHNOLOGY STACK                                  │
└─────────────────────────────────────────────────────────────────────────┘

FRONTEND:
├── 🌐 Next.js 16.1.6 (App Router)
├── ⚛️  React 19
├── 🎨 Tailwind CSS v3
├── 📱 TypeScript
└── 🎭 Material Design

BACKEND:
├── 🐍 Python 3.8+
├── ⚡ FastAPI
├── 🦄 Uvicorn
└── 🔗 httpx (HTTP client)

VIRTUALIZATION:
├── 📦 VirtualBox
├── 🪟 Windows 7 Sandbox VM
└── 🔧 VBoxManage CLI

MONITORING TOOLS (Guest):
├── 🔍 Sysmon
├── 📊 Process Monitor
├── 🌐 FakeNet-NG
├── 🔗 Tcpvcon64
├── 📂 Handle64
└── 📸 PowerShell (screenshots)

AI/ML:
├── 🤖 GitHub Copilot SDK
├── 🧠 GPT-5-mini Model
└── 🔄 Multi-Agent Architecture

STORAGE:
├── 📁 File System (artifacts)
├── 🗄️ SQLite (planned)
└── 📦 Zip Archives

NETWORKING:
├── 🌐 HTTP/HTTPS APIs
├── 🔒 Host-Only Network (192.168.56.0/24)
└── 📂 VirtualBox Shared Folder
```

---

## Performance Metrics (Add to Diagram)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       TYPICAL PERFORMANCE METRICS                        │
└─────────────────────────────────────────────────────────────────────────┘

PHASE                          | DURATION      | NOTES
───────────────────────────────┼───────────────┼──────────────────────────
User Upload                    | 2-5 seconds   | Depends on file size
VM Startup (if off)            | 30-60 seconds | Cached if already running
Sample Execution               | 10-300 sec    | User-configurable timeout
Artifact Collection            | 10-30 seconds | 7 collectors in sequence
Result Retrieval               | 5-10 seconds  | Depends on artifact size
AI Analysis (per-tool agents)  | 15-30 seconds | 6 agents parallel
AI Analysis (summarizer)       | 5-10 seconds  | Final synthesis
TOTAL (typical 120s timeout)   | 3-5 minutes   | End-to-end with AI

RESOURCE USAGE:
├── Disk Space per Analysis: ~50-200 MB
├── VM RAM: 2-4 GB allocated
├── Host RAM: 4-8 GB recommended
└── Network: Host-only (no internet)
```

---

## Security Boundaries (Show Visually)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SECURITY ARCHITECTURE                            │
└─────────────────────────────────────────────────────────────────────────┘

[TRUSTED ZONE - Host System]
├── User Interface (Next.js)
├── API Gateway (FastAPI)
├── Orchestrator
├── Storage
└── AI Analysis

       ↕ (Controlled Communication)
       ↕ (HTTP API + Shared Folder)

[ISOLATED ZONE - Sandbox VM]
├── 🔒 No Internet Access (Host-Only Network)
├── 🔒 No Direct File System Access
├── 🔒 Snapshot Restore After Each Run
├── ⚠️  MALWARE EXECUTES HERE
└── 📤 Results exported via shared folder only

SECURITY CONTROLS:
✓ Network isolation (192.168.56.0/24 host-only)
✓ File transfer via controlled shared folder
✓ VM snapshot revert for clean state
✓ No credentials or secrets in code
✓ Agent HTTP API: read-only status, write-only commands
```

---

## Title and Header for Diagram

**Main Title:** "IsoLens Malware Sandbox - Complete End-to-End Workflow"

**Subtitle:** "From Sample Upload to AI-Powered Threat Intelligence Report"

**Footer:** "Academic Mini-Project | Modular Architecture | AI-Enhanced Analysis | v1.3.0"

---

## Visual Design Notes

1. **Use light gray boxes or thin borders** instead of colored swimlanes to separate:
   - UI Layer (labeled "User Interface Layer")
   - API Layer (labeled "API Gateway Layer")
   - Orchestration Layer (labeled "Orchestration Layer")
   - VM/Sandbox Layer (labeled "Isolated Sandbox Environment" - can use subtle red tint)
   - AI Layer (labeled "AI Analysis Pipeline" - can use subtle blue/purple tint)
   - Storage Layer (labeled "Storage Layer")

2. **Numbered steps (1-50) with prominent flow arrows** showing progression - **all arrows labeled**

3. **Decision diamonds** for conditional paths with **clear labels** (e.g., "VM already running?", "AI analysis requested?")

4. **Parallel process indicators** for concurrent operations (6 AI agents) - use multiple arrows diverging/converging with labels

5. **Time indicators** on steps showing typical duration - as text annotations (e.g., "~30s", "2-5 min")

6. **Status badges** showing state at each phase (pending, running, complete) - simple text labels in boxes

7. **Minimal, strategic icons** for quick visual recognition:
   - Browser icon for UI
   - Server/API icon for gateway
   - Gear icon for orchestrator
   - Computer/VM icon for sandbox
   - Brain icon for AI agents
   - Database/folder icon for storage
   - **All icons must be labeled with text beneath/beside them**

8. **Highlight the AI pipeline** with a slightly bordered/shaded section and **detailed arrow flows between 6 agents → summarizer**

9. **Show data size/volume** as text labels where relevant (e.g., "~100MB artifacts", "247 events")

10. **Include a prominent legend** explaining:
    - Solid arrows = primary data flow
    - Dashed arrows = optional/conditional flow
    - Dotted arrows = monitoring/status checks
    - Line thickness = data volume
    - Box styles and their meanings
    - Icon meanings

---

## Output Format

- **High resolution**: Minimum 4000x3000 pixels (landscape or portrait)
- **Format**: PNG or SVG (vector preferred for presentations)
- **Background**: Clean white or very light gray (#F8F8F8) - print-friendly
- **Professional quality**: Suitable for academic defense or technical documentation
- **Clear readability**: All text legible at full zoom, high contrast
- **Logical flow**: Easy to follow from start to finish with clear arrow paths
- **Impressive detail**: Shows sophistication through well-organized structure and comprehensive labeling
- **Line-focused design**: Beautiful, clean connecting lines and arrows are the primary visual element
- **Minimal icons**: Use icons sparingly (5-10 total), always with accompanying text labels
- **Whitespace**: Generous spacing between components for clarity

---

## Target Audience

- Academic evaluators and reviewers
- Technical assessment panels
- Project documentation readers
- Future developers/contributors

## Purpose

Demonstrate the comprehensive, well-architected, multi-phase workflow of the IsoLens malware sandbox system, highlighting the integration of VM isolation, behavioral monitoring, and cutting-edge AI analysis for automated threat intelligence generation.

---

## Critical Design Requirements (Summary)

1. ✅ **WHITE BACKGROUND THEME** - Professional, clean, print-ready
2. ✅ **LINE AND ARROW FOCUSED** - Make connecting flows the star of the diagram
3. ✅ **MINIMAL ICONS** - Only 5-10 strategic icons, all clearly labeled with text
4. ✅ **LABEL EVERYTHING** - Every box, arrow, icon, and section must have clear text labels
5. ✅ **CLEAN AND SIMPLE** - No heavy colors, gradients, or unnecessary decoration
6. ✅ **HIGH CONTRAST** - Black text on white background for maximum readability
7. ✅ **PROFESSIONAL** - Suitable for academic presentation and technical documentation
