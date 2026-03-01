#!/usr/bin/env python3
"""TEST_17_ai_ui_integration – Verify AI analysis is fully wired into the reports UI."""

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
        print(f"\n[TEST_17_ai_ui_integration:{name}] PASS")
    else:
        FAIL_COUNT += 1
        print(f"\n[TEST_17_ai_ui_integration:{name}] FAIL")
    print(f"  About: {about}")
    print(f"  Output: {output}")


def read(path):
    with open(path, "r") as f:
        return f.read()


# ─── 1. API lib has AI types and functions ───────────────────────────────

api_path = os.path.join(INTERFACE, "lib", "api.ts")
api_src = read(api_path)

for iface in ["AIToolResult", "AIReport"]:
    check(
        f"api_has_{iface}",
        f"api.ts exports interface {iface}",
        f"export interface {iface}" in api_src,
        f"found={'export interface ' + iface in api_src}",
    )

for fn in ["runAIAnalysis", "getAIReport"]:
    check(
        f"api_has_{fn}",
        f"api.ts exports function {fn}",
        f"export async function {fn}" in api_src,
        f"found={'export async function ' + fn in api_src}",
    )

# ─── 2. Reports page exists and imports AI types ────────────────────────

reports_path = os.path.join(INTERFACE, "app", "reports", "page.tsx")
reports_exists = os.path.isfile(reports_path)
check(
    "reports_page_exists",
    "reports/page.tsx file exists",
    reports_exists,
    f"exists={reports_exists}",
)

if not reports_exists:
    print(f"\nTotal: {PASS_COUNT} PASS, {FAIL_COUNT} FAIL")
    sys.exit(1 if FAIL_COUNT else 0)

rpt = read(reports_path)

# Must import AI types from api.ts
for sym in ["getAIReport", "runAIAnalysis", "AIReport", "AIToolResult"]:
    check(
        f"reports_imports_{sym}",
        f"reports/page.tsx imports {sym}",
        sym in rpt,
        f"found={sym in rpt}",
    )

# ─── 3. Key AI components exist ─────────────────────────────────────────

for component in ["AIAnalysisTab", "RiskGauge", "VerdictBadge", "SeverityBadge"]:
    check(
        f"has_{component}",
        f"reports/page.tsx contains {component} component",
        f"function {component}" in rpt,
        f"found={'function ' + component in rpt}",
    )

# ─── 4. JSON data consumption (replaced XML parsers) ───────────────────

for field in ["key_findings", "iocs", "mitre_attack", "recommendations"]:
    check(
        f"has_{field}_usage",
        f"reports/page.tsx consumes aiReport.{field} array",
        f"aiReport.{field}" in rpt or f".{field}" in rpt,
        f"found={field in rpt}",
    )

# ─── 5. AI tab functionality ────────────────────────────────────────────

check(
    "has_ai_tab_switcher",
    "reports page has AI tab button",
    "AI Analysis" in rpt and 'setActiveTab("ai")' in rpt,
    f"found_tab={'AI Analysis' in rpt}",
)

check(
    "has_risk_score_display",
    "reports page displays risk score from AI report",
    "risk_score" in rpt and "threat_level" in rpt,
    f"risk_score={'risk_score' in rpt}, threat_level={'threat_level' in rpt}",
)

check(
    "has_mitre_mapping",
    "reports page renders MITRE ATT&CK mapping",
    "MITRE" in rpt and "mitre_attack" in rpt,
    f"mitre={'MITRE' in rpt}",
)

check(
    "has_ioc_table",
    "reports page renders IOC table",
    "Indicators of Compromise" in rpt and "iocs" in rpt,
    f"ioc={'Indicators of Compromise' in rpt}",
)

check(
    "has_executive_summary",
    "reports page renders executive summary",
    "executive_summary" in rpt and "Executive Summary" in rpt,
    f"found={'Executive Summary' in rpt}",
)

check(
    "has_recommendations",
    "reports page renders recommendations from AI",
    "recommendations" in rpt and "Recommendations" in rpt,
    f"found={'Recommendations' in rpt}",
)

check(
    "has_per_tool_results",
    "reports page shows per-tool agent results",
    "tool_results" in rpt and "Per-Tool Agent" in rpt,
    f"found={'Per-Tool Agent' in rpt}",
)

check(
    "has_auto_load_ai_report",
    "reports page auto-loads existing AI report when selecting a report",
    "getAIReport(report.analysis_id)" in rpt or "getAIReport" in rpt,
    f"found={'getAIReport' in rpt}",
)

# ─── 6. Preserved original report components ────────────────────────────

for component in ["SysmonSection", "ProcmonSection", "NetworkSection", "HandleSection",
                   "TcpvconSection", "ScreenshotGallery", "CollectorBadges"]:
    check(
        f"preserved_{component}",
        f"reports/page.tsx still has original {component}",
        f"function {component}" in rpt,
        f"found={'function ' + component in rpt}",
    )

# ─── 7. Search functionality ────────────────────────────────────────────

check(
    "has_search",
    "reports page has search/filter for report list",
    "searchQuery" in rpt and "Search reports" in rpt,
    f"found={'searchQuery' in rpt}",
)

# ─── Summary ─────────────────────────────────────────────────────────────

print(f"\n{'='*60}")
print(f"TEST_17_ai_ui_integration: {PASS_COUNT} PASS, {FAIL_COUNT} FAIL")
print(f"{'='*60}")
sys.exit(1 if FAIL_COUNT else 0)
