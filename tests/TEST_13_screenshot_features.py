#!/usr/bin/env python3
"""TEST_13 — Screenshot and GUI features tests (no VM needed).

Verifies:
  - Agent ScreenshotCollector has start_capture / stop_capture lifecycle
  - Agent execute_sample accepts screenshot_interval parameter
  - Orchestrator has VBoxManage screenshot support
  - Malware emulator source has PhaseGUIActivity
  - Agent version bumped to 1.3.0
"""

import inspect
import os
import sys

TEST_NAME = "TEST_13_screenshot_features"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, PROJECT_ROOT)

passed = 0
failed = 0


def report(name, ok, output, reason=""):
    global passed, failed
    tag = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
    print(f"[{TEST_NAME}:{name}] {tag}")
    print(f"  About: {name}")
    if not ok and reason:
        print(f"  Reason: {reason}")
    print(f"  Output: {output}\n")


def test_agent_version():
    """Agent version should be 1.3.0."""
    from core.agent.isolens_agent import AGENT_VERSION
    ok = AGENT_VERSION == "1.3.0"
    report("Agent version 1.3.0", ok, f"AGENT_VERSION={AGENT_VERSION}",
           f"Expected 1.3.0, got {AGENT_VERSION}")


def test_screenshot_collector_lifecycle():
    """ScreenshotCollector must have start_capture and stop_capture methods."""
    from core.agent.isolens_agent import ScreenshotCollector
    has_start = hasattr(ScreenshotCollector, "start_capture")
    has_stop = hasattr(ScreenshotCollector, "stop_capture")
    ok = has_start and has_stop
    report(
        "ScreenshotCollector lifecycle",
        ok,
        f"start_capture={has_start}, stop_capture={has_stop}",
        "Missing start_capture or stop_capture method",
    )


def test_screenshot_collector_start_signature():
    """start_capture should accept an interval parameter."""
    from core.agent.isolens_agent import ScreenshotCollector
    sig = inspect.signature(ScreenshotCollector.start_capture)
    params = list(sig.parameters.keys())
    has_interval = "interval" in params
    ok = has_interval
    report(
        "start_capture accepts interval",
        ok,
        f"params={params}",
        "Missing 'interval' parameter",
    )


def test_execute_sample_screenshot_interval():
    """execute_sample should accept screenshot_interval parameter."""
    from core.agent.isolens_agent import IsoLensAgent
    sig = inspect.signature(IsoLensAgent.execute_sample)
    params = list(sig.parameters.keys())
    ok = "screenshot_interval" in params
    report(
        "execute_sample has screenshot_interval",
        ok,
        f"params={params}",
        "Missing 'screenshot_interval' parameter in execute_sample",
    )


def test_schtasks_launch():
    """execute_sample should use schtasks for interactive session launch."""
    from core.agent.isolens_agent import IsoLensAgent
    source = inspect.getsource(IsoLensAgent.execute_sample)
    has_schtasks = "schtasks" in source
    has_interactive = "/it" in source
    ok = has_schtasks and has_interactive
    report(
        "schtasks /it sample launch",
        ok,
        f"schtasks={has_schtasks}, /it={has_interactive}",
        "execute_sample should use schtasks /it for interactive session launch",
    )


def test_orchestrator_vboxmanage_screenshots():
    """Orchestrator should have VBoxManage screenshot methods."""
    from core.controller.sandbox_orchestrator import SandboxOrchestrator
    has_loop = hasattr(SandboxOrchestrator, "_screenshot_loop")
    has_take = hasattr(SandboxOrchestrator, "_take_screenshot")
    ok = has_loop and has_take
    report(
        "Orchestrator VBoxManage screenshots",
        ok,
        f"_screenshot_loop={has_loop}, _take_screenshot={has_take}",
        "Missing screenshot methods in orchestrator",
    )


def test_orchestrator_screenshot_interval():
    """Orchestrator run_analysis should accept screenshot_interval."""
    from core.controller.sandbox_orchestrator import SandboxOrchestrator
    sig = inspect.signature(SandboxOrchestrator.run_analysis)
    params = list(sig.parameters.keys())
    ok = "screenshot_interval" in params
    report(
        "Orchestrator screenshot_interval param",
        ok,
        f"params={params}",
        "Missing 'screenshot_interval' in run_analysis",
    )


def test_agent_config_vm_name():
    """AgentConfig should have vm_name field."""
    from core.controller.sandbox_orchestrator import AgentConfig
    cfg = AgentConfig()
    ok = hasattr(cfg, "vm_name") and cfg.vm_name == "WindowsSandbox"
    report(
        "AgentConfig has vm_name",
        ok,
        f"vm_name={getattr(cfg, 'vm_name', 'MISSING')}",
        "AgentConfig missing vm_name or wrong default",
    )


def test_malware_emulator_gui_phase():
    """malware_emulator.cs should have PhaseGUIActivity."""
    emulator_path = os.path.join(PROJECT_ROOT, "SandboxShare", "malware_emulator.cs")
    if not os.path.isfile(emulator_path):
        report("Emulator GUI phase", False, "File not found", emulator_path)
        return
    with open(emulator_path, "r") as f:
        source = f.read()
    has_phase = "PhaseGUIActivity" in source
    has_ransom = "README_DECRYPT" in source
    has_notepad = "notepad.exe" in source
    has_ps = "c2_beacon.ps1" in source
    ok = has_phase and has_ransom and has_notepad and has_ps
    report(
        "Emulator GUI phase",
        ok,
        f"PhaseGUIActivity={has_phase}, ransom={has_ransom}, "
        f"notepad={has_notepad}, ps_beacon={has_ps}",
        "Missing GUI activity elements in malware_emulator.cs",
    )


def test_gateway_screenshot_interval():
    """Gateway submit_analysis should accept screenshot_interval."""
    from core.gateway.analysis_routes import submit_analysis
    sig = inspect.signature(submit_analysis)
    params = list(sig.parameters.keys())
    ok = "screenshot_interval" in params
    report(
        "Gateway screenshot_interval param",
        ok,
        f"params={params}",
        "Missing 'screenshot_interval' in submit_analysis endpoint",
    )


if __name__ == "__main__":
    print(f"{'='*60}")
    print(f"  {TEST_NAME}")
    print(f"  Screenshot and GUI features verification")
    print(f"{'='*60}\n")

    test_agent_version()
    test_screenshot_collector_lifecycle()
    test_screenshot_collector_start_signature()
    test_execute_sample_screenshot_interval()
    test_schtasks_launch()
    test_orchestrator_vboxmanage_screenshots()
    test_orchestrator_screenshot_interval()
    test_agent_config_vm_name()
    test_malware_emulator_gui_phase()
    test_gateway_screenshot_interval()

    total = passed + failed
    print(f"{'='*60}")
    print(f"  Results: {passed}/{total} passed, {failed}/{total} failed")
    print(f"{'='*60}")

    if failed > 0:
        print(f"\n[{TEST_NAME}] FAIL")
    else:
        print(f"\n[{TEST_NAME}] PASS")
    
    sys.exit(1 if failed else 0)
