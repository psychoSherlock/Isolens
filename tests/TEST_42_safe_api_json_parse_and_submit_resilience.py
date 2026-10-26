#!/usr/bin/env python3
"""TEST_42_safe_api_json_parse_and_submit_resilience.py

Verify frontend safe JSON parsing, proxy timeout configuration,
and submit error status resilience during long-running VM scans.
"""

import os
import sys
import json
import urllib.request

TEST_NAME = "TEST_42_safe_api_json_parse_and_submit_resilience"

def run_test():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    api_ts = os.path.join(repo_root, "core", "interface", "src", "lib", "api.ts")
    next_cfg = os.path.join(repo_root, "core", "interface", "next.config.ts")
    scan_page = os.path.join(repo_root, "core", "interface", "src", "app", "scan", "page.tsx")

    output_details = {}

    # Check 1: api.ts has parseApiResponse and uses it across get, post, submitAnalysis, runAIAnalysis
    if not os.path.exists(api_ts):
        return False, f"api.ts not found at {api_ts}", output_details

    with open(api_ts, "r", encoding="utf-8") as f:
        api_content = f.read()

    has_parse_api_resp = "parseApiResponse" in api_content
    has_content_type_check = 'contentType.includes("application/json")' in api_content
    has_safe_submit = "parseApiResponse<AnalysisResult>(res)" in api_content
    has_safe_run_ai = "parseApiResponse<AIReport>(res)" in api_content

    output_details["api_ts_parse_api_response"] = has_parse_api_resp
    output_details["api_ts_content_type_check"] = has_content_type_check
    output_details["api_ts_safe_submit"] = has_safe_submit
    output_details["api_ts_safe_run_ai"] = has_safe_run_ai

    if not (has_parse_api_resp and has_content_type_check and has_safe_submit and has_safe_run_ai):
        return False, "api.ts lacks safe parseApiResponse handling", output_details

    # Check 2: next.config.ts has proxyTimeout >= 300000
    if not os.path.exists(next_cfg):
        return False, f"next.config.ts not found at {next_cfg}", output_details

    with open(next_cfg, "r", encoding="utf-8") as f:
        next_content = f.read()

    has_proxy_timeout = "proxyTimeout: 300_000" in next_content or "proxyTimeout: 300000" in next_content
    output_details["next_config_proxy_timeout_300k"] = has_proxy_timeout

    if not has_proxy_timeout:
        return False, "next.config.ts does not configure proxyTimeout >= 300000", output_details

    # Check 3: scan/page.tsx has fallback getAnalysisStatus checks
    if not os.path.exists(scan_page):
        return False, f"scan/page.tsx not found at {scan_page}", output_details

    with open(scan_page, "r", encoding="utf-8") as f:
        scan_content = f.read()

    has_resilient_error_check = (
        'statusResp.data.status === "running"' in scan_content
        or 'curStatus === "running"' in scan_content
    )
    output_details["scan_page_resilient_status_check"] = has_resilient_error_check

    if not has_resilient_error_check:
        return False, "scan/page.tsx does not check active backend status before failing", output_details

    # Check 4: Gateway API ping & analysis/status check
    try:
        req = urllib.request.Request("http://127.0.0.1:6969/api/ping")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            output_details["gateway_ping"] = data
            if data.get("status") != "ok":
                return False, f"Unexpected ping status: {data}", output_details
    except Exception as exc:
        output_details["gateway_ping_error"] = str(exc)
        return False, f"Failed to ping gateway: {exc}", output_details

    try:
        req = urllib.request.Request("http://127.0.0.1:6969/api/analysis/status")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            output_details["analysis_status"] = data
            if data.get("status") != "ok":
                return False, f"Unexpected analysis/status response: {data}", output_details
    except Exception as exc:
        output_details["gateway_status_error"] = str(exc)
        return False, f"Failed to fetch analysis status: {exc}", output_details

    return True, "Safe JSON parse, proxy timeout, and submit resilience verified", output_details

if __name__ == "__main__":
    success, message, details = run_test()
    if success:
        print(f"[{TEST_NAME}] PASS")
        print(f"About: {message}")
        print("Output:")
        print(json.dumps(details, indent=2))
        sys.exit(0)
    else:
        print(f"[{TEST_NAME}] FAIL")
        print(f"About: {message}")
        print("Output:")
        print(json.dumps(details, indent=2))
        sys.exit(1)
