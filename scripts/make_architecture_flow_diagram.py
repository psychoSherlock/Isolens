#!/usr/bin/env python3
"""
Generate publication-quality, labeled architecture flow diagram for IsoLens.
Covers the entire end-to-end pipeline across 5 distinct phases:
  - Phase 1: Ingestion, Triage & Static Inspection
  - Phase 2: Hypervisor Orchestration & Dynamic Guest Execution
  - Phase 3: Deep Behavioral Analytics & Multi-Engine Machine Learning
  - Phase 4: Multi-Tier AI Cascade & Multi-Agent Intelligence Pipeline
  - Phase 5: Presentation, Explainability & User Delivery

Outputs:
  - docs/figures/fig8_overall_system_architecture_flow.png
  - Miniproject_Report/figure/overall_architecture_new.png
"""

import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_FIG_DIR = PROJECT_ROOT / "docs" / "figures"
REPORT_FIG_DIR = PROJECT_ROOT / "Miniproject_Report" / "figure"
DOCS_FIG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FIG_DIR.mkdir(parents=True, exist_ok=True)

# Color Palette (High contrast, modern cybersecurity palette on white background)
C_BG = "#ffffff"
C_PHASE_HEADER = "#0f172a"      # Deep slate 900
C_CARD_BG = "#f8fafc"           # Slate 50
C_CARD_BORDER = "#cbd5e1"       # Slate 300
C_INNER_CARD_BG = "#ffffff"     # White
C_INNER_BORDER = "#e2e8f0"      # Slate 200

# Phase Theme Accent Colors
C_P1 = "#2563eb"   # Phase 1: Royal Blue 600 (Ingestion / Static)
C_P2 = "#4f46e5"   # Phase 2: Indigo 600 (Hypervisor / Dynamic)
C_P3 = "#059669"   # Phase 3: Emerald 600 (Behavioral ML / Deterministic)
C_P4 = "#7c3aed"   # Phase 4: Purple 600 (AI Cascade / Multi-Agent)
C_P5 = "#d97706"   # Phase 5: Amber 600 (Presentation / UI / PDF)

# Text Colors
C_TEXT_DARK = "#0f172a"
C_TEXT_MUTED = "#475569"
C_TEXT_LIGHT = "#ffffff"

# High-impact accent tags
C_TAG_RED = "#dc2626"
C_TAG_GREEN = "#10b981"
C_TAG_AMBER = "#f59e0b"
C_TAG_BLUE = "#2563eb"
C_TAG_PURPLE = "#7c3aed"
C_TAG_CYAN = "#0891b2"


def draw_rounded_card(ax, x, y, w, h, bg_color, border_color, border_width=1.2, radius=0.8, zorder=1):
    """Draw a smooth rounded card with bounding box."""
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad={radius},rounding_size={radius}",
        facecolor=bg_color,
        edgecolor=border_color,
        linewidth=border_width,
        zorder=zorder
    )
    ax.add_patch(box)
    return box


def draw_badge(ax, x, y, text, bg_color, text_color=C_TEXT_LIGHT, font_size=8, pad=0.35, zorder=5):
    """Draw an inline pill badge."""
    ax.text(
        x, y, text,
        color=text_color,
        fontsize=font_size,
        fontweight="bold",
        va="center",
        ha="center",
        zorder=zorder,
        bbox=dict(
            boxstyle=f"round,pad={pad},rounding_size=0.4",
            facecolor=bg_color,
            edgecolor="none"
        )
    )


def draw_flow_arrow(ax, x1, y1, x2, y2, label="", color="#475569", rad=0.0, lw=2.2, zorder=4, label_pos=(0.5, 0.5), label_offset=(0, 0)):
    """Draw a directional flow arrow with optional label."""
    connectionstyle = f"arc3,rad={rad}" if rad != 0.0 else "arc3"
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        connectionstyle=connectionstyle,
        arrowstyle="-|>",
        mutation_scale=17,
        color=color,
        linewidth=lw,
        linestyle="-",
        zorder=zorder
    )
    ax.add_patch(arrow)
    if label:
        lx = x1 + (x2 - x1) * label_pos[0] + label_offset[0]
        ly = y1 + (y2 - y1) * label_pos[1] + label_offset[1]
        ax.text(
            lx, ly, label,
            color="#0f172a",
            fontsize=8.5,
            fontweight="bold",
            va="center",
            ha="center",
            zorder=zorder + 1,
            bbox=dict(
                boxstyle="round,pad=0.3,rounding_size=0.3",
                facecolor="#ffffff",
                edgecolor=color,
                linewidth=1.2,
                alpha=0.97
            )
        )


def build_architecture_diagram():
    fig = plt.figure(figsize=(24, 15.2), dpi=300, facecolor=C_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # ==========================================================================
    # 0. MAIN HEADER BANNER (Top: Y in [93.4, 98.8])
    # ==========================================================================
    draw_rounded_card(ax, 1.5, 93.4, 97.0, 5.4, "#0f172a", "#1e293b", border_width=1.5, radius=0.6, zorder=2)

    # Title
    ax.text(
        3.0, 96.8,
        "IsoLens: Autonomous Malware Sandbox Architecture & Behavioral Pipeline",
        color="#ffffff",
        fontsize=16.5,
        fontweight="bold",
        va="center",
        zorder=3
    )
    # Subtitle
    ax.text(
        3.0, 94.7,
        "End-to-End Workflow: Ingestion & Static Triage ➔ Hypervisor Dynamic Orchestration ➔ Multi-Engine Behavioral ML ➔ 4-Tier AI Cascade ➔ Explainable Presentation",
        color="#94a3b8",
        fontsize=9.5,
        fontweight="normal",
        va="center",
        zorder=3
    )
    # Status badges on the right
    draw_badge(ax, 72.0, 96.1, "160K+ C2 Threat DB", C_TAG_GREEN, font_size=8.5)
    draw_badge(ax, 81.3, 96.1, "BiLSTM Sequence ML", C_TAG_BLUE, font_size=8.5)
    draw_badge(ax, 90.0, 96.1, "4-Tier AI Cascade", C_TAG_PURPLE, font_size=8.5)
    draw_badge(ax, 96.2, 96.1, "VirtualBox 7.x", "#475569", font_size=8.5)


    # ==========================================================================
    # 1. PHASE 1: INGESTION, TRIAGE & STATIC INSPECTION (X: [1.5, 36.5], Y: [62.5, 92.0])
    # ==========================================================================
    # Phase Outer Container
    draw_rounded_card(ax, 1.5, 62.5, 35.0, 29.5, "#f0f7ff", "#bfdbfe", border_width=1.5, radius=0.8, zorder=1)

    # Phase Header Bar
    draw_rounded_card(ax, 2.0, 88.5, 34.0, 3.0, C_P1, "none", border_width=0, radius=0.4, zorder=2)
    ax.text(2.8, 90.0, "PHASE 1: INGESTION, TRIAGE & STATIC INSPECTION", color="#ffffff", fontsize=11, fontweight="bold", va="center", zorder=3)
    draw_badge(ax, 33.5, 90.0, "ENTRY TIER", "#1d4ed8", font_size=7.5)

    # 1A. User Interface & Upload Portal
    draw_rounded_card(ax, 2.5, 80.5, 33.0, 7.2, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 5.0, 86.2, "WEB UI", C_P1, font_size=7.5)
    ax.text(8.0, 86.2, "Next.js 14 Web Portal (App Router)", color=C_TEXT_DARK, fontsize=9.5, fontweight="bold", va="center", zorder=3)
    ax.text(3.5, 84.4, "• Drag-and-drop sample submission (PE binaries, scripts, installers)", color=C_TEXT_MUTED, fontsize=8.2, va="center", zorder=3)
    ax.text(3.5, 83.1, "• Execution parameters: Timeout (10-180s), screenshot capture interval (2-10s)", color=C_TEXT_MUTED, fontsize=8.2, va="center", zorder=3)
    ax.text(3.5, 81.8, "• Live execution progress monitor, real-time status polling, active analysis feed", color=C_TEXT_MUTED, fontsize=8.2, va="center", zorder=3)

    # Intra-phase arrow 1A -> 1B
    draw_flow_arrow(ax, 19.0, 80.5, 19.0, 79.7, color=C_P1, lw=1.8, zorder=3)

    # 1B. FastAPI REST Gateway
    draw_rounded_card(ax, 2.5, 72.5, 33.0, 7.2, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 5.2, 78.2, "GATEWAY", "#0284c7", font_size=7.5)
    ax.text(9.0, 78.2, "FastAPI System Gateway (:6969)", color=C_TEXT_DARK, fontsize=9.5, fontweight="bold", va="center", zorder=3)
    ax.text(3.5, 76.4, "• Endpoints: /api/analysis/submit, /status, /check-vm, /report/{id}/ai-analyze", color=C_TEXT_MUTED, fontsize=8.2, va="center", zorder=3)
    ax.text(3.5, 75.1, "• Strict Pydantic v2 schema validation, standardized JSON error envelopes", color=C_TEXT_MUTED, fontsize=8.2, va="center", zorder=3)
    ax.text(3.5, 73.8, "• Staging isolation in core/storage/samples/ with SHA-256 & MD5 hash generation", color=C_TEXT_MUTED, fontsize=8.2, va="center", zorder=3)

    # Intra-phase arrow 1B -> 1C
    draw_flow_arrow(ax, 19.0, 72.5, 19.0, 71.7, color=C_P1, lw=1.8, zorder=3)

    # 1C. Static Feature & YARA Capability Scanner
    draw_rounded_card(ax, 2.5, 63.5, 33.0, 8.2, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 5.2, 70.0, "YARA ENGINE", "#1d4ed8", font_size=7.5)
    ax.text(10.8, 70.0, "Static Capability & Evasion Scanner", color=C_TEXT_DARK, fontsize=9.5, fontweight="bold", va="center", zorder=3)
    ax.text(3.5, 68.2, "• packers_and_evasion.yar: UPX packing, anti-debugging, VM evasion patterns", color=C_TEXT_MUTED, fontsize=8.2, va="center", zorder=3)
    ax.text(3.5, 66.9, "• malware_capabilities.yar: Process hollowing, reflective DLL injection (T1055)", color=C_TEXT_MUTED, fontsize=8.2, va="center", zorder=3)
    ax.text(3.5, 65.6, "• Encoded PowerShell execution & obfuscated script downloaders (T1059.001)", color=C_TEXT_MUTED, fontsize=8.2, va="center", zorder=3)
    ax.text(3.5, 64.3, "• Zero-Execution Triage: Instant capability footprint before hypervisor dispatch", color="#1d4ed8", fontsize=8.2, fontweight="bold", va="center", zorder=3)


    # ==========================================================================
    # 2. PHASE 2: HYPERVISOR ORCHESTRATION & GUEST EXECUTION (X: [40.5, 98.5], Y: [62.5, 92.0])
    # ==========================================================================
    # Phase Outer Container
    draw_rounded_card(ax, 40.5, 62.5, 58.0, 29.5, "#f5f3ff", "#ddd6fe", border_width=1.5, radius=0.8, zorder=1)

    # Phase Header Bar
    draw_rounded_card(ax, 41.0, 88.5, 57.0, 3.0, C_P2, "none", border_width=0, radius=0.4, zorder=2)
    ax.text(41.8, 90.0, "PHASE 2: HYPERVISOR ORCHESTRATION & DYNAMIC GUEST EXECUTION", color="#ffffff", fontsize=11, fontweight="bold", va="center", zorder=3)
    draw_badge(ax, 94.5, 90.0, "ISOLATION TIER", "#3730a3", font_size=7.5)

    # 2A. Host Orchestrator & VBox Controller (Left sub-panel)
    draw_rounded_card(ax, 41.5, 73.0, 27.5, 14.7, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 44.5, 85.8, "CONTROLLER", C_P2, font_size=7.5)
    ax.text(49.2, 85.8, "Host Orchestrator & Hypervisor", color=C_TEXT_DARK, fontsize=9.5, fontweight="bold", va="center", zorder=3)
    ax.text(42.5, 84.0, "• sandbox_orchestrator.py + vbox_controller.py", color="#1e293b", fontsize=8.2, fontweight="bold", va="center", zorder=3)
    ax.text(42.5, 82.5, "• Automated Snapshot Revert: snapshot_restore_current", color=C_TEXT_MUTED, fontsize=8.0, va="center", zorder=3)
    ax.text(42.5, 81.1, "  guarantees 100% clean baseline & zero contamination", color="#4338ca", fontsize=8.0, fontweight="bold", va="center", zorder=3)
    ax.text(42.5, 79.5, "• Headless VM Start: VBoxManage startvm --type headless", color=C_TEXT_MUTED, fontsize=8.0, va="center", zorder=3)
    ax.text(42.5, 78.0, "• Dual Host-Side Screenshot Stream: Background thread calls", color=C_TEXT_MUTED, fontsize=8.0, va="center", zorder=3)
    ax.text(42.5, 76.7, "  VBoxManage controlvm screenshotpng every 4 seconds", color=C_TEXT_MUTED, fontsize=8.0, va="center", zorder=3)
    ax.text(42.5, 75.1, "• Shared Folder IPC: SandboxShare/ file transfer bridge", color=C_TEXT_MUTED, fontsize=8.0, va="center", zorder=3)
    ax.text(42.5, 73.8, "• Timeout Watchdog & Emergency Graceful Poweroff", color=C_TEXT_MUTED, fontsize=8.0, va="center", zorder=3)

    # Intra-phase connector 2A -> 2B (Shared Folder IPC Bridge)
    draw_flow_arrow(ax, 69.0, 80.0, 70.0, 80.0, color=C_P2, lw=1.8, zorder=3)

    # 2B. In-VM Guest Sandbox Agent (Right sub-panel)
    draw_rounded_card(ax, 70.0, 73.0, 28.0, 14.7, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 73.0, 85.8, "GUEST AGENT", "#4338ca", font_size=7.5)
    ax.text(78.5, 85.8, "In-VM Agent (isolens_agent.py)", color=C_TEXT_DARK, fontsize=9.5, fontweight="bold", va="center", zorder=3)
    ax.text(71.0, 84.0, "• Native Python Stdlib HTTP service (:9090 on 192.168.56.105)", color="#1e293b", fontsize=8.2, fontweight="bold", va="center", zorder=3)
    ax.text(71.0, 82.5, "• Zero pip dependencies (resilient to guest network isolation)", color="#059669", fontsize=8.0, fontweight="bold", va="center", zorder=3)
    ax.text(71.0, 81.1, "• Pre-Execution: Clears Sysmon baseline via wevtutil cl", color=C_TEXT_MUTED, fontsize=8.0, va="center", zorder=3)
    ax.text(71.0, 79.5, "• Execution: schtasks /it (interactive) or cmd /c start fallback", color=C_TEXT_MUTED, fontsize=8.0, va="center", zorder=3)
    ax.text(71.0, 78.0, "• Active Artifact Packaging: Compresses all logs & screenshots", color=C_TEXT_MUTED, fontsize=8.0, va="center", zorder=3)
    ax.text(71.0, 76.7, "  into results_<sample>_<timestamp>.zip for host extraction", color=C_TEXT_MUTED, fontsize=8.0, va="center", zorder=3)
    ax.text(71.0, 75.1, "• Unpacked to: core/storage/reports/<analysis_id>/artifacts/", color="#1e293b", fontsize=8.0, fontweight="bold", va="center", zorder=3)
    ax.text(71.0, 73.8, "• Manifest: analysis_manifest.json with full file index", color=C_TEXT_MUTED, fontsize=8.0, va="center", zorder=3)

    # Intra-phase arrow 2B -> 2C (Agent drives collectors)
    draw_flow_arrow(ax, 84.0, 73.0, 84.0, 72.0, color=C_P2, lw=1.8, zorder=3)

    # 2C. Pluggable 5-Collector Matrix (Bottom sub-panel of Phase 2)
    draw_rounded_card(ax, 41.5, 63.3, 56.5, 8.8, C_INNER_CARD_BG, "#c7d2fe", radius=0.4, zorder=2)
    ax.text(42.5, 70.5, "PLUGGABLE 5-COLLECTOR TELEMETRY MATRIX (In-Guest Continuous Behavioral Capture):", color="#312e81", fontsize=8.8, fontweight="bold", va="center", zorder=3)

    # 5 Collector Chips
    # Collector 1: Sysmon
    draw_rounded_card(ax, 42.0, 64.0, 10.6, 5.7, "#f8fafc", "#cbd5e1", radius=0.3, zorder=3)
    draw_badge(ax, 47.3, 68.3, "1. Sysmon", "#4338ca", font_size=7.2, zorder=4)
    ax.text(47.3, 66.8, "Kernel Event Logs", color=C_TEXT_DARK, fontsize=7.5, fontweight="bold", ha="center", zorder=4)
    ax.text(47.3, 65.5, "Process trees, DLL loads,", color=C_TEXT_MUTED, fontsize=6.8, ha="center", zorder=4)
    ax.text(47.3, 64.6, "net sockets (sysmon.xml)", color=C_TEXT_MUTED, fontsize=6.8, ha="center", zorder=4)

    # Collector 2: Procmon
    draw_rounded_card(ax, 53.2, 64.0, 10.6, 5.7, "#f8fafc", "#cbd5e1", radius=0.3, zorder=3)
    draw_badge(ax, 58.5, 68.3, "2. Procmon", "#4338ca", font_size=7.2, zorder=4)
    ax.text(58.5, 66.8, "Process Monitor", color=C_TEXT_DARK, fontsize=7.5, fontweight="bold", ha="center", zorder=4)
    ax.text(58.5, 65.5, "High-res file, registry,", color=C_TEXT_MUTED, fontsize=6.8, ha="center", zorder=4)
    ax.text(58.5, 64.6, "process I/O (procmon.csv)", color=C_TEXT_MUTED, fontsize=6.8, ha="center", zorder=4)

    # Collector 3: Screenshots
    draw_rounded_card(ax, 64.4, 64.0, 10.6, 5.7, "#f8fafc", "#cbd5e1", radius=0.3, zorder=3)
    draw_badge(ax, 69.7, 68.3, "3. Screenshots", "#4338ca", font_size=7.2, zorder=4)
    ax.text(69.7, 66.8, "In-Guest GUI Stream", color=C_TEXT_DARK, fontsize=7.5, fontweight="bold", ha="center", zorder=4)
    ax.text(69.7, 65.5, "PowerShell [Drawing]", color=C_TEXT_MUTED, fontsize=6.8, ha="center", zorder=4)
    ax.text(69.7, 64.6, "captures user dialogs", color=C_TEXT_MUTED, fontsize=6.8, ha="center", zorder=4)

    # Collector 4: TCPVcon
    draw_rounded_card(ax, 75.6, 64.0, 10.6, 5.7, "#f8fafc", "#cbd5e1", radius=0.3, zorder=3)
    draw_badge(ax, 80.9, 68.3, "4. TCPVcon", "#4338ca", font_size=7.2, zorder=4)
    ax.text(80.9, 66.8, "Network Sockets", color=C_TEXT_DARK, fontsize=7.5, fontweight="bold", ha="center", zorder=4)
    ax.text(80.9, 65.5, "Active connections,", color=C_TEXT_MUTED, fontsize=6.8, ha="center", zorder=4)
    ax.text(80.9, 64.6, "ports (tcpvcon.csv)", color=C_TEXT_MUTED, fontsize=6.8, ha="center", zorder=4)

    # Collector 5: Handle
    draw_rounded_card(ax, 86.8, 64.0, 10.6, 5.7, "#f8fafc", "#cbd5e1", radius=0.3, zorder=3)
    draw_badge(ax, 92.1, 68.3, "5. Handle", "#4338ca", font_size=7.2, zorder=4)
    ax.text(92.1, 66.8, "Kernel Handles", color=C_TEXT_DARK, fontsize=7.5, fontweight="bold", ha="center", zorder=4)
    ax.text(92.1, 65.5, "Mutexes, named pipes,", color=C_TEXT_MUTED, fontsize=6.8, ha="center", zorder=4)
    ax.text(92.1, 64.6, "file locks (handle.txt)", color=C_TEXT_MUTED, fontsize=6.8, ha="center", zorder=4)


    # Flow Arrow 1 -> 2
    draw_flow_arrow(ax, 36.5, 77.0, 40.5, 77.0, label="Sample Staging &\nExecute Trigger", color=C_P1, lw=2.4, label_pos=(0.5, 0.5), label_offset=(0, 2.5))


    # ==========================================================================
    # 3. PHASE 3: DEEP BEHAVIORAL ANALYTICS & MULTI-ENGINE MACHINE LEARNING (X: [1.5, 98.5], Y: [32.0, 60.5])
    # ==========================================================================
    # Phase Outer Container (Full Width)
    draw_rounded_card(ax, 1.5, 32.0, 97.0, 28.5, "#ecfdf5", "#a7f3d0", border_width=1.5, radius=0.8, zorder=1)

    # Phase Header Bar
    draw_rounded_card(ax, 2.0, 56.8, 96.0, 3.0, C_P3, "none", border_width=0, radius=0.4, zorder=2)
    ax.text(2.8, 58.3, "PHASE 3: DEEP BEHAVIORAL ANALYTICS & MULTI-ENGINE MACHINE LEARNING INFERENCE", color="#ffffff", fontsize=11, fontweight="bold", va="center", zorder=3)
    draw_badge(ax, 93.0, 58.3, "ANALYTICS ENGINE TIER", "#047857", font_size=7.5)

    # Sub-Engine 3A: Procmon-to-LSTM Bridge & Telemetry Synthesizer
    draw_rounded_card(ax, 2.5, 41.0, 18.2, 15.0, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 6.0, 54.2, "API TRANSLATOR", C_P3, font_size=7.2)
    ax.text(2.8, 52.4, "Procmon-to-LSTM Bridge", color=C_TEXT_DARK, fontsize=9.0, fontweight="bold", va="center", zorder=3)
    ax.text(2.8, 51.0, "& Telemetry Synthesizer", color=C_P3, fontsize=8.2, fontweight="bold", va="center", zorder=3)
    ax.text(2.8, 49.3, "• procmon_lstm_bridge.py", color="#1e293b", fontsize=7.8, fontweight="bold", va="center", zorder=3)
    ax.text(2.8, 47.9, "• Canonical Windows API mapping", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)
    ax.text(2.8, 46.5, "• PE loader noise filter (LdrLoadDll)", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)
    ax.text(2.8, 44.9, "• Multi-Source Synthesizer:", color="#065f46", fontsize=7.6, fontweight="bold", va="center", zorder=3)
    ax.text(2.8, 43.6, "  Synthesizes API sequence from", color=C_TEXT_MUTED, fontsize=7.4, va="center", zorder=3)
    ax.text(2.8, 42.4, "  Sysmon/Registry if Procmon is 0", color=C_TEXT_MUTED, fontsize=7.4, va="center", zorder=3)

    # Sub-Engine 3B: BiLSTM Sequential Behavioral Classifier
    draw_rounded_card(ax, 21.3, 41.0, 18.2, 15.0, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 24.8, 54.2, "NEURAL NETWORK", "#0284c7", font_size=7.2)
    ax.text(21.6, 52.4, "BiLSTM Sequence Classifier", color=C_TEXT_DARK, fontsize=9.0, fontweight="bold", va="center", zorder=3)
    ax.text(21.6, 51.0, "2-Layer PyTorch Inference", color="#0284c7", fontsize=8.2, fontweight="bold", va="center", zorder=3)
    ax.text(21.6, 49.3, "• predict_lstm.py (PyTorch)", color="#1e293b", fontsize=7.8, fontweight="bold", va="center", zorder=3)
    ax.text(21.6, 47.9, "• 2-Layer Bidirectional LSTM (h=128)", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)
    ax.text(21.6, 46.5, "• 100-call sliding window evaluation", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)
    ax.text(21.6, 44.9, "• Output: p_malware vs p_benign,", color="#0369a1", fontsize=7.6, fontweight="bold", va="center", zorder=3)
    ax.text(21.6, 43.6, "  peak anomaly window range,", color=C_TEXT_MUTED, fontsize=7.4, va="center", zorder=3)
    ax.text(21.6, 42.4, "  API transition category breakdown", color=C_TEXT_MUTED, fontsize=7.4, va="center", zorder=3)

    # Sub-Engine 3C: Host Behavior Normalizer & MITRE Mapping
    draw_rounded_card(ax, 40.1, 41.0, 18.2, 15.0, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 43.6, 54.2, "BEHAVIOR AUDIT", "#059669", font_size=7.2)
    ax.text(40.4, 52.4, "Host Behavior Normalizer", color=C_TEXT_DARK, fontsize=9.0, fontweight="bold", va="center", zorder=3)
    ax.text(40.4, 51.0, "& MITRE ATT&CK Mapping", color="#059669", fontsize=8.2, fontweight="bold", va="center", zorder=3)
    ax.text(40.4, 49.3, "• behavior_normalizer.py", color="#1e293b", fontsize=7.8, fontweight="bold", va="center", zorder=3)
    ax.text(40.4, 47.9, "• File Drops: AppData, Temp, Sys32", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)
    ax.text(40.4, 46.5, "• Persistence: Run/RunOnce (T1547.001)", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)
    ax.text(40.4, 44.9, "• Defense Tampering: Disabling", color="#b91c1c", fontsize=7.6, fontweight="bold", va="center", zorder=3)
    ax.text(40.4, 43.6, "  Defender, UAC bypass (T1562.001)", color=C_TEXT_MUTED, fontsize=7.4, va="center", zorder=3)
    ax.text(40.4, 42.4, "• Sensitive file reads & credential recon", color=C_TEXT_MUTED, fontsize=7.4, va="center", zorder=3)

    # Sub-Engine 3D: Offline Network Threat Intelligence Matcher
    draw_rounded_card(ax, 58.9, 41.0, 19.5, 15.0, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 62.4, 54.2, "THREAT INTEL DB", "#d97706", font_size=7.2)
    ax.text(59.2, 52.4, "Deterministic Network C2 DB", color=C_TEXT_DARK, fontsize=9.0, fontweight="bold", va="center", zorder=3)
    ax.text(59.2, 51.0, "160,716 Malicious Indicators", color="#d97706", fontsize=8.2, fontweight="bold", va="center", zorder=3)
    ax.text(59.2, 49.3, "• network_db_matcher.py (SQLite)", color="#1e293b", fontsize=7.8, fontweight="bold", va="center", zorder=3)
    ax.text(59.2, 47.9, "• Ingestion: URLhaus, Feodo, ThreatFox", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)
    ax.text(59.2, 46.5, "• Zero Token Cost deterministic matching", color="#047857", fontsize=7.6, fontweight="bold", va="center", zorder=3)
    ax.text(59.2, 44.9, "• OS Noise Filter: Discards broadcast,", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)
    ax.text(59.2, 43.6, "  mDNS, SSDP, Windows Update noise", color=C_TEXT_MUTED, fontsize=7.4, va="center", zorder=3)
    ax.text(59.2, 42.4, "• Attribution: Emotet, Amadey, Cobalt", color=C_TEXT_MUTED, fontsize=7.4, va="center", zorder=3)

    # Sub-Engine 3E: GUI Application Window OCR & Threat Triage
    draw_rounded_card(ax, 79.0, 41.0, 19.0, 15.0, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 82.5, 54.2, "COMPUTER VISION", "#7c3aed", font_size=7.2)
    ax.text(79.3, 52.4, "GUI Window OCR & Triage", color=C_TEXT_DARK, fontsize=9.0, fontweight="bold", va="center", zorder=3)
    ax.text(79.3, 51.0, "Tesseract 5.5 + Laya Model", color="#7c3aed", fontsize=8.2, fontweight="bold", va="center", zorder=3)
    ax.text(79.3, 49.3, "• gui_analyzer.py (Dual Stream)", color="#1e293b", fontsize=7.8, fontweight="bold", va="center", zorder=3)
    ax.text(79.3, 47.9, "• Automated window contour extraction", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)
    ax.text(79.3, 46.5, "• Tesseract OCR on-screen text parsing", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)
    ax.text(79.3, 44.9, "• Laya System 1 Threat Classifier:", color="#6d28d9", fontsize=7.6, fontweight="bold", va="center", zorder=3)
    ax.text(79.3, 43.6, "  Ransomware extortion notes, locks,", color=C_TEXT_MUTED, fontsize=7.4, va="center", zorder=3)
    ax.text(79.3, 42.4, "  phishing, fake update scam alerts", color=C_TEXT_MUTED, fontsize=7.4, va="center", zorder=3)

    # 5 Convergence Feeder Arrows from 3A-3E into 3F (Risk Scorer)
    feeder_xs = [11.6, 30.4, 49.2, 68.6, 88.5]
    for fx in feeder_xs:
        draw_flow_arrow(ax, fx, 41.0, fx, 40.5, color="#059669", lw=1.6, zorder=3)

    # Sub-Engine 3F: Multi-Layer Deterministic Objective Risk Scorer (Unified Horizontal Strip)
    draw_rounded_card(ax, 2.5, 32.6, 95.5, 7.8, "#ffffff", "#6ee7b7", border_width=1.3, radius=0.4, zorder=2)
    draw_badge(ax, 7.5, 38.6, "RISK ARBITER", "#047857", font_size=7.5)
    ax.text(12.8, 38.6, "Multi-Layer Deterministic Risk Scorer (risk_scorer.py)", color="#064e3b", fontsize=9.5, fontweight="bold", va="center", zorder=3)

    # Mathematical equation & calibration rules
    ax.text(3.5, 36.8, "Calibrated Scoring Formula:   Score = min( 100,  ∑ [ w_i · Confidence_i ] )   across 5 Autonomous Detection Layers", color="#0f172a", fontsize=8.5, fontweight="bold", va="center", zorder=3)
    ax.text(3.5, 35.2, "• [Static YARA: max 25 pts]   • [BiLSTM Sequential: max 35 pts]   • [Host Behavior / MITRE: max 30 pts]   • [Network Threat DB: max 30 pts]   • [GUI Visual OCR: max 25 pts]", color=C_TEXT_MUTED, fontsize=7.8, va="center", zorder=3)
    ax.text(3.5, 33.7, "Calibrated Threat Levels:  Benign (0 - 19)  |  Low (20 - 39)  |  Medium (40 - 69)  |  High (70 - 89)  |  Critical (90 - 100) — Stored in risk_score.json", color="#065f46", fontsize=7.8, fontweight="bold", va="center", zorder=3)

    # Flow Arrow Phase 2 -> Phase 3
    draw_flow_arrow(ax, 69.5, 62.5, 69.5, 60.5, label="Unpacked Telemetry Artifacts (.csv, .xml, .txt, .png)", color=C_P2, lw=2.4, label_pos=(0.5, 0.5), label_offset=(11.5, 0))


    # ==========================================================================
    # 4. PHASE 4: MULTI-TIER AI CASCADE & MULTI-AGENT INTELLIGENCE (X: [1.5, 52.5], Y: [1.2, 30.5])
    # ==========================================================================
    # Phase Outer Container
    draw_rounded_card(ax, 1.5, 1.2, 51.0, 29.3, "#faf5ff", "#e9d5ff", border_width=1.5, radius=0.8, zorder=1)

    # Phase Header Bar
    draw_rounded_card(ax, 2.0, 27.5, 50.0, 2.6, C_P4, "none", border_width=0, radius=0.4, zorder=2)
    ax.text(2.8, 28.8, "PHASE 4: MULTI-TIER AI CASCADE & MULTI-AGENT INTELLIGENCE PIPELINE", color="#ffffff", fontsize=10.5, fontweight="bold", va="center", zorder=3)
    draw_badge(ax, 47.5, 28.8, "AI REASONING TIER", "#6b21a8", font_size=7.5)

    # 4A. 4-Tier Automated AI Cascade Router
    draw_rounded_card(ax, 2.5, 19.4, 49.0, 7.6, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 5.8, 25.5, "ROUTER", C_P4, font_size=7.2)
    ax.text(10.0, 25.5, "Automated 4-Tier Cascade Router (ai_router.py)", color=C_TEXT_DARK, fontsize=9.2, fontweight="bold", va="center", zorder=3)
    ax.text(3.5, 24.1, "Failover on timeout, rate-limits (HTTP 429), or authentication token exhaustion:", color=C_TEXT_MUTED, fontsize=7.8, va="center", zorder=3)

    # 4 Tier Boxes
    tier_w = 11.5
    tier_h = 4.0
    # Tier 1: NVIDIA NIM
    draw_rounded_card(ax, 3.2, 19.8, tier_w, tier_h, "#f8fafc", "#cbd5e1", radius=0.3, zorder=3)
    draw_badge(ax, 8.9, 22.8, "Tier 1: NVIDIA NIM", "#059669", font_size=6.8, zorder=4)
    ax.text(8.9, 21.4, "Llama-3.3-70B-Instruct", color=C_TEXT_DARK, fontsize=7.0, fontweight="bold", ha="center", zorder=4)
    ax.text(8.9, 20.3, "integrate.api.nvidia.com", color=C_TEXT_MUTED, fontsize=6.2, ha="center", zorder=4)

    # Tier 2: Gemini Flash
    draw_rounded_card(ax, 15.3, 19.8, tier_w, tier_h, "#f8fafc", "#cbd5e1", radius=0.3, zorder=3)
    draw_badge(ax, 21.0, 22.8, "Tier 2: Gemini Flash", "#2563eb", font_size=6.8, zorder=4)
    ax.text(21.0, 21.4, "gemini-2.0-flash", color=C_TEXT_DARK, fontsize=7.0, fontweight="bold", ha="center", zorder=4)
    ax.text(21.0, 20.3, "Generative Language API", color=C_TEXT_MUTED, fontsize=6.2, ha="center", zorder=4)

    # Tier 3: GitHub Copilot
    draw_rounded_card(ax, 27.4, 19.8, tier_w, tier_h, "#f8fafc", "#cbd5e1", radius=0.3, zorder=3)
    draw_badge(ax, 33.1, 22.8, "Tier 3: Copilot SDK", "#6b21a8", font_size=6.8, zorder=4)
    ax.text(33.1, 21.4, "gpt-5-mini Model", color=C_TEXT_DARK, fontsize=7.0, fontweight="bold", ha="center", zorder=4)
    ax.text(33.1, 20.3, "Local Auth Session", color=C_TEXT_MUTED, fontsize=6.2, ha="center", zorder=4)

    # Tier 4: Ollama Offline
    draw_rounded_card(ax, 39.5, 19.8, tier_w, tier_h, "#f8fafc", "#cbd5e1", radius=0.3, zorder=3)
    draw_badge(ax, 45.2, 22.8, "Tier 4: LAN Ollama", "#475569", font_size=6.8, zorder=4)
    ax.text(45.2, 21.4, "llama3.1:8b (Offline)", color=C_TEXT_DARK, fontsize=7.0, fontweight="bold", ha="center", zorder=4)
    ax.text(45.2, 20.3, "10.42.0.88:11434 / local", color=C_TEXT_MUTED, fontsize=6.2, ha="center", zorder=4)

    # Intra-phase arrow 4A -> 4B
    draw_flow_arrow(ax, 27.0, 19.4, 27.0, 18.6, color=C_P4, lw=1.8, zorder=3)

    # 4B. Specialized Multi-Agent Analysts
    draw_rounded_card(ax, 2.5, 9.8, 49.0, 8.8, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 6.0, 17.2, "SPECIALISTS", "#7c3aed", font_size=7.2)
    ax.text(12.2, 17.2, "Token-Minimized Specialist Tool Agents (copilot_agents.py)", color=C_TEXT_DARK, fontsize=9.2, fontweight="bold", va="center", zorder=3)
    ax.text(3.5, 15.9, "Targeted prompts with strict JSON schema contracts (eliminates context window bloat):", color=C_TEXT_MUTED, fontsize=7.8, va="center", zorder=3)

    # 6 Specialist Cards in 2x3 grid
    agents = [
        ("sysmon-analyzer", "Process Injection, LOLBins, Parent-Child Trees"),
        ("procmon-analyzer", "Filesystem Drops, Registry Persistence, Tampering"),
        ("network-analyzer", "C2 Communication, External Telemetry, Beaconing"),
        ("handle-analyzer", "Mutex Ownership, Named Pipes, Injection Handles"),
        ("tcpvcon-analyzer", "Active TCP/UDP Sockets, Listening Backdoor Ports"),
        ("metadata-analyzer", "Execution Anomalies, Timeout, Sandbox Evasion")
    ]
    for idx, (aname, adesc) in enumerate(agents):
        row = idx // 3
        col = idx % 3
        cx = 3.2 + col * 16.1
        cy = 13.0 - row * 2.8
        draw_rounded_card(ax, cx, cy, 15.5, 2.5, "#fdf4ff", "#f5d0fe", radius=0.25, zorder=3)
        ax.text(cx + 0.5, cy + 1.7, f"• {aname}", color="#86198f", fontsize=7.4, fontweight="bold", va="center", zorder=4)
        ax.text(cx + 0.5, cy + 0.7, adesc, color=C_TEXT_MUTED, fontsize=6.3, va="center", zorder=4)

    # Intra-phase arrow 4B -> 4C
    draw_flow_arrow(ax, 27.0, 9.8, 27.0, 8.8, color=C_P4, lw=1.8, zorder=3)

    # 4C. Threat Summarizer Master Agent
    draw_rounded_card(ax, 2.5, 1.8, 49.0, 7.0, C_INNER_CARD_BG, "#d8b4fe", border_width=1.2, radius=0.4, zorder=2)
    draw_badge(ax, 6.5, 7.4, "SUMMARIZER", "#581c87", font_size=7.2)
    ax.text(14.0, 7.4, "Threat Summarizer Master Agent (threat_analyzer.py)", color="#4c1d95", fontsize=9.2, fontweight="bold", va="center", zorder=3)
    ax.text(3.5, 5.9, "• Synthesizes structured JSON findings from all 6 specialist agents into threat_report.json", color=C_TEXT_MUTED, fontsize=7.8, va="center", zorder=3)
    ax.text(3.5, 4.6, "• Executive Threat Summary, Final Classification, Deduplicated IOCs (Files, IPs, Domains, Keys)", color=C_TEXT_MUTED, fontsize=7.8, va="center", zorder=3)
    ax.text(3.5, 3.3, "• Unified MITRE ATT&CK Matrix Mapping & Actionable Incident Response Recommendations", color="#4c1d95", fontsize=7.8, fontweight="bold", va="center", zorder=3)
    ax.text(3.5, 2.1, "• Output Staging: core/storage/reports/<analysis_id>/ai_analysis/ (ai_report.json, progress.json)", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)


    # Flow Arrow Phase 3 -> Phase 4
    draw_flow_arrow(ax, 25.0, 32.0, 25.0, 30.5, label="Structured Behavioral Findings & Summaries", color=C_P3, lw=2.4, label_pos=(0.5, 0.5), label_offset=(10.0, 0))


    # ==========================================================================
    # 5. PHASE 5: PRESENTATION, EXPLAINABILITY & USER DELIVERY (X: [55.5, 98.5], Y: [1.2, 30.5])
    # ==========================================================================
    # Phase Outer Container
    draw_rounded_card(ax, 55.5, 1.2, 43.0, 29.3, "#fffbeb", "#fde68a", border_width=1.5, radius=0.8, zorder=1)

    # Phase Header Bar
    draw_rounded_card(ax, 56.0, 27.5, 42.0, 2.6, C_P5, "none", border_width=0, radius=0.4, zorder=2)
    ax.text(56.8, 28.8, "PHASE 5: PRESENTATION, EXPLAINABILITY & USER DELIVERY", color="#ffffff", fontsize=10.5, fontweight="bold", va="center", zorder=3)
    draw_badge(ax, 93.5, 28.8, "DELIVERY TIER", "#b45309", font_size=7.5)

    # 5A. VirusTotal-Style Animated Hero Banner
    draw_rounded_card(ax, 56.5, 20.2, 41.0, 6.8, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 59.8, 25.4, "HERO BANNER", C_P5, font_size=7.2)
    ax.text(66.5, 25.4, "VirusTotal-Style Hero Gauge & Consensus Bar", color=C_TEXT_DARK, fontsize=9.2, fontweight="bold", va="center", zorder=3)
    ax.text(57.5, 23.9, "• 0-100 Dynamic SVG Radial Progress Gauge with smooth filling animation", color=C_TEXT_MUTED, fontsize=7.8, va="center", zorder=3)
    ax.text(57.5, 22.6, "• Color-Coded Severity Ring: Clean (Green), Low (Blue), Med (Amber), High/Crit (Red)", color=C_TEXT_MUTED, fontsize=7.8, va="center", zorder=3)
    ax.text(57.5, 21.3, "• Multi-Engine Consensus Ratio Bar (Flagged / Total) & Unified Verdict Badge", color="#b45309", fontsize=7.8, fontweight="bold", va="center", zorder=3)

    # 5B. Technical Overview & Distribution Charts
    draw_rounded_card(ax, 56.5, 11.2, 20.0, 8.5, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 59.5, 18.2, "ANALYTICS", "#0284c7", font_size=7.0)
    ax.text(64.2, 18.2, "Overview Dashboard", color=C_TEXT_DARK, fontsize=8.6, fontweight="bold", va="center", zorder=3)
    ax.text(57.2, 16.8, "• Windows API Category Chart:", color=C_TEXT_MUTED, fontsize=7.5, va="center", zorder=3)
    ax.text(57.2, 15.6, "  Process, File, Reg, Net, Memory", color=C_TEXT_MUTED, fontsize=7.3, va="center", zorder=3)
    ax.text(57.2, 14.3, "• MITRE ATT&CK Matrix Grid:", color=C_TEXT_MUTED, fontsize=7.5, va="center", zorder=3)
    ax.text(57.2, 13.1, "  Tactic badges & technique IDs", color=C_TEXT_MUTED, fontsize=7.3, va="center", zorder=3)
    ax.text(57.2, 11.9, "• Layered Risk Contribution Breakdown", color=C_TEXT_MUTED, fontsize=7.3, va="center", zorder=3)

    # 5C. Deep Evidence Explorer & Screenshots
    draw_rounded_card(ax, 77.0, 11.2, 20.5, 8.5, C_INNER_CARD_BG, C_INNER_BORDER, radius=0.4, zorder=2)
    draw_badge(ax, 80.2, 18.2, "EVIDENCE", "#059669", font_size=7.0)
    ax.text(85.2, 18.2, "Forensic Evidence Explorer", color=C_TEXT_DARK, fontsize=8.6, fontweight="bold", va="center", zorder=3)
    ax.text(77.7, 16.8, "• Raw Telemetry Event Streams:", color=C_TEXT_MUTED, fontsize=7.5, va="center", zorder=3)
    ax.text(77.7, 15.6, "  Sysmon, Procmon, TCPVcon, Handle", color=C_TEXT_MUTED, fontsize=7.3, va="center", zorder=3)
    ax.text(77.7, 14.3, "• BiLSTM Sequence Trace & Synthesized", color=C_TEXT_MUTED, fontsize=7.5, va="center", zorder=3)
    ax.text(77.7, 13.1, "• Screenshot Gallery & Ransomware Flags", color=C_TEXT_MUTED, fontsize=7.3, va="center", zorder=3)
    ax.text(77.7, 11.9, "• Dual Host / Guest screenshot viewer", color=C_TEXT_MUTED, fontsize=7.3, va="center", zorder=3)

    # 5D. AI Insights Tab & Vector PDF Export
    draw_rounded_card(ax, 56.5, 1.8, 41.0, 8.8, C_INNER_CARD_BG, "#fcd34d", border_width=1.2, radius=0.4, zorder=2)
    draw_badge(ax, 60.0, 9.0, "DELIVERY & PDF", "#b45309", font_size=7.2)
    ax.text(67.5, 9.0, "Multi-Agent AI Intelligence Tab & Multi-Page PDF Export", color="#78350f", fontsize=9.2, fontweight="bold", va="center", zorder=3)
    ax.text(57.5, 7.5, "• Interactive AI Insights Surface: Real-time pipeline stage animation & agent consensus breakdown", color=C_TEXT_MUTED, fontsize=7.8, va="center", zorder=3)
    ax.text(57.5, 6.2, "• Executive Forensic PDF Export (lib/pdf.ts): Built with jsPDF and html2canvas", color="#92400e", fontsize=7.8, fontweight="bold", va="center", zorder=3)
    ax.text(57.5, 4.9, "• Multi-Page Formal Report Generation: Executive summary, risk score gauge, MITRE matrix, IOC tables,", color=C_TEXT_MUTED, fontsize=7.8, va="center", zorder=3)
    ax.text(57.5, 3.6, "  behavioral timelines, and remediation recommendations for instant forensic audit compliance", color=C_TEXT_MUTED, fontsize=7.8, va="center", zorder=3)
    ax.text(57.5, 2.4, "• Historical Scan Archive: Instant reload and re-examination via /scan-history", color=C_TEXT_MUTED, fontsize=7.6, va="center", zorder=3)


    # Flow Arrow Phase 4 -> Phase 5
    draw_flow_arrow(ax, 52.5, 15.5, 55.5, 15.5, label="Final AI Intelligence &\nMITRE Synthesis", color=C_P4, lw=2.4, label_pos=(0.5, 0.5), label_offset=(0, 2.5))

    # Flow Arrow Phase 3 Direct -> Phase 5 (Deterministic Risk & Raw Evidence)
    draw_flow_arrow(ax, 82.0, 32.0, 82.0, 27.0, label="Risk Scores & Evidence", color=C_P3, lw=2.2, label_pos=(0.5, 0.5), label_offset=(6.0, 0))


    # Save figures to both locations
    for target_dir in [DOCS_FIG_DIR, REPORT_FIG_DIR]:
        p1 = target_dir / "fig8_overall_system_architecture_flow.png"
        fig.savefig(p1, bbox_inches="tight")
        print(f"[+] Saved: {p1}")

        # Also overwrite overall_architecture_new.png in Miniproject_Report
        if target_dir == REPORT_FIG_DIR:
            p2 = target_dir / "overall_architecture_new.png"
            fig.savefig(p2, bbox_inches="tight")
            print(f"[+] Overwrote: {p2}")

    plt.close(fig)


if __name__ == "__main__":
    build_architecture_diagram()
