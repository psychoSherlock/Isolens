#!/usr/bin/env python3
"""Run full live sandbox assessment on malware.exe with all IsoLens pipeline modules.

Pipeline steps executed:
1. YARA Static Pattern & Capability Detection
2. In-VM Execution with Sysmon, Procmon, tcpvcon, handle capture
3. VBoxManage Host Screenshot Harvesting
4. Procmon-to-LSTM Behavioral Sequence Malice Prediction
5. Filesystem & Registry Behavioral Normalization and MITRE ATT&CK Mapping
6. Application Window Cropping, Tesseract OCR & Laya System 1 Threat Triage
7. Deterministic Unified Multi-Layer Risk Scoring
8. Multi-Agent AI Threat Intelligence Analysis & Synthesis
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("isolens.assessment")

# Ensure repository root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.controller.sandbox_orchestrator import SandboxOrchestrator, AgentConfig
from core.threatintelligence.threat_analyzer import ThreatAnalyzer


def main() -> None:
    sample_path = os.path.join(PROJECT_ROOT, "SandboxShare", "malware.exe")
    if not os.path.isfile(sample_path):
        log.error("Sample binary not found at %s", sample_path)
        sys.exit(1)

    print("=" * 70)
    print("   ISOLENS MALWARE SANDBOX - FULL END-TO-END PIPELINE ASSESSMENT")
    print(f"   Target Binary : {sample_path}")
    print(f"   File Size     : {os.path.getsize(sample_path):,} bytes")
    print("=" * 70)

    # 1. Initialize Orchestrator
    config = AgentConfig(
        host="192.168.56.105",
        port=9090,
        vm_name="WindowsSandbox",
    )
    orchestrator = SandboxOrchestrator(agent_config=config)

    # 2. Run Sandbox Execution and Deterministic Feature Extractors
    print("\n[*] Phase 1: Initiating Sandbox Execution (timeout=35s, screenshot_interval=4s)...")
    t0 = time.time()
    result = orchestrator.run_analysis(
        sample_path=sample_path,
        timeout=35,
        screenshot_interval=4,
    )
    duration = time.time() - t0

    print(f"\n[+] Phase 1 Complete in {duration:.1f}s!")
    print(f"    Analysis ID       : {result.analysis_id}")
    print(f"    Status            : {result.status}")
    print(f"    Report Directory  : {result.report_dir}")
    print(f"    Files Collected   : {len(result.files_collected)}")
    print(f"    Sysmon Events     : {result.sysmon_events}")
    print(f"    Deterministic Risk: {result.deterministic_risk_score}/100 ({result.deterministic_threat_level})")

    report_dir = result.report_dir
    if not report_dir or not os.path.isdir(report_dir):
        log.error("Report directory missing; aborting.")
        sys.exit(1)

    # 3. Print Module Findings
    print("\n" + "=" * 70)
    print("             MODULE FINDINGS BREAKDOWN")
    print("=" * 70)

    # YARA
    yara_file = os.path.join(report_dir, "artifacts", "yara", "yara_summary.json")
    if os.path.isfile(yara_file):
        with open(yara_file, "r") as f:
            yara_data = json.load(f)
        print("\n--- [Module 1: YARA Static Capabilities] ---")
        print(f"  Matched Rules Count : {yara_data.get('matched_rules_count', 0)}")
        print(f"  Threat Level        : {yara_data.get('threat_level', 'none')}")
        print(f"  Capabilities Flagged: {yara_data.get('capabilities_flagged', [])}")
        for match in yara_data.get("matches", []):
            print(f"    * Rule: {match.get('rule')} (tags: {match.get('tags')})")

    # LSTM Behavioral Prediction
    lstm_file = os.path.join(report_dir, "artifacts", "lstm", "lstm_prediction.json")
    if os.path.isfile(lstm_file):
        with open(lstm_file, "r") as f:
            lstm_data = json.load(f)
        print("\n--- [Module 2: Procmon BiLSTM Behavioral Sequence Prediction] ---")
        print(f"  Verdict             : {lstm_data.get('verdict')}")
        print(f"  Malware Probability : {lstm_data.get('p_malware', 0.0):.4f}")
        print(f"  Model Confidence    : {lstm_data.get('confidence', 0.0):.2f}%")
        print(f"  Extracted API Calls : {lstm_data.get('sequence_length', 0)}")

    # Behavior Normalization
    behav_file = os.path.join(report_dir, "artifacts", "behavior", "behavior_summary.json")
    if os.path.isfile(behav_file):
        with open(behav_file, "r") as f:
            behav_data = json.load(f)
        print("\n--- [Module 3: Behavior Normalizer & MITRE Extraction] ---")
        summary = behav_data.get("summary", {})
        print(f"  Sensitive Reads     : {summary.get('total_sensitive_reads', 0)}")
        print(f"  Files Written       : {summary.get('total_files_written', 0)}")
        print(f"  Persistence Keys    : {summary.get('total_persistence_keys', 0)}")
        print(f"  MITRE ATT&CK Techs  : {len(behav_data.get('mitre_attack', []))}")
        for t in behav_data.get("mitre_attack", []):
            print(f"    * {t.get('technique_id')} - {t.get('technique_name')}: {t.get('matched_evidence')}")

    # GUI Screen OCR & Laya Triage
    gui_file = os.path.join(report_dir, "artifacts", "gui", "gui_analysis.json")
    if os.path.isfile(gui_file):
        with open(gui_file, "r") as f:
            gui_data = json.load(f)
        print("\n--- [Module 4: GUI Screen OCR & Laya Threat Triage] ---")
        print(f"  Screenshots Examined: {gui_data.get('total_screenshots', 0)}")
        print(f"  Has Malicious GUI   : {gui_data.get('has_malicious_gui', False)}")
        print(f"  Highest Threat Type : {gui_data.get('highest_threat_type', 'none')}")
        print(f"  Max Confidence      : {gui_data.get('max_confidence', 0.0):.2%}")
        for w in gui_data.get("flagged_windows", []):
            print(f"    * [{w.get('filename')}] Flagged as: {w.get('threat_type')} (conf: {w.get('confidence'):.2f})")
            print(f"      Matched keywords: {w.get('matched_keywords', [])}")
            snippet = w.get("ocr_text", "").replace("\n", " ")[:140]
            print(f"      OCR snippet: \"{snippet}...\"")

    # Deterministic Risk Scorer
    risk_file = os.path.join(report_dir, "artifacts", "risk", "risk_score.json")
    if os.path.isfile(risk_file):
        with open(risk_file, "r") as f:
            risk_data = json.load(f)
        print("\n--- [Module 5: Unified Deterministic Risk Score] ---")
        print(f"  Final Score         : {risk_data.get('risk_score')}/100")
        print(f"  Threat Level        : {risk_data.get('threat_level')}")
        print(f"  Layers Flagged      : {risk_data.get('total_layers_flagged', 0)}")
        for b in risk_data.get("breakdown", []):
            print(f"    * Layer {b.get('layer'):<12}: +{b.get('points'):>2} pts [{b.get('threat_level')}] - {b.get('summary')}")

    # 4. Phase 2: Run Multi-Agent AI Threat Analyzer
    print("\n" + "=" * 70)
    print("[*] Phase 2: Running Multi-Agent AI Threat Intelligence Analysis...")
    print("=" * 70)

    analyzer = ThreatAnalyzer()
    t1 = time.time()
    ai_report = asyncio.run(analyzer.analyze_report(result.analysis_id))
    ai_duration = time.time() - t1

    print(f"\n[+] Phase 2 Complete in {ai_duration:.1f}s!")
    print("\n--- [Module 6: Multi-Agent AI Synthesis Report] ---")
    print(f"  Malware Type        : {ai_report.malware_type}")
    print(f"  Threat Level        : {ai_report.threat_level}")
    print(f"  AI Risk Score       : {ai_report.risk_score}/100")
    print(f"  Confidence          : {ai_report.classification_confidence}%")
    print(f"  Provider Used       : {ai_report.provider}")
    print(f"  Agents Executed     : {len(ai_report.tool_results)}")
    for tr in ai_report.tool_results:
        print(f"    * Agent {tr.agent_name:<19} [{tr.tool}]: verdict={tr.verdict}, conf={tr.confidence}% (provider: {tr.provider})")

    print("\n--- [Executive Summary] ---")
    print(ai_report.executive_summary or ai_report.raw_summary)

    if ai_report.key_findings:
        print("\n--- [Key Findings] ---")
        for kf in ai_report.key_findings:
            if isinstance(kf, dict):
                print(f"  - [{kf.get('tool', 'Finding')}] {kf.get('title', '')}: {kf.get('description', '')}")
            else:
                print(f"  - {kf}")

    if ai_report.mitre_attack:
        print("\n--- [AI MITRE ATT&CK Mappings] ---")
        for m in ai_report.mitre_attack:
            if isinstance(m, dict):
                print(f"  - [{m.get('technique_id')}] {m.get('technique_name')} ({m.get('tactic')}): {m.get('evidence')}")
            else:
                print(f"  - {m}")

    print("\n" + "=" * 70)
    print("                  ASSESSMENT FULLY COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
