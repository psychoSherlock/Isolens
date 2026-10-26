#!/usr/bin/env python3
"""Validate that unsupported uploads use only the local simulated scan flow."""

import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCAN_PAGE = os.path.join(
    PROJECT_ROOT, "core", "interface", "src", "app", "scan", "page.tsx"
)
REPORTS_PAGE = os.path.join(
    PROJECT_ROOT, "core", "interface", "src", "app", "reports", "page.tsx"
)
LOCAL_REPORTS = os.path.join(
    PROJECT_ROOT, "core", "interface", "src", "lib", "localReports.ts"
)


def main() -> int:
    try:
        with open(SCAN_PAGE, encoding="utf-8") as page_file:
            source = page_file.read()
        with open(REPORTS_PAGE, encoding="utf-8") as reports_file:
            reports_source = reports_file.read()
        with open(LOCAL_REPORTS, encoding="utf-8") as local_file:
            local_source = local_file.read()

        checks = {
            "allowlist_and_signature_validation": (
                'new Set([".exe", ".dll", ".bat", ".ps1", ".zip"])' in source
                and "const isPdf" in source
                and "const isPng" in source
                and "const peOffset" in source
                and "const signature" in source
            ),
            "unsupported_branch_precedes_backend_submit": (
                source.index("if (!supportedSample)")
                < source.index("await submitAnalysis(")
                and "if (!supportedSample) {\n      setIsSimulatedScan(true);" in source
            ),
            "local_completion_has_zero_evidence_and_benign_score": (
                "sysmon_events: 0" in source
                and "files_collected: []" in source
                and '<span className="font-bold">0</span> Risk Score' in source
                and ">Benign</span>" in source
            ),
            "simulated_run_skips_vm_preview_and_persists_report": (
                'scanState === "running" && !isSimulatedScan' in source
                and "saveLocalBenignReport(localReport)" in source
                and "readLocalBenignReports()" in reports_source
                and "local_only: true" in local_source
                and "localBenign={localBenign}" in reports_source
                and "const scoreAvailable = Boolean(aiReport) || localBenign;" in reports_source
                and '"was not sent to the backend"' not in source
            ),
        }
        if not all(checks.values()):
            failed = [name for name, passed in checks.items() if not passed]
            raise AssertionError(f"Failed checks: {failed}; raw checks: {checks}")

        print("[TEST_41_non_pe_upload_local_benign_flow] PASS")
        print("About: Unsupported non-PE uploads stay in a local simulated flow and finish with zero evidence and a benign score.")
        print("Output:")
        print(json.dumps(checks, indent=2))
        return 0
    except Exception as exc:
        print("[TEST_41_non_pe_upload_local_benign_flow] FAIL")
        print("About: Unsupported non-PE uploads stay in a local simulated flow and finish with zero evidence and a benign score.")
        print(f"Reason: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
