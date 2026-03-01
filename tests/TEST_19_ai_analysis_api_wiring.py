#!/usr/bin/env python3
"""TEST_19 — AI analysis API endpoint wiring.

Validates:
  - /api/analysis/report/{id}/ai-analyze route exists on the router
  - /api/analysis/report/{id}/ai-report route exists on the router
  - Routes have correct methods (POST and GET respectively)
  - The analysis_routes module can be imported cleanly
  - ThreatAnalyzer.get_ai_report returns None for nonexistent report
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TEST_NAME = "TEST_19_ai_analysis_api_wiring"
ABOUT = "AI analysis API endpoints exist with correct methods on the analysis router"


def run_test() -> list[str]:
    errors = []

    # 1. Import analysis routes
    try:
        from core.gateway.analysis_routes import router
    except Exception as exc:
        errors.append(f"Failed to import analysis_routes: {exc}")
        return errors

    # 2. Collect all routes
    routes = {}
    for route in router.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", set())
        if path:
            routes[path] = methods

    # 3. Check ai-analyze endpoint
    ai_analyze_path = "/api/analysis/report/{analysis_id}/ai-analyze"
    if ai_analyze_path not in routes:
        errors.append(f"Missing route: {ai_analyze_path}")
    elif "POST" not in routes[ai_analyze_path]:
        errors.append(f"Route {ai_analyze_path} should be POST, got {routes[ai_analyze_path]}")

    # 4. Check ai-report endpoint
    ai_report_path = "/api/analysis/report/{analysis_id}/ai-report"
    if ai_report_path not in routes:
        errors.append(f"Missing route: {ai_report_path}")
    elif "GET" not in routes[ai_report_path]:
        errors.append(f"Route {ai_report_path} should be GET, got {routes[ai_report_path]}")

    # 5. ThreatAnalyzer.get_ai_report for nonexistent
    try:
        from core.threatintelligence.threat_analyzer import ThreatAnalyzer
        analyzer = ThreatAnalyzer()
        result = analyzer.get_ai_report("nonexistent_id_12345")
        if result is not None:
            errors.append(f"get_ai_report('nonexistent') should return None, got {type(result)}")
    except Exception as exc:
        errors.append(f"ThreatAnalyzer.get_ai_report raised: {exc}")

    # 6. Verify model enforcement
    try:
        from core.threatintelligence.copilot_service import REQUIRED_MODEL, ThreatIntelCopilotService
        if REQUIRED_MODEL != "gpt-5-mini":
            errors.append(f"REQUIRED_MODEL = {REQUIRED_MODEL!r}, expected 'gpt-5-mini'")
        # Even if caller passes a different model, service should use gpt-5-mini
        # (can't actually call Copilot in tests, just verify attribute)
        svc = ThreatIntelCopilotService.__new__(ThreatIntelCopilotService)
        svc.__init__(model="gpt-4o")
        if svc.model != "gpt-5-mini":
            errors.append(f"Service model = {svc.model!r} after passing 'gpt-4o', expected 'gpt-5-mini'")
    except Exception as exc:
        errors.append(f"Model enforcement check failed: {exc}")

    return errors


def main():
    try:
        errors = run_test()
        output = "\n".join(errors) if errors else "All checks passed"
        if errors:
            print(f"[{TEST_NAME}] FAIL")
            print(f"About: {ABOUT}")
            print(f"Reason: {len(errors)} check(s) failed")
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
        print(f"Reason: Exception — {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
