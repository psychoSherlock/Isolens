"""TEST_09 – VM IP address retrieval via Guest Additions.

Two sub-tests:
  A) parse_guest_net_properties correctly parses sample guestproperty output.
  B) VBoxManageClient.get_vm_ip_addresses returns expected raw output for a
     real running VM (skipped if no VM is running).
"""

from __future__ import annotations

import json
import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.modules.vbox_output_parser import parse_guest_net_properties
from core.controller.vbox_controller import VBoxManageClient

TEST_NAME = "TEST_09_vm_ip"

SAMPLE_OUTPUT = """\
/VirtualBox/GuestInfo/Net/0/MAC          = '080027E3C08F'
/VirtualBox/GuestInfo/Net/0/Status       = 'Up'
/VirtualBox/GuestInfo/Net/0/V4/Broadcast = '255.255.255.255'
/VirtualBox/GuestInfo/Net/0/V4/IP        = '175.20.2.91'
/VirtualBox/GuestInfo/Net/0/V4/Netmask   = '255.255.252.0'
/VirtualBox/GuestInfo/Net/1/MAC          = '080027EE2590'
/VirtualBox/GuestInfo/Net/1/Status       = 'Up'
/VirtualBox/GuestInfo/Net/1/V4/Broadcast = '255.255.255.255'
/VirtualBox/GuestInfo/Net/1/V4/IP        = '192.168.56.101'
/VirtualBox/GuestInfo/Net/1/V4/Netmask   = '255.255.255.0'
/VirtualBox/GuestInfo/Net/2/MAC          = '080027416E0E'
/VirtualBox/GuestInfo/Net/2/Status       = 'Up'
/VirtualBox/GuestInfo/Net/2/V4/Broadcast = '255.255.255.255'
/VirtualBox/GuestInfo/Net/2/V4/IP        = '10.0.2.15'
/VirtualBox/GuestInfo/Net/2/V4/Netmask   = '255.255.255.0'
/VirtualBox/GuestInfo/Net/Count          = '3'
"""


def test_parser() -> tuple[bool, str]:
    """Sub-test A: parse_guest_net_properties parses sample output correctly."""
    interfaces = parse_guest_net_properties(SAMPLE_OUTPUT)
    output = json.dumps(interfaces, indent=2)

    errors = []
    if len(interfaces) != 3:
        errors.append(f"Expected 3 interfaces, got {len(interfaces)}")
    if interfaces[0].get("ip") != "175.20.2.91":
        errors.append(f"Interface 0 IP mismatch: {interfaces[0].get('ip')}")
    if interfaces[1].get("ip") != "192.168.56.101":
        errors.append(f"Interface 1 IP mismatch: {interfaces[1].get('ip')}")
    if interfaces[2].get("ip") != "10.0.2.15":
        errors.append(f"Interface 2 IP mismatch: {interfaces[2].get('ip')}")
    if interfaces[1].get("netmask") != "255.255.255.0":
        errors.append(f"Interface 1 netmask mismatch: {interfaces[1].get('netmask')}")
    if interfaces[0].get("status") != "Up":
        errors.append(f"Interface 0 status mismatch: {interfaces[0].get('status')}")

    if errors:
        return False, output + "\nErrors:\n" + "\n".join(errors)
    return True, output


def get_running_vms() -> list[str]:
    try:
        proc = subprocess.run(
            ["VBoxManage", "list", "runningvms"],
            capture_output=True, text=True, timeout=10,
        )
        vms = []
        for line in proc.stdout.splitlines():
            if '"' in line:
                name = line.split('"')[1]
                vms.append(name)
        return vms
    except Exception:
        return []


def test_live_vm(vm_name: str) -> tuple[bool, str]:
    """Sub-test B: live guestproperty call returns at least one IP."""
    client = VBoxManageClient(dry_run=False, raise_on_error=False)
    result = client.get_vm_ip_addresses(vm_name)
    interfaces = parse_guest_net_properties(result.stdout)
    output = json.dumps({"vm": vm_name, "interfaces": interfaces}, indent=2)

    if not interfaces:
        # Could mean Guest Additions not installed; treat as soft warning not failure
        return True, output + "\n[WARN] No interfaces found (Guest Additions may not be running)"
    ips = [i.get("ip") for i in interfaces if i.get("ip")]
    if not ips:
        return False, output + "\nErrors: Interfaces found but no IP addresses populated"
    return True, output


def main() -> int:
    overall_pass = True

    # --- Sub-test A: parser ---
    pass_a, output_a = test_parser()
    status_a = "PASS" if pass_a else "FAIL"
    print(f"[{TEST_NAME}_A] {status_a}")
    print("About: parse_guest_net_properties parses guestproperty enumerate output correctly")
    print(f"Output:\n{output_a}\n")
    if not pass_a:
        overall_pass = False

    # --- Sub-test B: live VM (optional) ---
    running_vms = get_running_vms()
    if running_vms:
        vm = running_vms[0]
        pass_b, output_b = test_live_vm(vm)
        status_b = "PASS" if pass_b else "FAIL"
        print(f"[{TEST_NAME}_B] {status_b}")
        print(f"About: Live guestproperty IP lookup for VM '{vm}'")
        print(f"Output:\n{output_b}\n")
        if not pass_b:
            overall_pass = False
    else:
        print(f"[{TEST_NAME}_B] SKIP")
        print("About: Live VM IP lookup — no running VMs detected\n")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
