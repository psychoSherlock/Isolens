#!/usr/bin/env python3
"""
Generate a clean, minimalist, icon-and-box architecture flow diagram for IsoLens.
Focuses strictly on:
  - Clean labeled boxes
  - Bold vector icons (Font Awesome)
  - Clear directional workflow arrows
  - 5 grouped phases with zero text clutter

Outputs:
  - docs/figures/fig8_system_architecture_flow_simple.png
  - Miniproject_Report/figure/overall_architecture_simple.png
"""

import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
from matplotlib.font_manager import FontProperties

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_FIG_DIR = PROJECT_ROOT / "docs" / "figures"
REPORT_FIG_DIR = PROJECT_ROOT / "Miniproject_Report" / "figure"
DOCS_FIG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FIG_DIR.mkdir(parents=True, exist_ok=True)

# Font Awesome setup
FA_PATH = "/usr/share/fonts/truetype/font-awesome/fa-solid-900.ttf"
fa_font = FontProperties(fname=FA_PATH)

# Palette
C_BG = "#ffffff"
C_TEXT_DARK = "#0f172a"
C_TEXT_MUTED = "#475569"

# Phase Theme Accents
P_COLORS = {
    "p1": {"accent": "#2563eb", "bg": "#f0f7ff", "border": "#bfdbfe"}, # Blue
    "p2": {"accent": "#4f46e5", "bg": "#f5f3ff", "border": "#ddd6fe"}, # Indigo
    "p3": {"accent": "#059669", "bg": "#ecfdf5", "border": "#a7f3d0"}, # Emerald
    "p4": {"accent": "#7c3aed", "bg": "#faf5ff", "border": "#e9d5ff"}, # Purple
    "p5": {"accent": "#d97706", "bg": "#fffbeb", "border": "#fde68a"}, # Amber
}


def draw_rounded_card(ax, x, y, w, h, bg_color, border_color, border_width=1.2, radius=0.6, zorder=1):
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


def draw_icon_box(ax, x, y, w, h, icon_char, title, subtitle, accent_color, zorder=2, icon_size=15):
    """Draw a clean, minimalist box with a circular icon badge and 2-line label."""
    # Box container
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.4,rounding_size=0.4",
        facecolor="#ffffff",
        edgecolor="#cbd5e1",
        linewidth=1.2,
        zorder=zorder
    )
    ax.add_patch(box)

    # Icon Circle
    circle_r = min(h * 0.32, 1.8)
    circle_x = x + circle_r + 0.8
    circle_y = y + h / 2.0
    circle = Circle(
        (circle_x, circle_y), circle_r,
        facecolor=accent_color,
        edgecolor="none",
        zorder=zorder + 1
    )
    ax.add_patch(circle)

    # Font Awesome Glyph centered in circle
    ax.text(
        circle_x, circle_y, icon_char,
        fontproperties=fa_font,
        fontsize=icon_size,
        color="#ffffff",
        ha="center",
        va="center",
        zorder=zorder + 2
    )

    # Text content on the right
    text_x = circle_x + circle_r + 1.2
    title_y = circle_y + h * 0.16
    sub_y = circle_y - h * 0.18

    ax.text(
        text_x, title_y, title,
        color=C_TEXT_DARK,
        fontsize=9.2,
        fontweight="bold",
        va="center",
        ha="left",
        zorder=zorder + 1
    )
    ax.text(
        text_x, sub_y, subtitle,
        color=C_TEXT_MUTED,
        fontsize=7.6,
        fontweight="normal",
        va="center",
        ha="left",
        zorder=zorder + 1
    )


def draw_flow_arrow(ax, x1, y1, x2, y2, label="", color="#475569", rad=0.0, lw=2.2, zorder=4, label_offset=(0, 0)):
    connectionstyle = f"arc3,rad={rad}" if rad != 0.0 else "arc3"
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        connectionstyle=connectionstyle,
        arrowstyle="-|>",
        mutation_scale=16,
        color=color,
        linewidth=lw,
        linestyle="-",
        zorder=zorder
    )
    ax.add_patch(arrow)
    if label:
        lx = (x1 + x2) / 2.0 + label_offset[0]
        ly = (y1 + y2) / 2.0 + label_offset[1]
        ax.text(
            lx, ly, label,
            color="#0f172a",
            fontsize=8.0,
            fontweight="bold",
            va="center",
            ha="center",
            zorder=zorder + 1,
            bbox=dict(
                boxstyle="round,pad=0.25,rounding_size=0.3",
                facecolor="#ffffff",
                edgecolor=color,
                linewidth=1.1,
                alpha=0.97
            )
        )


def build_simple_architecture_diagram():
    fig = plt.figure(figsize=(22, 13.5), dpi=300, facecolor=C_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # ==========================================================================
    # 0. HEADER BANNER (Top)
    # ==========================================================================
    draw_rounded_card(ax, 1.5, 93.6, 97.0, 5.2, "#0f172a", "#1e293b", border_width=1.5, radius=0.6, zorder=2)
    ax.text(
        3.0, 96.8,
        "IsoLens: Autonomous Malware Sandbox Architecture & Workflow",
        color="#ffffff",
        fontsize=16.0,
        fontweight="bold",
        va="center",
        zorder=3
    )
    ax.text(
        3.0, 94.8,
        "Simplified System Flow: Ingestion ➔ Hypervisor Orchestration ➔ Multi-Engine Behavioral ML ➔ 4-Tier AI Cascade ➔ User Delivery",
        color="#94a3b8",
        fontsize=9.2,
        fontweight="normal",
        va="center",
        zorder=3
    )

    # Phase Badges on top-right
    badges = [
        ("Phase 1: Ingestion", P_COLORS["p1"]["accent"]),
        ("Phase 2: Hypervisor", P_COLORS["p2"]["accent"]),
        ("Phase 3: Behavioral ML", P_COLORS["p3"]["accent"]),
        ("Phase 4: AI Cascade", P_COLORS["p4"]["accent"]),
        ("Phase 5: Presentation", P_COLORS["p5"]["accent"]),
    ]
    for i, (bname, bcol) in enumerate(badges):
        bx = 52.0 + i * 9.5
        ax.text(
            bx, 96.2, bname,
            color="#ffffff",
            fontsize=7.2,
            fontweight="bold",
            va="center",
            ha="center",
            zorder=3,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=bcol, edgecolor="none")
        )

    # ==========================================================================
    # 1. PHASE 1: INGESTION, TRIAGE & STATIC INSPECTION (X: [1.5, 36.5], Y: [63.0, 91.8])
    # ==========================================================================
    draw_rounded_card(ax, 1.5, 63.0, 35.0, 28.8, P_COLORS["p1"]["bg"], P_COLORS["p1"]["border"], border_width=1.5, radius=0.7)

    # Phase Header Bar
    draw_rounded_card(ax, 2.0, 87.8, 34.0, 3.2, P_COLORS["p1"]["accent"], "none", border_width=0, radius=0.4, zorder=2)
    ax.text(3.0, 89.4, "PHASE 1: INGESTION, TRIAGE & STATIC INSPECTION", color="#ffffff", fontsize=10.5, fontweight="bold", va="center", zorder=3)

    # Boxes in Phase 1
    # 1A: Web Client UI (\uf0ac = globe)
    draw_icon_box(ax, 2.5, 80.0, 33.0, 6.4, "\uf0ac", "Web Client Portal", "Next.js 14 App Router • File Upload & Parameters", P_COLORS["p1"]["accent"])

    # Arrow 1A -> 1B
    draw_flow_arrow(ax, 19.0, 80.0, 19.0, 78.4, color=P_COLORS["p1"]["accent"], lw=1.8)

    # 1B: FastAPI Gateway (\uf0e7 = bolt)
    draw_icon_box(ax, 2.5, 72.0, 33.0, 6.4, "\uf0e7", "FastAPI System Gateway", ":6969 • Pydantic Schema Validation & File Staging", "#0284c7")

    # Arrow 1B -> 1C
    draw_flow_arrow(ax, 19.0, 72.0, 19.0, 70.4, color=P_COLORS["p1"]["accent"], lw=1.8)

    # 1C: Static YARA Scanner (\uf002 = search)
    draw_icon_box(ax, 2.5, 64.0, 33.0, 6.4, "\uf002", "Static YARA Capability Scanner", "packers_and_evasion.yar & malware_capabilities.yar (T1059 / T1055)", "#1d4ed8")


    # Flow Arrow Phase 1 -> Phase 2
    draw_flow_arrow(ax, 36.5, 77.0, 40.5, 77.0, label="Sample Staging &\nExecute Trigger", color=P_COLORS["p1"]["accent"], lw=2.4, label_offset=(0, 2.5))


    # ==========================================================================
    # 2. PHASE 2: HYPERVISOR ORCHESTRATION & GUEST EXECUTION (X: [40.5, 98.5], Y: [63.0, 91.8])
    # ==========================================================================
    draw_rounded_card(ax, 40.5, 63.0, 58.0, 28.8, P_COLORS["p2"]["bg"], P_COLORS["p2"]["border"], border_width=1.5, radius=0.7)

    # Phase Header Bar
    draw_rounded_card(ax, 41.0, 87.8, 57.0, 3.2, P_COLORS["p2"]["accent"], "none", border_width=0, radius=0.4, zorder=2)
    ax.text(42.0, 89.4, "PHASE 2: HYPERVISOR ORCHESTRATION & DYNAMIC GUEST EXECUTION", color="#ffffff", fontsize=10.5, fontweight="bold", va="center", zorder=3)

    # 2A: Host Orchestrator (\uf233 = server)
    draw_icon_box(ax, 41.5, 76.5, 27.5, 9.8, "\uf233", "Host Orchestrator", "VBoxManage CLI • Clean Snapshot Revert\nDual Host Screenshot Loop (every 4s)", P_COLORS["p2"]["accent"])

    # Arrow 2A -> 2B (SharedFolder IPC)
    draw_flow_arrow(ax, 69.0, 81.4, 70.5, 81.4, label="IPC", color=P_COLORS["p2"]["accent"], lw=1.8)

    # 2B: In-VM Guest Agent (\uf544 = robot)
    draw_icon_box(ax, 70.5, 76.5, 27.0, 9.8, "\uf544", "In-VM Guest Agent", "isolens_agent.py on :9090 (Host-Only)\nPython Stdlib • Zero-Pip Isolation", "#4338ca")

    # Arrow 2B -> 2C
    draw_flow_arrow(ax, 84.0, 76.5, 84.0, 72.8, label="Drives Collectors", color=P_COLORS["p2"]["accent"], lw=1.8, label_offset=(5.5, 0))

    # 2C: 5 Telemetry Collectors (\uf5fd = layer-group)
    draw_icon_box(ax, 41.5, 64.0, 56.0, 8.4, "\uf5fd", "Pluggable 5-Collector Matrix (In-Guest Continuous Capture)", "Sysmon (Kernel Logs) • Procmon (Syscalls) • Screenshots (GUI) • TCPVcon (Sockets) • Handle (Mutexes)", "#3730a3", icon_size=16)


    # Flow Arrow Phase 2 -> Phase 3
    draw_flow_arrow(ax, 69.5, 63.0, 69.5, 60.5, label="Unpacked Telemetry Artifacts (.csv, .xml, .txt, .png)", color=P_COLORS["p2"]["accent"], lw=2.4, label_offset=(11.5, 0))


    # ==========================================================================
    # 3. PHASE 3: DEEP BEHAVIORAL ANALYTICS & MULTI-ENGINE ML (X: [1.5, 98.5], Y: [32.5, 60.5])
    # ==========================================================================
    draw_rounded_card(ax, 1.5, 32.5, 97.0, 28.0, P_COLORS["p3"]["bg"], P_COLORS["p3"]["border"], border_width=1.5, radius=0.7)

    # Phase Header Bar
    draw_rounded_card(ax, 2.0, 56.8, 96.0, 3.0, P_COLORS["p3"]["accent"], "none", border_width=0, radius=0.4, zorder=2)
    ax.text(3.0, 58.3, "PHASE 3: DEEP BEHAVIORAL ANALYTICS & MULTI-ENGINE MACHINE LEARNING INFERENCE", color="#ffffff", fontsize=10.5, fontweight="bold", va="center", zorder=3)

    # 5 Parallel Engines running side-by-side
    engine_w = 18.4
    engine_h = 10.5
    engine_y = 44.5

    # 3A: Procmon-to-LSTM Bridge (\uf120 = terminal)
    draw_icon_box(ax, 2.5, engine_y, engine_w, engine_h, "\uf120", "Procmon-to-LSTM Bridge", "Noise Filter & Fallback\nTelemetry Synthesizer", P_COLORS["p3"]["accent"], icon_size=14)

    # 3B: BiLSTM Sequence ML (\uf5dc = brain)
    draw_icon_box(ax, 22.0, engine_y, engine_w, engine_h, "\uf5dc", "BiLSTM Sequence ML", "2-Layer PyTorch Classifier\n100-Call Sliding Window", "#0284c7", icon_size=14)

    # 3C: Host Behavior Normalizer (\uf3ed = shield)
    draw_icon_box(ax, 41.5, engine_y, engine_w, engine_h, "\uf3ed", "Host Behavior Normalizer", "Persistence (T1547.001)\n& Defense Tampering Audit", "#059669", icon_size=14)

    # 3D: Offline Network Threat DB (\uf1c0 = database)
    draw_icon_box(ax, 61.0, engine_y, engine_w, engine_h, "\uf1c0", "Offline Threat DB", "160,716 C2 Indicators\nZero-Token C2 Matching", "#d97706", icon_size=14)

    # 3E: GUI Window OCR & Triage (\uf06e = eye)
    draw_icon_box(ax, 80.5, engine_y, engine_w, engine_h, "\uf06e", "GUI Window OCR & Triage", "Tesseract 5.5 + Laya\nRansomware / Scam Alert", "#7c3aed", icon_size=14)

    # 5 Downward Feeder Arrows into 3F (Risk Scorer)
    feeder_xs = [11.7, 31.2, 50.7, 70.2, 89.7]
    for fx in feeder_xs:
        draw_flow_arrow(ax, fx, 44.5, fx, 42.4, color=P_COLORS["p3"]["accent"], lw=1.6)

    # 3F: Multi-Layer Deterministic Risk Scorer (\uf140 = bullseye)
    draw_icon_box(ax, 2.5, 33.5, 95.5, 8.4, "\uf140", "Multi-Layer Deterministic Objective Risk Scorer (risk_scorer.py)", "Calibrated 0–100 Score Arbiter: min(100, ∑ [w_i · Conf_i]) across YARA (25), BiLSTM (35), Host (30), Network (30), and GUI (25) Layers", "#047857", icon_size=16)


    # Flow Arrow Phase 3 -> Phase 4
    draw_flow_arrow(ax, 25.0, 32.5, 25.0, 30.5, label="Structured Behavioral Findings & Summaries", color=P_COLORS["p3"]["accent"], lw=2.4, label_offset=(10.0, 0))


    # ==========================================================================
    # 4. PHASE 4: MULTI-TIER AI CASCADE & MULTI-AGENT PIPELINE (X: [1.5, 51.5], Y: [1.2, 30.5])
    # ==========================================================================
    draw_rounded_card(ax, 1.5, 1.2, 50.0, 29.3, P_COLORS["p4"]["bg"], P_COLORS["p4"]["border"], border_width=1.5, radius=0.7)

    # Phase Header Bar
    draw_rounded_card(ax, 2.0, 27.2, 49.0, 2.8, P_COLORS["p4"]["accent"], "none", border_width=0, radius=0.4, zorder=2)
    ax.text(3.0, 28.6, "PHASE 4: MULTI-TIER AI CASCADE & MULTI-AGENT PIPELINE", color="#ffffff", fontsize=10.0, fontweight="bold", va="center", zorder=3)

    # 4A: 4-Tier Fallback AI Router (\uf0e8 = sitemap)
    draw_icon_box(ax, 2.5, 19.0, 48.0, 7.2, "\uf0e8", "Automated 4-Tier Cascade AI Router (ai_router.py)", "Tier 1: NVIDIA NIM (Llama 70B) ➔ Tier 2: Gemini Flash ➔ Tier 3: Copilot ➔ Tier 4: LAN Ollama", P_COLORS["p4"]["accent"])

    # Arrow 4A -> 4B
    draw_flow_arrow(ax, 26.5, 19.0, 26.5, 17.6, color=P_COLORS["p4"]["accent"], lw=1.8)

    # 4B: 6 Specialist Tool Agents (\uf0c0 = users)
    draw_icon_box(ax, 2.5, 10.4, 48.0, 7.2, "\uf0c0", "6 Specialized Multi-Agent Analysts (copilot_agents.py)", "sysmon • procmon • network • handle • tcpvcon • metadata (Strict JSON Schema Output)", "#6b21a8")

    # Arrow 4B -> 4C
    draw_flow_arrow(ax, 26.5, 10.4, 26.5, 9.0, color=P_COLORS["p4"]["accent"], lw=1.8)

    # 4C: Threat Summarizer Agent (\uf46c = clipboard-check)
    draw_icon_box(ax, 2.5, 1.8, 48.0, 7.2, "\uf46c", "Threat Summarizer Master Agent (threat_analyzer.py)", "Executive Summary • Final Classification • Deduplicated IOCs • Unified MITRE Matrix", "#4c1d95")


    # Flow Arrow Phase 4 -> Phase 5
    draw_flow_arrow(ax, 51.5, 15.5, 54.5, 15.5, label="Synthesized AI Intelligence &\nRemediation Plan", color=P_COLORS["p4"]["accent"], lw=2.4, label_offset=(0, 2.5))

    # Flow Arrow Phase 3 Direct -> Phase 5 (Objective Scores & Evidence)
    draw_flow_arrow(ax, 82.0, 32.5, 82.0, 27.0, label="Risk Scores & Evidence", color=P_COLORS["p3"]["accent"], lw=2.2, label_offset=(6.0, 0))


    # ==========================================================================
    # 5. PHASE 5: PRESENTATION, EXPLAINABILITY & USER DELIVERY (X: [54.5, 98.5], Y: [1.2, 30.5])
    # ==========================================================================
    draw_rounded_card(ax, 54.5, 1.2, 44.0, 29.3, P_COLORS["p5"]["bg"], P_COLORS["p5"]["border"], border_width=1.5, radius=0.7)

    # Phase Header Bar
    draw_rounded_card(ax, 55.0, 27.2, 43.0, 2.8, P_COLORS["p5"]["accent"], "none", border_width=0, radius=0.4, zorder=2)
    ax.text(56.0, 28.6, "PHASE 5: PRESENTATION, EXPLAINABILITY & USER DELIVERY", color="#ffffff", fontsize=10.0, fontweight="bold", va="center", zorder=3)

    # 4 Presentation Boxes in 2x2 grid
    p5_w = 20.8
    p5_h = 11.2

    # 5A: VirusTotal Hero Banner (\uf091 = trophy)
    draw_icon_box(ax, 55.5, 15.0, p5_w, p5_h, "\uf091", "VirusTotal Hero Banner", "Animated 0–100 Radial Gauge\nConsensus Ratio Bar & Severity Ring", P_COLORS["p5"]["accent"], icon_size=15)

    # 5B: Technical Analytics Dashboard (\uf201 = chart-line)
    draw_icon_box(ax, 77.0, 15.0, p5_w, p5_h, "\uf201", "Technical Overview Charts", "Windows API Transition Profile\nMITRE ATT&CK Matrix & Score Breakdown", "#0284c7", icon_size=15)

    # 5C: Forensic Evidence Explorer (\uf07c = folder-open)
    draw_icon_box(ax, 55.5, 2.4, p5_w, p5_h, "\uf07c", "Forensic Evidence Explorer", "Raw Event Telemetry Streams\nInteractive Screenshot Carousel", "#059669", icon_size=15)

    # 5D: Multi-Page Vector PDF Export (\uf1c1 = file-pdf)
    draw_icon_box(ax, 77.0, 2.4, p5_w, p5_h, "\uf1c1", "Executive PDF Report Export", "jsPDF + html2canvas Vector Export\nMulti-Page Audit & IR Compliance", "#b45309", icon_size=15)


    # Save figure to both locations
    for target_dir in [DOCS_FIG_DIR, REPORT_FIG_DIR]:
        p1 = target_dir / "fig8_system_architecture_flow_simple.png"
        fig.savefig(p1, bbox_inches="tight")
        print(f"[+] Saved simple flow diagram: {p1}")

        # Also save as overall_architecture_simple.png in Miniproject_Report
        if target_dir == REPORT_FIG_DIR:
            p2 = target_dir / "overall_architecture_simple.png"
            fig.savefig(p2, bbox_inches="tight")
            print(f"[+] Saved simple report figure: {p2}")

    plt.close(fig)


if __name__ == "__main__":
    build_simple_architecture_diagram()
