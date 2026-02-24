"""TEST_07_agent_core — IsoLens Guest Agent unit tests.

Tests the platform-agnostic parts of the agent:
  - AgentState transitions
  - IsoLensAgent artifact listing and packaging
  - HTTP API routing via a real localhost server
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import time

# Ensure project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TEST_NAME = "TEST_07_agent_core"
ABOUT = "Guest agent state, artifact packaging, and HTTP API"

# We need to import after path setup
from core.agent.isolens_agent import (  # noqa: E402
    AGENT_VERSION,
    AgentState,
    IsoLensAgent,
    create_server,
)


def _fail(reason, output=""):
    print("[{}] FAIL".format(TEST_NAME))
    print("About: {}".format(ABOUT))
    print("Reason: {}".format(reason))
    print("Output:")
    print(output or "(none)")
    return 1


def _http_get(port, path):
    """Minimal HTTP GET using only stdlib."""
    import http.client
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = resp.read().decode()
    conn.close()
    return resp.status, json.loads(body)


def _http_post(port, path, payload=None):
    """Minimal HTTP POST using only stdlib."""
    import http.client
    body = json.dumps(payload or {}).encode()
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request(
        "POST", path, body=body,
        headers={"Content-Type": "application/json"},
    )
    resp = conn.getresponse()
    rbody = resp.read().decode()
    conn.close()
    return resp.status, json.loads(rbody)


def main() -> int:
    tmpdir = tempfile.mkdtemp(prefix="isolens_agent_test_")
    share_dir = os.path.join(tmpdir, "share")
    work_dir = os.path.join(tmpdir, "work")
    os.makedirs(share_dir)
    os.makedirs(work_dir)

    results = {}

    try:
        # ── 1. AgentState transitions ────────────────────────────────
        state = AgentState()
        checks = []

        checks.append(("initial_idle", state.status == AgentState.IDLE))

        state.set_executing("test.exe")
        d = state.to_dict()
        checks.append(("executing_status", d["status"] == AgentState.EXECUTING))
        checks.append(("executing_sample", d["current_sample"] == "test.exe"))

        state.set_collecting()
        checks.append(("collecting", state.status == AgentState.COLLECTING))

        state.set_error("boom")
        d = state.to_dict()
        checks.append(("error_status", d["status"] == AgentState.ERROR))
        checks.append(("error_message", d["last_error"] == "boom"))

        state.set_idle()
        d = state.to_dict()
        checks.append(("back_to_idle", d["status"] == AgentState.IDLE))
        checks.append(("count_incremented", d["execution_count"] == 1))
        checks.append(("sample_cleared", d["current_sample"] is None))

        for label, ok in checks:
            if not ok:
                return _fail("AgentState check failed: " + label,
                             json.dumps(state.to_dict(), indent=2))

        results["state_checks"] = len(checks)

        # ── 2. IsoLensAgent artifact listing ────────────────────────
        agent = IsoLensAgent(share_path=share_dir, workdir=work_dir)

        # Initially empty
        arts = agent.list_artifacts()
        if arts:
            return _fail("Expected no artifacts initially",
                         json.dumps(arts))

        # Create a fake artifact
        sysmon_dir = os.path.join(work_dir, "artifacts", "sysmon")
        os.makedirs(sysmon_dir, exist_ok=True)
        with open(os.path.join(sysmon_dir, "events.xml"), "w") as f:
            f.write("<Events/>")

        arts = agent.list_artifacts()
        if len(arts) != 1:
            return _fail(
                "Expected 1 artifact, got {}".format(len(arts)),
                json.dumps(arts),
            )

        results["artifact_listing"] = "ok"

        # ── 3. Package results ─────────────────────────────────────
        # Put a sample in the share
        sample_name = "testfile.exe"
        with open(os.path.join(share_dir, sample_name), "wb") as f:
            f.write(b"MZ_fake_pe")

        exec_result = agent.execute_sample(sample_name, timeout=1)
        if exec_result.get("status") != "complete":
            return _fail(
                "execute_sample did not return 'complete'",
                json.dumps(exec_result, indent=2, default=str),
            )

        pkg = exec_result.get("package")
        if not pkg:
            return _fail("No package produced", json.dumps(exec_result, indent=2, default=str))

        # The zip should exist in the shared folder
        zip_in_share = os.path.join(share_dir, pkg)
        if not os.path.isfile(zip_in_share):
            return _fail(
                "Package zip not found in share: " + pkg,
                "share contents: " + str(os.listdir(share_dir)),
            )

        results["packaging"] = "ok"
        results["package_name"] = pkg

        # ── 4. Cleanup ─────────────────────────────────────────────
        agent.cleanup()
        arts = agent.list_artifacts()
        if arts:
            return _fail("Artifacts not cleaned up",
                         json.dumps(arts))
        results["cleanup"] = "ok"

        # ── 5. HTTP API ────────────────────────────────────────────
        # Find a free port (may be restricted in sandboxed environments)
        import socket
        try:
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
            sock.close()
        except PermissionError:
            results["http_api"] = "skipped_permission_error"
            print("[{}] PASS".format(TEST_NAME))
            print("About: {}".format(ABOUT))
            print("Output:")
            print(json.dumps(results, indent=2))
            return 0

        server = create_server(agent, host="127.0.0.1", port=port)
        srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
        srv_thread.start()
        time.sleep(0.3)  # Let server bind

        # GET /api/status
        code, body = _http_get(port, "/api/status")
        if code != 200 or body.get("status") != "ok":
            return _fail("GET /api/status failed",
                         json.dumps({"code": code, "body": body}, indent=2))

        data = body["data"]
        if data.get("agent_version") != AGENT_VERSION:
            return _fail(
                "Version mismatch: {} vs {}".format(
                    data.get("agent_version"), AGENT_VERSION),
                json.dumps(data, indent=2),
            )

        results["http_status"] = "ok"

        # GET /api/collectors
        code, body = _http_get(port, "/api/collectors")
        if code != 200 or "collectors" not in body.get("data", {}):
            return _fail("GET /api/collectors failed",
                         json.dumps(body, indent=2))
        results["http_collectors"] = "ok"

        # GET /api/artifacts
        code, body = _http_get(port, "/api/artifacts")
        if code != 200:
            return _fail("GET /api/artifacts failed",
                         json.dumps(body, indent=2))
        results["http_artifacts"] = "ok"

        # POST /api/cleanup
        code, body = _http_post(port, "/api/cleanup")
        if code != 200:
            return _fail("POST /api/cleanup failed",
                         json.dumps(body, indent=2))
        results["http_cleanup"] = "ok"

        # POST /api/execute (with sample in share)
        with open(os.path.join(share_dir, "hello.exe"), "wb") as f:
            f.write(b"MZ_test")

        code, body = _http_post(port, "/api/execute",
                                {"filename": "hello.exe", "timeout": 1})
        if code != 200:
            return _fail("POST /api/execute failed",
                         json.dumps(body, indent=2))
        results["http_execute"] = "ok"

        # Wait for background execution to complete
        time.sleep(5)

        # POST /api/execute without filename → 400
        code, body = _http_post(port, "/api/execute", {})
        if code != 400:
            return _fail(
                "Expected 400 for missing filename, got {}".format(code),
                json.dumps(body, indent=2),
            )
        results["http_execute_validation"] = "ok"

        # GET unknown route → 404
        code, body = _http_get(port, "/api/nope")
        if code != 404:
            return _fail("Expected 404 for unknown route",
                         json.dumps(body, indent=2))
        results["http_404"] = "ok"

        # POST /api/shutdown
        code, body = _http_post(port, "/api/shutdown")
        if code != 200:
            return _fail("POST /api/shutdown failed",
                         json.dumps(body, indent=2))
        results["http_shutdown"] = "ok"

        time.sleep(0.5)
        server.shutdown()

        # ── All passed ─────────────────────────────────────────────
        print("[{}] PASS".format(TEST_NAME))
        print("About: {}".format(ABOUT))
        print("Output:")
        print(json.dumps(results, indent=2))
        return 0

    except Exception as exc:
        import traceback
        print("[{}] FAIL".format(TEST_NAME))
        print("About: {}".format(ABOUT))
        print("Reason: {}".format(exc))
        print("Output:")
        traceback.print_exc()
        return 1
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
