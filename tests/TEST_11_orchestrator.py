#!/usr/bin/env python3
"""TEST_11 — SandboxOrchestrator unit tests (dry-run, no VM needed).

Tests the orchestrator logic: initialisation, directory creation,
dry-run HTTP helpers, and result dataclass serialisation.
"""

import json
import os
import shutil
import sys
import tempfile

TEST_NAME = "TEST_11_orchestrator"
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


def test_imports():
    """Ensure the orchestrator module can be imported."""
    try:
        from core.controller.sandbox_orchestrator import (
            AgentConfig,
            AnalysisResult,
            SandboxOrchestrator,
        )
        report("Import orchestrator", True, "AgentConfig, AnalysisResult, SandboxOrchestrator imported")
    except Exception as exc:
        report("Import orchestrator", False, str(exc), "Import error")


def test_agent_config_base_url():
    """AgentConfig builds a correct base URL."""
    from core.controller.sandbox_orchestrator import AgentConfig
    cfg = AgentConfig(host="10.0.0.1", port=8080)
    url = cfg.base_url
    ok = url == "http://10.0.0.1:8080"
    report("AgentConfig.base_url", ok, url, f"Expected http://10.0.0.1:8080, got {url}")


def test_analysis_result_to_dict():
    """AnalysisResult.to_dict() returns all expected fields."""
    from core.controller.sandbox_orchestrator import AnalysisResult
    result = AnalysisResult(
        analysis_id="20260228_120000_abc12345",
        sample_name="test.exe",
        status="complete",
        timeout=60,
        sysmon_events=42,
        files_collected=["sysmon_events.xml", "metadata.json"],
        agent_package="results_test_20260228_120000.zip",
    )
    d = result.to_dict()
    required_keys = {
        "analysis_id", "sample_name", "status", "started_at",
        "completed_at", "timeout", "error", "report_dir",
        "sysmon_events", "files_collected", "agent_package",
    }
    missing = required_keys - set(d.keys())
    ok = len(missing) == 0 and d["sysmon_events"] == 42
    report(
        "AnalysisResult.to_dict()",
        ok,
        json.dumps(d, indent=2, default=str),
        f"Missing keys: {missing}" if missing else "",
    )


def test_orchestrator_init_creates_dirs():
    """SandboxOrchestrator.__init__ creates required directories."""
    from core.controller.sandbox_orchestrator import (
        AgentConfig,
        SandboxOrchestrator,
    )
    tmp = tempfile.mkdtemp(prefix="isolens_test_orch_")
    try:
        orch = SandboxOrchestrator(
            agent_config=AgentConfig(),
            share_dir=os.path.join(tmp, "share"),
            samples_dir=os.path.join(tmp, "samples"),
            reports_dir=os.path.join(tmp, "reports"),
            dry_run=True,
        )
        dirs_exist = all(
            os.path.isdir(d)
            for d in [orch.share_dir, orch.samples_dir, orch.reports_dir]
        )
        ok = dirs_exist and orch.current_analysis is None
        report(
            "Orchestrator init creates dirs",
            ok,
            f"share={os.path.isdir(orch.share_dir)} "
            f"samples={os.path.isdir(orch.samples_dir)} "
            f"reports={os.path.isdir(orch.reports_dir)}",
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_dry_run_get():
    """Dry-run GET returns stub response."""
    from core.controller.sandbox_orchestrator import (
        AgentConfig,
        SandboxOrchestrator,
    )
    tmp = tempfile.mkdtemp(prefix="isolens_test_orch_")
    try:
        orch = SandboxOrchestrator(
            agent_config=AgentConfig(),
            share_dir=os.path.join(tmp, "share"),
            samples_dir=os.path.join(tmp, "samples"),
            reports_dir=os.path.join(tmp, "reports"),
            dry_run=True,
        )
        resp = orch._agent_get("/api/status")
        ok = resp.get("status") == "ok"
        report("Dry-run GET", ok, json.dumps(resp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_dry_run_post():
    """Dry-run POST returns stub response."""
    from core.controller.sandbox_orchestrator import (
        AgentConfig,
        SandboxOrchestrator,
    )
    tmp = tempfile.mkdtemp(prefix="isolens_test_orch_")
    try:
        orch = SandboxOrchestrator(
            agent_config=AgentConfig(),
            share_dir=os.path.join(tmp, "share"),
            samples_dir=os.path.join(tmp, "samples"),
            reports_dir=os.path.join(tmp, "reports"),
            dry_run=True,
        )
        resp = orch._agent_post("/api/execute", {"filename": "test.exe", "timeout": 30})
        ok = resp.get("status") == "ok"
        report("Dry-run POST", ok, json.dumps(resp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_no_ssh_references():
    """Orchestrator must NOT contain SSH/SCP logic."""
    import inspect
    from core.controller import sandbox_orchestrator as mod
    source = inspect.getsource(mod)
    has_ssh = "subprocess.run" in source and "ssh" in source.lower()
    has_scp = "scp" in source.lower()
    ok = not has_ssh and not has_scp
    report(
        "No SSH/SCP in orchestrator",
        ok,
        f"ssh_mentioned={has_ssh}, scp_mentioned={has_scp}",
        "Orchestrator should use HTTP + shared folder, not SSH",
    )


if __name__ == "__main__":
    print(f"\n{'=' * 60}")
    print(f"  {TEST_NAME}")
    print(f"{'=' * 60}\n")

    test_imports()
    test_agent_config_base_url()
    test_analysis_result_to_dict()
    test_orchestrator_init_creates_dirs()
    test_dry_run_get()
    test_dry_run_post()
    test_no_ssh_references()

    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"  Results: {passed}/{total} passed, {failed}/{total} failed")
    print(f"{'=' * 60}")
    sys.exit(0 if failed == 0 else 1)
