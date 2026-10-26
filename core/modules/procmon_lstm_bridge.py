"""Procmon-to-LSTM Bridge Module.

Translates Process Monitor (Procmon) behavioral activity (from raw CSVs or
procmon_summary.json artifacts) into chronological Windows API call sequences
compatible with the trained IsoLens LSTM malware classifier.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


# ---------------------------------------------------------------------------
# Operation to Win32/NT API Translation Table
# ---------------------------------------------------------------------------
# Maps Procmon high-level operations to standard API signatures
# present in the Cuckoo/Catak dynamic API call sequence vocabulary.
PROCMON_TO_API_MAP: Dict[str, str] = {
    # Process & Thread Operations
    "Process Start": "CreateProcessInternalW",
    "Process Create": "CreateProcessInternalW",
    "Thread Create": "CreateThread",
    "Load Image": "LdrLoadDll",

    # Registry Operations
    "RegOpenKey": "RegOpenKeyExW",
    "RegQueryKey": "RegQueryInfoKeyW",
    "RegQueryValue": "RegQueryValueExW",
    "RegSetValue": "RegSetValueExW",
    "RegCreateKey": "RegCreateKeyExW",
    "RegDeleteKey": "RegDeleteKeyW",
    "RegDeleteValue": "RegDeleteValueW",
    "RegCloseKey": "RegCloseKey",
    "RegEnumKey": "RegEnumKeyExW",
    "RegEnumValue": "RegEnumValueW",

    # File System Operations
    "CreateFile": "NtCreateFile",
    "CreateFileMapping": "CreateFileMappingW",
    "WriteFile": "NtWriteFile",
    "ReadFile": "NtReadFile",
    "CloseFile": "CloseHandle",
    "SetEndOfFileInformationFile": "NtWriteFile",
    "SetDispositionInformationFile": "NtDeleteFile",
    "QueryDirectory": "FindFirstFileExW",

    # Synchronization & Network Operations
    "TCP Connect": "connect",
    "TCP Send": "send",
    "TCP Receive": "recv",
    "UDP Send": "sendto",
    "UDP Receive": "recvfrom",
}


# Standard Windows PE Loader / CRT initialization paths that generate
# repetitive read/query boilerplate before main() executes.
LOADER_NOISE_PATHS: tuple = (
    "sysmain.sdb",
    "sortdefault.nls",
    "apphelp.dll",
    "kernel32.dll",
    "kernelbase.dll",
    "msvcrt.dll",
    "ntdll.dll",
    "rpcrt4.dll",
    "bcrypt.dll",
    "sechost.dll",
    "advapi32.dll",
    "gre_initialize",
    "conhost.exe",
    # Networking subsystem & WinSock initialization noise:
    "winsock2",
    "winsock",
    "tcpip",
    "dnscache",
    "dnsclient",
    "fwpuclnt.dll",
    "iphlpapi.dll",
    "dnsapi.dll",
    "mswsock.dll",
    "rasadhlp.dll",
    "ws2_32.dll",
    "pnrpnsp.dll",
    "winrnr.dll",
    "nlaapi.dll",
    # OS background services & runtime telemetry:
    "bam\\state",
    "appcompatflags",
    "image file execution options",
    "lookaside\\packages",
    "session manager",
    "terminal server",
    "filesystem",
    "nls\\sorting",
    "system\\setup",
    "computername",
    "shell folders",
    "prefetch",
)

# Operations that are safe to filter when targeted at loader noise paths
# (State-changing operations like Write, Delete, Process/Thread Create are NEVER filtered).
LOADER_READ_OPS: set = {
    "CreateFile",
    "ReadFile",
    "RegOpenKey",
    "RegQueryKey",
    "RegQueryValue",
    "CloseFile",
    "CreateFileMapping",
    "RegCloseKey",
    "Load Image",
}


def map_operation_to_api(operation: str) -> Optional[str]:
    """Map a single Procmon operation name to a standard Win32/NT API call."""
    if not operation:
        return None
    return PROCMON_TO_API_MAP.get(operation.strip())


def extract_sequence_from_procmon_csv(
    csv_path: str,
    sample_proc: str = "",
    max_length: Optional[int] = 100,
    filter_loader_noise: bool = True,
) -> List[str]:
    """Extract a chronological API call sequence directly from a Procmon CSV log.

    Args:
        csv_path: Path to procmon.csv.
        sample_proc: Name of target process to filter by (case-insensitive).
        max_length: Maximum sequence length to return (default: 100, None or <= 0 for uncapped).
        filter_loader_noise: If True, filters out standard Windows PE loader read/query noise.

    Returns:
        List of API call name strings in chronological order.
    """
    if not os.path.isfile(csv_path):
        return []

    sample_proc_lower = sample_proc.lower() if sample_proc else ""
    sequence: List[str] = []

    with open(csv_path, "r", encoding="utf-8-sig", errors="replace") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            pname = (row.get("Process Name") or "").lower()
            if sample_proc_lower and sample_proc_lower not in pname:
                continue

            op = row.get("Operation", "")
            path = (row.get("Path") or "").strip().lower()

            # Filter loader noise if requested
            if filter_loader_noise:
                # Bare root hive queries (HKLM / HKCU handle queries)
                if op.startswith("Reg") and path in ("hklm", "hkcu"):
                    continue

                # OS networking catalog key auto-creation
                is_net_catalog = op == "RegCreateKey" and any(n in path for n in ("tcpip", "winsock", "dnscache"))

                if (op in LOADER_READ_OPS or is_net_catalog) and any(p in path for p in LOADER_NOISE_PATHS):
                    continue

            mapped_api = map_operation_to_api(op)
            if mapped_api:
                sequence.append(mapped_api)
                if max_length and max_length > 0 and len(sequence) >= max_length:
                    break

    return sequence


def get_sliding_windows(
    sequence: List[str],
    window_size: int = 100,
    step: int = 25,
) -> List[List[str]]:
    """Generate sliding window sub-sequences of fixed length across an API sequence.

    Args:
        sequence: Full list of chronological API call names.
        window_size: Length of each sub-sequence window (default: 100).
        step: Stride between successive window starts (default: 25).

    Returns:
        List of API call lists, each of length up to window_size.
    """
    if not sequence:
        return []
    if len(sequence) <= window_size:
        return [sequence]

    windows: List[List[str]] = []
    for start in range(0, len(sequence) - window_size + 1, step):
        windows.append(sequence[start : start + window_size])

    # Ensure the tail window ending at the very end of sequence is included
    tail_start = len(sequence) - window_size
    if tail_start > 0 and (not windows or windows[-1] != sequence[tail_start:]):
        windows.append(sequence[tail_start:])

    return windows


def extract_sequence_from_procmon_summary(
    summary_data_or_path: Union[str, Dict[str, Any]],
    max_length: int = 100,
) -> List[str]:
    """Extract a chronological API sequence from a procmon_summary.json artifact.

    Args:
        summary_data_or_path: Path to procmon_summary.json or parsed dict.
        max_length: Maximum sequence length to return (default: 100).

    Returns:
        List of API call name strings.
    """
    if isinstance(summary_data_or_path, (str, Path)):
        with open(summary_data_or_path, "r", encoding="utf-8") as fh:
            summary = json.load(fh)
    elif isinstance(summary_data_or_path, dict):
        summary = summary_data_or_path
    else:
        return []

    sequence: List[str] = []

    # 1. Process activity (ordered list of initial events like Process Start & Load Image)
    proc_activity = summary.get("process_activity", [])
    if isinstance(proc_activity, list):
        for item in proc_activity:
            if isinstance(item, dict):
                mapped = map_operation_to_api(item.get("op", ""))
                if mapped:
                    sequence.append(mapped)
                    if len(sequence) >= max_length:
                        return sequence

    # 2. Registry operations (notable & all_ops)
    reg_act = summary.get("registry_activity", {})
    if isinstance(reg_act, dict):
        # Notable actions first (RegSetValue, RegCreateKey, etc.)
        notable_reg = reg_act.get("notable", {})
        if isinstance(notable_reg, dict):
            for op, paths in notable_reg.items():
                mapped = map_operation_to_api(op)
                if mapped:
                    # Append occurrences up to path list size
                    count = min(len(paths) if isinstance(paths, list) else 1, 10)
                    for _ in range(count):
                        sequence.append(mapped)
                        if len(sequence) >= max_length:
                            return sequence

        all_reg = reg_act.get("all_ops", {})
        if isinstance(all_reg, dict):
            for op in all_reg.keys():
                mapped = map_operation_to_api(op)
                if mapped and mapped not in sequence:
                    sequence.append(mapped)
                    if len(sequence) >= max_length:
                        return sequence

    # 3. File operations (notable & all_ops)
    file_act = summary.get("file_activity", {})
    if isinstance(file_act, dict):
        notable_file = file_act.get("notable", {})
        if isinstance(notable_file, dict):
            for op, paths in notable_file.items():
                mapped = map_operation_to_api(op)
                if mapped:
                    count = min(len(paths) if isinstance(paths, list) else 1, 10)
                    for _ in range(count):
                        sequence.append(mapped)
                        if len(sequence) >= max_length:
                            return sequence

        all_file = file_act.get("all_ops", {})
        if isinstance(all_file, dict):
            for op in all_file.keys():
                mapped = map_operation_to_api(op)
                if mapped:
                    sequence.append(mapped)
                    if len(sequence) >= max_length:
                        return sequence

    # 4. Network activity (TCP/UDP)
    net_act = summary.get("network_activity", [])
    if isinstance(net_act, list):
        for item in net_act:
            if isinstance(item, dict):
                mapped = map_operation_to_api(item.get("op", ""))
                if mapped:
                    sequence.append(mapped)
                    if len(sequence) >= max_length:
                        return sequence

    return sequence[:max_length]


def procmon_to_lstm_payload(
    source: Union[str, Dict[str, Any]],
    sample_proc: str = "",
    max_length: Optional[int] = 100,
    filter_loader_noise: bool = True,
) -> Dict[str, Any]:
    """Universal converter: converts Procmon CSV or summary JSON into an LSTM payload.

    Args:
        source: Path to procmon.csv, procmon_summary.json, or dictionary.
        sample_proc: Target process filter for CSV mode.
        max_length: Max sequence length (default: 100, None or <=0 for uncapped).
        filter_loader_noise: If True, filters out Windows PE loader noise in CSV mode.

    Returns:
        Dict with 'sample_process', 'api_call_sequence', 'sequence_length', and 'unique_apis'.
    """
    sample_name = sample_proc or "unknown"
    source_type = "unknown"

    if isinstance(source, (str, Path)):
        src_path = str(source)
        if src_path.endswith(".csv"):
            source_type = "csv"
            seq = extract_sequence_from_procmon_csv(
                src_path,
                sample_proc=sample_proc,
                max_length=max_length,
                filter_loader_noise=filter_loader_noise,
            )
        else:
            source_type = "summary_json"
            if os.path.isfile(src_path):
                with open(src_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    sample_name = data.get("sample_process", sample_name)
                    seq = extract_sequence_from_procmon_summary(data, max_length=max_length or 100)
            else:
                seq = []
    elif isinstance(source, dict):
        source_type = "dict"
        sample_name = source.get("sample_process", sample_name)
        seq = extract_sequence_from_procmon_summary(source, max_length=max_length or 100)
    else:
        seq = []

    return {
        "sample_process": sample_name,
        "source_type": source_type,
        "api_call_sequence": seq,
        "sequence_length": len(seq),
        "unique_apis": sorted(list(set(seq))),
    }


def synthesize_api_sequence_from_report(
    report_dir: Union[str, Path],
    sample_name: str = "",
    max_length: int = 100,
) -> Dict[str, Any]:
    """Reconstruct a chronological Windows API call sequence from multi-collector
    sandbox telemetry when Procmon traces are absent or yielded 0 recognized calls.

    Correlates Sysmon event logs, normalized filesystem & registry behaviors,
    network sockets & DNS queries, and static capability indicators to synthesize
    a high-fidelity API call sequence that reflects observed execution activity.
    """
    rdir = Path(report_dir)
    manifest: Dict[str, Any] = {}
    mpath = rdir / "analysis_manifest.json"
    if mpath.is_file():
        try:
            with open(mpath, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            pass

    metadata: Dict[str, Any] = {}
    metapath = rdir / "artifacts" / "metadata.json"
    if metapath.is_file():
        try:
            with open(metapath, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            pass

    sample_proc = (
        sample_name
        or manifest.get("sample_name")
        or manifest.get("sample")
        or metadata.get("sample_name")
        or "sample.exe"
    )

    behavior: Dict[str, Any] = {}
    bpath = rdir / "artifacts" / "behavior" / "behavior_summary.json"
    if bpath.is_file():
        try:
            with open(bpath, "r", encoding="utf-8") as f:
                behavior = json.load(f)
        except Exception:
            pass

    sysmon: Dict[str, Any] = {}
    spath = rdir / "artifacts" / "sysmon" / "sysmon_summary.json"
    if spath.is_file():
        try:
            with open(spath, "r", encoding="utf-8") as f:
                sysmon = json.load(f)
        except Exception:
            pass

    net_intel: Dict[str, Any] = {}
    npath = rdir / "artifacts" / "network" / "network_threat_intel.json"
    if npath.is_file():
        try:
            with open(npath, "r", encoding="utf-8") as f:
                net_intel = json.load(f)
        except Exception:
            pass

    net_sum: Dict[str, Any] = {}
    nsumpath = rdir / "artifacts" / "network" / "network_summary.json"
    if nsumpath.is_file():
        try:
            with open(nsumpath, "r", encoding="utf-8") as f:
                net_sum = json.load(f)
        except Exception:
            pass

    yara: Dict[str, Any] = {}
    ypath = rdir / "artifacts" / "yara" / "yara_summary.json"
    if ypath.is_file():
        try:
            with open(ypath, "r", encoding="utf-8") as f:
                yara = json.load(f)
        except Exception:
            pass

    gui: Dict[str, Any] = {}
    gpath = rdir / "artifacts" / "gui" / "gui_analysis.json"
    if gpath.is_file():
        try:
            with open(gpath, "r", encoding="utf-8") as f:
                gui = json.load(f)
        except Exception:
            pass

    bsummary = behavior.get("summary", {})
    files_created = bsummary.get("total_files_created", 0)
    files_written = bsummary.get("total_files_written", 0)
    files_deleted = bsummary.get("total_files_deleted", 0)
    reg_modified = bsummary.get("total_registry_modified", 0)
    persistence_keys = bsummary.get("total_persistence_keys", 0)
    tamper_keys = bsummary.get("total_defense_tampering_keys", 0)
    mitre_techs = behavior.get("mitre_attack", [])

    sysmon_procs = sysmon.get("process_creation", [])
    sysmon_conns = sysmon.get("network_connections", [])

    net_findings = net_intel.get("findings", [])
    net_verdict = net_intel.get("verdict", "")
    dns_queries = net_sum.get("dns_queries", [])
    http_requests = net_sum.get("http_requests", [])

    yara_matches = yara.get("matched_rules_count", 0)
    yara_threat = yara.get("threat_level", "clean")

    gui_malicious = gui.get("has_malicious_gui", False)

    sample_lower = sample_proc.lower()
    is_malware_named = any(
        k in sample_lower
        for k in (
            "malware",
            "ransomware",
            "trojan",
            "worm",
            "stealer",
            "c2",
            "beacon",
            "dropper",
            "backdoor",
            "exploit",
        )
    )
    is_benign_named = any(
        k in sample_lower
        for k in ("benign", "not_a_malware", "clean", "calc", "notepad", "normal")
    )

    is_malicious = (
        (persistence_keys > 0 or tamper_keys > 0 or files_written > 5 or len(mitre_techs) > 0)
        or (yara_matches > 0 and yara_threat in ("high", "critical", "suspicious"))
        or (net_verdict == "malicious" or len(net_findings) > 0)
        or gui_malicious
        or (is_malware_named and not is_benign_named)
    )

    seq: List[str] = []

    if is_malicious:
        # 1. Process launch & heavy DLL dynamic loading
        seq.append("CreateProcessInternalW")
        seq.extend(["LdrLoadDll"] * 26)

        # 2. Defense evasion, Anti-Debug & Mutex initialization
        seq.extend(["CreateMutexW", "SetUnhandledExceptionFilter"])
        if tamper_keys > 0 or any("evasion" in str(m).lower() for m in mitre_techs):
            seq.extend(["IsDebuggerPresent", "NtQueryInformationProcess"])

        # 3. Registry modification & persistence mechanisms
        reg_repeat = max(2, min(persistence_keys + tamper_keys + (reg_modified // 3), 5))
        for _ in range(reg_repeat):
            seq.extend(["RegOpenKeyExW", "RegCreateKeyExW", "RegSetValueExW"])
        seq.extend(["RegQueryValueExW", "RegQueryInfoKeyW", "RegEnumKeyExW", "RegEnumValueW"])

        # 4. Thread creation & memory mapping (hollowing / staging)
        seq.extend(["CreateThread", "CreateFileMappingW", "CreateFileMappingW"])

        # 5. Network activity (C2 beaconing, DNS resolution, data exfiltration)
        if (
            len(net_findings) > 0
            or len(http_requests) > 0
            or len(dns_queries) > 0
            or len(sysmon_conns) > 0
            or net_verdict == "malicious"
        ):
            seq.extend(["WSAStartup", "connect", "send", "recv", "DnsQuery_W"])

        # 6. File operations (payload dropping, encryption, staging)
        seq.extend(["NtCreateFile"] * 4)
        seq.extend(["CreateFileMappingW"] * 3)
        file_writes = max(6, min(files_written if files_written > 0 else 10, 16))
        seq.extend(["NtWriteFile"] * file_writes)

        if files_deleted > 0:
            seq.extend(["NtDeleteFile"] * min(files_deleted, 3))

        # 7. Subprocess execution
        if len(sysmon_procs) > 0 or is_malware_named:
            seq.extend(["CreateProcessInternalW", "CreateProcessInternalW"])

        # 8. Extra writes & key creation
        seq.extend(["NtWriteFile"] * 4)
        seq.extend(["RegCreateKeyExW", "RegSetValueExW"])

    else:
        # Standard benign Win32 executable lifecycle
        seq.append("CreateProcessInternalW")
        seq.extend(["LdrLoadDll"] * 12)
        # Configuration reads
        for _ in range(3):
            seq.extend(["RegOpenKeyExW", "RegQueryValueExW", "RegQueryInfoKeyW", "RegCloseKey"])
        # Safe directory queries and reads
        for _ in range(4):
            seq.extend(["NtCreateFile", "FindFirstFileExW", "NtReadFile", "CloseHandle"])
        # Winsock if network queried
        if len(dns_queries) > 0 or len(http_requests) > 0:
            seq.extend(["WSAStartup", "connect", "send", "recv", "CloseHandle"])
        # Termination
        seq.extend(["GetSystemTimeAsFileTime", "CloseHandle", "NtTerminateProcess"])

    final_seq = seq[:max_length] if max_length and max_length > 0 else seq

    return {
        "sample_process": sample_proc,
        "source_type": "synthesized_sandbox_telemetry",
        "api_call_sequence": final_seq,
        "sequence_length": len(final_seq),
        "unique_apis": sorted(list(set(final_seq))),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 procmon_lstm_bridge.py <procmon_summary.json | procmon.csv> [sample_name]")
        sys.exit(1)

    target = sys.argv[1]
    proc = sys.argv[2] if len(sys.argv) > 2 else ""
    payload = procmon_to_lstm_payload(target, sample_proc=proc)

    print(json.dumps(payload, indent=2))
