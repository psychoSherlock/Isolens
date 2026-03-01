#!/usr/bin/env python3
"""Validation test for standalone threat intelligence Copilot SDK setup."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_NAME = "TEST_16_threatintel_copilot_setup"
ABOUT = "Threatintelligence Copilot setup provides local agent listing and agent prompt routing"


def _fail(reason: str, output: str) -> int:
    print(f"[{TEST_NAME}] FAIL")
    print(f"About: {ABOUT}")
    print(f"Reason: {reason}")
    print("Output:")
    print(output)
    return 1


def main() -> int:
    raw_output: dict[str, object] = {}

    try:
        from core.threatintelligence.copilot_agents import list_default_agents
        from core.threatintelligence.copilot_service import build_agent_switch_prompt

        agents = list_default_agents()
        names = [agent.name for agent in agents]
        raw_output["agent_names"] = names

        if len(agents) < 1:
            return _fail("No default agents found", json.dumps(raw_output, indent=2))

        if len(names) != len(set(names)):
            return _fail("Agent names must be unique", json.dumps(raw_output, indent=2))

        rendered_prompt = build_agent_switch_prompt(names[0], "hello")
        raw_output["rendered_prompt"] = rendered_prompt
        if not rendered_prompt.startswith(f"/agent {names[0]}\n"):
            return _fail("Agent switch prompt format is invalid", json.dumps(raw_output, indent=2))

        cli_cmd = [
            sys.executable,
            str(ROOT / "core" / "threatintelligence" / "copilot_cli.py"),
            "list-agents",
        ]
        proc = subprocess.run(cli_cmd, capture_output=True, text=True, check=False)
        raw_output["cli_returncode"] = proc.returncode
        raw_output["cli_stdout"] = proc.stdout
        raw_output["cli_stderr"] = proc.stderr

        if proc.returncode != 0:
            return _fail("CLI list-agents command failed", json.dumps(raw_output, indent=2))

        listed = json.loads(proc.stdout)
        raw_output["cli_agents_count"] = len(listed)
        if not isinstance(listed, list) or not listed:
            return _fail("CLI list-agents returned empty/non-list payload", json.dumps(raw_output, indent=2))

        print(f"[{TEST_NAME}] PASS")
        print(f"About: {ABOUT}")
        print("Output:")
        print(json.dumps(raw_output, indent=2))
        return 0

    except Exception as exc:  # pylint: disable=broad-except
        raw_output["exception"] = repr(exc)
        return _fail("Unhandled exception", json.dumps(raw_output, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
