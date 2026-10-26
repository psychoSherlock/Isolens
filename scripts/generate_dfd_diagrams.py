#!/usr/bin/env python3
"""
Generate ultra-high-resolution, publication-quality Data Flow Diagrams (DFD)
for the IsoLens automated malware sandbox architecture:
  - Level 0 DFD (Context Diagram)
  - Level 1 DFD (Major System Processes)
  - Level 2 DFD (Granular Behavioral & Intelligence Processing Pipeline)

Outputs at 300 DPI across all report and documentation directories.
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch, PathPatch
from matplotlib.path import Path as MPath

# Colors
C_BG = "#ffffff"
C_TEXT_DARK = "#0f172a"      # Slate 900
C_TEXT_MUTED = "#334155"     # Slate 700
C_TEXT_LIGHT = "#ffffff"

# Entity Colors
C_ENTITY_BG = "#f8fafc"
C_ENTITY_BORDER = "#1e293b"
C_ENTITY_HEADER = "#1e293b"

# Process Colors (IsoLens 5-Phase color theme)
C_P0_BORDER = "#1e40af"       # Blue 800
C_P0_BG = "#eff6ff"
C_P1_BORDER = "#2563eb"       # Blue 600
C_P1_BG = "#f0f7ff"
C_P2_BORDER = "#4f46e5"       # Indigo 600
C_P2_BG = "#f5f3ff"
C_P3_BORDER = "#059669"       # Emerald 600
C_P3_BG = "#f0fdf4"
C_P4_BORDER = "#0d9488"       # Teal 600
C_P4_BG = "#f0fdfa"
C_P5_BORDER = "#7c3aed"       # Purple 600
C_P5_BG = "#faf5ff"
C_P6_BORDER = "#d97706"       # Amber 600
C_P6_BG = "#fffbeb"

# Data Store Colors
C_DS_BORDER = "#047857"       # Emerald 700
C_DS_BG = "#ecfdf5"

# Flow Colors
C_FLOW = "#334155"           # Slate 700
C_FLOW_ACCENT = "#2563eb"
C_LABEL_BG = "#ffffff"
C_LABEL_BORDER = "#cbd5e1"


def draw_entity(ax, x, y, w, h, name, description, icon_text=None):
    """Draw an External Entity (Terminator): Double rectangle / sharp-edged card."""
    # Outer box
    outer = Rectangle((x, y), w, h, facecolor=C_ENTITY_BG, edgecolor=C_ENTITY_BORDER, linewidth=2.0, zorder=2)
    ax.add_patch(outer)
    # Header bar
    hbar_h = h * 0.32
    hbar = Rectangle((x, y + h - hbar_h), w, hbar_h, facecolor=C_ENTITY_HEADER, edgecolor=C_ENTITY_BORDER, linewidth=1.0, zorder=3)
    ax.add_patch(hbar)

    # Title
    ax.text(x + w / 2, y + h - hbar_h / 2, name, color=C_TEXT_LIGHT, fontsize=10.5, fontweight="bold",
            ha="center", va="center", zorder=4)
    # Description lines
    lines = description.split("\n")
    line_y = y + h - hbar_h - 0.25
    for line in lines:
        ax.text(x + w / 2, line_y, line, color=C_TEXT_DARK, fontsize=8.5, ha="center", va="top", zorder=4)
        line_y -= 0.28


def draw_process(ax, x, y, w, h, pid, name, details, border_color, bg_color):
    """Draw a DFD Process: Smooth rounded card with process number badge."""
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.3",
                         facecolor=bg_color, edgecolor=border_color, linewidth=2.0, zorder=2)
    ax.add_patch(box)

    # Header area
    badge_w = 0.9
    badge_h = 0.45
    badge = FancyBboxPatch((x + 0.15, y + h - badge_h - 0.15), badge_w, badge_h,
                           boxstyle="round,pad=0.05,rounding_size=0.15",
                           facecolor=border_color, edgecolor=border_color, zorder=3)
    ax.add_patch(badge)
    ax.text(x + 0.15 + badge_w / 2, y + h - 0.15 - badge_h / 2, pid,
            color=C_TEXT_LIGHT, fontsize=9.5, fontweight="bold", ha="center", va="center", zorder=4)

    # Process Title
    ax.text(x + 0.2 + badge_w + 0.15, y + h - 0.15 - badge_h / 2, name,
            color=C_TEXT_DARK, fontsize=10.5, fontweight="bold", ha="left", va="center", zorder=4)

    # Separator line
    ax.plot([x + 0.15, x + w - 0.15], [y + h - 0.7, y + h - 0.7], color=border_color, lw=0.8, alpha=0.5, zorder=3)

    # Details lines
    lines = details.split("\n")
    cur_y = y + h - 0.92
    for line in lines:
        ax.text(x + 0.25, cur_y, line, color=C_TEXT_MUTED, fontsize=8.2, ha="left", va="top", zorder=4)
        cur_y -= 0.26


def draw_datastore(ax, x, y, w, h, ds_id, name, content):
    """Draw an Open-Ended DFD Data Store."""
    # Background
    bg = Rectangle((x, y), w, h, facecolor=C_DS_BG, edgecolor="none", zorder=1)
    ax.add_patch(bg)
    # Parallel lines (top and bottom open-ended style)
    ax.plot([x, x + w], [y + h, y + h], color=C_DS_BORDER, lw=2.2, zorder=3)
    ax.plot([x, x + w], [y, y], color=C_DS_BORDER, lw=2.2, zorder=3)
    # Left vertical boundary with ID partition
    id_w = 0.75
    ax.plot([x, x], [y, y + h], color=C_DS_BORDER, lw=2.2, zorder=3)
    ax.plot([x + id_w, x + id_w], [y, y + h], color=C_DS_BORDER, lw=1.2, zorder=3)

    # ID text
    ax.text(x + id_w / 2, y + h / 2, ds_id, color=C_DS_BORDER, fontsize=9.5, fontweight="bold",
            ha="center", va="center", zorder=4)
    # Name
    ax.text(x + id_w + 0.15, y + h - 0.25, name, color=C_TEXT_DARK, fontsize=9.5, fontweight="bold",
            ha="left", va="top", zorder=4)
    # Content summary
    ax.text(x + id_w + 0.15, y + 0.22, content, color=C_TEXT_MUTED, fontsize=7.8,
            ha="left", va="bottom", zorder=4)


def draw_flow(ax, p1, p2, label, label_pos=0.5, offset=(0, 0), connectionstyle="arc3,rad=0.0", color=C_FLOW):
    """Draw a directed flow arrow with a neat background capsule label."""
    arrow = FancyArrowPatch(p1, p2, connectionstyle=connectionstyle,
                            arrowstyle="-|>,head_length=5,head_width=3",
                            color=color, lw=1.5, zorder=5)
    ax.add_patch(arrow)

    # Calculate label position along line
    lx = p1[0] + (p2[0] - p1[0]) * label_pos + offset[0]
    ly = p1[1] + (p2[1] - p1[1]) * label_pos + offset[1]

    # Draw label box
    lbl = ax.text(lx, ly, label, fontsize=8.0, color=C_TEXT_DARK, fontweight="medium",
                  ha="center", va="center", zorder=7,
                  bbox=dict(boxstyle="round,pad=0.25", facecolor=C_LABEL_BG,
                            edgecolor=C_LABEL_BORDER, lw=0.8, alpha=0.95))


# ==============================================================================
# LEVEL 0 DFD (CONTEXT DIAGRAM)
# ==============================================================================
def generate_dfd_level_0(output_paths):
    fig, ax = plt.subplots(figsize=(16, 10.5), dpi=300)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 13)
    ax.axis("off")

    # Header Banner
    ax.text(10, 12.4, "Level 0 Data Flow Diagram (Context Diagram) — IsoLens Malware Sandbox",
            fontsize=15, fontweight="bold", color=C_TEXT_DARK, ha="center", va="center")
    ax.text(10, 12.0, "Boundary interaction between external entities, primary data stores, and central system process",
            fontsize=9.5, color=C_TEXT_MUTED, ha="center", va="center")

    # Central Process 0.0
    p_box = FancyBboxPatch((7.2, 4.6), 5.6, 3.4, boxstyle="round,pad=0.2,rounding_size=0.6",
                           facecolor="#eff6ff", edgecolor="#1e40af", lw=2.5, zorder=2)
    ax.add_patch(p_box)
    badge = FancyBboxPatch((9.1, 7.3), 1.8, 0.45, boxstyle="round,pad=0.05,rounding_size=0.15",
                           facecolor="#1e40af", edgecolor="#1e40af", zorder=3)
    ax.add_patch(badge)
    ax.text(10, 7.52, "PROCESS 0.0", color="#ffffff", fontsize=9.5, fontweight="bold", ha="center", va="center", zorder=4)
    ax.text(10, 6.75, "IsoLens Autonomous\nMalware Sandbox System",
            fontsize=13, fontweight="bold", color="#0f172a", ha="center", va="center", zorder=4)
    ax.text(10, 5.4,
            "• Isolated Hypervisor Detonation & Telemetry Collection\n"
            "• Static YARA Pattern & Capability Inspection\n"
            "• BiLSTM Sequential Modeling & Telemetry Normalization\n"
            "• Deterministic Offline Threat DB (160K+ IOCs)\n"
            "• 4-Tier AI Cascade & Multi-Agent Forensic Synthesis",
            fontsize=8.2, color="#334155", ha="center", va="center", zorder=4)

    # External Entities
    # E1: Security Analyst / User (Top-Left)
    draw_entity(ax, 0.8, 8.8, 4.6, 2.3, "Security Analyst / User",
                "• Submits executable binaries / scripts\n"
                "• Configures execution timeout & options\n"
                "• Inspects interactive triage dashboard\n"
                "• Exports forensic reports & ATT&CK maps")

    # E2: VirtualBox Guest VM Environment (Bottom-Left)
    draw_entity(ax, 0.8, 1.3, 4.6, 2.3, "VirtualBox Guest VM",
                "• Isolated Windows 10/11 Analysis Machine\n"
                "• In-guest agent (schtasks execution)\n"
                "• Sysinternals & Sysmon telemetry engines\n"
                "• Shared folder bridge (SandboxShare)")

    # E3: External Threat Intel Feeds (Top-Right)
    draw_entity(ax, 14.6, 8.8, 4.6, 2.3, "Threat Intelligence Feeds",
                "• Abuse.ch Feodo Tracker (Botnet C2)\n"
                "• URLhaus (Malware URLs & Hosts)\n"
                "• ThreatFox (Compromised IOCs & Tags)\n"
                "• Active compromised IP blocklists")

    # E4: Multi-Tier AI Provider Cloud (Bottom-Right)
    draw_entity(ax, 14.6, 1.3, 4.6, 2.3, "Multi-Tier AI Cascade",
                "• Tier 1: NVIDIA NIM (Llama-3.3-70B)\n"
                "• Tier 2: Google Gemini (2.0 Flash)\n"
                "• Tier 3: GitHub Copilot SDK (gpt-5-mini)\n"
                "• Tier 4: Local LAN Ollama (Llama-3.1-8B)")

    # Data Stores (Bottom Center & Top Center)
    draw_datastore(ax, 7.3, 1.1, 5.4, 1.1, "D1", "D1: Sample & Telemetry Store",
                   "Uploaded binaries, Sysmon XML, Procmon CSV, screenshots")
    draw_datastore(ax, 7.3, 9.7, 5.4, 1.1, "D2", "D2: Offline Threat Intel DB",
                   "SQLite B-Trees: 33K IPs, 38K domains, 89K URLs (160,716 IOCs)")
    draw_datastore(ax, 7.3, 2.5, 5.4, 1.1, "D3", "D3: Structured Forensic Reports",
                   "JSON/XML analysis dossiers, 0-100 risk scores, ATT&CK techniques")

    # Flows: Analyst <-> IsoLens
    draw_flow(ax, (5.4, 9.6), (7.2, 7.6), "Suspicious Sample & Detonation Parameters", connectionstyle="arc3,rad=-0.12", offset=(0, 0.2))
    draw_flow(ax, (7.2, 6.9), (5.4, 8.9), "Risk Score, ATT&CK Matrix & Forensic Reports", connectionstyle="arc3,rad=-0.12", offset=(0, -0.2))

    # Flows: VirtualBox VM <-> IsoLens
    draw_flow(ax, (7.2, 5.5), (5.4, 3.2), "Snapshot Restore & Sample Injection Commands", connectionstyle="arc3,rad=0.12", offset=(-0.2, -0.15))
    draw_flow(ax, (5.4, 2.5), (7.2, 4.9), "Raw Telemetry, Screenshot Frames & Process Trees", connectionstyle="arc3,rad=0.12", offset=(0.2, 0.15))

    # Flows: Threat Feeds -> IsoLens / D2
    draw_flow(ax, (14.6, 9.8), (12.7, 10.2), "Periodic Feed Ingestion", connectionstyle="arc3,rad=0.0", offset=(0, 0.18))
    draw_flow(ax, (10.0, 9.7), (10.0, 8.0), "Deterministic B-Tree Lookups (0.42 ms)", connectionstyle="arc3,rad=0.0", offset=(1.7, 0))

    # Flows: Multi-Tier AI <-> IsoLens
    draw_flow(ax, (12.8, 5.2), (14.6, 3.2), "Token-Minimized Analyst Prompts (94.3% reduction)", connectionstyle="arc3,rad=0.12", offset=(0.1, 0.2))
    draw_flow(ax, (14.6, 2.4), (12.8, 4.6), "Synthesized Threat Intelligence & Attribution", connectionstyle="arc3,rad=0.12", offset=(0, -0.2))

    # Flows: Data Stores <-> IsoLens
    draw_flow(ax, (9.0, 4.6), (9.0, 3.6), "Persist Forensic Dossier", connectionstyle="arc3,rad=0.0", offset=(-1.4, 0))
    draw_flow(ax, (10.8, 4.6), (10.8, 2.2), "Save Raw Artifacts & Hashes", connectionstyle="arc3,rad=0.0", offset=(1.5, 0))

    plt.tight_layout()
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=300, facecolor=C_BG)
    plt.close(fig)
    print("Level 0 DFD generated.")


# ==============================================================================
# LEVEL 1 DFD (MAJOR PROCESSES)
# ==============================================================================
def generate_dfd_level_1(output_paths):
    fig, ax = plt.subplots(figsize=(19, 13), dpi=300)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 16.5)
    ax.axis("off")

    # Header Banner
    ax.text(12, 15.9, "Level 1 Data Flow Diagram — Major System Decomposition",
            fontsize=16, fontweight="bold", color=C_TEXT_DARK, ha="center", va="center")
    ax.text(12, 15.4, "Functional decomposition of IsoLens: ingestion, orchestration, telemetry, normalization, AI synthesis, and visualization",
            fontsize=10, color=C_TEXT_MUTED, ha="center", va="center")

    # External Entities
    draw_entity(ax, 0.6, 12.2, 3.8, 2.3, "Security Analyst",
                "• Uploads executable sample\n• Configures analysis opts\n• Views triage dashboard\n• Exports PDF / XML report")
    draw_entity(ax, 0.6, 5.0, 3.8, 2.3, "VirtualBox Hypervisor",
                "• Clean snapshot restore\n• Shared folder transport\n• Headless execution engine\n• Host screenshot capture")
    draw_entity(ax, 19.6, 0.8, 3.8, 2.3, "AI Provider Cascade",
                "• NVIDIA NIM (70B)\n• Gemini 2.0 Flash\n• Copilot SDK (gpt-5-mini)\n• Local Ollama (8B)")
    draw_entity(ax, 19.6, 7.8, 3.8, 2.3, "Threat Feed Sources",
                "• Feodo Tracker\n• URLhaus & ThreatFox\n• Compromised IP blocklist")

    # Data Stores
    draw_datastore(ax, 6.2, 14.0, 4.4, 1.1, "D1", "D1: Sample Store", "Binary files, hashes, PE headers")
    draw_datastore(ax, 6.2, 1.0, 4.6, 1.1, "D2", "D2: Telemetry Store", "Sysmon, Procmon, screenshots, handles")
    draw_datastore(ax, 14.8, 8.4, 4.4, 1.1, "D3", "D3: Threat Intel DB", "SQLite: 160,716 indicators (B-Tree)")
    draw_datastore(ax, 14.8, 14.0, 4.4, 1.1, "D4", "D4: Forensic Reports", "JSON/XML dossiers, 0-100 risk score")

    # 6 Major Processes
    # P1.0: Ingestion & Static Triage
    draw_process(ax, 5.8, 9.6, 5.2, 3.0, "1.0", "Ingestion & Static Triage",
                 "• Next.js portal & FastAPI gateway upload\n"
                 "• Compute SHA-256 / SHA-1 / MD5 hashes\n"
                 "• Parse PE headers & section entropy\n"
                 "• YARA static scan (packers, evasion, anti-debug)",
                 C_P1_BORDER, C_P1_BG)

    # P2.0: Hypervisor Orchestration
    draw_process(ax, 5.8, 4.8, 5.2, 3.0, "2.0", "Hypervisor Orchestration",
                 "• Revert VM to clean base snapshot\n"
                 "• Mount shared folder (SandboxShare)\n"
                 "• Deliver sample into guest environment\n"
                 "• Trigger host VBoxManage screenshot loop",
                 C_P2_BORDER, C_P2_BG)

    # P3.0: Guest Execution & Telemetry
    draw_process(ax, 0.6, 0.8, 4.8, 3.2, "3.0", "In-Guest Telemetry",
                 "• Agent invokes binary via schtasks /it\n"
                 "• Sysmon: process trees, network, injection\n"
                 "• Procmon: deep file, registry, DLL operations\n"
                 "• Snapshots: Handle.exe & TCPVcon connections\n"
                 "• In-guest active screenshot capture",
                 C_P3_BORDER, C_P3_BG)

    # P4.0: Behavioral Normalization & BiLSTM
    draw_process(ax, 12.2, 2.6, 5.6, 3.4, "4.0", "Behavior Normalization & ML",
                 "• 99.998% OS noise filtering (754K -> 14 events)\n"
                 "• Procmon-to-API sequence bridge\n"
                 "• 2-layer BiLSTM sequential classifier\n"
                 "• Forward + backward context concatenation\n"
                 "• GUI Screen OCR & Laya System 1 threat triage",
                 C_P4_BORDER, C_P4_BG)

    # P5.0: Threat Intelligence & AI Synthesis
    draw_process(ax, 12.2, 8.4, 5.6, 3.4, "5.0", "Threat Intel & AI Synthesis",
                 "• Deterministic SQLite B-tree match (0.42 ms)\n"
                 "• Automated 4-tier AI cascade router\n"
                 "• 6 specialist sub-agents (94.3% token savings)\n"
                 "• Master Threat Summarizer agent fusion\n"
                 "• Multi-layer deterministic 0-100 risk scoring",
                 C_P5_BORDER, C_P5_BG)

    # P6.0: Report Delivery & Dashboard
    draw_process(ax, 18.2, 12.0, 5.2, 2.8, "6.0", "Dashboard Visualization",
                 "• VirusTotal-style hero gauge risk display\n"
                 "• MITRE ATT&CK technique mapping matrix\n"
                 "• Interactive execution screenshot carousel\n"
                 "• Comprehensive forensic audit logging",
                 C_P6_BORDER, C_P6_BG)

    # Connecting Data Flows
    # Analyst -> P1.0
    draw_flow(ax, (4.4, 13.0), (5.8, 11.6), "Upload Sample & Parameters", offset=(0, 0.2))
    # P1.0 -> D1
    draw_flow(ax, (8.4, 12.6), (8.4, 14.0), "Store Sample & Hashes", offset=(1.2, 0))
    # P1.0 -> P2.0
    draw_flow(ax, (8.4, 9.6), (8.4, 7.8), "Trigger Execution & YARA Pre-Check", offset=(1.7, 0))
    # P2.0 -> VirtualBox
    draw_flow(ax, (5.8, 6.2), (4.4, 6.2), "VBoxManage Commands", offset=(0, 0.2))
    # VirtualBox -> P3.0
    draw_flow(ax, (2.5, 5.0), (2.5, 4.0), "Guest Detonation", offset=(0.8, 0))
    # P3.0 -> D2
    draw_flow(ax, (5.4, 2.0), (6.2, 1.8), "Export Telemetry Package (ZIP)", offset=(0, 0.2))
    # D2 -> P4.0
    draw_flow(ax, (10.8, 1.8), (12.2, 3.4), "Raw Sysmon, Procmon, Handles", offset=(0.2, -0.2))
    # P4.0 -> P5.0
    draw_flow(ax, (15.0, 6.0), (15.0, 8.4), "BiLSTM Malice Score & Mapped Events", offset=(1.8, 0))
    # Feed -> D3
    draw_flow(ax, (19.6, 9.0), (19.2, 9.0), "Feed Updates", offset=(0, 0.2))
    # D3 <-> P5.0
    draw_flow(ax, (17.8, 9.6), (17.8, 10.4), "0.42 ms Local B-Tree Lookup", offset=(0.2, 0.4), connectionstyle="arc3,rad=-0.15")
    # P5.0 <-> AI Cascade
    draw_flow(ax, (17.8, 8.4), (20.5, 3.1), "Tool Prompts / AI Summaries", offset=(0.2, 0.2), connectionstyle="arc3,rad=0.15")
    # P5.0 -> D4
    draw_flow(ax, (16.0, 11.8), (16.0, 14.0), "Save Structured Forensic Dossier", offset=(1.6, 0))
    # D4 -> P6.0
    draw_flow(ax, (19.2, 14.5), (20.0, 14.8), "Read Report JSON", offset=(0, 0.2))
    # P6.0 -> Analyst
    draw_flow(ax, (20.0, 14.8), (4.4, 14.2), "Interactive Dashboard, Risk Score, MITRE Matrix", connectionstyle="arc3,rad=-0.18", offset=(0, 0.25))

    plt.tight_layout()
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=300, facecolor=C_BG)
    plt.close(fig)
    print("Level 1 DFD generated.")


# ==============================================================================
# LEVEL 2 DFD (DEEP-DIVE ANALYTICS & SYNTHESIS PIPELINE)
# ==============================================================================
def generate_dfd_level_2(output_paths):
    fig, ax = plt.subplots(figsize=(20, 13.5), dpi=300)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, 25)
    ax.set_ylim(0, 17)
    ax.axis("off")

    # Header Banner
    ax.text(12.5, 16.4, "Level 2 Data Flow Diagram — Behavioral Analytics & Multi-Tier AI Synthesis",
            fontsize=16, fontweight="bold", color=C_TEXT_DARK, ha="center", va="center")
    ax.text(12.5, 15.9, "Detailed internal subprocess decomposition of Normalization, BiLSTM Sequence Modeling, Threat Matching, and AI Cascade",
            fontsize=10, color=C_TEXT_MUTED, ha="center", va="center")

    # Inbound Data Store
    draw_datastore(ax, 0.8, 9.8, 4.4, 1.4, "D2", "D2: Telemetry Store",
                   "• Sysmon XML events\n• Procmon CSV operation stream\n• Execution screenshot frames\n• TCPVcon & Handle text dumps")

    # Outbound Data Store
    draw_datastore(ax, 19.8, 9.8, 4.4, 1.4, "D4", "D4: Final Reports",
                   "• Unified 0-100 deterministic score\n• MITRE ATT&CK technique matrix\n• Extracted deduplicated IOCs\n• Natural language executive summary")

    # Central Data Store
    draw_datastore(ax, 10.3, 14.0, 4.6, 1.3, "D3", "D3: Threat Intel DB",
                   "• SQLite B-Tree tables (160,716 rows)\n• 33,681 IPs, 38,033 Domains, 89,002 URLs")

    # Behavioral Processing Column (Processes 4.1 to 4.4)
    # 4.1: Noise Filtering
    draw_process(ax, 5.8, 12.0, 4.2, 2.5, "4.1", "Noise Scoping & Filter",
                 "• Process tree PID filtering\n"
                 "• Strip Windows loader noise\n"
                 "• 99.998% volume reduction\n"
                 "• Focus on suspicious activity",
                 C_P3_BORDER, C_P3_BG)

    # 4.2: Procmon Bridge
    draw_process(ax, 5.8, 8.4, 4.2, 2.5, "4.2", "Procmon-to-API Bridge",
                 "• Map operations to API tokens\n"
                 "• Slicing sliding-window sequences\n"
                 "• Sequence length normalizer\n"
                 "• Generate integer token indices",
                 C_P3_BORDER, C_P3_BG)

    # 4.3: BiLSTM Neural Classifier
    draw_process(ax, 5.8, 4.8, 4.2, 2.5, "4.3", "BiLSTM Classifier",
                 "• 32-dim token embedding\n"
                 "• 2-layer stacked BiLSTM\n"
                 "• Forward + backward context\n"
                 "• Malice score (peak F1: 97.6%)",
                 C_P4_BORDER, C_P4_BG)

    # 4.4: Screen OCR & Triage
    draw_process(ax, 5.8, 1.2, 4.2, 2.5, "4.4", "GUI Screen OCR Triage",
                 "• Host screenshot frame capture\n"
                 "• Tesseract OCR text extraction\n"
                 "• Ransom note & lockscreen triage\n"
                 "• System 1 model query / fallback",
                 C_P4_BORDER, C_P4_BG)

    # Threat Intelligence & AI Cascade Column (Processes 5.1 to 5.3)
    # 5.1: Deterministic Threat DB Matcher
    draw_process(ax, 11.2, 9.6, 4.6, 2.8, "5.1", "Deterministic IOC Match",
                 "• Sub-millisecond B-tree lookup (0.42 ms)\n"
                 "• Zero AI token consumption & 100% privacy\n"
                 "• Matches C2 IPs, malicious domains & URLs\n"
                 "• Extracts threat families (Emotet, Cobalt Strike)",
                 C_P3_BORDER, C_P3_BG)

    # 5.2: Multi-Agent Cascade Dispatcher
    draw_process(ax, 11.2, 4.0, 4.6, 3.6, "5.2", "AI Cascade & Sub-Agents",
                 "• 4-tier fallback router (NIM -> Gemini -> Copilot -> Ollama)\n"
                 "• Dispatches specialized analyst sub-agents:\n"
                 "   - sysmon-analyzer (injection & LOLBins)\n"
                 "   - procmon-analyzer (files & registry)\n"
                 "   - handle & tcpvcon analyzers\n"
                 "• Token minimization: 94.3% token savings",
                 C_P5_BORDER, C_P5_BG)

    # 5.3: Threat Summarizer & Multi-Layer Scorer
    draw_process(ax, 17.2, 5.0, 4.6, 4.2, "5.3", "Threat Summarizer & Arbiter",
                 "• Master Threat Summarizer synthesizes findings\n"
                 "• Explainable multi-layer risk scoring:\n"
                 "   1. Static YARA Capability Points\n"
                 "   2. BiLSTM Sequential Behavioral Malice\n"
                 "   3. Deterministic Threat DB Hits\n"
                 "   4. Behavioral Rule Heuristics\n"
                 "   5. AI Specialist Consensus\n"
                 "• Standardized MITRE ATT&CK technique mapping",
                 C_P6_BORDER, C_P6_BG)

    # Interconnecting Data Flows
    # D2 -> 4.1
    draw_flow(ax, (5.2, 10.8), (5.8, 12.8), "Raw Procmon & Sysmon", offset=(0, 0.2))
    # D2 -> 4.4
    draw_flow(ax, (3.0, 9.8), (5.8, 2.5), "Execution Screenshots", connectionstyle="arc3,rad=0.2", offset=(0.3, 0.2))
    # 4.1 -> 4.2
    draw_flow(ax, (7.9, 12.0), (7.9, 10.9), "Filtered Clean Operations", offset=(1.2, 0))
    # 4.2 -> 4.3
    draw_flow(ax, (7.9, 8.4), (7.9, 7.3), "Ordered API Sequences", offset=(1.1, 0))
    # 4.1 -> 5.1
    draw_flow(ax, (10.0, 13.0), (11.2, 11.6), "Extracted Network Endpoints", offset=(0.1, 0.2))
    # D3 <-> 5.1
    draw_flow(ax, (12.6, 14.0), (12.6, 12.4), "B-Tree Table Lookup", offset=(-1.0, 0))
    # 4.3 -> 5.3
    draw_flow(ax, (10.0, 5.5), (17.2, 5.5), "BiLSTM Probability", connectionstyle="arc3,rad=-0.15", offset=(0, -0.2))
    # 4.4 -> 5.3
    draw_flow(ax, (10.0, 2.2), (17.2, 6.0), "Visual Lockscreen Verdict", connectionstyle="arc3,rad=-0.15", offset=(0, -0.2))
    # 5.1 -> 5.3
    draw_flow(ax, (15.8, 10.5), (17.2, 8.5), "Verified C2 Hits & Family Tags", offset=(0, 0.2))
    # 5.1 -> 5.2
    draw_flow(ax, (13.5, 9.6), (13.5, 7.6), "Threat Intelligence Context", offset=(1.2, 0))
    # 5.2 -> 5.3
    draw_flow(ax, (15.8, 5.8), (17.2, 7.0), "Specialist Findings JSONs", offset=(0, 0.2))
    # 5.3 -> D4
    draw_flow(ax, (21.8, 8.2), (21.8, 9.8), "Final Analysis Dossier", offset=(1.1, 0))

    plt.tight_layout()
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=300, facecolor=C_BG)
    plt.close(fig)
    print("Level 2 DFD generated.")


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent

    # Destination lists for all three DFD diagrams
    dfd0_destinations = [
        root / "MajorProjectReport" / "figures" / "dfd_level_0_new.png",
        root / "MajorProjectReport" / "report_figures" / "dfd_level_0_new.png",
        root / "MajorProjectReport" / "modified" / "figures" / "dfd_level_0_new.png",
        root / "MajorProjectReport" / "modified" / "report_figures" / "dfd_level_0_new.png",
        root / "Miniproject_Report" / "figure" / "dfd_level_0_new.png",
        root / "docs" / "figures" / "dfd_level_0_new.png",
    ]

    dfd1_destinations = [
        root / "MajorProjectReport" / "figures" / "dfd_level_1_new.png",
        root / "MajorProjectReport" / "report_figures" / "dfd_level_1_new.png",
        root / "MajorProjectReport" / "modified" / "figures" / "dfd_level_1_new.png",
        root / "MajorProjectReport" / "modified" / "report_figures" / "dfd_level_1_new.png",
        root / "Miniproject_Report" / "figure" / "dfd_level_1_new.png",
        root / "docs" / "figures" / "dfd_level_1_new.png",
    ]

    dfd2_destinations = [
        root / "MajorProjectReport" / "figures" / "dfd_level_2_new.png",
        root / "MajorProjectReport" / "report_figures" / "dfd_level_2_new.png",
        root / "MajorProjectReport" / "modified" / "figures" / "dfd_level_2_new.png",
        root / "MajorProjectReport" / "modified" / "report_figures" / "dfd_level_2_new.png",
        root / "Miniproject_Report" / "figure" / "dfd_level_2_new.png",
        root / "docs" / "figures" / "dfd_level_2_new.png",
    ]

    print("Generating Level 0 DFD...")
    generate_dfd_level_0(dfd0_destinations)

    print("Generating Level 1 DFD...")
    generate_dfd_level_1(dfd1_destinations)

    print("Generating Level 2 DFD...")
    generate_dfd_level_2(dfd2_destinations)

    print("All DFD diagrams successfully generated at 300 DPI!")
