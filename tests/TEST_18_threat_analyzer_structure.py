#!/usr/bin/env python3
"""TEST_18 ??? Threat analyzer module structure & data loaders.

Validates:
  - ThreatAnalyzer class instantiation
  - All TOOL_LOADERS keys match agent names
  - Data loader functions work on the existing sample report
  - JSON parsing helpers handle valid and malformed input
  - ThreatAnalysisReport / ToolAnalysisResult serialization
  - _clean_json_response strips markdown fences
  - Normalization helpers produce correct shapes
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TEST_NAME = "TEST_18_threat_analyzer_structure"
ABOUT = "Threat analyzer module: data loaders, JSON parsing, report serialization"


def run_test() -> list[str]:
    from core.threatintelligence.threat_analyzer import (
        ThreatAnalyzer,
        ThreatAnalysisReport,
        ToolAnalysisResult,
        TOOL_LOADERS,
        _clean_json_response,
        _parse_tool_json,
        _parse_summary_json,
        _normalize_findings,
        _normalize_iocs,
        _normalize_mitre,
        _normalize_recommendations,
    )
    from core.threatintelligence.copilot_agents import get_tool_agents

    errors = []

    # 1. Loader keys match agent names
    agent_names = {a.name for a in get_tool_agents()}
    loader_keys = set(TOOL_LOADERS.keys())
    if agent_names != loader_keys:
        errors.append(f"TOOL_LOADERS keys {loader_keys} != agent names {agent_names}")

    # 2. ThreatAnalyzer instantiation
    try:
        analyzer = ThreatAnalyzer()
        if not os.path.isdir(analyzer.reports_dir):
            errors.append(f"Default reports dir doesn't exist: {analyzer.reports_dir}")
    except Exception as exc:
        errors.append(f"ThreatAnalyzer() raised: {exc}")

    # 3. Test data loaders against existing report (if available)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    reports_dir = os.path.join(project_root, "core", "storage", "reports")
    report_dirs = [d for d in os.listdir(reports_dir) if os.path.isdir(os.path.join(reports_dir, d))] if os.path.isdir(reports_dir) else []

    if report_dirs:
        sample_dir = os.path.join(reports_dir, report_dirs[0])
        for name, loader in TOOL_LOADERS.items():
            try:
                payload, has_data = loader(sample_dir)
                if not isinstance(payload, str):
                    errors.append(f"Loader {name} returned non-string payload: {type(payload)}")
                if not isinstance(has_data, bool):
                    errors.append(f"Loader {name} returned non-bool has_data: {type(has_data)}")
            except Exception as exc:
                errors.append(f"Loader {name} raised: {exc}")
    else:
        for name, loader in TOOL_LOADERS.items():
            try:
                payload, has_data = loader("/nonexistent/path")
                if has_data:
                    errors.append(f"Loader {name} claims data in nonexistent dir")
            except Exception as exc:
                errors.append(f"Loader {name} crashed on missing dir: {exc}")

    # 4. _clean_json_response
    cases = [
        ('{"key": "val"}', '{"key": "val"}'),
        ('```json\n{"key": "val"}\n```', '{"key": "val"}'),
        ('  \n{"key": "val"}  \n', '{"key": "val"}'),
        ('Here is the result: {"key": "val"} end.', '{"key": "val"}'),
    ]
    for raw, expected in cases:
        got = _clean_json_response(raw)
        if got != expected:
            errors.append(f"_clean_json_response({raw!r}) -> {got!r}, expected {expected!r}")

    # 5. _parse_tool_json -- valid JSON
    valid_json = json.dumps({
        "tool": "procmon",
        "verdict": "malicious",
        "confidence": 85,
        "findings": [
            {"severity": "high", "indicator": "temp file", "description": "writes to temp"}
        ],
        "iocs": [
            {"type": "file", "value": "C:\\Temp\\bad.exe"}
        ],
        "summary": "Found suspicious activity."
    })
    result = ToolAnalysisResult(tool="procmon", agent_name="procmon-analyzer")
    _parse_tool_json(valid_json, result)
    if result.verdict != "malicious":
        errors.append(f"verdict={result.verdict}, expected 'malicious'")
    if result.confidence != 85:
        errors.append(f"confidence={result.confidence}, expected 85")
    if result.findings_count != 1:
        errors.append(f"findings_count={result.findings_count}, expected 1")
    if result.iocs_count != 1:
        errors.append(f"iocs_count={result.iocs_count}, expected 1")

    # 6. _parse_tool_json -- malformed input (should not crash)
    bad_result = ToolAnalysisResult(tool="test", agent_name="test")
    _parse_tool_json("not json at all", bad_result)
    if bad_result.error is None:
        errors.append("_parse_tool_json should set error on malformed JSON")

    # 7. _parse_summary_json -- valid JSON
    valid_summary = json.dumps({
        "risk_score": 72,
        "threat_level": "high",
        "classification": {
            "malware_type": "trojan",
            "malware_family": "emotet",
            "platform": "dotnet",
            "confidence": 80
        },
        "executive_summary": "This is a trojan.",
        "key_findings": [
            {"source": "procmon", "severity": "high", "description": "bad stuff"}
        ],
        "iocs": [
            {"type": "file", "severity": "high", "value": "bad.exe"}
        ],
        "mitre_attack": [
            {"id": "T1059", "name": "Scripting", "tactic": "execution", "description": "Command-line"}
        ],
        "recommendations": [
            {"priority": "high", "action": "Quarantine"}
        ],
        "detailed_analysis": "Long analysis here."
    })
    report = ThreatAnalysisReport(analysis_id="test")
    _parse_summary_json(valid_summary, report)
    if report.risk_score != 72:
        errors.append(f"risk_score={report.risk_score}, expected 72")
    if report.threat_level != "high":
        errors.append(f"threat_level={report.threat_level}, expected 'high'")
    if report.malware_type != "trojan":
        errors.append(f"malware_type={report.malware_type}, expected 'trojan'")
    if report.malware_family != "emotet":
        errors.append(f"malware_family={report.malware_family}, expected 'emotet'")
    if report.platform != "dotnet":
        errors.append(f"platform={report.platform}, expected 'dotnet'")
    if report.classification_confidence != 80:
        errors.append(f"classification_confidence={report.classification_confidence}, expected 80")
    if "trojan" not in report.executive_summary.lower():
        errors.append(f"executive_summary missing 'trojan': {report.executive_summary}")

    # 8. Normalization helpers
    nf = _normalize_findings(["test finding"])
    if not nf or nf[0].get("description") != "test finding":
        errors.append(f"_normalize_findings string failed: {nf}")
    nf2 = _normalize_findings([{"severity": "high", "description": "x"}])
    if not nf2 or nf2[0].get("severity") != "high":
        errors.append(f"_normalize_findings dict failed: {nf2}")

    ni = _normalize_iocs(["bad.exe"])
    if not ni or ni[0].get("value") != "bad.exe":
        errors.append(f"_normalize_iocs string failed: {ni}")

    nm = _normalize_mitre([{"technique_id": "T1059", "name": "Scripting"}])
    if not nm or nm[0].get("id") != "T1059":
        errors.append(f"_normalize_mitre technique_id->id failed: {nm}")

    nr = _normalize_recommendations(["Do this"])
    if not nr or nr[0].get("action") != "Do this":
        errors.append(f"_normalize_recommendations string failed: {nr}")

    # 9. Serialization round-trip
    report_dict = report.to_dict()
    if not isinstance(report_dict, dict):
        errors.append("to_dict() did not return dict")
    if report_dict.get("risk_score") != 72:
        errors.append("to_dict() risk_score mismatch")
    classification = report_dict.get("classification", {})
    if classification.get("malware_type") != "trojan":
        errors.append("to_dict() classification.malware_type mismatch")

    result_dict = result.to_dict()
    if result_dict.get("verdict") != "malicious":
        errors.append("ToolAnalysisResult.to_dict() verdict mismatch")

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
        print(f"Reason: Exception -- {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
