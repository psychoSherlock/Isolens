#!/usr/bin/env python3
"""TEST_33_c2_communication_and_evidence_fix.py - Test C2 network communication and technical evidence resolution.

Verifies:
1. Malware sample in SandboxShare includes hardcoded C2 IP (162.243.103.246) and domain (re-id-v3.com) from centralized DB.
2. NetworkThreatIntelMatcher matches the C2 observables against the centralized SQLite threat database.
3. get_report_data() ensures technical evidence layers (LSTM, YARA, Behavior, GUI, Risk, Network DB, Sysmon fallback) are populated without returning 'None'.
"""

import sys
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def run_test():
    test_name = "TEST_33_c2_communication_and_evidence_fix"
    results = {}

    try:
        # 1. Verify C2 source code and compiled PE
        c_file = PROJECT_ROOT / "SandboxShare" / "malware_network_gui.c"
        assert c_file.is_file(), "malware_network_gui.c source file missing"
        c_code = c_file.read_text(encoding="utf-8")
        assert "162.243.103.246" in c_code, "Hardcoded C2 IP missing in malware_network_gui.c"
        assert "re-id-v3.com" in c_code, "Hardcoded C2 domain missing in malware_network_gui.c"

        exe_file = PROJECT_ROOT / "SandboxShare" / "malware_network.exe"
        assert exe_file.is_file(), "Compiled malware_network.exe missing"
        assert exe_file.stat().st_size > 10000, "malware_network.exe size too small"
        results["c2_sample"] = "malware_network_gui.c and PE binary verified with hardcoded C2 observables"

        # 2. Match against centralized SQLite threat DB
        from core.modules.network_db_matcher import NetworkThreatIntelMatcher
        matcher = NetworkThreatIntelMatcher()
        ip_match = matcher.lookup_ip("162.243.103.246")
        assert ip_match is not None, "Failed to match 162.243.103.246 in threat DB"
        assert "Emotet" in (ip_match.get("malware_family") or ""), "Expected Emotet family match"

        dom_match = matcher.lookup_domain("re-id-v3.com")
        assert dom_match is not None, "Failed to match re-id-v3.com in threat DB"
        results["threat_db_matching"] = f"IP matched {ip_match['malware_family']} ({ip_match['threat_type']}); Domain matched {dom_match['threat_type']}"

        # 3. Verify get_report_data() populates technical evidence
        from core.gateway.analysis_routes import get_report_data
        report_data = get_report_data("20261021_132219_62b87e98")
        assert report_data.status == "ok", "get_report_data returned error"
        d = report_data.data
        for required_key in ["yara", "lstm", "behavior", "gui", "risk", "network_db", "sysmon", "procmon"]:
            val = d.get(required_key)
            assert val is not None, f"Required evidence key {required_key} is None in get_report_data"
        results["evidence_resolution"] = "All evidence layers (LSTM, YARA, Behavior, GUI, Risk, Sysmon, Procmon, Network DB) populated"

        print(f"[{test_name}] PASS")
        print("About: C2 communication observables and technical evidence on-the-fly resolution verified.")
        print("Output:")
        print(json.dumps(results, indent=2))
        return 0

    except Exception as exc:
        print(f"[{test_name}] FAIL")
        print("About: C2 communication observables and technical evidence on-the-fly resolution verified.")
        print(f"Reason: {exc}")
        print("Output:")
        print(json.dumps(results, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(run_test())
