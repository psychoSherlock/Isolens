#!/usr/bin/env python3
"""Validate report figures, image references, citations, and required sections."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "MajorProjectReport"
if not (REPORT_DIR / "main.tex").is_file():
    if (ROOT / "MajorProjectReport" / "backup" / "main.tex").is_file():
        REPORT_DIR = ROOT / "MajorProjectReport" / "backup"
    elif (ROOT / "MajorProjectReport" / "FinalReport" / "ActualReport" / "main.tex").is_file():
        REPORT_DIR = ROOT / "MajorProjectReport" / "FinalReport" / "ActualReport"
TEX = REPORT_DIR / "main.tex"
BIB = REPORT_DIR / "references.bib"
print("[TEST_37_report_assets] About: Report visuals, references, tables, DFDs, and UI captures are present")
try:
    tex = TEX.read_text(encoding="utf-8")
    bib = BIB.read_text(encoding="utf-8")
    assert not re.search(r"\\todo\b|TODO|FIXME", tex, re.I), "TODO marker remains"
    labels = re.findall(r"\\label\{([^}]+)\}", tex)
    assert len(labels) == len(set(labels)), "Duplicate LaTeX labels found"
    refs = re.findall(r"\\(?:ref|pageref)\{([^}]+)\}", tex)
    assert set(refs) <= set(labels), f"Unresolved references: {set(refs)-set(labels)}"
    keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    cites = set()
    for match in re.finditer(r"\\cite\w*\{([^}]+)\}", tex):
        cites.update(key.strip() for key in match.group(1).split(","))
    assert cites <= keys, f"Missing bibliography entries: {cites-keys}"
    for image in re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", tex):
        candidates = [REPORT_DIR / image,
                      REPORT_DIR / "figures" / image,
                      REPORT_DIR / "report_figures" / image,
                      ROOT / "MajorProjectReport" / image,
                      ROOT / "MajorProjectReport" / "figures" / image,
                      ROOT / "MajorProjectReport" / "report_figures" / image,
                      ROOT / "docs" / "figures" / image,
                      ROOT / "Miniproject_Report" / "figure" / image]
        assert any(path.is_file() for path in candidates), f"Missing figure: {image}"
    for required in ["YARA Static Pattern Scanner Module", "Behavioral Normalizer Module",
                     "Network Threat Intelligence DB Matcher Module", "GUI Screen Analyzer Module",
                     "Procmon-to-LSTM Bridge Module", "Configurable AI Cascade Router",
                     "Data Flow Diagrams", "Dashboard Screenshots"]:
        assert required in tex, f"Missing report section: {required}"
    assert tex.count("\\begin{table}") == tex.count("\\end{table}")
    assert tex.count("\\begin{figure}") == tex.count("\\end{figure}")
    image_refs = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", tex)
    forbidden = {"fig8_system_architecture_flow_simple.png",
                 "fig8_system_architecture_readme_style.png"}
    assert not (forbidden & set(image_refs)), "An inaccurate Fig. 8 architecture image is still referenced"
    assert {"isolens_workflow_bw_horizontal.png", "fig8_overall_system_architecture_flow.png"} <= set(image_refs), \
        "Both accurate vertical and horizontal architecture images must be embedded"
    expected_figure_assets = {
        "fig1_lstm_synthetic_augmentation_breakthrough.png",
        "fig2_network_threat_intel_distribution.png",
        "fig3_dynamic_telemetry_noise_reduction.png",
        "fig4_multitier_ai_cascade_and_multiagent.png",
        "fig5_defense_in_depth_capability_matrix.png",
        "fig6_sandbox_architecture_comparison.png",
        "fig7_dataset_composition_imbalance_and_synthetic_augmentation.png",
        "fig7_dataset_imbalance_and_baseline_defect.png",
        "fig7a_dataset_composition_and_imbalance_defect.png",
        "fig7b_synthetic_augmentation_and_breakthrough.png",
        "fig8_overall_system_architecture_flow.png",
        "fig8_synthetic_augmentation_and_performance_breakthrough.png",
        "fig9_simple_pipeline_flow.png",
        "fig9_verified_checkpoint_evaluation.png",
    }
    assert expected_figure_assets <= set(image_refs), \
        f"Relevant figures/ assets missing from report: {expected_figure_assets-set(image_refs)}"
    assert r"\gantttitle{Nov}{1}" in tex and "first week of November 2026" in tex \
        and "Usable product ready for deployment" in tex, \
        "Schedule must end in November 2026, Week 1, with the deployment-ready milestone"
    gantt = tex.split("\\begin{ganttchart}", 1)[1].split("\\end{ganttchart}", 1)[0]
    assert "2027" not in gantt, "The project timeline must not extend into 2027"
    assert "tab:bridgereplay" in tex, "Saved bridge replay outputs are missing"
    for figure_label in ["fig:traininghistory", "fig:augmentationmethod", "fig:procmoncounts", "fig:dbdistribution"]:
        assert figure_label in tex, f"Missing verified concept figure: {figure_label}"
    print("[TEST_37_report_assets] PASS")
    print("Output:")
    print({"images_checked": len(re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", tex)),
           "tables": tex.count("\\begin{table}"), "figures": tex.count("\\begin{figure}"),
           "cited_sources": len(cites), "required_sections": 8})
except Exception as exc:
    print("[TEST_37_report_assets] FAIL")
    print(f"Reason: {exc}")
    raise
