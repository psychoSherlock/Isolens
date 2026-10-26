#!/usr/bin/env python3
"""
Generate a publication-grade, clean black-and-white architecture flow diagram for IsoLens.
Modeled directly after the minimalist, high-contrast monochrome style in README.md:
  - Clean white background (#ffffff)
  - Pure black lines, borders, icons, and typography (#000000 / #111111)
  - Clear 5-layer column layout with prominent icons and directional arrows
  - Captures all new IsoLens features across the full dynamic analysis pipeline

Outputs:
  - docs/figures/fig8_system_architecture_readme_style.png
  - docs/figures/fig8_system_architecture_flow_simple.png
  - Miniproject_Report/figure/overall_architecture_simple.png
  - Miniproject_Report/figure/overall_architecture_new.png
"""

import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch
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

# Pure Black & White Palette
C_BG = "#ffffff"
C_LINE = "#000000"
C_TEXT = "#000000"
C_TEXT_SUB = "#222222"
C_BOX_BG = "#ffffff"


def draw_box(ax, x, y, w, h, icon_char, title, sub1="", sub2="", zorder=2, icon_size=14):
    """Draw a minimalist black-and-white box with icon and clean text."""
    # Outer box with black border
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.35,rounding_size=0.35",
        facecolor=C_BOX_BG,
        edgecolor=C_LINE,
        linewidth=1.2,
        zorder=zorder
    )
    ax.add_patch(box)

    # Circular Icon Outline (Black border, white fill)
    circle_r = min(h * 0.28, 1.55)
    circle_x = x + circle_r + 0.65
    circle_y = y + h / 2.0
    circle = Circle(
        (circle_x, circle_y), circle_r,
        facecolor="#ffffff",
        edgecolor=C_LINE,
        linewidth=1.1,
        zorder=zorder + 1
    )
    ax.add_patch(circle)

    # Black Font Awesome Glyph
    ax.text(
        circle_x, circle_y, icon_char,
        fontproperties=fa_font,
        fontsize=icon_size,
        color=C_LINE,
        ha="center",
        va="center",
        zorder=zorder + 2
    )

    # Text positioning
    text_x = circle_x + circle_r + 0.8
    if sub2:
        title_y = circle_y + h * 0.24
        sub1_y = circle_y - h * 0.04
        sub2_y = circle_y - h * 0.28
    elif sub1:
        title_y = circle_y + h * 0.17
        sub1_y = circle_y - h * 0.17
        sub2_y = None
    else:
        title_y = circle_y
        sub1_y = None
        sub2_y = None

    # Title
    ax.text(
        text_x, title_y, title,
        color=C_TEXT,
        fontsize=8.4,
        fontweight="bold",
        va="center",
        ha="left",
        zorder=zorder + 1
    )
    # Subtitle line 1
    if sub1:
        ax.text(
            text_x, sub1_y, sub1,
            color=C_TEXT_SUB,
            fontsize=7.1,
            fontweight="normal",
            va="center",
            ha="left",
            zorder=zorder + 1
        )
    # Subtitle line 2
    if sub2:
        ax.text(
            text_x, sub2_y, sub2,
            color=C_TEXT_SUB,
            fontsize=6.9,
            fontweight="normal",
            va="center",
            ha="left",
            zorder=zorder + 1
        )


def draw_arrow(ax, x1, y1, x2, y2, label="", rad=0.0, lw=1.4, zorder=4, label_offset=(0, 0)):
    """Draw a clean black directional arrow with optional label."""
    connectionstyle = f"arc3,rad={rad}" if rad != 0.0 else "arc3"
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        connectionstyle=connectionstyle,
        arrowstyle="-|>",
        mutation_scale=14,
        color=C_LINE,
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
            color=C_TEXT,
            fontsize=7.2,
            fontweight="bold",
            va="center",
            ha="center",
            zorder=zorder + 1,
            bbox=dict(
                boxstyle="round,pad=0.2,rounding_size=0.2",
                facecolor="#ffffff",
                edgecolor=C_LINE,
                linewidth=0.9,
                alpha=0.98
            )
        )


def build_readme_style_diagram():
    fig = plt.figure(figsize=(22, 12.5), dpi=300, facecolor=C_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # ==========================================================================
    # 0. MAIN TITLE & SUBTITLE (Top)
    # ==========================================================================
    ax.text(
        50.0, 97.2,
        "Automated Malware Analysis & Sandbox Platform — System Architecture",
        color=C_TEXT,
        fontsize=16.0,
        fontweight="bold",
        va="center",
        ha="center",
        zorder=3
    )
    ax.text(
        50.0, 94.8,
        "End-to-End Autonomous Pipeline: Ingestion ➔ Hypervisor Sandbox ➔ Behavioral ML & Analytics ➔ 4-Tier AI Cascade ➔ Presentation",
        color="#333333",
        fontsize=9.2,
        fontweight="normal",
        va="center",
        ha="center",
        zorder=3
    )

    # ==========================================================================
    # MAIN SYSTEM CONTAINER (Outer Box)
    # ==========================================================================
    outer_box = FancyBboxPatch(
        (1.2, 1.8), 97.6, 90.8,
        boxstyle="round,pad=0.5,rounding_size=0.5",
        facecolor="#ffffff",
        edgecolor=C_LINE,
        linewidth=1.6,
        zorder=1
    )
    ax.add_patch(outer_box)

    # Sub-header bar on top of outer box
    ax.text(
        3.0, 90.5,
        "●  Secure Malware Analysis Platform (IsoLens Core)",
        color=C_TEXT,
        fontsize=10.5,
        fontweight="bold",
        va="center",
        zorder=2
    )

    # 5 Layer Columns (Geometry with generous 2.4-unit inter-column gaps)
    col_w = 17.2
    col_gap = 2.4
    start_x = 2.4
    col_xs = [start_x + i * (col_w + col_gap) for i in range(5)]

    layers = [
        ("Layer 1 — Orchestration & Isolation", col_xs[0], col_w),
        ("Layer 2 — Behavioral Monitoring", col_xs[1], col_w),
        ("Layer 3 — Detection & Behavioral ML", col_xs[2], col_w),
        ("Layer 4 — Multi-Tier AI Intelligence", col_xs[3], col_w),
        ("Layer 5 — Reporting & Presentation", col_xs[4], col_w),
    ]

    for title, cx, cw in layers:
        # Header box with solid black fill, white text (identical to README diagram)
        hdr = FancyBboxPatch(
            (cx, 85.0), cw, 3.6,
            boxstyle="round,pad=0.25,rounding_size=0.25",
            facecolor="#000000",
            edgecolor="#000000",
            linewidth=1.0,
            zorder=2
        )
        ax.add_patch(hdr)
        ax.text(
            cx + cw / 2.0, 86.8, title,
            color="#ffffff",
            fontsize=8.3,
            fontweight="bold",
            va="center",
            ha="center",
            zorder=3
        )

    # ==========================================================================
    # LAYER 1: ORCHESTRATION & ISOLATION LAYER (Col 1)
    # 4 Boxes: Web Portal, Gateway, Host Orchestrator, In-VM Agent
    # ==========================================================================
    c1_x = col_xs[0]
    c1_w = col_w
    h_box_4 = 14.8
    gap_4 = 5.2

    # 1A: Next.js Web Portal (\uf0ac = globe)
    y_1a = 85.0 - h_box_4 - 1.2
    draw_box(ax, c1_x, y_1a, c1_w, h_box_4, "\uf0ac", "Web Client Portal", "Next.js 14 App Router", "Sample Upload & Parameters")

    # Arrow 1A -> 1B
    draw_arrow(ax, c1_x + c1_w/2.0, y_1a, c1_x + c1_w/2.0, y_1a - gap_4)

    # 1B: FastAPI Gateway (\uf0e7 = bolt)
    y_1b = y_1a - h_box_4 - gap_4
    draw_box(ax, c1_x, y_1b, c1_w, h_box_4, "\uf0e7", "FastAPI System Gateway", "REST API on port :6969", "Schema Validation & Staging")

    # Arrow 1B -> 1C
    draw_arrow(ax, c1_x + c1_w/2.0, y_1b, c1_x + c1_w/2.0, y_1b - gap_4)

    # 1C: VirtualBox Hypervisor (\uf233 = server)
    y_1c = y_1b - h_box_4 - gap_4
    draw_box(ax, c1_x, y_1c, c1_w, h_box_4, "\uf233", "VirtualBox Orchestrator", "VBoxManage CLI Automation", "Snapshot Revert & Dual Screens")

    # Arrow 1C -> 1D
    draw_arrow(ax, c1_x + c1_w/2.0, y_1c, c1_x + c1_w/2.0, y_1c - gap_4)

    # 1D: In-VM Guest Agent (\uf544 = robot)
    y_1d = y_1c - h_box_4 - gap_4
    draw_box(ax, c1_x, y_1d, c1_w, h_box_4, "\uf544", "In-VM Guest Agent", "isolens_agent.py (:9090)", "Python Stdlib • Zero-Pip")


    # ==========================================================================
    # LAYER 2: BEHAVIORAL MONITORING LAYER (Col 2)
    # 5 Boxes: Sysmon, Procmon, Screenshots, TCPVcon, Handle
    # ==========================================================================
    c2_x = col_xs[1]
    c2_w = col_w
    h_box_5 = 11.8
    gap_5 = 4.3

    # 2A: Sysmon (\uf2db = microchip)
    y_2a = 85.0 - h_box_5 - 1.2
    draw_box(ax, c2_x, y_2a, c2_w, h_box_5, "\uf2db", "Sysmon Kernel Monitor", "Process Trees & DLL Injection", "Network Sockets (XML export)")

    # Arrow 2A -> 2B
    draw_arrow(ax, c2_x + c2_w/2.0, y_2a, c2_x + c2_w/2.0, y_2a - gap_5)

    # 2B: Procmon (\uf120 = terminal)
    y_2b = y_2a - h_box_5 - gap_5
    draw_box(ax, c2_x, y_2b, c2_w, h_box_5, "\uf120", "Process Monitor (Procmon)", "File & Registry Syscalls", "CSV Execution Trace Export")

    # Arrow 2B -> 2C
    draw_arrow(ax, c2_x + c2_w/2.0, y_2b, c2_x + c2_w/2.0, y_2b - gap_5)

    # 2C: Screenshots (\uf030 = camera)
    y_2c = y_2b - h_box_5 - gap_5
    draw_box(ax, c2_x, y_2c, c2_w, h_box_5, "\uf030", "Desktop Screenshot Stream", "Host VBoxManage (every 4s)", "In-Guest PowerShell Window Capture")

    # Arrow 2C -> 2D
    draw_arrow(ax, c2_x + c2_w/2.0, y_2c, c2_x + c2_w/2.0, y_2c - gap_5)

    # 2D: TCPVcon (\uf6ff = network-wired)
    y_2d = y_2c - h_box_5 - gap_5
    draw_box(ax, c2_x, y_2d, c2_w, h_box_5, "\uf6ff", "TCPVcon Socket Monitor", "Active TCP/UDP Endpoints", "Listening Backdoor Ports")

    # Arrow 2D -> 2E
    draw_arrow(ax, c2_x + c2_w/2.0, y_2d, c2_x + c2_w/2.0, y_2d - gap_5)

    # 2E: Handle (\uf084 = key)
    y_2e = y_2d - h_box_5 - gap_5
    draw_box(ax, c2_x, y_2e, c2_w, h_box_5, "\uf084", "Handle Resource Monitor", "Open Mutexes & Named Pipes", "Sensitive File Handles & Locks")


    # ==========================================================================
    # LAYER 3: DETECTION & BEHAVIORAL ML LAYER (Col 3)
    # 6 Boxes: Static YARA, Procmon-to-LSTM, BiLSTM, Host Normalizer, Threat DB, GUI OCR
    # ==========================================================================
    c3_x = col_xs[2]
    c3_w = col_w
    h_box_6 = 9.8
    gap_6 = 3.6

    # 3A: Static YARA (\uf002 = search)
    y_3a = 85.0 - h_box_6 - 1.2
    draw_box(ax, c3_x, y_3a, c3_w, h_box_6, "\uf002", "Curated YARA Scanner", "Packers, Evasion & Injection", "MITRE T1059.001 / T1055")

    # Arrow 3A -> 3B
    draw_arrow(ax, c3_x + c3_w/2.0, y_3a, c3_x + c3_w/2.0, y_3a - gap_6)

    # 3B: Procmon-to-LSTM Bridge (\uf4d7 = route)
    y_3b = y_3a - h_box_6 - gap_6
    draw_box(ax, c3_x, y_3b, c3_w, h_box_6, "\uf4d7", "Procmon-to-LSTM Bridge", "PE Loader Noise Filter", "Multi-Source Telemetry Synthesizer")

    # Arrow 3B -> 3C
    draw_arrow(ax, c3_x + c3_w/2.0, y_3b, c3_x + c3_w/2.0, y_3b - gap_6)

    # 3C: BiLSTM Model (\uf5dc = brain)
    y_3c = y_3b - h_box_6 - gap_6
    draw_box(ax, c3_x, y_3c, c3_w, h_box_6, "\uf5dc", "2-Layer BiLSTM Model", "PyTorch Sequential Classifier", "100-Call Sliding Window Inference")

    # Arrow 3C -> 3D
    draw_arrow(ax, c3_x + c3_w/2.0, y_3c, c3_x + c3_w/2.0, y_3c - gap_6)

    # 3D: Host Behavior Normalizer (\uf3ed = shield)
    y_3d = y_3c - h_box_6 - gap_6
    draw_box(ax, c3_x, y_3d, c3_w, h_box_6, "\uf3ed", "Host Behavior Normalizer", "Run / Startup Keys (T1547.001)", "Defense Tampering Audit (T1562)")

    # Arrow 3D -> 3E
    draw_arrow(ax, c3_x + c3_w/2.0, y_3d, c3_x + c3_w/2.0, y_3d - gap_6)

    # 3E: Offline Threat DB (\uf1c0 = database)
    y_3e = y_3d - h_box_6 - gap_6
    draw_box(ax, c3_x, y_3e, c3_w, h_box_6, "\uf1c0", "Offline Threat DB", "160,716 Malicious C2 Indicators", "Zero-Token Deterministic Matching")

    # Arrow 3E -> 3F
    draw_arrow(ax, c3_x + c3_w/2.0, y_3e, c3_x + c3_w/2.0, y_3e - gap_6)

    # 3F: GUI OCR & Triage (\uf06e = eye)
    y_3f = y_3e - h_box_6 - gap_6
    draw_box(ax, c3_x, y_3f, c3_w, h_box_6, "\uf06e", "GUI Window OCR & Triage", "Tesseract 5.5 + Laya Model", "Ransomware Extortion / Scam Alerts")


    # ==========================================================================
    # LAYER 4: MULTI-TIER AI INTELLIGENCE LAYER (Col 4)
    # 4 Boxes: Risk Scorer, 4-Tier Router, 6 Specialist Agents, Threat Summarizer
    # ==========================================================================
    c4_x = col_xs[3]
    c4_w = col_w

    # 4A: Risk Scorer (\uf140 = bullseye)
    y_4a = 85.0 - h_box_4 - 1.2
    draw_box(ax, c4_x, y_4a, c4_w, h_box_4, "\uf140", "Deterministic Risk Scorer", "Calibrated 0–100 Score Arbiter", "5-Layer Weighted Confidence Sum")

    # Arrow 4A -> 4B
    draw_arrow(ax, c4_x + c4_w/2.0, y_4a, c4_x + c4_w/2.0, y_4a - gap_4)

    # 4B: 4-Tier Fallback AI Router (\uf0e8 = sitemap)
    y_4b = y_4a - h_box_4 - gap_4
    draw_box(ax, c4_x, y_4b, c4_w, h_box_4, "\uf0e8", "4-Tier Cascade AI Router", "T1: NVIDIA NIM (Llama 70B)", "T2: Gemini • T3: Copilot • T4: Ollama")

    # Arrow 4B -> 4C
    draw_arrow(ax, c4_x + c4_w/2.0, y_4b, c4_x + c4_w/2.0, y_4b - gap_4)

    # 4C: 6 Specialist Agents (\uf0c0 = users)
    y_4c = y_4b - h_box_4 - gap_4
    draw_box(ax, c4_x, y_4c, c4_w, h_box_4, "\uf0c0", "6 Specialist Tool Agents", "Sysmon • Procmon • Net • Handle", "TCPVcon • Metadata (JSON Schema)")

    # Arrow 4C -> 4D
    draw_arrow(ax, c4_x + c4_w/2.0, y_4c, c4_x + c4_w/2.0, y_4c - gap_4)

    # 4D: Threat Summarizer (\uf46c = clipboard-check)
    y_4d = y_4c - h_box_4 - gap_4
    draw_box(ax, c4_x, y_4d, c4_w, h_box_4, "\uf46c", "Threat Summarizer Agent", "Executive Threat Summary & IOCs", "Unified MITRE ATT&CK Matrix")


    # ==========================================================================
    # LAYER 5: REPORTING & PRESENTATION LAYER (Col 5)
    # 4 Boxes: VirusTotal Hero Banner, Technical Dashboard, Evidence Explorer, PDF Export
    # ==========================================================================
    c5_x = col_xs[4]
    c5_w = col_w

    # 5A: VirusTotal Banner (\uf091 = trophy)
    y_5a = 85.0 - h_box_4 - 1.2
    draw_box(ax, c5_x, y_5a, c5_w, h_box_4, "\uf091", "VirusTotal Hero Banner", "Animated 0–100 Radial Gauge", "Consensus Ratio & Severity Ring")

    # Arrow 5A -> 5B
    draw_arrow(ax, c5_x + c5_w/2.0, y_5a, c5_x + c5_w/2.0, y_5a - gap_4)

    # 5B: Technical Dashboard (\uf201 = chart-line)
    y_5b = y_5a - h_box_4 - gap_4
    draw_box(ax, c5_x, y_5b, c5_w, h_box_4, "\uf201", "Technical Overview Charts", "API Transition Profile", "MITRE ATT&CK Technique Cards")

    # Arrow 5B -> 5C
    draw_arrow(ax, c5_x + c5_w/2.0, y_5b, c5_x + c5_w/2.0, y_5b - gap_4)

    # 5C: Evidence Explorer (\uf07c = folder-open)
    y_5c = y_5b - h_box_4 - gap_4
    draw_box(ax, c5_x, y_5c, c5_w, h_box_4, "\uf07c", "Forensic Evidence Explorer", "Raw Telemetry Event Streams", "Dual Screenshot Gallery View")

    # Arrow 5C -> 5D
    draw_arrow(ax, c5_x + c5_w/2.0, y_5c, c5_x + c5_w/2.0, y_5c - gap_4)

    # 5D: PDF Export (\uf1c1 = file-pdf)
    y_5d = y_5c - h_box_4 - gap_4
    draw_box(ax, c5_x, y_5d, c5_w, h_box_4, "\uf1c1", "Executive PDF Report Export", "jsPDF + html2canvas Engine", "Multi-Page Audit & IR Compliance")


    # ==========================================================================
    # INTER-LAYER PIPELINE FLOW ARROWS (Across the 2.4-unit gaps)
    # ==========================================================================
    # Layer 1 -> Layer 2 (SharedFolder IPC / Sample Launch)
    draw_arrow(
        ax,
        c1_x + c1_w, y_1c + h_box_4/2.0,
        c2_x, y_2b + h_box_5/2.0,
        label="Execution",
        lw=1.8,
        label_offset=(0, 1.8)
    )

    # Layer 2 -> Layer 3 (Artifacts Zip Export)
    draw_arrow(
        ax,
        c2_x + c2_w, y_2c + h_box_5/2.0,
        c3_x, y_3b + h_box_6/2.0,
        label="Artifacts",
        lw=1.8,
        label_offset=(0, 1.8)
    )

    # Layer 3 -> Layer 4 (Behavioral Features to Risk Scorer & AI)
    draw_arrow(
        ax,
        c3_x + c3_w, y_3c + h_box_6/2.0,
        c4_x, y_4a + h_box_4/2.0,
        label="Features",
        lw=1.8,
        label_offset=(0, 1.8)
    )

    # Layer 4 -> Layer 5 (Synthesized Intelligence to Presentation)
    draw_arrow(
        ax,
        c4_x + c4_w, y_4d + h_box_4/2.0,
        c5_x, y_5a + h_box_4/2.0,
        label="Report",
        lw=1.8,
        label_offset=(0, 1.8)
    )

    # Direct Feed from Risk Scorer to VirusTotal Banner
    draw_arrow(
        ax,
        c4_x + c4_w, y_4a + h_box_4/2.0,
        c5_x, y_5a + h_box_4/2.0,
        label="Score",
        lw=1.5,
        label_offset=(0, 1.8)
    )


    # Save figure to both locations
    for target_dir in [DOCS_FIG_DIR, REPORT_FIG_DIR]:
        p1 = target_dir / "fig8_system_architecture_readme_style.png"
        fig.savefig(p1, bbox_inches="tight")
        print(f"[+] Saved README-style diagram: {p1}")

        p2 = target_dir / "fig8_system_architecture_flow_simple.png"
        fig.savefig(p2, bbox_inches="tight")
        print(f"[+] Saved simple flow diagram: {p2}")

        # In Miniproject_Report, overwrite overall_architecture_new.png and overall_architecture_simple.png
        if target_dir == REPORT_FIG_DIR:
            p3 = target_dir / "overall_architecture_new.png"
            fig.savefig(p3, bbox_inches="tight")
            print(f"[+] Overwrote report figure: {p3}")

            p4 = target_dir / "overall_architecture_simple.png"
            fig.savefig(p4, bbox_inches="tight")
            print(f"[+] Overwrote simple report figure: {p4}")

    plt.close(fig)


if __name__ == "__main__":
    build_readme_style_diagram()
