#!/usr/bin/env python3
"""
TEST_31_risk_scorer.py - Standalone test for Deterministic Risk Scorer Integration.

Verifies:
  1. run_risk_scorer_on_report() evaluates multi-layer artifacts and calculates explainable 0-100 score.
  2. Produces artifacts/risk/risk_score.json with detailed breakdown.
  3. Threat analyzer (_load_metadata) ingests deterministic risk score and layer summaries.
  4. Gateway endpoint GET /api/analysis/report/{id}/risk returns structured findings.
  5. Gateway endpoint GET /api/analysis/report/{id}/data includes 'risk' payload.
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.modules.risk_scorer import run_risk_scorer_on_report, DeterministicRiskScorer
from core.threatintelligence.threat_analyzer import _load_metadata
from fastapi.testclient import TestClient
from core.gateway.app import app


def run_test():
    test_name = "TEST_31_risk_scorer"
    about = "Deterministic Risk Scorer: Multi-Layer Objective Scoring, Artifact Generation, and API Integration"

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_dir = Path(temp_dir) / "test_report_risk"
            artifacts_dir = report_dir / "artifacts"

            # Setup subdirectories
            yara_dir = artifacts_dir / "yara"
            lstm_dir = artifacts_dir / "lstm"
            behav_dir = artifacts_dir / "behavior"
            gui_dir = artifacts_dir / "gui"
            for d in [yara_dir, lstm_dir, behav_dir, gui_dir]:
                d.mkdir(parents=True)

            # 1. Mock YARA finding (+25 pts)
            (yara_dir / "yara_summary.json").write_text(json.dumps({
                "matched_rules_count": 2,
                "threat_level": "high",
                "matches": [
                    {"rule_name": "ransomware_lockscreen", "tags": ["ransomware", "crypto"]},
                    {"rule_name": "anti_debug_rdtsc", "tags": ["evasion"]}
                ],
                "mitre_attack": [{"id": "T1486", "name": "Data Encrypted for Impact"}]
            }))

            # 2. Mock LSTM finding (+25 pts)
            (lstm_dir / "lstm_prediction.json").write_text(json.dumps({
                "verdict": "malware",
                "p_malware": 0.985,
                "confidence": 98.5,
                "total_sequence_length": 150,
                "peak_window_range": [20, 120]
            }))

            # 3. Mock Behavior finding (+35 pts: persistence + defense evasion)
            (behav_dir / "behavior_summary.json").write_text(json.dumps({
                "summary": {
                    "total_files_written": 12,
                    "total_persistence_keys": 2,
                    "total_defense_tampering_keys": 1,
                    "total_sensitive_reads": 3
                },
                "mitre_attack": [
                    {"id": "T1547.001", "name": "Registry Run Keys"},
                    {"id": "T1562.001", "name": "Disable Security Tools"}
                ],
                "registry": {
                    "persistence_keys": ["HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\bad.exe"],
                    "defense_tampering_keys": ["HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\DisableAntiSpyware"]
                }
            }))

            # 4. Mock GUI Screen finding (+25 pts)
            (gui_dir / "gui_analysis.json").write_text(json.dumps({
                "sample": "ransomware_test.exe",
                "total_screenshots": 4,
                "has_malicious_gui": True,
                "highest_threat_type": "ransomware_extortion",
                "max_confidence": 0.975,
                "flagged_count": 1,
                "flagged_windows": [{
                    "filename": "screenshot_002.png",
                    "threat_type": "ransomware_extortion",
                    "confidence": 0.975,
                    "matched_keywords": ["encrypt", "bitcoin", "pay 300"],
                    "ocr_text": "Your files are encrypted! Pay 300 in Bitcoin to recover."
                }]
            }))

            # 5. Run Risk Scorer
            risk_res = run_risk_scorer_on_report(report_dir, save_artifact=True)

            artifact_path = artifacts_dir / "risk" / "risk_score.json"
            if not artifact_path.is_file():
                print(f"[{test_name}] FAIL")
                print(f"About: {about}")
                print(f"Reason: Expected artifact {artifact_path} was not created.")
                sys.exit(1)

            # Assert score and level
            score = risk_res.get("risk_score", 0)
            level = risk_res.get("threat_level")
            layers = risk_res.get("total_layers_flagged", 0)

            # Expected score: 25 (YARA) + 25 (LSTM) + 25 (GUI) + 35 (Behavior) = 110 -> capped at 100
            if score != 100 or level != "Critical" or layers < 4:
                print(f"[{test_name}] FAIL")
                print(f"About: {about}")
                print(f"Reason: Expected score 100 / Critical / >=4 layers, got score={score}, level={level}, layers={layers}")
                sys.exit(1)

            # 6. Test Threat Analyzer _load_metadata ingestion
            meta_str, success = _load_metadata(str(report_dir))
            if not success or "deterministic_risk_assessment" not in meta_str:
                print(f"[{test_name}] FAIL")
                print(f"About: {about}")
                print("Reason: Threat analyzer _load_metadata did not ingest deterministic_risk_assessment.")
                print("Output:", meta_str)
                sys.exit(1)

            # 7. Test Gateway Endpoints using temporary report override
            live_reports_dir = PROJECT_ROOT / "core" / "storage" / "reports"
            dest_test_dir = live_reports_dir / "_test_risk_integration"
            if dest_test_dir.exists():
                shutil.rmtree(dest_test_dir)
            shutil.copytree(report_dir, dest_test_dir)

            try:
                client = TestClient(app)

                # Test GET /api/analysis/report/{id}/risk
                resp_risk = client.get("/api/analysis/report/_test_risk_integration/risk")
                if resp_risk.status_code != 200:
                    print(f"[{test_name}] FAIL")
                    print(f"About: {about}")
                    print(f"Reason: GET /api/analysis/report/_test_risk_integration/risk returned HTTP {resp_risk.status_code}")
                    sys.exit(1)
                risk_api_data = resp_risk.json().get("data", {})
                if risk_api_data.get("risk_score") != 100:
                    print(f"[{test_name}] FAIL")
                    print(f"About: {about}")
                    print("Reason: Mismatched score in API output:", risk_api_data)
                    sys.exit(1)

                # Test GET /api/analysis/report/{id}/data
                resp_data = client.get("/api/analysis/report/_test_risk_integration/data")
                if resp_data.status_code != 200:
                    print(f"[{test_name}] FAIL")
                    print(f"About: {about}")
                    print(f"Reason: GET /api/analysis/report/_test_risk_integration/data returned HTTP {resp_data.status_code}")
                    sys.exit(1)
                full_data = resp_data.json().get("data", {})
                if "risk" not in full_data or full_data["risk"] is None:
                    print(f"[{test_name}] FAIL")
                    print(f"About: {about}")
                    print("Reason: 'risk' key missing in GET /data response")
                    sys.exit(1)

            finally:
                if dest_test_dir.exists():
                    shutil.rmtree(dest_test_dir)

            output_summary = {
                "artifact_saved": "risk_score.json",
                "risk_score": score,
                "threat_level": level,
                "layers_flagged": layers,
                "threat_analyzer_ingestion": "PASS",
                "gateway_risk_endpoint": "PASS",
                "gateway_data_endpoint": "PASS"
            }

            print(f"[{test_name}] PASS")
            print(f"About: {about}")
            print(f"Output:\n{json.dumps(output_summary, indent=2)}")

    except Exception as exc:
        print(f"[{test_name}] FAIL")
        print(f"About: {about}")
        print(f"Reason: Unexpected exception: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_test()
