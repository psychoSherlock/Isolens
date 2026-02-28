#!/usr/bin/env python3
"""TEST_12 — Agent code integrity tests (no VM needed).

Verifies that the agent module:
  - Imports cleanly
  - Has real execution logic (no STUB)
  - Has correct tool search paths (C:\\IsoLens\\tools\\)
  - Registers all expected collectors including tcpvcon and handle
  - Has Sysmon clear logic in execute_sample
"""

import inspect
import os
import sys

TEST_NAME = "TEST_12_agent_integrity"
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


def test_import():
    """Agent module imports without errors."""
    try:
        from core.agent.isolens_agent import IsoLensAgent, AgentState
        report("Import agent", True, "IsoLensAgent, AgentState imported")
    except Exception as exc:
        report("Import agent", False, str(exc), "Import error")


def test_no_execution_stub():
    """execute_sample must NOT contain [STUB]."""
    from core.agent.isolens_agent import IsoLensAgent
    source = inspect.getsource(IsoLensAgent.execute_sample)
    has_stub = "[STUB]" in source
    ok = not has_stub
    snippet = source[:200] + "..." if len(source) > 200 else source
    report(
        "No execution STUB",
        ok,
        f"STUB found={has_stub}",
        "execute_sample still contains [STUB] placeholder",
    )


def test_real_execution_logic():
    """execute_sample uses cmd /c start or os.startfile for execution."""
    from core.agent.isolens_agent import IsoLensAgent
    source = inspect.getsource(IsoLensAgent.execute_sample)
    has_cmd_start = "cmd /c start" in source or 'cmd", "/c", "start' in source
    has_startfile = "startfile" in source
    ok = has_cmd_start or has_startfile
    report(
        "Real execution logic present",
        ok,
        f"cmd_start={has_cmd_start}, startfile={has_startfile}",
        "execute_sample has no real execution mechanism",
    )


def test_sysmon_clear_before_execution():
    """execute_sample clears Sysmon logs before running the sample."""
    from core.agent.isolens_agent import IsoLensAgent
    source = inspect.getsource(IsoLensAgent.execute_sample)
    has_clear = "wevtutil" in source and "cl" in source
    ok = has_clear
    report(
        "Sysmon clear before execution",
        ok,
        f"wevtutil_cl_found={has_clear}",
        "execute_sample should clear Sysmon logs before running sample",
    )


def test_procmon_paths_fixed():
    """ProcmonCollector searches C:\\IsoLens\\tools\\ first."""
    from core.agent.isolens_agent import ProcmonCollector
    paths = ProcmonCollector._SEARCH_PATHS
    has_isolens_path = any("IsoLens" in p for p in paths)
    first_is_isolens = "IsoLens" in paths[0] if paths else False
    ok = has_isolens_path and first_is_isolens
    report(
        "Procmon paths include C:\\IsoLens\\tools",
        ok,
        f"paths={paths}",
        "C:\\IsoLens\\tools should be first in search paths",
    )


def test_tcpvcon_collector_exists():
    """TcpvconCollector class exists and is registered."""
    try:
        from core.agent.isolens_agent import TcpvconCollector
        ok = TcpvconCollector.name == "tcpvcon"
        report(
            "TcpvconCollector exists",
            ok,
            f"name={TcpvconCollector.name}",
        )
    except ImportError:
        report("TcpvconCollector exists", False, "ImportError", "Class not found")


def test_handle_collector_exists():
    """HandleCollector class exists and is registered."""
    try:
        from core.agent.isolens_agent import HandleCollector
        ok = HandleCollector.name == "handle"
        report(
            "HandleCollector exists",
            ok,
            f"name={HandleCollector.name}",
        )
    except ImportError:
        report("HandleCollector exists", False, "ImportError", "Class not found")


def test_all_collectors_registered():
    """IsoLensAgent registers all 7 expected collectors."""
    import tempfile
    from core.agent.isolens_agent import IsoLensAgent
    tmp = tempfile.mkdtemp(prefix="isolens_test_agent_")
    try:
        agent = IsoLensAgent(share_path=tmp, workdir=tmp)
        names = [c.name for c in agent.collectors]
        expected = {"sysmon", "procmon", "network", "fakenet", "screenshots", "tcpvcon", "handle"}
        missing = expected - set(names)
        ok = len(missing) == 0
        report(
            "All 7 collectors registered",
            ok,
            f"registered={names}",
            f"Missing: {missing}" if missing else "",
        )
    except Exception as exc:
        report("All 7 collectors registered", False, str(exc))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def test_analysis_routes_import():
    """Analysis gateway routes import without errors."""
    try:
        from core.gateway.analysis_routes import router
        routes = [r.path for r in router.routes]
        ok = (
            any("/submit" in r for r in routes)
            and any("/status" in r for r in routes)
            and any("/check-vm" in r for r in routes)
        )
        report("Analysis routes import", ok, f"routes={routes}")
    except Exception as exc:
        report("Analysis routes import", False, str(exc), "Import error")


def test_app_includes_analysis_router():
    """FastAPI app includes the analysis router."""
    try:
        from core.gateway.app import app
        paths = [r.path for r in app.routes]
        has_submit = any("/api/analysis/submit" in p for p in paths)
        has_status = any("/api/analysis/status" in p for p in paths)
        has_check = any("/api/analysis/check-vm" in p for p in paths)
        ok = has_submit and has_status and has_check
        report(
            "App includes analysis router",
            ok,
            f"submit={has_submit}, status={has_status}, check={has_check}",
        )
    except Exception as exc:
        report("App includes analysis router", False, str(exc), "Import error")


if __name__ == "__main__":
    print(f"\n{'=' * 60}")
    print(f"  {TEST_NAME}")
    print(f"{'=' * 60}\n")

    test_import()
    test_no_execution_stub()
    test_real_execution_logic()
    test_sysmon_clear_before_execution()
    test_procmon_paths_fixed()
    test_tcpvcon_collector_exists()
    test_handle_collector_exists()
    test_all_collectors_registered()
    test_analysis_routes_import()
    test_app_includes_analysis_router()

    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"  Results: {passed}/{total} passed, {failed}/{total} failed")
    print(f"{'=' * 60}")
    sys.exit(0 if failed == 0 else 1)
