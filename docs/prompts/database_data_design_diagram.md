# IsoLens Database & Data Design Diagram - Image Generation Prompt

## 🎨 Design Theme Summary

**CRITICAL STYLING REQUIREMENTS:**
- ✅ **WHITE BACKGROUND** - Clean, professional, print-friendly theme
- ✅ **LINE-FOCUSED DESIGN** - Emphasis on arrows and connecting lines (not colored blocks)
- ✅ **MINIMAL ICONS** - Only 5-10 strategic icons total, all with text labels
- ✅ **LABEL EVERYTHING** - Clear text labels on every element (boxes, arrows, icons, sections)
- ✅ **HIGH CONTRAST** - Black lines and text on white background
- ✅ **NO HEAVY COLORS** - Subtle gray tones for grouping; minimal accent colors only for critical zones

---

## Design Requirements

Create a **professional, comprehensive, and visually impressive database/data design diagram** for the IsoLens Malware Sandbox System. This is an academic mini-project, so the diagram should look elaborate and well-structured to showcase the complexity and thoroughness of the system design.

---

## Visual Style Guidelines

- **Style**: Modern, clean, professional technical diagram with **white/light background**
- **Color Scheme**: 
  - **Minimalist approach**: Primarily black lines on white background
  - Use subtle gray tones for grouping/sections (light gray boxes for containers)
  - Accent colors ONLY for critical elements (e.g., red for malware execution zone, light blue for AI components)
  - No gradients or heavy shadows - keep it clean and professional
  - High contrast for readability
- **Layout**: Top-to-bottom or left-to-right flow showing data lifecycle
- **Typography**: Clear, readable fonts; use different weights for headers vs details; ensure all text is **clearly labeled**
- **Icons**: Minimal, strategic icon usage (5-10 icons total for key components only - database, folder, AI, etc.) - **all icons must be labeled with text**
- **Connections**: **Emphasis on clean lines and arrows** showing data flow direction with **clear labels on all arrows**
- **Line Style**: Use solid lines for primary flows, dashed lines for optional/conditional flows, different arrow styles for different relationship types

---

## Main Components to Include

### 1. **STORAGE LAYER** (File System Hierarchy)

```
core/storage/
│
├── 📂 samples/
│   └── {sample_id}.bin/exe/dll
│       ├── Original malware samples
│       ├── Indexed by SHA256 hash
│       └── Immutable after upload
│
├── 📂 reports/
│   └── {analysis_id}/
│       ├── 📁 artifacts/
│       │   ├── sysmon/
│       │   │   ├── sysmon_events.xml
│       │   │   ├── sysmon_events.txt
│       │   │   └── sysmon_summary.json
│       │   ├── procmon/
│       │   │   ├── procmon.csv
│       │   │   └── procmon_summary.json
│       │   ├── network/
│       │   │   ├── capture.pcap
│       │   │   └── network_summary.json
│       │   ├── fakenet/
│       │   │   ├── fakenet.log
│       │   │   └── fakenet.pcap
│       │   ├── handle/
│       │   │   └── handle_snapshot.txt
│       │   ├── tcpvcon/
│       │   │   └── tcpvcon_snapshot.csv
│       │   └── metadata.json
│       │
│       ├── 📁 screenshots/
│       │   ├── screenshot_0000.png
│       │   ├── screenshot_0001.png
│       │   └── ... (timestamped captures)
│       │
│       ├── 📁 ai_analysis/
│       │   ├── tool_results/
│       │   │   ├── sysmon_analysis.json
│       │   │   ├── procmon_analysis.json
│       │   │   ├── network_analysis.json
│       │   │   ├── handle_analysis.json
│       │   │   ├── tcpvcon_analysis.json
│       │   │   └── metadata_analysis.json
│       │   ├── threat_report.json
│       │   └── full_analysis_log.txt
│       │
│       └── 📄 analysis_summary.json
│
├── 📂 logs/
│   ├── gateway.log
│   ├── orchestrator.log
│   └── agent_{timestamp}.log
│
└── 📂 database/
    └── isolens.db (SQLite - Future implementation)
```

---

### 2. **DATA MODELS** (Python Dataclasses & Pydantic Models)

Show these as structured entities with their fields:

#### **AnalysisResult** (Core Analysis Record)
```
AnalysisResult
├── analysis_id: str (UUID)
├── sample_name: str
├── status: enum ["pending", "running", "complete", "failed"]
├── started_at: datetime (ISO-8601)
├── completed_at: datetime (ISO-8601)
├── timeout: int (seconds)
├── error: Optional[str]
├── report_dir: str (path)
├── sysmon_events: int (count)
├── files_collected: List[str]
└── agent_package: Optional[str] (zip path)
```

#### **ThreatAnalysisReport** (AI Analysis Results)
```
ThreatAnalysisReport
├── analysis_id: str (UUID)
├── model: str ("gpt-5-mini")
├── started_at: datetime
├── completed_at: datetime
├── status: enum ["pending", "running", "complete", "failed"]
├── error: Optional[str]
│
├── 🎯 RISK ASSESSMENT
│   ├── risk_score: int (0-100)
│   ├── threat_level: enum ["none", "low", "medium", "high", "critical"]
│   └── classification_confidence: int (0-100)
│
├── 🦠 CLASSIFICATION
│   ├── malware_type: str (e.g., "trojan", "ransomware", "spyware")
│   ├── malware_family: str (e.g., "Emotet", "WannaCry")
│   └── platform: str (e.g., "Windows", "Cross-platform")
│
├── 📊 ANALYSIS OUTPUTS
│   ├── executive_summary: str
│   ├── detailed_analysis: str
│   ├── key_findings: List[Finding]
│   ├── iocs: List[IOC]
│   ├── mitre_attack: List[Technique]
│   ├── recommendations: List[Recommendation]
│   └── raw_summary: str
│
└── 🔍 TOOL RESULTS
    └── tool_results: List[ToolAnalysisResult]
```

#### **ToolAnalysisResult** (Per-Collector AI Analysis)
```
ToolAnalysisResult
├── tool: str ("sysmon", "procmon", "network", etc.)
├── agent_name: str ("sysmon-analyzer", etc.)
├── verdict: enum ["clean", "suspicious", "malicious", "inconclusive"]
├── confidence: int (0-100)
├── findings_count: int
├── iocs_count: int
├── summary: str
├── findings: List[Finding]
│   └── Finding
│       ├── type: str
│       ├── severity: str
│       ├── description: str
│       └── evidence: str
├── iocs: List[IOC]
│   └── IOC
│       ├── type: str ("ip", "domain", "hash", "file", "registry")
│       ├── value: str
│       └── context: str
├── raw_response: str (XML/JSON)
└── error: Optional[str]
```

#### **AgentConfig** (VM Agent Connection)
```
AgentConfig
├── host: str (default: "192.168.56.105")
├── port: int (default: 9090)
├── timeout: int (HTTP timeout in seconds)
└── vm_name: str (VirtualBox VM name)
```

#### **API Models** (FastAPI Request/Response)
```
StandardResponse
├── status: enum ["ok", "error"]
├── data: Optional[dict]
└── error: Optional[ErrorPayload]
    ├── message: str
    └── details: Optional[str]

AnalysisSubmitRequest
└── timeout: int (10-300 seconds)

AnalysisStatusResponse
├── analysis_id: Optional[str]
├── sample_name: Optional[str]
├── status: Optional[str]
├── started_at: Optional[str]
├── completed_at: Optional[str]
└── report_dir: Optional[str]
```

---

### 3. **DATA FLOW ARCHITECTURE**

Show the complete data lifecycle with numbered steps and arrows:

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA FLOW PIPELINE                          │
└─────────────────────────────────────────────────────────────────┘

1. USER UPLOAD
   ↓
   [File Upload via Next.js UI]
   ↓
2. API INGESTION
   ↓
   [FastAPI Gateway: POST /api/analysis/submit]
   ↓
   [Save to storage/samples/{sha256}]
   ↓
3. VM EXECUTION
   ↓
   [Copy sample to SandboxShare/]
   ↓
   [Orchestrator → Agent HTTP API: POST /api/execute]
   ↓
   [Agent executes sample for {timeout} seconds]
   ↓
4. ARTIFACT COLLECTION
   ↓
   [7 Collectors gather data in parallel]
   ├── SysmonCollector → sysmon_events.xml
   ├── ProcmonCollector → procmon.csv
   ├── NetworkCollector → capture.pcap
   ├── FakeNetCollector → fakenet.log
   ├── ScreenshotCollector → screenshots/*.png
   ├── HandleCollector → handle_snapshot.txt
   └── TcpvconCollector → tcpvcon_snapshot.csv
   ↓
   [Agent packages to results_{analysis_id}.zip]
   ↓
   [Agent exports to SandboxShare/]
   ↓
5. HOST RETRIEVAL
   ↓
   [Orchestrator retrieves zip from SandboxShare/]
   ↓
   [Unpack to storage/reports/{analysis_id}/artifacts/]
   ↓
6. AI ANALYSIS (Optional)
   ↓
   [User triggers: POST /api/analysis/report/{id}/ai-analyze]
   ↓
   [ThreatAnalyzer loads artifacts]
   ↓
   [Dispatch to 6 specialized Copilot agents in parallel]
   ├── sysmon-analyzer (Sysmon XML)
   ├── procmon-analyzer (Procmon JSON)
   ├── network-analyzer (Network summary)
   ├── handle-analyzer (Handle snapshot)
   ├── tcpvcon-analyzer (TCPVcon CSV)
   └── metadata-analyzer (Execution metadata)
   ↓
   [Collect 6 JSON responses]
   ↓
   [Feed all to threat-summarizer agent]
   ↓
   [Generate final ThreatAnalysisReport JSON]
   ↓
   [Save to storage/reports/{analysis_id}/ai_analysis/]
   ↓
7. REPORT DISPLAY
   ↓
   [UI fetches: GET /api/analysis/report/{id}/ai-report]
   ↓
   [Display risk score, findings, IOCs, MITRE ATT&CK]
```

---

### 4. **DATABASE SCHEMA** (Future Implementation)

Show a professional ER diagram for the planned SQLite database:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLANNED DATABASE SCHEMA                       │
│                      (SQLite - Future)                           │
└─────────────────────────────────────────────────────────────────┘

TABLE: analyses
├── PK: analysis_id (TEXT, UUID)
├── sample_sha256 (TEXT, INDEX)
├── sample_name (TEXT)
├── sample_size (INTEGER)
├── status (TEXT)
├── started_at (TIMESTAMP)
├── completed_at (TIMESTAMP)
├── timeout (INTEGER)
├── error_message (TEXT, NULL)
├── report_path (TEXT)
└── created_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

TABLE: samples
├── PK: sha256 (TEXT)
├── original_name (TEXT)
├── file_type (TEXT)
├── file_size (INTEGER)
├── first_seen (TIMESTAMP)
├── upload_count (INTEGER DEFAULT 1)
└── file_path (TEXT)

TABLE: artifacts
├── PK: artifact_id (INTEGER AUTOINCREMENT)
├── FK: analysis_id → analyses.analysis_id
├── collector_type (TEXT) -- "sysmon", "procmon", etc.
├── artifact_path (TEXT)
├── file_size (INTEGER)
├── collected_at (TIMESTAMP)
└── INDEX: (analysis_id, collector_type)

TABLE: ai_analyses
├── PK: ai_analysis_id (INTEGER AUTOINCREMENT)
├── FK: analysis_id → analyses.analysis_id (UNIQUE)
├── model (TEXT DEFAULT "gpt-5-mini")
├── risk_score (INTEGER)
├── threat_level (TEXT)
├── malware_type (TEXT)
├── malware_family (TEXT)
├── platform (TEXT)
├── classification_confidence (INTEGER)
├── executive_summary (TEXT)
├── started_at (TIMESTAMP)
├── completed_at (TIMESTAMP)
└── status (TEXT)

TABLE: iocs
├── PK: ioc_id (INTEGER AUTOINCREMENT)
├── FK: ai_analysis_id → ai_analyses.ai_analysis_id
├── ioc_type (TEXT) -- "ip", "domain", "hash", "file", "registry"
├── ioc_value (TEXT)
├── context (TEXT)
├── severity (TEXT)
└── INDEX: (ioc_type, ioc_value)

TABLE: mitre_techniques
├── PK: technique_id (INTEGER AUTOINCREMENT)
├── FK: ai_analysis_id → ai_analyses.ai_analysis_id
├── technique_id_code (TEXT) -- "T1055", "T1021", etc.
├── technique_name (TEXT)
├── tactic (TEXT)
├── description (TEXT)
└── INDEX: (ai_analysis_id)

TABLE: screenshots
├── PK: screenshot_id (INTEGER AUTOINCREMENT)
├── FK: analysis_id → analyses.analysis_id
├── filename (TEXT)
├── file_path (TEXT)
├── captured_at (TIMESTAMP)
├── sequence_number (INTEGER)
└── INDEX: (analysis_id, sequence_number)
```

---

### 5. **SHARED FOLDER EXCHANGE PROTOCOL**

Show the VirtualBox shared folder as a data exchange buffer:

```
┌─────────────────────────────────────────────────────────────────┐
│             SANDBOXSHARE/ (VirtualBox Shared Folder)             │
│                    Data Exchange Buffer                          │
└─────────────────────────────────────────────────────────────────┘

HOST SIDE: /home/user/Isolens/SandboxShare/
GUEST SIDE: \\VBOXSVR\SandboxShare\

INBOUND (Host → Guest):
├── sample_{timestamp}.exe  ← Orchestrator places sample here
└── Agent copies to C:\IsoLens\samples\

OUTBOUND (Guest → Host):
├── results_{analysis_id}.zip ← Agent exports collection here
└── Orchestrator retrieves and unpacks

LIFECYCLE:
1. Host writes sample
2. Guest reads and executes
3. Guest writes results
4. Host reads and processes
5. Cleanup after retrieval
```

---

### 6. **AI AGENT ARCHITECTURE**

Show the multi-agent AI pipeline as a structured diagram:

```
┌─────────────────────────────────────────────────────────────────┐
│          MULTI-AGENT AI ANALYSIS ARCHITECTURE                    │
│                (GitHub Copilot SDK - gpt-5-mini)                 │
└─────────────────────────────────────────────────────────────────┘

SPECIALIZED TOOL AGENTS (Parallel Execution):

┌──────────────────────┐
│  sysmon-analyzer     │ ← Sysmon XML (max 6000 chars)
│  Input: Process logs │
│  Output: JSON        │
│  Focus: Injection,   │
│         LOLBin abuse │
└──────────────────────┘

┌──────────────────────┐
│  procmon-analyzer    │ ← Procmon CSV summary
│  Input: File/Reg ops │
│  Output: JSON        │
│  Focus: Persistence, │
│         Data theft   │
└──────────────────────┘

┌──────────────────────┐
│  network-analyzer    │ ← Network capture summary
│  Input: Traffic data │
│  Output: JSON        │
│  Focus: C2, Exfil,   │
│         Beaconing    │
└──────────────────────┘

┌──────────────────────┐
│  handle-analyzer     │ ← Handle snapshot text
│  Input: Open handles │
│  Output: JSON        │
│  Focus: Mutex, Files │
└──────────────────────┘

┌──────────────────────┐
│  tcpvcon-analyzer    │ ← TCPVcon CSV snapshot
│  Input: Connections  │
│  Output: JSON        │
│  Focus: Active TCP   │
└──────────────────────┘

┌──────────────────────┐
│  metadata-analyzer   │ ← Execution metadata
│  Input: Runtime info │
│  Output: JSON        │
│  Focus: Evasion      │
└──────────────────────┘

         ↓ (All 6 JSON responses)
         ↓

┌──────────────────────────────────────┐
│     threat-summarizer (Agent 7)       │
│  Input: All 6 per-tool JSON results   │
│  Output: ThreatAnalysisReport JSON    │
│  Focus: Risk score, Classification,   │
│         MITRE ATT&CK, IOC synthesis   │
└──────────────────────────────────────┘

         ↓

┌──────────────────────────────────────┐
│     FINAL THREAT REPORT              │
│  ├── Risk Score (0-100)              │
│  ├── Threat Level                    │
│  ├── Malware Classification          │
│  ├── Key Findings                    │
│  ├── IOCs (deduplicated)             │
│  ├── MITRE ATT&CK Techniques         │
│  └── Recommendations                 │
└──────────────────────────────────────┘
```

---

## Additional Visual Elements to Include

1. **Legend/Key** explaining symbols, line styles, arrow types, and data types
2. **Cardinality notation** for relationships (1:1, 1:N, M:N) using standard ER diagram notation
3. **Data type annotations** (str, int, List, Optional, enum) - clearly labeled on each field
4. **Status state machines** showing lifecycle transitions with **labeled arrows**
5. **Volume indicators** (e.g., "~100MB per analysis", "~500 events per sample") - as text labels
6. **Timeline markers** showing typical durations - as text annotations
7. **Security zones** (isolated VM, host-only network, shared folder) - use light gray boxes with **clear labels**
8. **Version indicators** (e.g., "Schema v1.0", "Agent v1.3.0") - as text labels
9. **All components must have clear text labels** - no unlabeled icons or boxes
10. **Arrow labels** explaining what data flows between components

---

## Title and Header

Main Title: **"IsoLens Malware Sandbox - Database & Data Design Architecture"**

Subtitle: **"Comprehensive Data Model, Storage Schema & Multi-Agent AI Pipeline"**

Footer: Include version number, date, and "Academic Mini-Project"

---

## Output Format

- **High resolution**: Minimum 3000x2000 pixels
- **Format**: PNG or SVG (vector preferred for clarity)
- **Background**: Clean white or very light gray (#F8F8F8)
- **Professional quality**: Suitable for academic presentation or documentation (print-friendly)
- **Clear hierarchy**: Primary components prominent, details readable at zoom
- **Balanced layout**: Not too crowded, generous use of whitespace
- **Line-focused design**: Emphasis on clean, well-labeled connecting lines and arrows rather than colored blocks
- **Minimal icons**: Use icons sparingly (only for major component types), always with text labels

---

## Notes for the AI Generator

- This is an **academic mini-project**, so emphasize professionalism and detail
- The system is **modular and well-architected** - show this clearly with well-organized boxes and clear connecting lines
- Highlight the **AI multi-agent pipeline** as a key innovation (can use subtle light blue/purple tint for this section only)
- Show **data flow lifecycle** from upload to final report using **prominent, labeled arrows**
- Use **modern software architecture diagram conventions** (think UML, ER diagrams, system architecture diagrams)
- Make it look **impressive and comprehensive** for project evaluation
- **WHITE BACKGROUND THEME** - professional, clean, print-friendly
- **LINE-FOCUSED DESIGN** - arrows and connectors are the stars, not colored blocks
- **LABEL EVERYTHING** - every box, every arrow, every icon should have clear text labels
- **MINIMAL ICONS** - only use icons where they add real value (database symbol, folder, AI brain), always paired with text
- Use **consistent styling** throughout the diagram (same box styles, same arrow styles, same fonts)

---

**Target Audience**: Academic evaluators, technical reviewers, project documentation

**Purpose**: Demonstrate comprehensive data design, storage architecture, and AI integration in the IsoLens malware sandbox system.
