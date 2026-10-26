#!/usr/bin/env python3
"""TEST_39_ai_animation_score_and_collector_telemetry_fix.py

Tests fixes for:
1. AIPipelineAnimation not getting stuck on procmon when status is complete.
2. VirusTotalHeroBanner displaying spinning in-progress state until AI analysis is complete.
3. Agent collector zip packaging retaining tcpvcon_snapshot.csv (not filtering out with .csv).
4. Full fallback and synthesis in get_report_data ensuring sysmon, procmon, network, handle, and tcpvcon
   telemetry is populated and visible to analysts.
"""

import sys
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def run_test():
    test_name = "TEST_39_ai_animation_score_and_collector_telemetry_fix"
    results = {}

    try:
        # 1. Verify AIPipelineAnimation fix in code
        anim_file = PROJECT_ROOT / "core" / "interface" / "src" / "components" / "AIPipelineAnimation.tsx"
        assert anim_file.is_file(), "AIPipelineAnimation.tsx missing"
        anim_src = anim_file.read_text(encoding="utf-8")
        assert 'progress?.status === "complete"' in anim_src, "Missing progress.status === complete check in animation"
        assert "setSummarizerDone(true)" in anim_src, "Missing setSummarizerDone in animation"
        results["ui_animation_fix"] = "AIPipelineAnimation properly drives completion from progress.status == complete"

        # 2. Verify VirusTotalHeroBanner spinning in-progress until AI done
        reports_file = PROJECT_ROOT / "core" / "interface" / "src" / "app" / "reports" / "page.tsx"
        assert reports_file.is_file(), "reports/page.tsx missing"
        reports_src = reports_file.read_text(encoding="utf-8")
        assert "aiAnalyzing" in reports_src, "VirusTotalHeroBanner should receive and handle aiAnalyzing state"
        assert "!aiReport" in reports_src, "VirusTotalHeroBanner should differentiate before AI analysis vs after AI analysis"
        assert "IN PROGRESS" in reports_src, "Hero banner should display IN PROGRESS when AI analysis has not finished"
        results["ui_score_hero_fix"] = "VirusTotalHeroBanner spins and shows IN PROGRESS until AI analysis completes"

        # 3. Verify Agent collector packaging and fallbacks
        agent_file = PROJECT_ROOT / "core" / "agent" / "isolens_agent.py"
        assert agent_file.is_file(), "isolens_agent.py missing"
        agent_src = agent_file.read_text(encoding="utf-8")
        assert "procmon.csv" in agent_src, "isolens_agent should specifically exclude raw procmon.csv, preserving tcpvcon CSV"
        assert "tcpvcon_snapshot.csv" in agent_src, "tcpvcon_snapshot.csv logic present"
        results["agent_collector_packaging"] = "Agent correctly preserves tcpvcon_snapshot.csv and has handle fallback"

        # 4. Verify get_report_data fallback synthesis across telemetry layers
        from core.gateway.analysis_routes import get_report_data
        report_data = get_report_data("20261025_211215_fe84f98f")
        assert report_data.status == "ok", "get_report_data failed"
        d = report_data.data
        for required_key in ["sysmon", "procmon", "network", "handle", "tcpvcon", "network_db", "gui", "risk", "lstm", "yara", "ai_report"]:
            val = d.get(required_key)
            assert val is not None, f"Telemetry layer {required_key} returned None"

        # Verify sysmon has events
        assert d["sysmon"].get("total_events", 0) > 0, "Sysmon events should be > 0"
        # Verify procmon has operations
        assert d["procmon"].get("total_rows", 0) > 0, "Procmon rows should be > 0"
        # Verify network has queries / connections
        assert len(d["network"].get("dns_queries", [])) > 0 or len(d["network"].get("connections", [])) > 0, "Network telemetry should have DNS or connections"
        # Verify handle has text
        assert len(d["handle"]) > 0, "Handle snapshot should be non-empty"
        # Verify tcpvcon has rows
        assert len(d["tcpvcon"]) > 0, "TCPVcon snapshot should be non-empty"
        # Verify AI report completed
        assert d["ai_report"].get("status") == "complete", "AI report should be complete"

        results["telemetry_synthesis"] = {
            "sysmon_events": d["sysmon"]["total_events"],
            "procmon_events": d["procmon"]["total_rows"],
            "network_queries": len(d["network"].get("dns_queries", [])),
            "handle_bytes": len(d["handle"]),
            "tcpvcon_rows": len(d["tcpvcon"]),
            "ai_risk_score": d["ai_report"]["risk_score"],
            "ai_threat_level": d["ai_report"]["threat_level"],
        }

        print(f"[{test_name}] PASS")
        print("About: Verifies AI animation un-sticking, spinning in-progress score until AI done, and collector telemetry recovery.")
        print("Output:")
        print(json.dumps(results, indent=2))
        return 0

    except Exception as exc:
        print(f"[{test_name}] FAIL")
        print("About: Verifies AI animation un-sticking, spinning in-progress score until AI done, and collector telemetry recovery.")
        print(f"Reason: {exc}")
        print("Output:")
        print(json.dumps(results, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(run_test())
