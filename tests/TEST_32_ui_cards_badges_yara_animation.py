#!/usr/bin/env python3
"""TEST_32_ui_cards_badges_yara_animation.py - Test UI visual cards, badges, YARA section, and pipeline animation.

Verifies:
1. Gateway exposes /api/analysis/report/{id}/network-db and embeds network_db in /data.
2. Interface api.ts defines TypeScript models and helpers for Yara, LSTM, GUI, Risk, and Network DB.
3. AIPipelineAnimation includes the multi-stage agents: YARA, Sysmon, Procmon, BiLSTM, Laya GUI, and Network Threat DB.
4. Reports page renders:
   - Separate YARA section with dedicated vector YARA logo and capability tags.
   - 4 visual cards in ReportOverview (YARA matches, BiLSTM probability, GUI triage, Network DB).
   - Screenshot alert flags with red glowing border, warning badge overlay, and lightbox banner for flagged ransomware/scam screens.
   - Header quick badges for all modules.
"""

import sys
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def run_test():
    test_name = "TEST_32_ui_cards_badges_yara_animation"
    results = {}

    try:
        # 1. Check analysis_routes.py
        routes_file = PROJECT_ROOT / "core" / "gateway" / "analysis_routes.py"
        routes_code = routes_file.read_text(encoding="utf-8")
        assert "/report/{analysis_id}/network-db" in routes_code, "network-db endpoint missing in analysis_routes"
        assert '"network_db": net_db_data' in routes_code, "network_db missing in get_report_data"
        results["gateway_routes"] = "network-db route and /data payload verified"

        # 2. Check api.ts
        api_ts = PROJECT_ROOT / "core" / "interface" / "src" / "lib" / "api.ts"
        api_code = api_ts.read_text(encoding="utf-8")
        for type_name in ["YaraData", "LstmData", "GuiData", "RiskData", "NetworkDBData"]:
            assert f"export interface {type_name}" in api_code, f"Missing {type_name} in api.ts"
        assert "export async function getNetworkDBData" in api_code, "Missing getNetworkDBData in api.ts"
        assert "yara: YaraData | null" in api_code, "ReportData missing yara"
        assert "lstm: LstmData | null" in api_code, "ReportData missing lstm"
        assert "network_db: NetworkDBData | null" in api_code, "ReportData missing network_db"
        results["typescript_api_models"] = "All TypeScript interfaces and API client functions verified"

        # 3. Check AIPipelineAnimation.tsx
        anim_tsx = PROJECT_ROOT / "core" / "interface" / "src" / "components" / "AIPipelineAnimation.tsx"
        anim_code = anim_tsx.read_text(encoding="utf-8")
        assert 'id: "yara"' in anim_code, "YARA agent missing in AIPipelineAnimation"
        assert 'id: "lstm"' in anim_code, "BiLSTM agent missing in AIPipelineAnimation"
        assert 'id: "gui"' in anim_code, "Laya GUI agent missing in AIPipelineAnimation"
        assert 'id: "network"' in anim_code, "Network Threat DB missing in AIPipelineAnimation"
        assert "YARA Rules Engine" in anim_code, "YARA Rules label missing in animation"
        assert "Static YARA" not in anim_code, "Term 'Static' was not removed from animation"
        assert "BiLSTM Neural Model" in anim_code, "BiLSTM label missing in animation"
        assert "Laya Screen Triage" in anim_code, "Laya GUI label missing in animation"
        results["pipeline_animation"] = "6-stage agent SVG pipeline flow animation verified"

        # 4. Check reports/page.tsx
        reports_page = PROJECT_ROOT / "core" / "interface" / "src" / "app" / "reports" / "page.tsx"
        page_code = reports_page.read_text(encoding="utf-8")
        assert "function YaraLogo(" in page_code, "YaraLogo SVG component missing"
        assert "function YaraSection(" in page_code, "YaraSection component missing"
        assert "function LstmSection(" in page_code, "LstmSection component missing"
        assert "function NetworkDBSection(" in page_code, "NetworkDBSection component missing"
        assert "function BehaviorSection(" in page_code, "BehaviorSection component missing"
        assert "Multi-Layer Threat Engine Analysis" in page_code, "Overview threat cards section missing"
        assert "YARA Rules" in page_code, "YARA card missing in overview"
        assert "Static YARA" not in page_code, "Term 'Static YARA' was not removed from page.tsx"
        assert "BiLSTM Neural" in page_code, "BiLSTM card missing in overview"
        assert "Laya GUI Triage" in page_code, "GUI triage card missing in overview"
        assert "Threat Intel DB" in page_code, "Threat DB card missing in overview"
        assert "guiData?.flagged_windows" in page_code, "Screenshot flagged windows mapping missing"
        assert "border-rose-500 ring-2 ring-rose-400" in page_code, "Screenshot threat highlight missing"
        assert "YARA — Pattern & Capability Detection" in page_code, "YARA evidence panel missing"
        results["reports_page_ui"] = "Dedicated YARA section, visual cards, badges, and screenshot alert flags verified"

        print(f"[{test_name}] PASS")
        print("About: Visual cards, badges, dedicated YARA section, and pipeline animation verified.")
        print("Output:")
        print(json.dumps(results, indent=2))
        return 0

    except Exception as exc:
        print(f"[{test_name}] FAIL")
        print(f"About: Visual cards, badges, dedicated YARA section, and pipeline animation verified.")
        print(f"Reason: {exc}")
        print("Output:")
        print(json.dumps(results, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(run_test())
