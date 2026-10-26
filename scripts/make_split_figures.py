#!/usr/bin/env python3
"""scripts/make_split_figures.py

Generates two easily readable, publication-quality figures representing the
dataset architecture, severe class imbalance, and synthetic augmentation breakthrough:

1. fig7a_dataset_composition_and_imbalance_defect.png
2. fig7b_synthetic_augmentation_and_breakthrough.png
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.ticker as ticker
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_FIG_DIR = PROJECT_ROOT / "docs" / "figures"
REPORT_FIG_DIR = PROJECT_ROOT / "Miniproject_Report" / "figure"
DOCS_FIG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.5,
    "figure.titlesize": 13,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

def save_both(fig, filename_base):
    for fn in [f"{filename_base}.png"]:
        for d in [DOCS_FIG_DIR, REPORT_FIG_DIR]:
            p = d / fn
            fig.savefig(p, bbox_inches="tight")
            print(f"[+] Saved: {p}")
    plt.close(fig)

# ==============================================================================
# FIGURE 7A: DATASET COMPOSITION & THE 25.7:1 CLASS IMBALANCE DEFECT
# ==============================================================================
def generate_fig7a():
    fig = plt.figure(figsize=(15, 7.5), facecolor="#ffffff")
    gs = fig.add_gridspec(1, 2, top=0.84, bottom=0.12, left=0.07, right=0.96, wspace=0.28)

    # Subplot A1: Composition & Imbalance Across Splits
    ax1 = fig.add_subplot(gs[0, 0])
    splits = ["Raw Cuckoo Corpus\n(Catak Benchmark)", "Academic Train Split\n(Original train.json)", "Holdout Test Split\n(Pristine test.json)"]
    malware = [42797, 15714, 6262]
    benign = [1079, 611, 243]
    totals = [m + b for m, b in zip(malware, benign)]

    x = np.arange(len(splits))
    width = 0.48

    ax1.bar(x, malware, width, label="Malware Samples (Class 1)", color="#e11d48", edgecolor="#9f1239", linewidth=1.2)
    ax1.bar(x, benign, width, bottom=malware, label="Benign Samples (Class 0)", color="#10b981", edgecolor="#047857", linewidth=1.2)

    ratios = ["39.7 : 1", "25.72 : 1\n(Severe Defect)", "25.77 : 1\n(Holdout Test)"]
    for i, (m, b, t, r) in enumerate(zip(malware, benign, totals, ratios)):
        ben_pct = (b / t) * 100
        # Label malware
        ax1.text(i, m * 0.5, f"{m:,}\n({(m/t)*100:.1f}%)", ha="center", va="center", color="white", fontweight="bold", fontsize=9)
        # Label benign
        ax1.text(i, t + 1100, f"{b:,} ({ben_pct:.1f}%)", ha="center", va="bottom", color="#047857", fontweight="bold", fontsize=9)
        # Ratio badge
        ax1.text(i, t + 4200, f"Imbalance: {r}", ha="center", va="bottom", fontsize=8.5, color="#1e293b",
                 bbox=dict(boxstyle="round,pad=0.25", facecolor="#f1f5f9", edgecolor="#cbd5e1", lw=1))

    ax1.set_title("(a) Dynamic API Traces & Severe Class Imbalance", fontweight="bold", pad=12)
    ax1.set_ylabel("Binary Execution Trace Count")
    ax1.set_xticks(x)
    ax1.set_xticklabels(splits, fontweight="bold")
    ax1.set_ylim(0, 53000)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f"{int(y):,}"))
    ax1.grid(True, axis="y", linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", framealpha=0.95)

    # Subplot A2: Baseline Defect & 49.4% False-Positive Disaster
    ax2 = fig.add_subplot(gs[0, 1])
    metrics = ["Test Accuracy\n(Skewed by Majority)", "Malware Recall\n(Majority Class)", "Benign Precision\n(Minority Class)", "Benign Recall\n(Minority Class)", "Benign F1-Score\n(Minority Class)"]
    vals = [96.34, 98.12, 51.04, 50.62, 50.83]
    colors = ["#64748b", "#3b82f6", "#f59e0b", "#f97316", "#ef4444"]

    bars = ax2.barh(metrics, vals, color=colors, edgecolor="#334155", linewidth=1.1, height=0.52)
    ax2.axvline(50.0, color="#b91c1c", linestyle="--", linewidth=1.6, alpha=0.85)
    ax2.text(50.5, 2.2, "Coin-Flip Random Guess (50.0%)", color="#b91c1c", fontsize=8.5, fontweight="bold")

    for bar in bars:
        w = bar.get_width()
        ax2.text(w + 1.2, bar.get_y() + bar.get_height() / 2, f"{w:.2f}%", va="center", ha="left", fontweight="bold", fontsize=9.5, color="#0f172a")

    ax2.set_xlim(0, 116)
    ax2.set_xlabel("Baseline Model (EXP-00) Performance (%) on 6,505 Pristine Test Samples")
    ax2.set_title("(b) The 'Accuracy Paradox': High Accuracy with 49.4% False Alarms", fontweight="bold", pad=12)
    ax2.grid(True, axis="x", linestyle=":", alpha=0.6)

    # Impact Warning Card inside Subplot A2
    warn_text = (
        "THE MINORITY CLASS COLLAPSE (BASELINE EXP-00):\n"
        "• 96.34% Accuracy is a mathematical illusion caused by 96.3% malware in the dataset.\n"
        "• On legitimate applications, Benign Precision is only 51.04% (coin-flip reliability).\n"
        "• 120 out of 243 genuine benign applications were falsely condemned as malware!"
    )
    ax2.text(0.04, 0.13, warn_text, transform=ax2.transAxes, fontsize=8.5,
             verticalalignment="top", color="#991b1b",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#fef2f2", edgecolor="#fca5a5", lw=1.2))

    fig.suptitle("IsoLens Dataset Architecture: Catak/Cuckoo Provenance & The Severe 25.7:1 Class Imbalance Defect\n"
                 "Analysis of 43,876 dynamic execution traces revealing minority-class collapse on legitimate Windows binaries",
                 fontsize=12.5, fontweight="bold", y=0.96, color="#0f172a")

    save_both(fig, "fig7a_dataset_composition_and_imbalance_defect")
    # Also save as fig7_dataset_imbalance_and_baseline_defect for reference
    save_both(fig, "fig7_dataset_imbalance_and_baseline_defect")


# ==============================================================================
# FIGURE 7B: SYNTHETIC AUGMENTATION & QUANTITATIVE BREAKTHROUGH
# ==============================================================================
def generate_fig7b():
    fig = plt.figure(figsize=(15, 7.5), facecolor="#ffffff")
    gs = fig.add_gridspec(1, 2, top=0.84, bottom=0.12, left=0.07, right=0.96, wspace=0.28)

    # Subplot B1: Augmentation Mechanics Flow
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis("off")
    ax1.set_title("(a) Domain-Aware Semantic Augmentation Mechanics (+11,389 Traces)", fontweight="bold", pad=12)

    strategies = [
        ("Base Benign Pool", "611 Original Traces (Catak)", "Genuine benign Windows binaries executed in Cuckoo Sandbox", "#f1f5f9", "#475569", 0.88),
        ("Strategy 1: Sliding-Window Slicing", "Windows: 50-80 APIs | Stride: 10", "Extracts valid execution sub-lifecycles without violating causal temporal order", "#eff6ff", "#1d4ed8", 0.64),
        ("Strategy 2: System Telemetry Interleaving", "p = 0.08 - 0.15 Injection Rate", "Interleaves non-stateful queries: GetTickCount, GetSystemMetrics, NtQuerySystemInfo", "#f0fdf4", "#047857", 0.40),
        ("Strategy 3: Win32/NT API Substitution", "Semantic Equivalence Pairs", "Swaps identical syscall variants: RegOpenKeyExW <-> RegOpenKeyExA, NtClose <-> CloseHandle", "#fdf4ff", "#7e22ce", 0.16),
    ]

    for title, badge, desc, bg, border, y_pos in strategies:
        rect = patches.FancyBboxPatch((0.02, y_pos - 0.09), 0.96, 0.19, boxstyle="round,pad=0.03,rounding_size=0.04",
                                      facecolor=bg, edgecolor=border, linewidth=1.2, transform=ax1.transAxes)
        ax1.add_patch(rect)
        ax1.text(0.05, y_pos + 0.05, title, transform=ax1.transAxes, fontweight="bold", fontsize=9.5, color="#0f172a")
        ax1.text(0.94, y_pos + 0.05, badge, transform=ax1.transAxes, ha="right", fontweight="bold", fontsize=8,
                 color="white", bbox=dict(boxstyle="round,pad=0.25", facecolor=border, edgecolor="none"))
        ax1.text(0.05, y_pos - 0.04, desc, transform=ax1.transAxes, fontsize=8, color="#475569")

    # Connective arrows
    ax1.annotate("", xy=(0.5, 0.77), xytext=(0.5, 0.80), xycoords="axes fraction",
                 arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.5))
    ax1.annotate("", xy=(0.5, 0.53), xytext=(0.5, 0.56), xycoords="axes fraction",
                 arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.5))
    ax1.annotate("", xy=(0.5, 0.29), xytext=(0.5, 0.32), xycoords="axes fraction",
                 arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.5))

    # Subplot B2: Empirical Performance Breakthrough (EXP-00 vs EXP-01)
    ax2 = fig.add_subplot(gs[0, 1])
    comp_metrics = ["Benign\nPrecision", "Benign\nF1-Score", "Macro\nF1-Score", "Malware\nRecall", "Test\nAccuracy"]
    exp00 = [51.04, 50.83, 74.46, 98.12, 96.34]
    exp01 = [69.66, 58.91, 78.77, 99.14, 97.34]
    deltas = ["+18.62%", "+8.08%", "+4.31%", "+1.02%", "+1.00%"]

    x = np.arange(len(comp_metrics))
    width = 0.35

    ax2.bar(x - width/2, exp00, width, label="Baseline (EXP-00: 611 Benign)", color="#94a3b8", edgecolor="#64748b", linewidth=1.1)
    ax2.bar(x + width/2, exp01, width, label="Augmented (EXP-01: 12,000 Benign)", color="#0284c7", edgecolor="#0369a1", linewidth=1.1)

    for i in range(len(comp_metrics)):
        ax2.text(x[i], max(exp00[i], exp01[i]) + 3.8, deltas[i], ha="center", va="bottom",
                 fontweight="bold", fontsize=9, color="#0369a1",
                 bbox=dict(boxstyle="round,pad=0.22", facecolor="#e0f2fe", edgecolor="#7dd3fc", lw=0.9))
        ax2.text(x[i] - width/2, exp00[i] / 2, f"{exp00[i]:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=8)
        ax2.text(x[i] + width/2, exp01[i] / 2, f"{exp01[i]:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=8)

    ax2.set_title("(b) Empirical Breakthrough on 6,505 Pristine Test Samples", fontweight="bold", pad=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(comp_metrics, fontweight="bold")
    ax2.set_ylabel("Evaluation Metric Score (%)")
    ax2.set_ylim(40, 115)
    ax2.grid(True, axis="y", linestyle=":", alpha=0.6)
    ax2.legend(loc="lower right", framealpha=0.95)

    # Breakthrough highlight box
    breakthrough_box = (
        "KEY QUANTITATIVE ACHIEVEMENTS (EXP-01):\n"
        "• Benign Precision soared +18.62% (from 51.04% to 69.66%).\n"
        "• Missed Malware (False Negatives) cut by -54.2% (118 down to 54 missed).\n"
        "• Test set (6,505 samples) remained 100% untouched (zero data leakage)."
    )
    ax2.text(0.04, 0.95, breakthrough_box, transform=ax2.transAxes, fontsize=8.5,
             verticalalignment="top", color="#065f46",
             bbox=dict(boxstyle="round,pad=0.45", facecolor="#ecfdf5", edgecolor="#6ee7b7", lw=1.2))

    fig.suptitle("IsoLens Synthetic Augmentation Pipeline & Empirical Detection Breakthrough\n"
                 "Balancing training ratio to 1.31:1 via +11,389 semantic benign traces with strict holdout verification",
                 fontsize=12.5, fontweight="bold", y=0.96, color="#0f172a")

    save_both(fig, "fig7b_synthetic_augmentation_and_breakthrough")
    # Also save as fig8_synthetic_augmentation_and_performance_breakthrough for reference
    save_both(fig, "fig8_synthetic_augmentation_and_performance_breakthrough")

if __name__ == "__main__":
    print("[*] Generating Figure 7A...")
    generate_fig7a()
    print("[*] Generating Figure 7B...")
    generate_fig7b()
    print("[✓] All split figures generated successfully!")
