"""Structural regression checks for the simple IsoLens interface refresh."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sidebar = (ROOT / "core/interface/src/components/Sidebar.tsx").read_text()
scan = (ROOT / "core/interface/src/app/scan/page.tsx").read_text()
reports = (ROOT / "core/interface/src/app/reports/page.tsx").read_text()
history = (ROOT / "core/interface/src/app/scan-history/page.tsx").read_text()
help_page = (ROOT / "core/interface/src/app/help-support/page.tsx").read_text()
settings = (ROOT / "core/interface/src/app/settings/page.tsx").read_text()
styles = (ROOT / "core/interface/src/app/globals.css").read_text()

checks = {
    "existing_sections_only": all(
        label in sidebar for label in ["Scan", "Reports", "Scan History", "Settings", "Help & Support"]
    ) and 'href: "/sandbox"' not in sidebar,
    "accessible_scan_progress": 'role="progressbar"' in scan and 'aria-valuenow={progress}' in scan,
    "stateful_analysis_flow": "flowStages" in scan and "scan-flow" in scan,
    "report_flow_preserved": "AIPipelineAnimation" in reports,
    "reports_open_with_plain_language_overview": 'useState<"overview" | "evidence" | "ai">("overview")' in reports and "What happened to this sample?" in reports,
    "reports_have_readable_activity_graph": "Activity collected" in reports and "System activity" in reports and "Network lookups" in reports,
    "risk_is_distinguished_from_activity_counts": "A higher count alone does not mean a file is malicious." in reports and "AI assessment not run" in reports,
    "technical_evidence_remains_available": 'setActiveTab("evidence")' in reports and "Technical evidence" in reports,
    "idle_preview_hidden": '{scanState === "running" && <div className="lg:col-span-2' in scan,
    "compact_sandbox_controls": 'className="environment-details p-6' in scan and 'data-idle={scanState !== "running"}' in scan,
    "violet_scan_action": "scan-primary" in scan and ".app-content button.scan-primary" in styles,
    "no_unimplemented_sandbox_page": 'href="/sandbox"' not in help_page and 'href: "/sandbox"' not in sidebar,
    "history_uses_available_data": "Past analyses saved in local report storage." in history,
    "settings_shows_live_configuration": "getVMInfo" in settings and "getVersion" in settings,
    "settings_has_no_placeholder_controls": "Coming Soon" not in settings and "Save Settings" not in settings,
    "responsive_navigation": "@media (max-width: 760px)" in styles,
    "reduced_motion": "prefers-reduced-motion: reduce" in styles,
}
raw_output = json.dumps(checks, indent=2)
failed = [name for name, passed in checks.items() if not passed]
print("[TEST_27_simple_ui_redesign] " + ("FAIL" if failed else "PASS"))
print("About: Existing navigation, animated scan/report progress, and responsive accessibility remain present")
if failed:
    print("Reason: " + ", ".join(failed))
print("Output:")
print(raw_output)
raise SystemExit(bool(failed))
