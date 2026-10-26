#!/usr/bin/env python3
"""
Generate publication-quality, standard academic (college-level) Data Flow Diagrams (DFDs)
using strict traditional textbook DFD schema (DeMarco / Yourdon / Gane-Sarson notation):
  - Black and white / monochrome (no colorful badges or fills)
  - Traditional circles / bubbles for Processes with process number partition
  - Sharp rectangles for External Entities
  - Parallel horizontal open-ended lines for Data Stores
  - Directed arrows with clean, legible data flow labels
  - Snug shape sizes wrapping closely around large, readable text

Outputs:
  - Level 0 DFD (Context Diagram)
  - Level 1 DFD (Major System Decomposition)
  - Level 2 DFD (Behavioral Analytics & AI Synthesis Deep-Dive)
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Rectangle, FancyArrowPatch

# Standard Academic Monochrome Palette
C_BG = "#ffffff"
C_LINE = "#000000"
C_TEXT = "#000000"
C_FILL_WHITE = "#ffffff"
C_BORDER_WIDTH = 1.4


def draw_academic_entity(ax, x, y, w, h, name, subtitle=None, name_size=11.2, sub_size=9.2):
    """Draw a traditional textbook External Entity: Sharp rectangle with black border."""
    rect = Rectangle((x - w/2, y - h/2), w, h, facecolor=C_FILL_WHITE,
                     edgecolor=C_LINE, linewidth=C_BORDER_WIDTH, zorder=2)
    ax.add_patch(rect)

    if subtitle:
        ax.text(x, y + h * 0.18, name, color=C_TEXT, fontsize=name_size, fontweight="bold",
                ha="center", va="center", zorder=4)
        ax.text(x, y - h * 0.22, subtitle, color=C_TEXT, fontsize=sub_size,
                ha="center", va="center", zorder=4)
    else:
        ax.text(x, y, name, color=C_TEXT, fontsize=name_size, fontweight="bold",
                ha="center", va="center", zorder=4)


def draw_academic_process(ax, x, y, r, pid, name, pid_size=12.0, text_size=9.5):
    """Draw a traditional textbook Process: Circle with horizontal partition for ID and name."""
    circle = Circle((x, y), r, facecolor=C_FILL_WHITE, edgecolor=C_LINE,
                    linewidth=C_BORDER_WIDTH, zorder=2)
    ax.add_patch(circle)

    # Horizontal partition line at y + r * 0.25
    split_y = y + r * 0.25
    chord_half = (r**2 - (split_y - y)**2)**0.5
    ax.plot([x - chord_half, x + chord_half], [split_y, split_y],
            color=C_LINE, linewidth=1.0, zorder=3)

    # Process ID above partition
    ax.text(x, y + r * 0.58, pid, color=C_TEXT, fontsize=pid_size, fontweight="bold",
            ha="center", va="center", zorder=4)

    # Process Name below partition
    ax.text(x, y - r * 0.34, name, color=C_TEXT, fontsize=text_size, fontweight="bold",
            ha="center", va="center", zorder=4, linespacing=1.05)


def draw_academic_datastore(ax, x, y, w, h, ds_id, name, id_size=11.0, text_size=9.4):
    """Draw a traditional textbook Data Store: Two parallel lines with ID partition, open right end."""
    bg = Rectangle((x, y), w, h, facecolor=C_FILL_WHITE, edgecolor="none", zorder=1)
    ax.add_patch(bg)

    # Top and bottom parallel lines
    ax.plot([x, x + w], [y + h, y + h], color=C_LINE, linewidth=C_BORDER_WIDTH, zorder=3)
    ax.plot([x, x + w], [y, y], color=C_LINE, linewidth=C_BORDER_WIDTH, zorder=3)

    # Closed left side
    ax.plot([x, x], [y, y + h], color=C_LINE, linewidth=C_BORDER_WIDTH, zorder=3)

    # Partition line for ID
    id_w = 0.55
    ax.plot([x + id_w, x + id_w], [y, y + h], color=C_LINE, linewidth=1.0, zorder=3)

    # ID
    ax.text(x + id_w / 2, y + h / 2, ds_id, color=C_TEXT, fontsize=id_size, fontweight="bold",
            ha="center", va="center", zorder=4)
    # Name
    ax.text(x + id_w + 0.12, y + h / 2, name, color=C_TEXT, fontsize=text_size, fontweight="bold",
            ha="left", va="center", zorder=4, linespacing=1.05)


def draw_academic_flow(ax, p1, p2, label, label_pos=0.5, offset=(0, 0), connectionstyle="arc3,rad=0.0", font_size=9.2):
    """Draw a clean directed arrow with plain text annotation on white capsule."""
    arrow = FancyArrowPatch(p1, p2, connectionstyle=connectionstyle,
                            arrowstyle="-|>,head_length=5.5,head_width=3.2",
                            color=C_LINE, lw=1.2, zorder=5)
    ax.add_patch(arrow)

    # Position
    lx = p1[0] + (p2[0] - p1[0]) * label_pos + offset[0]
    ly = p1[1] + (p2[1] - p1[1]) * label_pos + offset[1]

    ax.text(lx, ly, label, fontsize=font_size, color=C_TEXT, fontweight="semibold",
            ha="center", va="center", zorder=7,
            bbox=dict(boxstyle="square,pad=0.22", facecolor=C_FILL_WHITE, edgecolor=C_LINE, lw=0.6, alpha=1.0))


# ==============================================================================
# LEVEL 0 DFD (CONTEXT DIAGRAM) - ACADEMIC MONOCHROME
# ==============================================================================
def generate_level_0(output_paths):
    fig, ax = plt.subplots(figsize=(11.5, 7.5), dpi=300)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 7.5)
    ax.axis("off")

    # Title
    ax.text(5.75, 7.20, "Level 0 Data Flow Diagram (Context Diagram)",
            fontsize=14.5, fontweight="bold", color=C_TEXT, ha="center", va="center")
    ax.text(5.75, 6.85, "System Context and Boundary Interactions (DeMarco / Yourdon Notation)",
            fontsize=10.0, color=C_TEXT, style="italic", ha="center", va="center")

    # Process 0.0: Central System Circle (Snug size)
    draw_academic_process(ax, 5.75, 3.8, 0.95, "0.0", "IsoLens Autonomous\nMalware Sandbox", pid_size=12.5, text_size=10.2)

    # External Entities (Snug Rectangles)
    draw_academic_entity(ax, 1.35, 5.8, 2.0, 0.82, "Security Analyst", "System Operator")
    draw_academic_entity(ax, 1.35, 1.8, 2.0, 0.82, "VirtualBox Guest VM", "Isolated Detonation")
    draw_academic_entity(ax, 10.15, 5.8, 2.0, 0.82, "Threat Intel Feeds", "Feodo / URLhaus / Fox")
    draw_academic_entity(ax, 10.15, 1.8, 2.0, 0.82, "Multi-Tier AI Cascade", "NIM / Gemini / Ollama")

    # Primary Data Stores
    draw_academic_datastore(ax, 4.55, 5.95, 2.4, 0.52, "D2", "Threat Intel DB (160K+)")
    draw_academic_datastore(ax, 4.45, 1.35, 2.6, 0.52, "D1", "Sample & Telemetry Store")

    # Data Flows (Staggered offsets to ensure zero collision)
    draw_academic_flow(ax, (2.35, 5.9), (4.8, 4.4), "Suspicious Sample & Options", connectionstyle="arc3,rad=-0.08", label_pos=0.55, offset=(0, 0.22), font_size=9.2)
    draw_academic_flow(ax, (4.8, 3.8), (2.35, 5.3), "Forensic Report & Risk Score", connectionstyle="arc3,rad=-0.08", label_pos=0.45, offset=(0, -0.25), font_size=9.2)

    draw_academic_flow(ax, (4.8, 3.4), (2.35, 2.1), "Snapshot Restore & Detonate", connectionstyle="arc3,rad=0.08", label_pos=0.4, offset=(0, 0.25), font_size=9.2)
    draw_academic_flow(ax, (2.35, 1.5), (4.8, 2.8), "Raw Telemetry & Screenshots", connectionstyle="arc3,rad=0.08", label_pos=0.6, offset=(0, -0.25), font_size=9.2)

    draw_academic_flow(ax, (9.15, 5.8), (7.05, 6.2), "Feed Ingestion Stream", label_pos=0.5, offset=(0, 0.20), font_size=9.2)
    draw_academic_flow(ax, (5.75, 5.95), (5.75, 4.8), "0.42 ms Local Matches", offset=(1.25, 0), font_size=9.2)

    draw_academic_flow(ax, (6.7, 3.4), (9.15, 2.1), "Specialist Prompts (94.3% Cut)", connectionstyle="arc3,rad=0.08", label_pos=0.4, offset=(0, 0.25), font_size=9.2)
    draw_academic_flow(ax, (9.15, 1.5), (6.7, 2.8), "Threat Summaries & Attribution", connectionstyle="arc3,rad=0.08", label_pos=0.6, offset=(0, -0.25), font_size=9.2)

    draw_academic_flow(ax, (5.75, 2.8), (5.75, 1.9), "Persist Artifacts & Hashes", offset=(1.35, 0), font_size=9.2)

    plt.tight_layout()
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=300, facecolor=C_BG)
    plt.close(fig)
    print("Academic Level 0 DFD generated.")


# ==============================================================================
# LEVEL 1 DFD (MAJOR SYSTEM DECOMPOSITION) - ACADEMIC MONOCHROME
# ==============================================================================
def generate_level_1(output_paths):
    fig, ax = plt.subplots(figsize=(16.5, 10.2), dpi=300)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, 16.5)
    ax.set_ylim(0, 10.2)
    ax.axis("off")

    # Title
    ax.text(8.25, 9.85, "Level 1 Data Flow Diagram (Major System Decomposition)",
            fontsize=15.0, fontweight="bold", color=C_TEXT, ha="center", va="center")
    ax.text(8.25, 9.55, "System Process Decomposition in Standard DeMarco / Yourdon Bubble Notation",
            fontsize=10.2, color=C_TEXT, style="italic", ha="center", va="center")

    # External Entities
    draw_academic_entity(ax, 1.4, 8.0, 2.0, 0.82, "Security Analyst", "System Operator")
    draw_academic_entity(ax, 1.4, 4.3, 2.0, 0.82, "VirtualBox Hypervisor", "VM Orchestration Host")
    draw_academic_entity(ax, 15.2, 6.2, 2.0, 0.82, "Threat Feed Sources", "External Threat Intel")
    draw_academic_entity(ax, 15.2, 2.5, 2.0, 0.82, "AI Provider Cascade", "NIM / Gemini / Ollama")

    # Data Stores
    draw_academic_datastore(ax, 0.4, 6.2, 2.0, 0.52, "D1", "Sample Store (PE/DLL)")
    draw_academic_datastore(ax, 4.0, 1.1, 2.4, 0.52, "D2", "Telemetry Store (Pcap/Logs)")
    draw_academic_datastore(ax, 11.2, 6.2, 2.3, 0.52, "D3", "Threat Intel DB (160K+)")
    draw_academic_datastore(ax, 11.2, 8.8, 2.3, 0.52, "D4", "Forensic Reports (JSON/Risk)")

    # 6 Major Processes (Snug circles, radius 0.72)
    draw_academic_process(ax, 5.2, 6.4, 0.72, "1.0", "Ingest & Static\nYARA Triage", pid_size=11.5, text_size=9.0)
    draw_academic_process(ax, 5.2, 4.3, 0.72, "2.0", "Hypervisor\nOrchestration", pid_size=11.5, text_size=9.0)
    draw_academic_process(ax, 1.4, 1.35, 0.72, "3.0", "In-Guest Telemetry\nCollection", pid_size=11.5, text_size=8.8)
    draw_academic_process(ax, 8.6, 2.2, 0.72, "4.0", "Behavior Normalizer\n& BiLSTM Inference", pid_size=11.5, text_size=8.8)
    draw_academic_process(ax, 8.6, 5.8, 0.72, "5.0", "Threat Intel &\nAI Synthesis", pid_size=11.5, text_size=9.0)
    draw_academic_process(ax, 8.6, 8.8, 0.72, "6.0", "Dashboard &\nReport Delivery", pid_size=11.5, text_size=9.0)

    # Data Flows (Monochrome Directed Arrows with Dedicated Clear Paths)
    draw_academic_flow(ax, (2.4, 8.0), (4.5, 6.7), "Sample File & Config", offset=(-0.1, 0.20), font_size=9.0)
    draw_academic_flow(ax, (4.48, 6.4), (2.45, 6.4), "Store Binary & Hashes", offset=(0, 0.22), font_size=8.8)
    draw_academic_flow(ax, (5.2, 5.65), (5.2, 5.05), "Trigger Run & Static Flags", offset=(1.45, 0), font_size=8.8)
    draw_academic_flow(ax, (4.45, 4.3), (2.4, 4.3), "VBoxManage Control API", offset=(0, 0.20), font_size=8.8)
    draw_academic_flow(ax, (1.4, 3.85), (1.4, 2.1), "Detonate via schtasks", offset=(1.05, 0), font_size=8.8)
    draw_academic_flow(ax, (2.15, 1.35), (3.95, 1.35), "Export Artifact ZIP", offset=(0, 0.20), font_size=8.8)
    draw_academic_flow(ax, (6.45, 1.35), (7.9, 1.9), "Raw Telemetry & Screenshots", label_pos=0.45, offset=(0, -0.26), font_size=8.8)
    draw_academic_flow(ax, (8.6, 2.95), (8.6, 5.05), "BiLSTM Score & Mapped Events", offset=(1.45, 0), font_size=8.8)
    draw_academic_flow(ax, (14.2, 6.45), (13.55, 6.45), "Feed Stream", offset=(-0.15, 0.22), font_size=8.8)
    draw_academic_flow(ax, (11.15, 6.2), (9.35, 6.0), "0.42 ms Local Matches", offset=(0, -0.22), font_size=8.8)
    draw_academic_flow(ax, (9.3, 5.5), (14.2, 2.8), "Specialist Prompts & Summaries", offset=(0.1, 0.22), font_size=8.8)
    draw_academic_flow(ax, (9.1, 6.4), (11.15, 8.75), "Save Forensic Report", offset=(-0.2, 0.22), font_size=8.8)
    draw_academic_flow(ax, (11.15, 9.05), (9.35, 9.05), "Read Dossier", offset=(0, 0.20), font_size=8.8)

    # 6.0 to Security Analyst - completely unhindered top row delivery!
    draw_academic_flow(ax, (7.85, 8.8), (2.4, 8.2), "Interactive Risk Gauge & ATT&CK Matrix", offset=(0, 0.22), font_size=9.0)

    plt.tight_layout()
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=300, facecolor=C_BG)
    plt.close(fig)
    print("Academic Level 1 DFD generated.")


# ==============================================================================
# LEVEL 2 DFD (BEHAVIORAL ANALYTICS & AI DEEP-DIVE) - ACADEMIC MONOCHROME
# ==============================================================================
def generate_level_2(output_paths):
    fig, ax = plt.subplots(figsize=(16.5, 10.4), dpi=300)
    ax.set_facecolor(C_BG)
    ax.set_xlim(0, 16.5)
    ax.set_ylim(0, 10.4)
    ax.axis("off")

    # Title
    ax.text(8.25, 10.05, "Level 2 Data Flow Diagram (Granular Behavioral & Intelligence Pipeline)",
            fontsize=15.0, fontweight="bold", color=C_TEXT, ha="center", va="center")
    ax.text(8.25, 9.75, "Decomposition of Processes 4.0 and 5.0 into Detailed Subprocesses (DeMarco Notation)",
            fontsize=10.2, color=C_TEXT, style="italic", ha="center", va="center")

    # Inbound / Outbound Data Stores
    draw_academic_datastore(ax, 0.4, 5.6, 2.3, 0.58, "D2", "Telemetry Store\n(Sysmon/Procmon)")
    draw_academic_datastore(ax, 7.0, 9.0, 2.3, 0.58, "D3", "Threat Intel DB\n(SQLite 160K+)")
    draw_academic_datastore(ax, 13.8, 5.0, 2.3, 0.58, "D4", "Forensic Reports\n(Risk Score/IOCs)")

    # Column 1: Subprocesses 4.1 - 4.4 (Snug circles, radius 0.68)
    draw_academic_process(ax, 4.5, 8.0, 0.68, "4.1", "Telemetry Noise\nScoping & Filter", pid_size=11.2, text_size=8.8)
    draw_academic_process(ax, 4.5, 5.8, 0.68, "4.2", "Procmon-to-API\nToken Bridge", pid_size=11.2, text_size=8.8)
    draw_academic_process(ax, 4.5, 3.6, 0.68, "4.3", "BiLSTM Neural\nSequence Classifier", pid_size=11.2, text_size=8.8)
    draw_academic_process(ax, 4.5, 1.4, 0.68, "4.4", "GUI Screen OCR\n& Visual Triage", pid_size=11.2, text_size=8.8)

    # Column 2: Subprocesses 5.1 & 5.2
    draw_academic_process(ax, 8.2, 7.0, 0.68, "5.1", "Deterministic\nIOC Matcher", pid_size=11.2, text_size=8.8)
    draw_academic_process(ax, 8.2, 3.6, 0.68, "5.2", "AI Cascade &\nSub-Agents", pid_size=11.2, text_size=8.8)

    # Column 3: Subprocess 5.3
    draw_academic_process(ax, 11.4, 5.3, 0.72, "5.3", "Threat Summarizer\n& Risk Arbiter", pid_size=11.5, text_size=9.0)

    # Flows
    draw_academic_flow(ax, (1.8, 6.2), (3.8, 8.0), "Raw Telemetry CSV & XML", connectionstyle="arc3,rad=-0.08", offset=(-0.1, 0.22), font_size=8.8)
    draw_academic_flow(ax, (1.8, 5.6), (3.8, 1.5), "Execution Screenshots", connectionstyle="arc3,rad=0.15", offset=(-0.2, -0.22), font_size=8.8)

    draw_academic_flow(ax, (4.5, 7.3), (4.5, 6.5), "Filtered Operations (99.998% Cut)", offset=(1.5, 0), font_size=8.8)
    draw_academic_flow(ax, (4.5, 5.1), (4.5, 4.3), "Ordered API Sequences (dim 32)", offset=(1.4, 0), font_size=8.8)

    draw_academic_flow(ax, (5.2, 7.9), (7.5, 7.2), "Extracted Endpoints (IP/Domain)", offset=(0.1, 0.22), font_size=8.8)
    draw_academic_flow(ax, (8.2, 9.0), (8.2, 7.7), "0.42 ms Local Lookup", offset=(1.15, 0), font_size=8.8)

    draw_academic_flow(ax, (5.2, 3.6), (7.5, 3.6), "BiLSTM Malice (F1: 97.6%)", offset=(0, 0.22), font_size=8.8)
    draw_academic_flow(ax, (5.2, 1.6), (7.6, 3.1), "Visual Ransom Verdict", offset=(-0.1, -0.22), font_size=8.8)

    draw_academic_flow(ax, (8.2, 6.3), (8.2, 4.3), "Threat Context for Agents", offset=(1.25, 0), font_size=8.8)
    draw_academic_flow(ax, (8.9, 6.8), (10.7, 5.6), "Verified C2 Hits & Family Tags", offset=(0.1, 0.22), font_size=8.8)
    draw_academic_flow(ax, (8.9, 3.8), (10.7, 5.0), "Specialist Findings JSONs", offset=(0.1, -0.22), font_size=8.8)

    # 5.3 to D4 - ample space between 5.3 and D4
    draw_academic_flow(ax, (12.15, 5.3), (13.75, 5.3), "Final Report & Risk Score", offset=(-0.1, 0.25), font_size=8.8)

    plt.tight_layout()
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=300, facecolor=C_BG)
    plt.close(fig)
    print("Academic Level 2 DFD generated.")


def main():
    root = Path(__file__).resolve().parent.parent

    # Dynamically find all occurrences across the workspace so tectonic always picks up the new version
    targets_0 = list(root.glob("**/dfd_level_0_new.png"))
    targets_1 = list(root.glob("**/dfd_level_1_new.png"))
    targets_2 = list(root.glob("**/dfd_level_2_new.png"))

    print(f"Generating Academic Monochrome DFDs across {len(targets_0)} locations...")
    generate_level_0(targets_0)
    generate_level_1(targets_1)
    generate_level_2(targets_2)
    print("All DFD diagrams successfully refreshed with snug shapes and large readable fonts.")


if __name__ == "__main__":
    main()
