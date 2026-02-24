"""Parse VBoxManage command outputs into structured data.

Only extracts fields that are relevant for a malware sandbox workflow:
identity, state, resources, networking, snapshots, and shared folders.
"""

from __future__ import annotations

import re
from typing import Any


def parse_list_vms(stdout: str) -> list[dict[str, str]]:
    """Parse `VBoxManage list vms` / `list runningvms` output.

    Returns: [{"name": "...", "uuid": "..."}]
    """
    results: list[dict[str, str]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r'^"(.+)"\s+\{([0-9a-fA-F-]+)\}$', line)
        if match:
            results.append({"name": match.group(1), "uuid": match.group(2)})
    return results


# ---------------------------------------------------------------------------
# Value helpers
# ---------------------------------------------------------------------------

def _coerce(raw: str) -> Any:
    """Convert a machinereadable value to a Python-native type."""
    if raw in {"on", "off"}:
        return raw == "on"
    if raw in {"true", "false"}:
        return raw == "true"
    if raw in {"enabled", "disabled"}:
        return raw == "enabled"
    try:
        return int(raw)
    except ValueError:
        return raw


def _parse_raw(stdout: str) -> dict[str, Any]:
    """Parse key=value lines from machinereadable output into a flat dict."""
    data: dict[str, Any] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().strip('"')
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1].replace('\\"', '"')
        data[key] = _coerce(value)
    return data


# ---------------------------------------------------------------------------
# showvminfo --machinereadable  →  only sandbox-relevant fields
# ---------------------------------------------------------------------------

_NIC_RE = re.compile(
    r"^(nic|macaddress|cableconnected|natnet|hostonlyadapter|bridgeadapter)(\d+)$"
)
_SF_RE = re.compile(r"^SharedFolder(Name|Path)GlobalMapping(\d+)$")


def parse_showvminfo(stdout: str) -> dict[str, Any]:
    """Parse `VBoxManage showvminfo --machinereadable` into essential fields.

    Returns only what matters for a sandbox:
    - identity (name, uuid, os, state)
    - resources (memory, cpus)
    - network adapters (enabled only)
    - current snapshot
    - shared folders
    """
    raw = _parse_raw(stdout)

    # --- Identity & state ---
    info: dict[str, Any] = {
        "name": raw.get("name"),
        "uuid": raw.get("UUID"),
        "os": raw.get("ostype"),
        "state": raw.get("VMState"),
        "state_changed": raw.get("VMStateChangeTime"),
    }

    # --- Resources ---
    info["memory_mb"] = raw.get("memory")
    info["cpus"] = raw.get("cpus")

    # --- Network (enabled NICs only) ---
    nic_data: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        m = _NIC_RE.match(key)
        if m:
            prop, idx = m.group(1), m.group(2)
            nic_data.setdefault(idx, {})[prop] = value

    nics: list[dict[str, Any]] = []
    for idx in sorted(nic_data, key=int):
        nic = nic_data[idx]
        if nic.get("nic") == "none":
            continue
        nics.append({
            "slot": int(idx),
            "type": nic.get("nic"),
            "mac": nic.get("macaddress"),
            "cable": nic.get("cableconnected"),
            "attachment": (
                nic.get("natnet")
                or nic.get("hostonlyadapter")
                or nic.get("bridgeadapter")
            ),
        })
    info["network"] = nics

    # --- Current snapshot ---
    info["snapshot"] = raw.get("CurrentSnapshotName")
    info["snapshot_uuid"] = raw.get("CurrentSnapshotUUID")

    # --- Shared folders ---
    sf_names: dict[str, str] = {}
    sf_paths: dict[str, str] = {}
    for key, value in raw.items():
        m = _SF_RE.match(key)
        if m:
            prop, idx = m.group(1), m.group(2)
            if prop == "Name":
                sf_names[idx] = value
            else:
                sf_paths[idx] = value

    info["shared_folders"] = [
        {"name": sf_names[i], "path": sf_paths.get(i, "")}
        for i in sorted(sf_names, key=int)
    ]

    return info


# ---------------------------------------------------------------------------
# snapshot list --machinereadable
# ---------------------------------------------------------------------------

def parse_snapshot_list(stdout: str) -> dict[str, Any]:
    """Parse `VBoxManage snapshot <vm> list --machinereadable`.

    Returns {"snapshots": [{"name": ..., "uuid": ...}], "current": "name"}.
    """
    raw = _parse_raw(stdout)
    entries: dict[str, dict[str, str]] = {}
    current_name: str | None = None

    for key, value in raw.items():
        if key == "CurrentSnapshotName":
            current_name = value
            continue
        for prefix in ("SnapshotName", "SnapshotUUID"):
            if key.startswith(prefix):
                suffix = key[len(prefix):]
                prop = "name" if "Name" in prefix else "uuid"
                entries.setdefault(suffix, {})[prop] = value
                break

    return {
        "snapshots": [entries[s] for s in sorted(entries)],
        "current": current_name,
    }


# ---------------------------------------------------------------------------
# guestproperty enumerate  →  network interface IPs
# ---------------------------------------------------------------------------

_GUEST_PROP_RE = re.compile(
    r"/VirtualBox/GuestInfo/Net/(\d+)/([^\s]+)\s+=\s+'([^']*)'"
)


def parse_guest_net_properties(stdout: str) -> list[dict[str, Any]]:
    """Parse `VBoxManage guestproperty enumerate <vm> /VirtualBox/GuestInfo/Net/*`.

    Returns a list of network interface dicts, one per interface index, e.g.:
    [
      {"interface": 0, "ip": "175.20.2.91", "netmask": "255.255.252.0",
       "broadcast": "255.255.255.255", "mac": "080027E3C08F", "status": "Up"},
      ...
    ]
    Requires VirtualBox Guest Additions to be installed and running inside the VM.
    """
    interfaces: dict[int, dict[str, Any]] = {}

    for line in stdout.splitlines():
        m = _GUEST_PROP_RE.search(line)
        if not m:
            continue
        idx, key, value = int(m.group(1)), m.group(2), m.group(3)
        iface = interfaces.setdefault(idx, {"interface": idx})
        if key == "V4/IP":
            iface["ip"] = value
        elif key == "V4/Netmask":
            iface["netmask"] = value
        elif key == "V4/Broadcast":
            iface["broadcast"] = value
        elif key == "Status":
            iface["status"] = value
        elif key == "MAC":
            iface["mac"] = value

    return [interfaces[i] for i in sorted(interfaces)]
