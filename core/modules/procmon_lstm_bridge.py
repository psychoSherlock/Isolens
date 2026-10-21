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


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 procmon_lstm_bridge.py <procmon_summary.json | procmon.csv> [sample_name]")
        sys.exit(1)

    target = sys.argv[1]
    proc = sys.argv[2] if len(sys.argv) > 2 else ""
    payload = procmon_to_lstm_payload(target, sample_proc=proc)

    print(json.dumps(payload, indent=2))
