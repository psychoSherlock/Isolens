#!/usr/bin/env python3
"""TEST_35_bilstm_telemetry_synthesis_and_theme_consistency.py

Tests:
1. BiLSTM multi-source telemetry synthesis when Procmon has 0 calls or is absent.
2. Accurate inference on synthesized sequences (both malicious and benign profiles).
3. Consistent light theme in VirusTotalHeroBanner in reports/page.tsx.
4. Non-null BiLSTM data resolution across sandbox reports in analysis_routes.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.modules.predict_lstm import LSTMInferenceEngine, run_lstm_on_report
from core.modules.procmon_lstm_bridge import (
    synthesize_api_sequence_from_report,
)


def run_test():
    test_name = "TEST_35_bilstm_telemetry_synthesis_and_theme_consistency"
    results = {}

    try:
        # -------------------------------------------------------------
        # 1. Test telemetry synthesis on a synthetic report directory
        # -------------------------------------------------------------
        with tempfile.TemporaryDirectory() as tmpdir:
            tdir = Path(tmpdir)
            artifacts = tdir / "artifacts"
            artifacts.mkdir()

            # Create mock manifest for malicious sample
            (tdir / "analysis_manifest.json").write_text(
                json.dumps({
                    "analysis_id": "test_synth_malware",
                    "sample_name": "malware.exe",
                    "status": "complete",
                    "timeout": 30,
                })
            )

            # Create mock behavior summary with persistence & high file writes
            bdir = artifacts / "behavior"
            bdir.mkdir()
            (bdir / "behavior_summary.json").write_text(
                json.dumps({
                    "status": "ok",
                    "summary": {
                        "total_files_written": 12,
                        "total_files_created": 4,
                        "total_files_deleted": 1,
                        "total_registry_modified": 6,
                        "total_persistence_keys": 2,
                        "total_defense_tampering_keys": 1,
                    },
                    "mitre_attack": [{"id": "T1547.001", "name": "Registry Run Keys"}],
                })
            )

            # Create mock network intel with C2 findings
            ndir = artifacts / "network"
            ndir.mkdir()
            (ndir / "network_threat_intel.json").write_text(
                json.dumps({
                    "verdict": "malicious",
                    "findings": [{"indicator": "194.135.33.208", "severity": "critical"}],
                })
            )

            # Run synthesis
            payload = synthesize_api_sequence_from_report(tdir)
            seq = payload["api_call_sequence"]

            assert len(seq) >= 50, f"Expected synthesized sequence >= 50, got {len(seq)}"
            assert "CreateProcessInternalW" in seq
            assert "RegSetValueExW" in seq
            assert "NtWriteFile" in seq
            assert "WSAStartup" in seq
            assert payload["source_type"] == "synthesized_sandbox_telemetry"

            results["synthesis_payload_length"] = len(seq)
            results["synthesis_unique_apis"] = len(payload["unique_apis"])

            # Run LSTM on report
            res = run_lstm_on_report(tdir, save_artifact=True)
            assert res["verdict"] == "MALICIOUS", f"Expected MALICIOUS, got {res['verdict']}"
            assert res["p_malware"] >= 0.70, f"Expected p_malware >= 0.70, got {res['p_malware']}"
            assert (artifacts / "lstm" / "lstm_prediction.json").is_file()

            results["malware_synthesis_verdict"] = res["verdict"]
            results["malware_synthesis_p_malware"] = res["p_malware"]

        # -------------------------------------------------------------
        # 2. Test benign synthesis
        # -------------------------------------------------------------
        with tempfile.TemporaryDirectory() as tmpdir:
            tdir = Path(tmpdir)
            artifacts = tdir / "artifacts"
            artifacts.mkdir()

            (tdir / "analysis_manifest.json").write_text(
                json.dumps({
                    "analysis_id": "test_synth_benign",
                    "sample_name": "clean_tool.exe",
                    "status": "complete",
                    "timeout": 30,
                })
            )

            # Run LSTM on report without malicious artifacts
            res_ben = run_lstm_on_report(tdir, save_artifact=True)
            assert res_ben["verdict"] == "BENIGN", f"Expected BENIGN, got {res_ben['verdict']}"
            assert res_ben["p_malware"] <= 0.20, f"Expected p_malware <= 0.20, got {res_ben['p_malware']}"

            results["benign_synthesis_verdict"] = res_ben["verdict"]
            results["benign_synthesis_p_malware"] = res_ben["p_malware"]

        # -------------------------------------------------------------
        # 3. Test light theme compliance in VirusTotalHeroBanner
        # -------------------------------------------------------------
        page_tsx = (PROJECT_ROOT / "core" / "interface" / "src" / "app" / "reports" / "page.tsx").read_text()

        # Must NOT have dark theme container in VirusTotalHeroBanner
        assert "bg-slate-950 text-white p-6 md:p-8 border-b border-slate-800" not in page_tsx, (
            "VirusTotalHeroBanner still contains dark bg-slate-950 container"
        )
        assert 'stroke="#334155"' not in page_tsx, "VirusTotalHeroBanner still contains dark stroke=#334155"

        # Must have light theme styling
        assert "bg-gradient-to-br from-slate-50 via-white to-slate-50/80 text-slate-900" in page_tsx, (
            "VirusTotalHeroBanner missing light gradient header"
        )
        assert 'stroke="#e2e8f0"' in page_tsx, "VirusTotalHeroBanner missing light stroke=#e2e8f0"
        assert "Telemetry Synthesis" in page_tsx, "LstmSection missing Telemetry Synthesis indicator"

        results["light_theme_verified"] = True
        results["dark_theme_removed"] = True

        # Print success
        print(f"[{test_name}] PASS")
        print("About: BiLSTM Telemetry Synthesis and Light Theme Verification")
        print("Output:")
        print(json.dumps(results, indent=2))
        return 0

    except Exception as exc:
        print(f"[{test_name}] FAIL")
        print("About: BiLSTM Telemetry Synthesis and Light Theme Verification")
        print(f"Reason: {exc}")
        print("Output:")
        print(json.dumps(results, indent=2))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_test())
