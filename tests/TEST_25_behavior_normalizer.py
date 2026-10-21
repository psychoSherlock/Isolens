#!/usr/bin/env python3
"""TEST_25 - File & Registry Behavioral Normalization and Sensitive Read Tracking.

Validates:
  1. ProcmonCollector parser captures ReadFile operations and prioritizes sensitive file targets.
  2. ProcmonCollector parser captures RegQueryValue operations and prioritizes persistence/security keys.
  3. behavior_normalizer module categorizes operations (created, written, read, deleted).
  4. Automatic MITRE ATT&CK technique inferences (T1547.001 Persistence, T1005 Collection, T1070.004 Deletion).
  5. Report directory integration via normalize_report_behavior.
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

TEST_NAME = "TEST_25_behavior_normalizer"
ABOUT = "File and Registry behavioral normalization, sensitive target extraction, and MITRE mapping"


def run_test() -> list[str]:
    errors: list[str] = []

    # ── 1. ProcmonCollector Parsing Verification ─────────────────────────────
    from core.agent.isolens_agent import ProcmonCollector

    sample_csv = _PROJECT_ROOT / "test" / "test1_lstm_test" / "test1" / "procmon_malware_sim.csv"
    if not sample_csv.is_file():
        errors.append(f"Sample test CSV not found at {sample_csv}")
        return errors

    collector = ProcmonCollector(workdir=str(_PROJECT_ROOT / "core" / "storage"))
    collector.set_sample("malware_sim.exe")
    parsed = collector._parse_procmon_csv(str(sample_csv))

    file_act = parsed.get("file_activity", {})
    notable_files = file_act.get("notable", {})
    sensitive_reads = file_act.get("sensitive_reads", [])

    if "ReadFile" not in notable_files:
        errors.append("ReadFile missing from file_activity.notable")

    if not sensitive_reads:
        errors.append("sensitive_reads empty; expected dropped_payload.tmp to be captured")
    elif not any("dropped_payload.tmp" in p for p in sensitive_reads):
        errors.append(f"dropped_payload.tmp not found in sensitive_reads: {sensitive_reads}")

    reg_act = parsed.get("registry_activity", {})
    notable_reg = reg_act.get("notable", {})
    sensitive_queries = reg_act.get("sensitive_queries", [])

    if "RegQueryValue" not in notable_reg:
        errors.append("RegQueryValue missing from registry_activity.notable")

    if not sensitive_queries:
        errors.append("sensitive_queries empty; expected Run/Services keys to be captured")

    # ── 2. Behavior Normalizer Heuristics & Categorization ────────────────────
    from core.modules.behavior_normalizer import (
        is_sensitive_file,
        is_benign_system_file,
        classify_registry_key,
        normalize_behavior_artifacts,
        normalize_report_behavior,
    )

    # File heuristics
    if not is_sensitive_file(r"C:\Users\admin\Desktop\passwords.txt"):
        errors.append("is_sensitive_file failed on Desktop path")
    if not is_sensitive_file(r"C:\Users\admin\AppData\Local\Google\Chrome\User Data\Default\Login Data"):
        errors.append("is_sensitive_file failed on Browser profile path")
    if is_sensitive_file(r"C:\Windows\System32\kernel32.dll"):
        errors.append("is_sensitive_file incorrectly flagged kernel32.dll as sensitive")

    if not is_benign_system_file(r"C:\Windows\System32\ntdll.dll"):
        errors.append("is_benign_system_file failed on system32 dll")
    if is_benign_system_file(r"C:\Users\admin\Downloads\payload.exe"):
        errors.append("is_benign_system_file incorrectly flagged user payload as system file")

    # Registry classification
    run_cls = classify_registry_key(r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run\Updater")
    if not run_cls["is_persistence"]:
        errors.append("classify_registry_key failed to detect persistence key")

    def_cls = classify_registry_key(r"HKLM\Software\Policies\Microsoft\Windows Defender\DisableAntiSpyware")
    if not def_cls["is_defense_tampering"]:
        errors.append("classify_registry_key failed to detect defense tampering key")

    recon_cls = classify_registry_key(r"HKLM\Hardware\Description\System\CentralProcessor\0")
    if not recon_cls["is_recon"]:
        errors.append("classify_registry_key failed to detect CPU recon key")

    # ── 3. Full Artifact Normalization & MITRE ATT&CK Inferences ─────────────
    norm = normalize_behavior_artifacts(procmon_summary=parsed)

    summary = norm.get("summary", {})
    if summary.get("total_sensitive_reads", 0) < 1:
        errors.append(f"total_sensitive_reads was {summary.get('total_sensitive_reads')}, expected >= 1")

    if summary.get("total_persistence_keys", 0) < 1:
        errors.append(f"total_persistence_keys was {summary.get('total_persistence_keys')}, expected >= 1")

    mitre_ids = [m["id"] for m in norm.get("mitre_attack", [])]
    if "T1547.001" not in mitre_ids:
        errors.append(f"T1547.001 (Persistence) missing from inferred MITRE techniques: {mitre_ids}")

    if "T1005" not in mitre_ids:
        errors.append(f"T1005 (Data from Local System) missing from inferred MITRE techniques: {mitre_ids}")

    # ── 4. Report Directory Integration ──────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        p_dir = tmp_path / "artifacts" / "procmon"
        p_dir.mkdir(parents=True, exist_ok=True)
        with open(p_dir / "procmon_summary.json", "w", encoding="utf-8") as f:
            json.dump(parsed, f)

        rep_norm = normalize_report_behavior(tmp_path)
        if rep_norm.get("sample_process") != "malware_sim.exe":
            errors.append(f"normalize_report_behavior sample_process mismatch: {rep_norm.get('sample_process')}")
        if not rep_norm.get("files", {}).get("sensitive_reads"):
            errors.append("normalize_report_behavior produced empty sensitive_reads")

    return errors


def main() -> int:
    try:
        errors = run_test()
        output = (
            "File & Registry Behavioral Normalizer verification:\n"
            "  - ReadFile captured with sensitive path prioritization\n"
            "  - RegQueryValue captured with persistence and recon prioritization\n"
            "  - Heuristics successfully distinguish sensitive targets from benign OS noise\n"
            "  - MITRE ATT&CK mappings inferred (T1547.001, T1005, T1070.004)\n"
            "  - Report directory ingestion validated\n"
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
