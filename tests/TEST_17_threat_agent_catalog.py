#!/usr/bin/env python3
"""TEST_17 — Threat-intel agent catalog integrity.

Validates:
  - All expected per-tool agents exist with correct names
  - Threat-summarizer agent exists
  - All agents produce valid custom_agent_config dicts
  - XML schema references are present in each agent prompt
  - gpt-5-mini model constant is set correctly
  - get_agent_by_name / get_tool_agents helpers work
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TEST_NAME = "TEST_17_threat_agent_catalog"
ABOUT = "Threat intelligence agent catalog integrity and JSON prompt contracts"

EXPECTED_TOOL_AGENTS = {
    "sysmon-analyzer",
    "procmon-analyzer",
    "network-analyzer",
    "handle-analyzer",
    "tcpvcon-analyzer",
    "metadata-analyzer",
}

EXPECTED_ALL_AGENTS = EXPECTED_TOOL_AGENTS | {"threat-summarizer"}


def run_test() -> bool:
    from core.threatintelligence.copilot_agents import (
        DEFAULT_THREATINTEL_AGENTS,
        TOOL_AGENTS,
        list_default_agents,
        get_tool_agents,
        get_agent_by_name,
    )
    from core.threatintelligence.copilot_service import REQUIRED_MODEL

    errors = []

    # 1. Check model constant
    if REQUIRED_MODEL != "gpt-5-mini":
        errors.append(f"REQUIRED_MODEL is '{REQUIRED_MODEL}', expected 'gpt-5-mini'")

    # 2. Check all expected agents exist
    all_names = {a.name for a in DEFAULT_THREATINTEL_AGENTS}
    missing = EXPECTED_ALL_AGENTS - all_names
    if missing:
        errors.append(f"Missing agents: {missing}")
    extra = all_names - EXPECTED_ALL_AGENTS
    if extra:
        errors.append(f"Unexpected agents: {extra}")

    # 3. Check tool agents subset
    tool_names = {a.name for a in TOOL_AGENTS}
    if tool_names != EXPECTED_TOOL_AGENTS:
        errors.append(f"TOOL_AGENTS mismatch: {tool_names} vs {EXPECTED_TOOL_AGENTS}")

    # 4. Helpers
    if len(list_default_agents()) != len(DEFAULT_THREATINTEL_AGENTS):
        errors.append("list_default_agents() length mismatch")
    if len(get_tool_agents()) != len(TOOL_AGENTS):
        errors.append("get_tool_agents() length mismatch")
    if get_agent_by_name("procmon-analyzer") is None:
        errors.append("get_agent_by_name('procmon-analyzer') returned None")
    if get_agent_by_name("nonexistent") is not None:
        errors.append("get_agent_by_name('nonexistent') should return None")

    # 5. Validate each agent's custom_agent_config
    for agent in DEFAULT_THREATINTEL_AGENTS:
        cfg = agent.to_custom_agent_config()
        for key in ("name", "display_name", "description", "prompt", "infer"):
            if key not in cfg:
                errors.append(f"Agent '{agent.name}' config missing key '{key}'")

    # 6. All tool agents must mention JSON schema keywords
    for agent in TOOL_AGENTS:
        if '"verdict"' not in agent.prompt and '"tool"' not in agent.prompt:
            errors.append(f"Agent '{agent.name}' prompt missing JSON schema keywords")
        if "CRITICAL RULES" not in agent.prompt:
            errors.append(f"Agent '{agent.name}' prompt missing CRITICAL RULES")

    # 7. Summarizer must mention threat_report schema
    summarizer = get_agent_by_name("threat-summarizer")
    if summarizer:
        if '"risk_score"' not in summarizer.prompt:
            errors.append("Summarizer prompt missing risk_score JSON key")
        if "risk_score" not in summarizer.prompt:
            errors.append("Summarizer prompt missing risk_score")

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
