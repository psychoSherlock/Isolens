#!/usr/bin/env python3
"""
Generate a simple black-and-white flow diagram showing the complete
IsoLens malware analysis pipeline.

Style: boxes and arrows, labels, grouped similar sections, no colors,
black foreground on white background. Simple enough for an external
party to understand the flow from suspicious file to final report.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.font_manager import FontProperties
import os, shutil
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]

# ── Icon setup (Font Awesome Solid) ──────────────────────────────────────────
FA_PATH = "/usr/share/fonts/truetype/font-awesome/fa-solid-900.ttf"
FA = None
if os.path.exists(FA_PATH):
    FA = FontProperties(fname=FA_PATH, size=14)

# Codepoints for icons we use
ICONS = {
    "file":      "\uf15b",  # file
    "upload":    "\uf093",  # upload
    "server":    "\uf233",  # server
    "shield":    "\uf132",  # shield (yara)
    "desktop":   "\uf108",  # desktop (VM)
    "robot":     "\uf544",  # robot (agent)
    "eye":       "\uf06e",  # eye (observe)
    "box":       "\uf466",  # box-open (package)
    "brain":     "\uf5dc",  # brain (AI)
    "network":   "\uf6ff",  # network-wired
    "chart":     "\uf200",  # chart (risk)
    "clipboard": "\uf46d",  # clipboard-check
    "globe":     "\uf0ac",  # globe
    "database":  "\uf1c0",  # database
    "camera":    "\uf030",  # camera
    "search":    "\uf002",  # search
    "bolt":      "\uf0e7",  # bolt
    "layer":     "\uf5fd",  # layer-group
    "terminal":  "\uf120",  # terminal
    "route":     "\uf4d7",  # route
    "users":     "\uf0c0",  # users
    "trophy":    "\uf091",  # trophy
    "pdf":       "\uf1c1",  # file-pdf
}


def draw_icon(ax, x, y, icon_key, size=14):
    """Draw a Font Awesome icon at (x, y)."""
    if FA is None or icon_key not in ICONS:
        return
    fa_local = FA.copy()
    fa_local.set_size(size)
    ax.text(x, y, ICONS[icon_key], fontproperties=fa_local,
            ha="center", va="center", color="black", zorder=10)


def draw_box(ax, x, y, w, h, label, icon_key=None, bold=False, fontsize=8):
    """Draw a rectangle with centered label and optional icon."""
    rect = mpatches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.02",
        facecolor="white", edgecolor="black", linewidth=1.2, zorder=5
    )
    ax.add_patch(rect)

    text_y = y
    if icon_key and FA:
        text_y = y - h * 0.15
        draw_icon(ax, x, y + h * 0.18, icon_key, size=11)

    weight = "bold" if bold else "normal"
    ax.text(x, text_y, label, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, color="black", zorder=10)


def draw_group_box(ax, x, y, w, h, title, items, icon_keys=None):
    """Draw a grouped box with a title and sub-items."""
    # Outer group border
    rect = mpatches.FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.03",
        facecolor="white", edgecolor="black", linewidth=1.5, zorder=4,
        linestyle="--"
    )
    ax.add_patch(rect)

    # Title
    ax.text(x, y + h/2 - 0.25, title, ha="center", va="top",
            fontsize=8, fontweight="bold", color="black", zorder=10)

    # Items arranged in a row or column
    n = len(items)
    if n <= 4:
        # horizontal row
        item_w = (w - 0.3) / n
        start_x = x - (w - 0.3) / 2 + item_w / 2
        for i, item in enumerate(items):
            ix = start_x + i * item_w
            iy = y - 0.1
            if icon_keys and i < len(icon_keys):
                draw_icon(ax, ix, iy + 0.15, icon_keys[i], size=9)
                ax.text(ix, iy - 0.12, item, ha="center", va="center",
                        fontsize=6, color="black", zorder=10)
            else:
                ax.text(ix, iy, item, ha="center", va="center",
                        fontsize=6, color="black", zorder=10)
    else:
        # Two rows
        row1 = items[:3]
        row2 = items[3:]
        ik1 = icon_keys[:3] if icon_keys else []
        ik2 = icon_keys[3:] if icon_keys else []

        for row_items, row_iks, row_y in [(row1, ik1, y + 0.05), (row2, ik2, y - 0.35)]:
            n_row = len(row_items)
            item_w = (w - 0.3) / max(n_row, 1)
            start_x = x - (w - 0.3) / 2 + item_w / 2
            for i, item in enumerate(row_items):
                ix = start_x + i * item_w
                if row_iks and i < len(row_iks):
                    draw_icon(ax, ix, row_y + 0.12, row_iks[i], size=8)
                    ax.text(ix, row_y - 0.1, item, ha="center", va="center",
                            fontsize=5.5, color="black", zorder=10)
                else:
                    ax.text(ix, row_y, item, ha="center", va="center",
                            fontsize=5.5, color="black", zorder=10)


def draw_arrow(ax, x1, y1, x2, y2, label=None):
    """Draw an arrow from (x1,y1) to (x2,y2) with optional label."""
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2),
        zorder=3
    )
    if label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        ax.text(mx + 0.15, my, label, fontsize=5.5, color="black",
                ha="left", va="center", style="italic", zorder=10)


def build_diagram():
    fig, ax = plt.subplots(figsize=(11, 16))
    ax.set_xlim(-1, 11)
    ax.set_ylim(-0.5, 17)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")

    cx = 5  # center x
    bw = 2.8  # box width
    bh = 0.6  # box height

    # ── Phase labels on the left ──
    phases = [
        (15.8, 14.5, "PHASE 1\nSubmission"),
        (13.8, 12.0, "PHASE 2\nPreparation"),
        (11.2, 9.4,  "PHASE 3\nExecution &\nCollection"),
        (8.2, 6.3,   "PHASE 4\nAnalysis\nEngines"),
        (5.2, 3.5,   "PHASE 5\nAI Intelligence"),
        (2.5, 1.2,   "PHASE 6\nReporting"),
    ]

    for y_top, y_bot, label in phases:
        # Phase bracket on the left
        bx = 0.3
        ax.plot([bx, bx], [y_bot, y_top], color="black", linewidth=1.0, zorder=2)
        ax.plot([bx, bx + 0.15], [y_top, y_top], color="black", linewidth=1.0, zorder=2)
        ax.plot([bx, bx + 0.15], [y_bot, y_bot], color="black", linewidth=1.0, zorder=2)
        mid_y = (y_top + y_bot) / 2
        ax.text(bx - 0.1, mid_y, label, ha="right", va="center",
                fontsize=6.5, fontweight="bold", color="black",
                rotation=90, zorder=10)

    # Title
    ax.text(cx, 16.6, "IsoLens — Malware Analysis Pipeline", ha="center", va="center",
            fontsize=14, fontweight="bold", color="black")
    ax.plot([1.5, 8.5], [16.3, 16.3], color="black", linewidth=0.8)

    # ── Row 1: Suspicious File ──
    y = 15.5
    draw_box(ax, cx, y, bw, bh, "Suspicious Executable", icon_key="file", bold=True)

    # ── Row 2: Web Upload ──
    y2 = 14.5
    draw_arrow(ax, cx, y - bh/2, cx, y2 + bh/2)
    draw_box(ax, cx, y2, bw, bh, "Web Dashboard (Upload)", icon_key="upload")

    # ── Row 3: FastAPI Gateway ──
    y3 = 13.5
    draw_arrow(ax, cx, y2 - bh/2, cx, y3 + bh/2, "REST API")
    draw_box(ax, cx, y3, bw, bh, "FastAPI Gateway", icon_key="server")

    # ── Split: YARA scan (left) + VM Prep (right) ──
    y4 = 12.4
    lx = 3.0   # left branch
    rx = 7.0   # right branch

    # Arrow down from gateway, splits
    ax.annotate("", xy=(lx, y4 + bh/2), xytext=(cx, y3 - bh/2),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2), zorder=3)
    ax.annotate("", xy=(rx, y4 + bh/2), xytext=(cx, y3 - bh/2),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2), zorder=3)

    draw_box(ax, lx, y4, 2.4, bh, "YARA Static Scan", icon_key="shield")
    draw_box(ax, rx, y4, 2.4, bh, "VM Snapshot Revert", icon_key="desktop")

    # ── Row 5: VM Start + Agent ──
    y5 = 11.3
    draw_arrow(ax, rx, y4 - bh/2, rx, y5 + bh/2, "VBoxManage")
    draw_box(ax, rx, y5, 2.4, bh, "Start VM & Agent", icon_key="robot")

    # YARA result arrow goes down to rejoin later
    # Arrow from YARA down
    draw_arrow(ax, lx, y4 - bh/2, lx, y5 - 0.1)
    ax.text(lx - 0.1, y5 - 0.0, "↓ results stored", fontsize=5, color="black",
            ha="right", va="center", style="italic")

    # ── Row 6: Sample Injection ──
    y6 = 10.2
    draw_arrow(ax, rx, y5 - bh/2, cx, y6 + bh/2, "Shared Folder")
    draw_box(ax, cx, y6, bw, bh, "Inject & Execute Sample", icon_key="bolt")

    # ── Row 7: Collectors Group ──
    y7 = 9.0
    draw_arrow(ax, cx, y6 - bh/2, cx, y7 + 0.55)
    draw_group_box(ax, cx, y7, 7.5, 1.1, "Guest Collectors (7 Sources)",
                   ["Sysmon", "Procmon", "Screenshots", "TCPVcon", "Handle", "FakeNet"],
                   ["terminal", "search", "camera", "network", "search", "globe"])

    # ── Row 8: Package & Export ──
    y8 = 7.9
    draw_arrow(ax, cx, y7 - 0.55, cx, y8 + bh/2)
    draw_box(ax, cx, y8, bw, bh, "Package & Export Artifacts", icon_key="box")

    # ── Row 9: Analysis Engines Group ──
    y9 = 6.6
    draw_arrow(ax, cx, y8 - bh/2, cx, y9 + 0.6)
    draw_group_box(ax, cx, y9, 8.0, 1.2, "Deterministic Analysis Engines",
                   ["BiLSTM\nInference", "Behavior\nNormalizer", "Network\nThreat DB", "GUI OCR\nTriage", "Risk\nScorer"],
                   ["brain", "search", "database", "eye", "chart"])

    # ── Row 10: AI Cascade Router ──
    y10 = 5.3
    draw_arrow(ax, cx, y9 - 0.6, cx, y10 + bh/2)
    draw_box(ax, cx, y10, 3.8, 0.7, "4-Tier AI Cascade Router\nNVIDIA NIM → Gemini → Copilot → Ollama", icon_key="route", fontsize=7)

    # ── Row 11: Multi-Agent Analysts Group ──
    y11 = 4.0
    draw_arrow(ax, cx, y10 - 0.35, cx, y11 + 0.55)
    draw_group_box(ax, cx, y11, 8.0, 1.1, "6 Specialist AI Analyst Agents",
                   ["Sysmon\nAnalyst", "Procmon\nAnalyst", "Handle\nAnalyst", "TCPVcon\nAnalyst", "Metadata\nAnalyst", "Network\nDB Match"],
                   ["terminal", "search", "search", "network", "search", "database"])

    # ── Row 12: Threat Summarizer ──
    y12 = 2.8
    draw_arrow(ax, cx, y11 - 0.55, cx, y12 + bh/2)
    draw_box(ax, cx, y12, bw, bh, "Threat Summarizer Agent", icon_key="users")

    # ── Row 13: Final Output ──
    y13 = 1.6
    draw_arrow(ax, cx, y12 - bh/2, cx, y13 + bh/2)
    draw_box(ax, cx, y13, 3.4, 0.7,
             "Risk Score · IOCs · MITRE ATT&CK\nClassification · Recommendations",
             icon_key="trophy", bold=True, fontsize=7)

    # ── Row 14: Dashboard + Report ──
    y14 = 0.4
    draw_arrow(ax, cx, y13 - 0.35, cx, y14 + bh/2)
    draw_box(ax, cx, y14, bw, bh, "Web Dashboard & Report", icon_key="clipboard", bold=True)

    # ── Left side: YARA result reconnects to analysis engines ──
    # Draw a line from YARA's result down to the analysis engines
    ax.annotate("", xy=(lx - 0.5, y9 + 0.6), xytext=(lx, y5 - 0.2),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=0.8, linestyle="--"), zorder=3)

    plt.tight_layout(pad=0.3)
    return fig


def main():
    fig = build_diagram()

    out_dir = PROJECT / "docs" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "fig9_simple_pipeline_flow.png"
    fig.savefig(str(out_path), dpi=200, facecolor="white", bbox_inches="tight")
    print(f"Saved: {out_path}")

    # Copy to MajorProjectReport
    major_dir = PROJECT / "MajorProjectReport"
    major_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(out_path), str(major_dir / "fig9_simple_pipeline_flow.png"))
    print(f"Copied to: {major_dir / 'fig9_simple_pipeline_flow.png'}")

    # Copy to Miniproject_Report/figure
    mini_dir = PROJECT / "Miniproject_Report" / "figure"
    if mini_dir.exists():
        shutil.copy2(str(out_path), str(mini_dir / "fig9_simple_pipeline_flow.png"))
        print(f"Copied to: {mini_dir / 'fig9_simple_pipeline_flow.png'}")

    plt.close(fig)


if __name__ == "__main__":
    main()
