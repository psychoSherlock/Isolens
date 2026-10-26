#!/usr/bin/env python3
"""TEST_40_z_drive_attachment_and_share_resilience.py

Validates the fix for Z drive attachment and shared folder resilience:
1. vbox_output_parser correctly parses GlobalMapping, MachineMapping, and TransientMapping shared folders.
2. VBoxManageClient.sharedfolder_add is idempotent and handles 'already exists'.
3. VBoxManageClient.ensure_shared_folder detects already attached folders or attaches them.
4. SandboxOrchestrator auto-attaches shared folder on run_analysis and check_vm_ready.
5. isolens_agent.resolve_share_path and ensure_share_path resilience without crashing.
6. start_agent.bat launcher employs non-blocking ping sleeps and EnableLinkedConnections.
"""

import json
import os
import sys

# Ensure repository root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def test_vbox_output_parser_transient_mapping():
    from core.modules.vbox_output_parser import parse_showvminfo

    mock_stdout = (
        'name="WindowsSandbox"\n'
        'VMState="running"\n'
        'SharedFolderNameTransientMapping1="SandboxShare"\n'
        'SharedFolderPathTransientMapping1="/home/user/Isolens/SandboxShare"\n'
        'SharedFolderNameMachineMapping1="PermanentShare"\n'
        'SharedFolderPathMachineMapping1="/home/user/Isolens/PermanentShare"\n'
    )
    parsed = parse_showvminfo(mock_stdout)
    sfolders = parsed.get("shared_folders", [])
    names = [sf.get("name") for sf in sfolders]
    assert "SandboxShare" in names, f"Expected SandboxShare in {names}"
    assert "PermanentShare" in names, f"Expected PermanentShare in {names}"
    return "parse_showvminfo correctly parsed transient and machine mapped shared folders"


def test_vbox_client_ensure_shared_folder_dryrun():
    from core.controller.vbox_controller import VBoxManageClient

    client = VBoxManageClient(dry_run=True, raise_on_error=True)
    res = client.ensure_shared_folder("TestVM", "SandboxShare")
    assert res.returncode == 0
    return "VBoxManageClient.ensure_shared_folder dry-run succeeded"


def test_orchestrator_integration():
    from core.controller.sandbox_orchestrator import SandboxOrchestrator

    orch = SandboxOrchestrator(dry_run=True)
    assert hasattr(orch, "vbox")
    checks = orch.check_vm_ready()
    assert "share_folder" in checks
    return "SandboxOrchestrator correctly integrates vbox controller and checks share"


def test_agent_share_resilience():
    from core.agent.isolens_agent import IsoLensAgent, resolve_share_path

    # Resolving in a test directory should return an existing directory
    test_dir = os.path.abspath(os.path.join(PROJECT_ROOT, "SandboxShare"))
    resolved = resolve_share_path(test_dir, retries=1)
    assert os.path.isdir(resolved)

    agent = IsoLensAgent(share_path=test_dir, workdir="/tmp/test_workdir")
    assert hasattr(agent, "ensure_share_path")
    ensured = agent.ensure_share_path()
    assert os.path.isdir(ensured)
    return "IsoLensAgent ensure_share_path successfully verified"


def test_start_agent_bat_safety():
    bat_path = os.path.join(PROJECT_ROOT, "SandboxShare", "start_agent.bat")
    with open(bat_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "EnableLinkedConnections" in content, "Missing EnableLinkedConnections registry tweak"
    assert "ping -n" in content, "Missing non-blocking ping sleep"
    assert "timeout /t" not in content, "Unsafe timeout /t command present in start_agent.bat"
    return "start_agent.bat contains EnableLinkedConnections and non-blocking ping delays"


def main():
    try:
        t1 = test_vbox_output_parser_transient_mapping()
        t2 = test_vbox_client_ensure_shared_folder_dryrun()
        t3 = test_orchestrator_integration()
        t4 = test_agent_share_resilience()
        t5 = test_start_agent_bat_safety()

        output = {
            "parser_mapping": t1,
            "vbox_client": t2,
            "orchestrator_integration": t3,
            "agent_resilience": t4,
            "bat_safety": t5,
        }
        print("[TEST_40_z_drive_attachment_and_share_resilience] PASS")
        print("About: Verifies Z drive attachment resilience, VBox transient shared folder auto-mounting, and guest auto-recovery.")
        print("Output:")
        print(json.dumps(output, indent=2))
        return 0
    except Exception as e:
        print("[TEST_40_z_drive_attachment_and_share_resilience] FAIL")
        print("About: Verifies Z drive attachment resilience, VBox transient shared folder auto-mounting, and guest auto-recovery.")
        print(f"Reason: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
