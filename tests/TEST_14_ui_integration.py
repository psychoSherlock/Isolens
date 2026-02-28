#!/usr/bin/env python3
"""TEST_14_ui_integration – Verify UI is wired to real APIs, no placeholder mock data."""

import json
import os
import re
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
INTERFACE = os.path.join(PROJECT_ROOT, "core", "interface", "src")

PASS_COUNT = 0
FAIL_COUNT = 0


def check(name, about, condition, output):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"\n[TEST_14_ui_integration:{name}] PASS")
    else:
        FAIL_COUNT += 1
        print(f"\n[TEST_14_ui_integration:{name}] FAIL")
    print(f"  About: {about}")
    print(f"  Output: {output}")


def read(path):
    with open(path, "r") as f:
        return f.read()


# ── Check API utility exists ──────────────────────────────────────────

api_path = os.path.join(INTERFACE, "lib", "api.ts")
api_exists = os.path.isfile(api_path)
check(
    "API lib exists",
    "API utility library exists at src/lib/api.ts",
    api_exists,
    f"exists={api_exists}",
)

if api_exists:
    api_src = read(api_path)
    exports = re.findall(r"export (?:async )?function (\w+)", api_src)
    check(
        "API lib has all functions",
        "API utility exports essential functions",
        all(
            fn in exports
            for fn in [
                "ping", "getVersion", "listVMs", "submitAnalysis",
                "getAnalysisStatus", "listScreenshots", "screenshotURL",
                "getAgentStatus", "listReports",
            ]
        ),
        f"exports={exports}",
    )

# ── Check Next.js proxy config ─────────────────────────────────────────

next_config = read(os.path.join(INTERFACE, "..", "next.config.ts"))
has_rewrite = "rewrites" in next_config and "localhost:6969" in next_config
check(
    "Next.js proxy configured",
    "next.config.ts has rewrite rules for API proxy",
    has_rewrite,
    f"rewrites={has_rewrite}",
)

# ── Check pages import from @/lib/api ────────────────────────────────

pages_to_check = {
    "scan": os.path.join(INTERFACE, "app", "scan", "page.tsx"),
    "reports": os.path.join(INTERFACE, "app", "reports", "page.tsx"),
    "sandbox": os.path.join(INTERFACE, "app", "sandbox", "page.tsx"),
    "scan-history": os.path.join(INTERFACE, "app", "scan-history", "page.tsx"),
    "settings": os.path.join(INTERFACE, "app", "settings", "page.tsx"),
    "help-support": os.path.join(INTERFACE, "app", "help-support", "page.tsx"),
}

for name, path in pages_to_check.items():
    src = read(path)
    uses_api = "@/lib/api" in src
    check(
        f"{name} uses API lib",
        f"{name}/page.tsx imports from @/lib/api",
        uses_api,
        f"imports_api={uses_api}",
    )

# ── Check NO mock data in scan page ──────────────────────────────────

scan_src = read(pages_to_check["scan"])
has_mock = "mockScans" in scan_src or "Mock Data" in scan_src
check(
    "Scan page no mock data",
    "Scan page does not contain mock/placeholder data arrays",
    not has_mock,
    f"has_mock={has_mock}",
)

# ── Check scan page has file upload + submit ─────────────────────────

has_upload = "submitAnalysis" in scan_src
has_file_input = 'type="file"' in scan_src or "type='file'" in scan_src
check(
    "Scan page has real upload",
    "Scan page calls submitAnalysis and has file input",
    has_upload and has_file_input,
    f"submitAnalysis={has_upload}, file_input={has_file_input}",
)

# ── Check reports page shows screenshots ─────────────────────────────

reports_src = read(pages_to_check["reports"])
has_screenshots = "screenshotURL" in reports_src and ("listScreenshots" in reports_src or "getReportData" in reports_src)
check(
    "Reports page shows screenshots",
    "Reports page uses screenshotURL and getReportData/listScreenshots",
    has_screenshots,
    f"screenshotURL={'screenshotURL' in reports_src}, reportData={'getReportData' in reports_src}",
)

# ── Check sandbox page has VM controls ──────────────────────────────

sandbox_src = read(pages_to_check["sandbox"])
has_start = "startVM" in sandbox_src
has_poweroff = "poweroffVM" in sandbox_src
has_agent = "getAgentStatus" in sandbox_src
check(
    "Sandbox page has VM controls",
    "Sandbox page uses startVM, poweroffVM, getAgentStatus",
    has_start and has_poweroff and has_agent,
    f"start={has_start}, poweroff={has_poweroff}, agent={has_agent}",
)

# ── Check scan-history page has mock data removed ──────────────────

history_src = read(pages_to_check["scan-history"])
has_old_mock = "mockScans" in history_src
has_coming_soon = "Coming Soon" in history_src
check(
    "Scan history no mock + coming soon",
    "Scan history removes mock data and has coming soon label",
    not has_old_mock and has_coming_soon,
    f"old_mock={has_old_mock}, coming_soon={has_coming_soon}",
)

# ── Check settings has coming soon labels ───────────────────────────

settings_src = read(pages_to_check["settings"])
settings_coming_soon = "Coming Soon" in settings_src
settings_uses_api = "getVersion" in settings_src or "ping" in settings_src
check(
    "Settings coming soon + live data",
    "Settings page has Coming Soon labels and uses live API data",
    settings_coming_soon and settings_uses_api,
    f"coming_soon={settings_coming_soon}, uses_api={settings_uses_api}",
)

# ── Check Header has gateway status ─────────────────────────────────

header_src = read(os.path.join(INTERFACE, "components", "Header.tsx"))
header_uses_api = "ping" in header_src
header_shows_status = "Gateway" in header_src
check(
    "Header shows gateway status",
    "Header component imports ping and shows gateway status",
    header_uses_api and header_shows_status,
    f"ping={header_uses_api}, status={header_shows_status}",
)

# ── Check gateway has CORS ──────────────────────────────────────────

gateway_app = read(os.path.join(PROJECT_ROOT, "core", "gateway", "app.py"))
has_cors = "CORSMiddleware" in gateway_app
check(
    "Gateway has CORS",
    "Gateway app.py includes CORS middleware",
    has_cors,
    f"cors={has_cors}",
)

# ── Check gateway has screenshot endpoints ───────────────────────────

analysis_routes = read(os.path.join(PROJECT_ROOT, "core", "gateway", "analysis_routes.py"))
has_screenshot_list = "list_screenshots" in analysis_routes
has_file_serve = "serve_report_file" in analysis_routes
has_reports_list = "list_reports" in analysis_routes
has_report_data = "get_report_data" in analysis_routes
check(
    "Gateway screenshot endpoints",
    "Gateway has screenshot list, file serve, reports list, and report data endpoints",
    has_screenshot_list and has_file_serve and has_reports_list and has_report_data,
    f"list={has_screenshot_list}, serve={has_file_serve}, reports_list={has_reports_list}, data={has_report_data}",
)

# ── Check reports page has two tabs (Report + AI Summary) ───────────

reports_src_full = read(pages_to_check["reports"])
has_report_tab = 'activeTab === "report"' in reports_src_full or "activeTab" in reports_src_full
has_ai_tab = "AI Summary" in reports_src_full or "Coming Soon" in reports_src_full
has_sysmon_section = "SysmonSection" in reports_src_full
has_procmon_section = "ProcmonSection" in reports_src_full
has_network_section = "NetworkSection" in reports_src_full
has_gallery = "ScreenshotGallery" in reports_src_full
has_hover = "startHoverAdvance" in reports_src_full or "hoverTimerRef" in reports_src_full
check(
    "Reports page two-tab layout",
    "Reports page has Report tab and AI Summary Coming Soon tab",
    has_report_tab and has_ai_tab,
    f"report_tab={has_report_tab}, ai_tab={has_ai_tab}",
)
check(
    "Reports page collector sections",
    "Reports page has Sysmon, Procmon, Network sections",
    has_sysmon_section and has_procmon_section and has_network_section,
    f"sysmon={has_sysmon_section}, procmon={has_procmon_section}, network={has_network_section}",
)
check(
    "Reports page screenshot gallery",
    "Reports page has ScreenshotGallery with hover-to-advance",
    has_gallery and has_hover,
    f"gallery={has_gallery}, hover={has_hover}",
)

# ── Summary ──────────────────────────────────────────────────────────

print(f"\n\n{'=' * 60}")
print(f"  Results: {PASS_COUNT}/{PASS_COUNT+FAIL_COUNT} passed, {FAIL_COUNT}/{PASS_COUNT+FAIL_COUNT} failed")
print(f"{'=' * 60}")

if FAIL_COUNT > 0:
    print(f"\n[TEST_14_ui_integration] FAIL")
    sys.exit(1)
else:
    print(f"\n[TEST_14_ui_integration] PASS")
