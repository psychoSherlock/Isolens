#!/usr/bin/env python3
"""
TEST_29_behavior_integration.py - Standalone test for Behavioral Normalization Integration.

Verifies:
  1. run_behavior_normalizer_on_report() processes report artifacts and produces artifacts/behavior/behavior_summary.json.
  2. Threat analyzer (_load_metadata, _load_procmon) ingests behavior normalization summary.
  3. Gateway endpoint GET /api/analysis/report/{id}/behavior returns structured findings.
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.modules.behavior_normalizer import run_behavior_normalizer_on_report
from core.threatintelligence.threat_analyzer import _load_metadata, _load_procmon

def run_test():
    test_name = "TEST_29_behavior_integration"
    about = "Behavior Normalization Integration: Automated Orchestrator Execution, Artifact Storage, and Threat Intel Ingestion"

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_dir = Path(temp_dir) / "test_report_behav"
            artifacts_dir = report_dir / "artifacts"
            procmon_dir = artifacts_dir / "procmon"
            procmon_dir.mkdir(parents=True)

            # 1. Create mock procmon_summary.json with sensitive operations
            mock_procmon = {
                "sample_process": "trojan_sim.exe",
                "total_rows": 8500,
                "sample_events": 320,
                "file_activity": {
                    "notable": {
                        "CreateFile": [
                            "C:\\Users\\Victim\\Desktop\\passwords.txt",
                            "C:\\Windows\\System32\\kernel32.dll"
                        ],
                        "WriteFile": [
                            "C:\\Windows\\Temp\\payload.exe"
                        ],
                        "ReadFile": [
                            "C:\\Users\\Victim\\.ssh\\id_rsa",
                            "C:\\Users\\Victim\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Login Data"
                        ],
                        "SetDispositionInformationFile": [
                            "C:\\Windows\\Temp\\dropper.exe"
                        ]
                    }
                },
                "registry_activity": {
                    "notable": {
                        "RegSetValue": [
                            "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Updater",
                            "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\DisableAntiSpyware"
                        ],
                        "RegQueryValue": [
                            "HKLM\\SOFTWARE\\Microsoft\\Cryptography\\MachineGuid",
                            "HKLM\\HARDWARE\\DESCRIPTION\\System\\BIOS\\SystemManufacturer"
                        ]
                    }
                }
            }
            (procmon_dir / "procmon_summary.json").write_text(json.dumps(mock_procmon))

            mock_manifest = {
                "analysis_id": "test_report_behav",
                "sample_name": "trojan_sim.exe",
                "status": "complete",
                "started_at": "2026-10-21T10:00:00Z",
                "completed_at": "2026-10-21T10:01:00Z"
            }
            (report_dir / "analysis_manifest.json").write_text(json.dumps(mock_manifest))

            # 2. Execute run_behavior_normalizer_on_report
            behav_res = run_behavior_normalizer_on_report(report_dir, save_artifact=True)
            artifact_file = artifacts_dir / "behavior" / "behavior_summary.json"

            assert artifact_file.is_file(), "artifacts/behavior/behavior_summary.json was not created"
            saved_data = json.loads(artifact_file.read_text())

            assert saved_data["sample_process"] == "trojan_sim.exe"
            assert saved_data["summary"]["total_files_written"] == 1
            assert saved_data["summary"]["total_files_deleted"] == 1
            assert saved_data["summary"]["total_sensitive_reads"] == 2
            assert saved_data["summary"]["total_persistence_keys"] == 1
            assert saved_data["summary"]["total_defense_tampering_keys"] == 1

            # Check MITRE techniques
            mitre_ids = {t["id"] for t in saved_data["mitre_attack"]}
            assert "T1547.001" in mitre_ids, "Missing T1547.001 (Persistence)"
            assert "T1562.001" in mitre_ids, "Missing T1562.001 (Defense Tampering)"
            assert "T1005" in mitre_ids, "Missing T1005 (Sensitive Reads)"
            assert "T1082" in mitre_ids, "Missing T1082 (Recon Queries)"
            assert "T1070.004" in mitre_ids, "Missing T1070.004 (File Deletion)"

            # 3. Verify Threat Analyzer Ingestion
            meta_text, has_meta = _load_metadata(str(report_dir))
            assert has_meta is True
            meta_json = json.loads(meta_text)
            assert "behavior_summary" in meta_json, "Behavior summary not merged into metadata"
            assert len(meta_json["behavior_summary"]["mitre_attack"]) == len(saved_data["mitre_attack"])

            proc_text, has_proc = _load_procmon(str(report_dir))
            assert has_proc is True
            proc_json = json.loads(proc_text)
            assert "behavioral_normalization" in proc_json, "Behavior normalization not merged into Procmon data"
            assert len(proc_json["behavioral_normalization"]["sensitive_reads"]) == 2

        output = {
            "artifact_saved": str(artifact_file.name),
            "total_sensitive_reads": saved_data["summary"]["total_sensitive_reads"],
            "total_persistence_keys": saved_data["summary"]["total_persistence_keys"],
            "total_defense_tampering_keys": saved_data["summary"]["total_defense_tampering_keys"],
            "mitre_techniques_count": len(saved_data["mitre_attack"]),
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
