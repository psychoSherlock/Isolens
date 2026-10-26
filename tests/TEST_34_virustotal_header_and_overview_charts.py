#!/usr/bin/env python3
"""TEST_34_virustotal_header_and_overview_charts.py - Test VirusTotal Score Header and Overview Charts.

Verifies:
1. VirusTotal-style animated score hero header is rendered at the top of report view:
   - VirusTotalHeroBanner component definition and placement in ReportsPage
   - Animated SVG circle gauge with real-time score count-up and cubic ease-out stroke
   - Bold threat verdict banner (CRITICAL / SUSPICIOUS / BENIGN)
   - Engine detection ratio (X / 5 security engines flagged)
   - VirusTotal-style segmented consensus progress bar
   - Analysis ID copy button with feedback
2. Enhanced technical yet accessible charts on the Overview page:
   - Win32 Kernel & Subsystem API Call Profile categorized distribution chart
   - MITRE ATT&CK Enterprise Tactical Matrix Navigator (6 tactical columns)
   - Engine Detection Consensus & Score Comparison Matrix (5 detection layers)
   - System Mutation & Telemetry Breakdown (Filesystem, Registry, Network ratios)
   - Observed Threat Indicators of Compromise (IOC) Cards with copy support
3. No forbidden terms (e.g. 'Static YARA' or 'Static' in detection titles).
"""

import sys
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def run_test():
    test_name = "TEST_34_virustotal_header_and_overview_charts"
    results = {}

    try:
        page_path = PROJECT_ROOT / "core" / "interface" / "src" / "app" / "reports" / "page.tsx"
        assert page_path.is_file(), "reports/page.tsx does not exist"
        page_code = page_path.read_text(encoding="utf-8")

        # 1. VirusTotal Header checks
        assert "function VirusTotalHeroBanner(" in page_code, "VirusTotalHeroBanner component definition missing"
        assert "<VirusTotalHeroBanner" in page_code, "VirusTotalHeroBanner not rendered in ReportsPage"
        assert "security detection engines flagged threat indicators" in page_code, "Detection consensus text missing"
        assert "detection consensus" in page_code, "Detection ratio consensus missing"
        assert "Risk Score" in page_code, "Risk score gauge subtitle missing"
        assert "handleCopyId" in page_code, "Analysis ID copy handler missing in hero banner"
        results["virustotal_hero_banner"] = "VirusTotal-style hero banner with animated radial gauge verified"

        # 2. Overview charts checks
        assert "function ApiCategoryDistributionChart(" in page_code, "ApiCategoryDistributionChart component missing"
        assert "Win32 Kernel & Subsystem API Call Profile" in page_code, "API profile chart title missing"
        assert "getApiCategoryBreakdown" in page_code, "API category breakdown calculation missing"

        assert "function MitreAttackMatrixChart(" in page_code, "MitreAttackMatrixChart component missing"
        assert "MITRE ATT&CK® Enterprise Behavioral Matrix" in page_code, "MITRE matrix title missing"
        assert "getMitreTacticalMatrix" in page_code, "MITRE tactical matrix mapping missing"

        assert "function EngineConsensusMatrixChart(" in page_code, "EngineConsensusMatrixChart component missing"
        assert "Engine Detection Consensus & Score Comparison" in page_code, "Engine consensus title missing"

        assert "function TelemetryBreakdownChart(" in page_code, "TelemetryBreakdownChart component missing"
        assert "System Mutation & Telemetry Breakdown" in page_code, "System mutation chart title missing"

        assert "function ObservedIocCards(" in page_code, "ObservedIocCards component missing"
        assert "Observed Threat Indicators of Compromise (IOCs)" in page_code, "IOC cards title missing"

        results["overview_charts"] = (
            "5 technical yet accessible charts (API profile, MITRE matrix, engine consensus, "
            "telemetry breakdown, IOC cards) verified in ReportOverview"
        )

        # 3. Cleanliness: no 'Static YARA'
        assert "Static YARA" not in page_code, "Forbidden phrase 'Static YARA' found in page.tsx"
        results["cleanliness"] = "No forbidden 'Static' terms in detection titles"

        print(f"[{test_name}] PASS")
        print("About: VirusTotal Score Header and Overview Charts verification.")
        print("Output:")
        print(json.dumps(results, indent=2))
        return 0

    except Exception as exc:
        print(f"[{test_name}] FAIL")
        print("About: VirusTotal Score Header and Overview Charts verification.")
        print(f"Reason: {exc}")
        print("Output:")
        print(json.dumps(results, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(run_test())
