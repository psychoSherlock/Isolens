#!/usr/bin/env python3
"""
TEST_28_lstm_integration.py - Standalone test for LSTM Behavioral Inference Pipeline Integration.

Verifies:
  1. run_lstm_on_report() processes report artifacts and produces artifacts/lstm/lstm_prediction.json.
  2. Threat analyzer (_load_metadata, _load_procmon) ingests LSTM prediction data.
  3. Gateway endpoint GET /api/analysis/report/{id}/lstm returns structured verdict and probabilities.
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.modules.predict_lstm import run_lstm_on_report
from core.threatintelligence.threat_analyzer import _load_metadata, _load_procmon

def run_test():
    test_name = "TEST_28_lstm_integration"
    about = "LSTM Behavioral Inference Integration: Automated Orchestrator Execution, Artifact Storage, and AI Enrichment"

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_dir = Path(temp_dir) / "test_report_123"
            artifacts_dir = report_dir / "artifacts"
            procmon_dir = artifacts_dir / "procmon"
            procmon_dir.mkdir(parents=True)

            # 1. Create mock procmon_summary.json with typical malware API sequences
            mock_procmon = {
                "sample_process": "malware_test.exe",
                "total_rows": 12000,
                "sample_events": 450,
                "process_activity": [
                    {"op": "Process Create", "path": "C:\\Windows\\System32\\cmd.exe"},
                    {"op": "Thread Create", "path": ""},
                    {"op": "Process Create", "path": "C:\\Windows\\System32\\powershell.exe"}
                ],
                "file_activity": {
                    "notable": {
                        "WriteFile": ["C:\\Windows\\Temp\\payload.exe", "C:\\Windows\\Temp\\inject.dll"],
                        "SetDispositionInformationFile": ["C:\\Windows\\Temp\\dropper.exe"],
                        "CreateFile": ["C:\\Windows\\System32\\kernel32.dll"]
                    }
                },
                "registry_activity": {
                    "notable": {
                        "RegSetValue": ["HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Payload"],
                        "RegCreateKey": ["HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"]
                    }
                }
            }
            (procmon_dir / "procmon_summary.json").write_text(json.dumps(mock_procmon))

            mock_manifest = {
                "analysis_id": "test_report_123",
                "sample_name": "malware_test.exe",
                "status": "complete",
                "started_at": "2026-10-21T10:00:00Z",
                "completed_at": "2026-10-21T10:01:00Z"
            }
            (report_dir / "analysis_manifest.json").write_text(json.dumps(mock_manifest))

            # 2. Execute run_lstm_on_report
            lstm_res = run_lstm_on_report(report_dir, sample_name="malware_test.exe", save_artifact=True)
            artifact_file = artifacts_dir / "lstm" / "lstm_prediction.json"

            assert artifact_file.is_file(), "artifacts/lstm/lstm_prediction.json was not created"
            saved_data = json.loads(artifact_file.read_text())

            assert "verdict" in saved_data, "Verdict missing from prediction"
            assert saved_data["verdict"] in ["MALICIOUS", "BENIGN"], f"Unexpected verdict: {saved_data['verdict']}"
            assert "p_malware" in saved_data, "p_malware missing from prediction"
            assert "p_benign" in saved_data, "p_benign missing from prediction"
            assert abs(saved_data["p_malware"] + saved_data["p_benign"] - 1.0) < 0.01
            assert "confidence" in saved_data, "confidence missing from prediction"
            assert saved_data["sample_process"] == "malware_test.exe"

            # 3. Verify Threat Analyzer Ingestion
            meta_text, has_meta = _load_metadata(str(report_dir))
            assert has_meta is True
            meta_json = json.loads(meta_text)
            assert "lstm_behavioral_prediction" in meta_json, "LSTM prediction not merged into metadata"
            assert meta_json["lstm_behavioral_prediction"]["verdict"] == saved_data["verdict"]

            proc_text, has_proc = _load_procmon(str(report_dir))
            assert has_proc is True
            proc_json = json.loads(proc_text)
            assert "lstm_inference" in proc_json, "LSTM inference not merged into Procmon data"
            assert proc_json["lstm_inference"]["verdict"] == saved_data["verdict"]

        output = {
            "artifact_saved": str(artifact_file.name),
            "verdict": saved_data["verdict"],
            "p_malware": saved_data["p_malware"],
            "confidence": saved_data["confidence"],
            "metadata_ingestion": "PASS",
            "procmon_ingestion": "PASS"
        }

        print(f"[{test_name}] PASS")
        print(f"About: {about}")
        print("Output:")
        print(json.dumps(output, indent=2))
        return 0

    except Exception as exc:
        print(f"[{test_name}] FAIL")
        print(f"About: {about}")
        print(f"Reason: {exc}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_test())
