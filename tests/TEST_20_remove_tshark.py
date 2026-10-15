"""TEST_20_remove_tshark — Verify removal of tshark and packet capture.

Validates that:
  1. NetworkCollector and tshark are removed from core/agent/isolens_agent.py.
  2. NetworkCollector and tshark are removed from SandboxShare/isolens_agent.py.
  3. IsoLensAgent collector list does not register network/tshark collector.
  4. scripts/setup_vm_tools.ps1 does not install Wireshark or tshark.
  5. check_vm_status.ps1 does not contain tshark checks.
"""

import json
import os
import sys

TEST_NAME = "TEST_20_remove_tshark"
ABOUT = "Verification of complete removal of tshark from VM scripts and agent workflow"


def report(name, passed, output="", reason=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{TEST_NAME}:{name}] {status}")
    print(f"  About: {name}")
    if output:
        print(f"  Output: {output}")
    if reason and not passed:
        print(f"  Reason: {reason}")
    print()
    return passed


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    results = []

    # Check 1: core/agent/isolens_agent.py has no tshark or NetworkCollector
    agent_path = os.path.join(root, "core", "agent", "isolens_agent.py")
    with open(agent_path, "r", encoding="utf-8") as f:
        agent_content = f.read()

    has_tshark = "tshark" in agent_content.lower()
    has_net_collector = "class NetworkCollector" in agent_content
    results.append(
        report(
            "core agent has no tshark or NetworkCollector",
            not has_tshark and not has_net_collector,
            f"has_tshark={has_tshark}, has_net_collector={has_net_collector}",
            "tshark or NetworkCollector still present in core/agent/isolens_agent.py",
        )
    )

    # Check 2: SandboxShare/isolens_agent.py has no tshark or NetworkCollector
    share_agent_path = os.path.join(root, "SandboxShare", "isolens_agent.py")
    with open(share_agent_path, "r", encoding="utf-8") as f:
        share_agent_content = f.read()

    has_tshark_share = "tshark" in share_agent_content.lower()
    has_net_collector_share = "class NetworkCollector" in share_agent_content
    results.append(
        report(
            "SandboxShare agent has no tshark or NetworkCollector",
            not has_tshark_share and not has_net_collector_share,
            f"has_tshark={has_tshark_share}, has_net_collector={has_net_collector_share}",
            "tshark or NetworkCollector still present in SandboxShare/isolens_agent.py",
        )
    )

    # Check 3: IsoLensAgent collectors list does not include network
    from core.agent.isolens_agent import IsoLensAgent
    agent = IsoLensAgent(share_path="/tmp", workdir="/tmp")
    collector_names = [c.name for c in agent.collectors]
    has_network = "network" in collector_names
    results.append(
        report(
            "IsoLensAgent collectors exclude network",
            not has_network,
            f"collectors={collector_names}",
            "network collector still registered in agent",
        )
    )

    # Check 4: setup_vm_tools.ps1 does not install Wireshark or tshark
    setup_tools_path = os.path.join(root, "scripts", "setup_vm_tools.ps1")
    with open(setup_tools_path, "r", encoding="utf-8") as f:
        setup_tools_content = f.read()
    has_setup_tshark = "tshark" in setup_tools_content.lower() or "wireshark" in setup_tools_content.lower()
    results.append(
        report(
            "setup_vm_tools.ps1 excludes Wireshark and tshark",
            not has_setup_tshark,
            f"has_tshark_in_setup={has_setup_tshark}",
            "tshark or wireshark still found in setup_vm_tools.ps1",
        )
    )

    # Check 5: check_vm_status.ps1 has no tshark checks
    check_status_path = os.path.join(root, "SandboxShare", "check_vm_status.ps1")
    with open(check_status_path, "r", encoding="utf-8") as f:
        check_status_content = f.read()
    has_check_tshark = "tshark" in check_status_content.lower()
    results.append(
        report(
            "check_vm_status.ps1 excludes tshark",
            not has_check_tshark,
            f"has_tshark_in_check={has_check_tshark}",
            "tshark still checked in check_vm_status.ps1",
        )
    )

    all_passed = all(results)
    print("=" * 60)
    print(f"  Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    if all_passed:
        print(f"[{TEST_NAME}] PASS")
        print(f"About: {ABOUT}")
        print("Output:\n" + json.dumps({"status": "clean", "checks_passed": len(results)}, indent=2))
        return 0
    else:
        print(f"[{TEST_NAME}] FAIL")
        print(f"About: {ABOUT}")
        print("Reason: One or more checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
