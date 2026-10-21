#!/usr/bin/env python3
"""TEST_26 - YARA Pattern Detection & Pipeline Integration.

Validates:
  1. YARA rule files exist in core/storage/yara_rules/ and compile successfully.
  2. YaraScanner detects ransomware, evasion, script execution, and credential dumping patterns.
  3. YaraScanner correctly identifies clean/benign buffers without false positives.
  4. Real binary scanning on malware_sim.exe detects execution signatures.
  5. Integration with report directory and threat analyzer metadata loader.
  6. Gateway endpoint GET /api/analysis/report/{id}/yara is registered.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))

TEST_NAME = "TEST_26_yara_integration"
ABOUT = "YARA ruleset compilation, pattern matching, binary scanning, and sandbox integration"


def run_test() -> list[str]:
    errors: list[str] = []

    # ── 1. Ruleset Directory & Files ─────────────────────────────────────────
    rules_dir = _PROJECT_ROOT / "core" / "storage" / "yara_rules"
    if not rules_dir.is_dir():
        errors.append(f"YARA rules directory missing: {rules_dir}")
        return errors

    yar_files = list(rules_dir.glob("*.yar"))
    if len(yar_files) < 2:
        errors.append(f"Expected at least 2 .yar rulesets, found {len(yar_files)}")

    from core.modules.yara_scanner import YaraScanner

    scanner = YaraScanner(rules_dir=rules_dir)

    # ── 2. Pattern Matching on Byte Buffers ──────────────────────────────────
    # 2a. Ransomware command detection
    ransomware_payload = b"Sample buffer ... vssadmin delete shadows /all /quiet ... EOF"
    res_rw = scanner.scan_bytes(ransomware_payload, filename="ransomware_test.exe")
    if res_rw.get("status") != "ok":
        errors.append(f"scan_bytes failed: {res_rw}")
    elif not any(m["rule"] == "Ransomware_ShadowCopy_Deletion" for m in res_rw.get("matches", [])):
        errors.append("Ransomware_ShadowCopy_Deletion rule failed to trigger on vssadmin command")
    if res_rw.get("threat_level") != "critical":
        errors.append(f"Expected critical threat level for ransomware match, got {res_rw.get('threat_level')}")

    # 2b. VM / Evasion detection
    evasion_payload = b"Checking environment: VBoxGuestAdditions driver found"
    res_ev = scanner.scan_bytes(evasion_payload, filename="evasion_test.exe")
    if not any(m["rule"] == "Virtual_Machine_Evasion" for m in res_ev.get("matches", [])):
        errors.append("Virtual_Machine_Evasion rule failed to trigger on VBoxGuestAdditions")

    # 2c. Credential dumping detection
    cred_payload = b"Executing sekurlsa::logonpasswords to dump hashes"
    res_cred = scanner.scan_bytes(cred_payload, filename="mimikatz_test.exe")
    if not any(m["rule"] == "Credential_Dumping_Signatures" for m in res_cred.get("matches", [])):
        errors.append("Credential_Dumping_Signatures rule failed to trigger on sekurlsa")

    # 2d. Clean buffer verification (no false positives)
    clean_payload = b"Hello, world! This is a totally benign utility program."
    res_clean = scanner.scan_bytes(clean_payload, filename="clean.exe")
    if res_clean.get("matched_rules_count", 0) != 0:
        errors.append(f"Clean buffer falsely triggered {res_clean.get('matched_rules_count')} rule(s)")

    # ── 3. File Scanning on Test Binary ──────────────────────────────────────
    binary_path = _PROJECT_ROOT / "test" / "test1_lstm_test" / "test1" / "malware_sim.exe"
    if binary_path.is_file():
        res_bin = scanner.scan_file(binary_path)
        if res_bin.get("matched_rules_count", 0) < 1:
            errors.append(f"Expected at least 1 YARA match on malware_sim.exe, got {res_bin}")
    else:
        errors.append(f"Test binary not found at {binary_path}")

    # ── 4. Report Directory Ingestion & Threat Analyzer Integration ──────────
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        art_yara = tmp_path / "artifacts" / "yara"
        art_yara.mkdir(parents=True, exist_ok=True)

        mock_yara = {
            "matched_rules_count": 1,
            "threat_level": "critical",
            "tags": ["ransomware", "T1490"],
            "matches": [
                {
                    "rule": "Ransomware_ShadowCopy_Deletion",
                    "severity": "critical",
                    "mitre_technique": "T1490",
                    "description": "VSSAdmin deletion detected",
                }
            ],
            "mitre_attack": [{"id": "T1490", "name": "Inhibit Recovery"}],
        }
        with open(art_yara / "yara_summary.json", "w", encoding="utf-8") as f:
            json.dump(mock_yara, f)

        # Test scan_report_directory loads cached yara summary
        report_scan = scanner.scan_report_directory(tmp_path)
        if report_scan.get("matched_rules_count") != 1:
            errors.append(f"scan_report_directory failed to load cached summary: {report_scan}")

        # Test threat analyzer metadata loader includes yara_scan
        from core.threatintelligence.threat_analyzer import _load_metadata
        payload_text, has_data = _load_metadata(str(tmp_path))
        if not has_data:
            errors.append("_load_metadata reported no data for directory with yara_summary")
        elif "yara_scan" not in payload_text:
            errors.append(f"yara_scan missing from _load_metadata payload: {payload_text}")

    # ── 5. Gateway Route Registration ────────────────────────────────────────
    from core.gateway.analysis_routes import router

    route_paths = [r.path for r in router.routes]
    if not any(p.endswith("/report/{analysis_id}/yara") for p in route_paths):
        errors.append(f"GET /report/{{analysis_id}}/yara route missing from analysis router: {route_paths}")

    return errors


def main() -> int:
    try:
        errors = run_test()
        output = (
            "YARA Integration verification:\n"
            "  - Curated rulesets loaded and compiled successfully\n"
            "  - Pattern matches for ransomware, evasion, and credential theft verified\n"
            "  - Clean buffers verified without false positive triggers\n"
            "  - Real binary scan on test executable validated\n"
            "  - Report directory artifacts and metadata analyzer integration verified\n"
            "  - Gateway GET /api/analysis/report/{analysis_id}/yara endpoint verified\n"
        )
        if errors:
            print(f"[{TEST_NAME}] FAIL")
            print(f"About: {ABOUT}")
            print(f"Reason: {len(errors)} check(s) failed:\n" + "\n".join(f"  - {e}" for e in errors))
            print(f"Output:\n{output}")
            return 1
        else:
            print(f"[{TEST_NAME}] PASS")
            print(f"About: {ABOUT}")
            print(f"Output:\n{output}")
            return 0
    except Exception as exc:
        print(f"[{TEST_NAME}] FAIL")
        print(f"About: {ABOUT}")
        print(f"Reason: Exception -- {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
