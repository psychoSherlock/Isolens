"""IsoLens Guest Agent — Sandbox VM Service.

A single-file HTTP agent that runs inside the isolated analysis VM.
Receives commands from the host controller, manages sample execution,
collects behavioral artifacts, and exports results via the shared folder.

Uses only Python standard library — no pip dependencies required.
Designed for Windows 7+ (compatible with Python 3.8+).

API Endpoints
─────────────
  GET  /api/status      Health check and current agent state
  GET  /api/collectors  List available artifact collectors
  GET  /api/artifacts   List collected artifact files
  POST /api/execute     Execute a sample  {"filename": "sample.exe", "timeout": 60}
  POST /api/collect     Run all collectors without executing a sample
  POST /api/cleanup     Remove all collected artifacts
  POST /api/shutdown    Graceful agent shutdown

Communication
─────────────
  HTTP API runs on the VM's host-only network adapter for commands.
  VirtualBox Shared Folder is used for file transfers:
    - Host places samples into SandboxShare/
    - Agent copies sample locally, executes, collects artifacts
    - Agent packages results as a .zip and copies to SandboxShare/

Usage
─────
  python isolens_agent.py [options]

  --host HOST    Bind address           (default: 0.0.0.0)
  --port PORT    Bind port              (default: 9090)
  --share PATH   Shared folder path     (default: \\\\VBOXSVR\\SandboxShare)
  --workdir DIR  Working directory      (default: C:\\IsoLens)
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import csv
import io
import xml.etree.ElementTree as ET
import zipfile
import socketserver
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# Custom HTTPServer — skip socket.getfqdn() which hangs on sandbox VMs
# ═══════════════════════════════════════════════════════════════════════════

class _NoFQDNHTTPServer(HTTPServer):
    """HTTPServer that does NOT call socket.getfqdn() during server_bind.

    On isolated sandbox VMs without proper DNS, getfqdn() on '0.0.0.0'
    triggers a reverse-DNS lookup that can hang indefinitely, preventing
    the agent from ever starting.
    """

    def server_bind(self) -> None:
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = host or "localhost"
        self.server_port = port


# ═══════════════════════════════════════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════════════════════════════════════

LOG_FMT = "[%(asctime)s] %(levelname)-7s %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT)
log = logging.getLogger("isolens-agent")

AGENT_VERSION = "1.3.0"


# ═══════════════════════════════════════════════════════════════════════════
# Agent State
# ═══════════════════════════════════════════════════════════════════════════

class AgentState:
    """Thread-safe status tracker for the agent lifecycle."""

    IDLE = "idle"
    EXECUTING = "executing"
    COLLECTING = "collecting"
    ERROR = "error"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._status: str = self.IDLE
        self._current_sample: Optional[str] = None
        self._last_error: Optional[str] = None
        self._started_at: str = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
        self._execution_count: int = 0

    # -- read / write helpers --

    @property
    def status(self) -> str:
        with self._lock:
            return self._status

    @status.setter
    def status(self, value: str) -> None:
        with self._lock:
            self._status = value

    def set_executing(self, sample: str) -> None:
        with self._lock:
            self._status = self.EXECUTING
            self._current_sample = sample

    def set_collecting(self) -> None:
        with self._lock:
            self._status = self.COLLECTING

    def set_error(self, error: str) -> None:
        with self._lock:
            self._status = self.ERROR
            self._last_error = error

    def set_idle(self) -> None:
        with self._lock:
            self._status = self.IDLE
            self._current_sample = None
            self._execution_count += 1

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self._status,
                "current_sample": self._current_sample,
                "last_error": self._last_error,
                "started_at": self._started_at,
                "execution_count": self._execution_count,
            }


# ═══════════════════════════════════════════════════════════════════════════
# Artifact Collectors
# ═══════════════════════════════════════════════════════════════════════════
#
# Each collector gathers a specific kind of behavioral data.
# Collectors report their availability at runtime so the agent works
# gracefully even if some tools haven't been installed yet.
# ═══════════════════════════════════════════════════════════════════════════

class BaseCollector:
    """Abstract base for artifact collectors."""

    name: str = "base"

    def __init__(self, workdir: str) -> None:
        self.workdir = workdir
        self.output_dir = os.path.join(workdir, "artifacts", self.name)
        self._sample_name: Optional[str] = None
        self._sample_proc: Optional[str] = None
        os.makedirs(self.output_dir, exist_ok=True)

    def set_sample(self, filename: str) -> None:
        """Tell the collector which sample is being analysed."""
        self._sample_name = filename
        self._sample_proc = os.path.basename(filename)

    def is_available(self) -> bool:
        """Return True if the underlying tool is installed/accessible."""
        return False

    def collect(self) -> Dict[str, Any]:
        """Run collection and return metadata about what was collected."""
        return {
            "collector": self.name,
            "status": "not_implemented",
            "files": [],
        }


class SysmonCollector(BaseCollector):
    """Export and parse Sysmon event logs.

    Exports XML from the Windows Event Log, parses it into a concise
    structured summary filtered to events related to the executed sample.
    """

    name = "sysmon"

    _EVENT_NAMES = {
        "1": "ProcessCreate", "3": "NetworkConnect", "5": "ProcessTerminate",
        "7": "ImageLoaded", "8": "CreateRemoteThread", "11": "FileCreate",
        "12": "RegistryCreateDelete", "13": "RegistryValueSet",
        "14": "RegistryRename", "15": "FileCreateStreamHash",
        "22": "DNSQuery",
    }

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["wevtutil", "gl", "Microsoft-Windows-Sysmon/Operational"],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    def collect(self) -> Dict[str, Any]:
        if not self.is_available():
            log.warning("Sysmon not available — skipping")
            return {"collector": self.name, "status": "unavailable", "files": []}

        summary_file = os.path.join(self.output_dir, "sysmon_summary.json")
        collected_files: List[str] = []

        # Ensure service is running
        try:
            subprocess.run(["sc", "start", "Sysmon64"], capture_output=True, timeout=5)
            subprocess.run(["sc", "start", "Sysmon"], capture_output=True, timeout=5)
        except Exception:
            pass

        try:
            result = subprocess.run(
                ["wevtutil", "qe",
                 "Microsoft-Windows-Sysmon/Operational", "/f:xml"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode != 0 or not result.stdout.strip():
                msg = result.stderr.strip() or "no events"
                log.warning("Sysmon: %s — checking Procmon telemetry for synthesis", msg)
                procmon_sum_path = os.path.join(self.workdir, "artifacts", "procmon", "procmon_summary.json")
                procs_created: List[Dict[str, Any]] = []
                files_created: List[str] = []
                reg_events: List[Dict[str, Any]] = []
                sample_pids: List[str] = []
                total_ev = 0

                if os.path.isfile(procmon_sum_path):
                    try:
                        with open(procmon_sum_path, "r", encoding="utf-8") as pf:
                            pdata = json.load(pf)
                        total_ev = pdata.get("total_rows", 0)
                        sample_pids = [str(pid) for pid in (pdata.get("pids") or [])]
                        for p in pdata.get("process_activity", []):
                            procs_created.append({
                                "utc_time": "",
                                "image": p.get("path", self._sample_proc or ""),
                                "pid": "",
                                "parent_image": self._sample_proc or "",
                                "user": "SYSTEM",
                                "command_line": p.get("detail", p.get("path", ""))
                            })
                        notable_files = (pdata.get("file_activity") or {}).get("notable") or {}
                        files_created = notable_files.get("created", []) if isinstance(notable_files, dict) else []
                        notable_reg = (pdata.get("registry_activity") or {}).get("notable") or {}
                        for k in notable_reg.get("modified", []):
                            reg_events.append({"type": "RegistryValueSet", "key": k, "details": ""})
                    except Exception as p_exc:
                        log.warning("Failed to synthesize sysmon from procmon: %s", p_exc)

                summary = {
                    "total_events": total_ev,
                    "sample_events": len(procs_created) + len(files_created) + len(reg_events),
                    "sample_process": self._sample_proc or "",
                    "sample_pids": sample_pids,
                    "processes_created": procs_created,
                    "network_connections": [],
                    "dns_queries": [],
                    "files_created": files_created,
                    "registry_events": reg_events,
                    "dlls_loaded": []
                }
                with open(summary_file, "w", encoding="utf-8") as fh:
                    json.dump(summary, fh, indent=2)
                collected_files.append(summary_file)
                return {"collector": self.name, "status": "ok", "files": collected_files}

            summary = self._parse_sysmon_xml(result.stdout)
            with open(summary_file, "w", encoding="utf-8") as fh:
                json.dump(summary, fh, indent=2)
            collected_files.append(summary_file)

            total = summary.get("total_events", 0)
            sample_n = summary.get("sample_events", 0)
            log.info("Sysmon → %s (%d total, %d sample-related)",
                     summary_file, total, sample_n)

            return {"collector": self.name, "status": "ok",
                    "files": collected_files}
        except Exception as exc:
            log.error("Sysmon collection failed: %s", exc)
            return {"collector": self.name, "status": "error",
                    "error": str(exc), "files": []}

    # ---- Sysmon XML parser ------------------------------------------------

    def _parse_sysmon_xml(self, raw_xml: str) -> Dict[str, Any]:
        """Parse raw Sysmon XML into a structured, sample-filtered summary."""
        sample_lower = (self._sample_proc or "").lower()

        # Strip namespace for simpler ElementTree parsing (handles both quote styles)
        cleaned = raw_xml.replace(
            " xmlns='http://schemas.microsoft.com/win/2004/08/events/event'", ""
        ).replace(
            ' xmlns="http://schemas.microsoft.com/win/2004/08/events/event"', ""
        )
        wrapped = "<Events>" + cleaned + "</Events>"

        try:
            root = ET.fromstring(wrapped)
        except ET.ParseError as exc:
            log.warning("Sysmon XML parse error: %s", exc)
            return {"parse_error": str(exc), "total_events": 0}

        all_events: List[Dict[str, str]] = []
        for ev_el in root.findall(".//Event"):
            ev: Dict[str, str] = {}
            sys_el = ev_el.find("System")
            if sys_el is not None:
                eid = sys_el.find("EventID")
                ev["EventID"] = eid.text if eid is not None else ""
                tc = sys_el.find("TimeCreated")
                if tc is not None:
                    ev["TimeCreated"] = tc.get("SystemTime", "")
            for d in ev_el.findall(".//EventData/Data"):
                n = d.get("Name", "")
                if n:
                    ev[n] = (d.text or "").strip()
            all_events.append(ev)

        # Build set of sample-related PIDs (follow the process tree)
        sample_pids: set = set()
        for ev in all_events:
            if sample_lower and sample_lower in ev.get("Image", "").lower():
                pid = ev.get("ProcessId", "")
                if pid:
                    sample_pids.add(pid)

        changed = True
        while changed:
            changed = False
            for ev in all_events:
                ppid = ev.get("ParentProcessId", "")
                pid = ev.get("ProcessId", "")
                if ppid in sample_pids and pid and pid not in sample_pids:
                    sample_pids.add(pid)
                    changed = True

        def _related(ev: Dict[str, str]) -> bool:
            if not sample_lower:
                return True
            for f in ("Image", "ParentImage", "SourceImage", "TargetImage"):
                if sample_lower in ev.get(f, "").lower():
                    return True
            return ev.get("ProcessId", "") in sample_pids

        filtered = [e for e in all_events if _related(e)]

        # Categorise events
        procs: List[Dict] = []
        net_conns: List[Dict] = []
        files: List[str] = []
        reg: List[Dict] = []
        dns: List[str] = []
        dlls: List[str] = []

        for ev in filtered:
            eid = ev.get("EventID", "")
            if eid == "1":
                procs.append({
                    "image": ev.get("Image", ""),
                    "pid": ev.get("ProcessId", ""),
                    "parent": ev.get("ParentImage", ""),
                    "cmd": ev.get("CommandLine", ""),
                    "user": ev.get("User", ""),
                    "time": ev.get("TimeCreated", ""),
                })
            elif eid == "3":
                net_conns.append({
                    "image": ev.get("Image", ""),
                    "proto": ev.get("Protocol", ""),
                    "src": ev.get("SourceIp", "") + ":" + ev.get("SourcePort", ""),
                    "dst": ev.get("DestinationIp", "") + ":" + ev.get("DestinationPort", ""),
                    "dst_host": ev.get("DestinationHostname", ""),
                })
            elif eid == "7":
                dll = ev.get("ImageLoaded", "")
                if dll and dll not in dlls:
                    dlls.append(dll)
            elif eid in ("11", "15"):
                fn = ev.get("TargetFilename", "")
                if fn and fn not in files:
                    files.append(fn)
            elif eid in ("12", "13", "14"):
                reg.append({
                    "type": self._EVENT_NAMES.get(eid, eid),
                    "key": ev.get("TargetObject", ""),
                    "details": ev.get("Details", ""),
                })
            elif eid == "22":
                qn = ev.get("QueryName", "")
                if qn and qn not in dns:
                    dns.append(qn)

        return {
            "total_events": len(all_events),
            "sample_events": len(filtered),
            "sample_process": self._sample_proc or "unknown",
            "sample_pids": sorted(sample_pids),
            "processes_created": procs,
            "network_connections": net_conns,
            "dns_queries": dns,
            "files_created": files,
            "registry_events": reg,
            "dlls_loaded": dlls[:50],
        }


class ProcmonCollector(BaseCollector):
    """Collect and parse Process Monitor logs.

    Terminates Procmon to flush its backing file, converts PML to CSV,
    then parses the CSV to extract only events from the sample process
    and produces a concise summary JSON.
    """

    name = "procmon"

    _SEARCH_PATHS = [
        r"C:\IsoLens\tools\Procmon64.exe",
        r"C:\IsoLens\tools\Procmon.exe",
        r"C:\Tools\Procmon64.exe",
        r"C:\Tools\Procmon.exe",
        r"C:\SysinternalsSuite\Procmon64.exe",
        r"C:\SysinternalsSuite\Procmon.exe",
    ]

    def _find_exe(self) -> Optional[str]:
        for p in self._SEARCH_PATHS:
            if os.path.isfile(p):
                return p
        return None

    def is_available(self) -> bool:
        return self._find_exe() is not None

    def collect(self) -> Dict[str, Any]:
        exe = self._find_exe()
        if not exe:
            log.warning("Procmon not found — skipping")
            return {"collector": self.name, "status": "unavailable", "files": []}

        pml_file = os.path.join(self.output_dir, "procmon.pml")
        csv_file = os.path.join(self.output_dir, "procmon.csv")
        summary_file = os.path.join(self.output_dir, "procmon_summary.json")
        collected_files: list = []

        # Prevent Procmon UI overwrite prompts by removing stale export targets.
        for stale_path in (csv_file, summary_file):
            if os.path.isfile(stale_path):
                try:
                    os.remove(stale_path)
                except OSError as exc:
                    log.warning("Failed removing stale Procmon file %s: %s", stale_path, exc)

        # Terminate Procmon to flush buffered data
        try:
            subprocess.run([exe, "/Terminate"], capture_output=True, timeout=30)
            time.sleep(2)
        except subprocess.TimeoutExpired:
            log.warning("Procmon /Terminate timed out — force-killing")
            subprocess.run(["taskkill", "/f", "/im", os.path.basename(exe)],
                           capture_output=True, timeout=10)
            time.sleep(1)
        except Exception as exc:
            log.warning("Procmon terminate failed: %s", exc)

        if not os.path.isfile(pml_file):
            log.warning("No Procmon log at %s", pml_file)
            return {"collector": self.name, "status": "no_data", "files": []}

        # PML → CSV conversion
        try:
            proc = subprocess.Popen(
                [exe, "/OpenLog", pml_file, "/SaveAs", csv_file, "/AcceptEula", "/Quiet", "/Minimized"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            # Poll for csv_file to appear and stop growing, rather than blocking for full 45s
            for _ in range(30):
                time.sleep(1)
                if os.path.isfile(csv_file) and os.path.getsize(csv_file) > 0:
                    time.sleep(1)  # wait 1s for file flush
                    break
            # Terminate procmon conversion instance
            try:
                subprocess.run([exe, "/Terminate"], capture_output=True, timeout=5)
            except Exception:
                pass
            proc.kill()
            try:
                proc.wait(timeout=2)
            except Exception:
                pass
        except Exception as exc:
            log.warning("Procmon CSV conversion skipped: %s", exc)

        # Force-kill remaining Procmon
        try:
            subprocess.run(["taskkill", "/f", "/im", os.path.basename(exe)],
                           capture_output=True, timeout=10)
        except Exception:
            pass

        # Parse CSV → sample-filtered summary
        if os.path.isfile(csv_file):
            summary = self._parse_procmon_csv(csv_file)
            with open(summary_file, "w", encoding="utf-8") as fh:
                json.dump(summary, fh, indent=2)
            collected_files.append(summary_file)
            log.info("Procmon summary → %s (%d sample events of %d total)",
                     summary_file, summary.get("sample_events", 0),
                     summary.get("total_rows", 0))
        else:
            log.warning("No Procmon CSV available for parsing")

        return {
            "collector": self.name,
            "status": "ok" if collected_files else "no_data",
            "files": collected_files,
        }

    def _parse_procmon_csv(self, csv_path: str) -> Dict[str, Any]:
        """Parse Procmon CSV, filter to sample process events, build summary."""
        sample_lower = (self._sample_proc or "").lower()

        file_ops: Dict[str, List[str]] = {}
        reg_ops: Dict[str, List[str]] = {}
        net_ops: List[Dict] = []
        proc_ops: List[Dict] = []
        sample_count = 0
        total_count = 0

        sensitive_file_reads: List[str] = []
        general_file_reads: List[str] = []
        sensitive_reg_queries: List[str] = []
        general_reg_queries: List[str] = []

        # Sensitive target heuristics for read prioritization
        _SENSITIVE_FILE_INDICATORS = (
            r"\desktop", r"\documents", r"\downloads", r"\pictures", r"\videos",
            r"\user data", r"\mozilla\firefox", r"\opera software",
            r"\.ssh", r"\.aws", r"\.azure", r"\.kube", r"\.git-credentials",
            r"\bitcoin", r"\ethereum", r"\exodus", r"\atomic", r"\electrum", "wallet.dat",
            r"\config\sam", r"\config\system", r"\config\security", r"\drivers\etc\hosts",
            r"\1password", r"\bitwarden", r"\keepass", ".kdbx", ".key", ".pem", ".rdp", ".ovpn",
            r"\appdata\local\temp", r"\appdata\roaming", r"\samples",
        )
        _BENIGN_SYSTEM_PREFIXES = (
            r"c:\windows\system32", r"c:\windows\syswow64", r"c:\windows\microsoft.net",
            r"c:\windows\assembly", r"c:\windows\winsxs", r"c:\windows\globalization",
            r"c:\windows\fonts", r"c:\windows\prefetch",
        )
        _SENSITIVE_REG_INDICATORS = (
            r"\currentversion\run", r"\currentversion\runonce", r"\startupapproved",
            r"\windows defender", r"\antivirusproduct", r"\firewallpolicy", r"\securityhealth",
            r"\policies\system", r"\winlogon", r"\internet settings",
            r"\systembiosversion", r"\videobiosversion", r"\centralprocessor",
            r"\cryptography\machineguid", r"\currentcontrolset\services",
        )

        try:
            with open(csv_path, "r", encoding="utf-8-sig",
                       errors="replace") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    total_count += 1
                    pname = (row.get("Process Name") or "").lower()
                    if sample_lower and sample_lower not in pname:
                        continue
                    sample_count += 1

                    op = row.get("Operation", "")
                    path = row.get("Path", "")
                    result_val = row.get("Result", "")
                    detail = row.get("Detail", "")

                    if any(k in op for k in ("File", "Create", "Write",
                                             "Read", "Close", "Delete",
                                             "Directory", "Flush")):
                        bucket = file_ops.setdefault(op, [])
                        if path and path not in bucket:
                            if "Read" in op:
                                path_lower = path.lower()
                                if any(ind in path_lower for ind in _SENSITIVE_FILE_INDICATORS) and path not in sensitive_file_reads and len(sensitive_file_reads) < 80:
                                    sensitive_file_reads.append(path)
                                elif not any(path_lower.startswith(pre) for pre in _BENIGN_SYSTEM_PREFIXES) and path not in general_file_reads and len(general_file_reads) < 50:
                                    general_file_reads.append(path)
                            if len(bucket) < 80:
                                bucket.append(path)
                    elif "Reg" in op:
                        bucket = reg_ops.setdefault(op, [])
                        if path and path not in bucket:
                            if any(k in op for k in ("QueryValue", "OpenKey", "QueryKey", "EnumerateValue", "EnumerateKey")):
                                path_lower = path.lower()
                                if any(ind in path_lower for ind in _SENSITIVE_REG_INDICATORS) and path not in sensitive_reg_queries and len(sensitive_reg_queries) < 80:
                                    sensitive_reg_queries.append(path)
                                elif path not in general_reg_queries and len(general_reg_queries) < 50:
                                    general_reg_queries.append(path)
                            if len(bucket) < 80:
                                bucket.append(path)
                    elif any(k in op for k in ("TCP", "UDP")):
                        if len(net_ops) < 50:
                            net_ops.append({"op": op, "path": path,
                                            "result": result_val})
                    elif any(k in op for k in ("Process", "Thread",
                                               "Load Image")):
                        if len(proc_ops) < 50:
                            proc_ops.append({"op": op, "path": path,
                                             "detail": detail})
        except Exception as exc:
            log.warning("Procmon CSV parse error: %s", exc)
            return {"parse_error": str(exc)}

        # Build notable operations: writes, creates, deletes, AND sensitive reads
        interesting_file = {}
        for op, paths in file_ops.items():
            if any(k in op for k in ("Write", "Create", "Delete",
                                     "SetDisposition", "SetRename")):
                interesting_file[op] = paths

        # Populate notable ReadFile: sensitive reads first, followed by general reads
        combined_file_reads = sensitive_file_reads + [p for p in general_file_reads if p not in sensitive_file_reads]
        if combined_file_reads:
            interesting_file["ReadFile"] = combined_file_reads[:80]
        elif "ReadFile" in file_ops:
            interesting_file["ReadFile"] = file_ops["ReadFile"][:80]

        interesting_reg = {}
        for op, paths in reg_ops.items():
            if any(k in op for k in ("SetValue", "CreateKey",
                                     "DeleteKey", "DeleteValue")):
                interesting_reg[op] = paths

        # Populate notable RegQueryValue: sensitive queries first, followed by general queries
        combined_reg_queries = sensitive_reg_queries + [p for p in general_reg_queries if p not in sensitive_reg_queries]
        if combined_reg_queries:
            interesting_reg["RegQueryValue"] = combined_reg_queries[:80]
        elif "RegQueryValue" in reg_ops:
            interesting_reg["RegQueryValue"] = reg_ops["RegQueryValue"][:80]

        return {
            "sample_process": self._sample_proc or "unknown",
            "total_rows": total_count,
            "sample_events": sample_count,
            "file_activity": {
                "notable": interesting_file,
                "sensitive_reads": sensitive_file_reads,
                "all_ops": {o: len(p) for o, p in file_ops.items()},
            },
            "registry_activity": {
                "notable": interesting_reg,
                "sensitive_queries": sensitive_reg_queries,
                "all_ops": {o: len(p) for o, p in reg_ops.items()},
            },
            "network_activity": net_ops,
            "process_activity": proc_ops,
        }



class ScreenshotCollector(BaseCollector):
    """Active screenshot capture during sample execution.

    Takes periodic screenshots using PowerShell + System.Drawing.
    Supports start/stop lifecycle for integration with execution flow.
    The capture runs in a background thread at a configurable interval.
    """

    name = "screenshots"

    def __init__(self, workdir: str) -> None:
        super().__init__(workdir)
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._interval: int = 5
        self._sample_name: Optional[str] = None
        self._captured_files: List[str] = []

    def is_available(self) -> bool:
        """Available on Windows where PowerShell can use System.Drawing."""
        return os.name == "nt"

    def start_capture(
        self, interval: int = 5, sample_name: Optional[str] = None
    ) -> None:
        """Start taking screenshots at the given interval (seconds).

        If sample_name is provided, attempts to capture only the application's window.
        """
        self._interval = max(2, interval)
        self._sample_name = sample_name
        self._stop_event.clear()
        self._captured_files = []
        os.makedirs(self.output_dir, exist_ok=True)

        self._capture_thread = threading.Thread(
            target=self._capture_loop, daemon=True
        )
        self._capture_thread.start()
        log.info(
            "Screenshot capture started (every %ds, target app: %s)",
            self._interval,
            self._sample_name or "full screen",
        )

    def stop_capture(self) -> None:
        """Stop the screenshot capture loop."""
        self._stop_event.set()
        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=15)
        self._capture_thread = None
        log.info(
            "Screenshot capture stopped (%d captured)",
            len(self._captured_files),
        )

    def _capture_loop(self) -> None:
        """Background loop that captures screenshots at the configured interval."""
        idx = 0
        sample_stem = ""
        if self._sample_name:
            sample_stem = os.path.splitext(os.path.basename(self._sample_name))[0]

        while not self._stop_event.is_set():
            try:
                ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
                filename = "screenshot_{idx:03d}_{ts}.png".format(idx=idx, ts=ts)
                filepath = os.path.join(self.output_dir, filename)
                filepath_escaped = filepath.replace("'", "''")
                stem_escaped = sample_stem.replace("'", "''")

                ps_cmd = (
                    "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
                    "$targetStem = '" + stem_escaped + "'; "
                    "$targetHwnd = [IntPtr]::Zero; $rect = $null; "
                    "if ($targetStem) { "
                    "  Add-Type @'\n"
                    "  using System;\n"
                    "  using System.Runtime.InteropServices;\n"
                    "  public class Win32Win {\n"
                    "    [DllImport(\"user32.dll\")]\n"
                    "    [return: MarshalAs(UnmanagedType.Bool)]\n"
                    "    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);\n"
                    "    [DllImport(\"user32.dll\")]\n"
                    "    [return: MarshalAs(UnmanagedType.Bool)]\n"
                    "    public static extern bool IsWindowVisible(IntPtr hWnd);\n"
                    "    [StructLayout(LayoutKind.Sequential)]\n"
                    "    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }\n"
                    "  }\n"
                    "'@ -ErrorAction SilentlyContinue; "
                    "  $procs = Get-Process -ErrorAction SilentlyContinue | Where-Object { "
                    "    ($_.ProcessName -like \"*$targetStem*\" -or $_.MainWindowTitle -ne \"\") -and $_.MainWindowHandle -ne 0 "
                    "  }; "
                    "  if ($procs) { foreach ($p in $procs) { "
                    "    if ([Win32Win]::IsWindowVisible($p.MainWindowHandle)) { "
                    "      $r = New-Object Win32Win+RECT; "
                    "      if ([Win32Win]::GetWindowRect($p.MainWindowHandle, [ref]$r)) { "
                    "        $w = $r.Right - $r.Left; $h = $r.Bottom - $r.Top; "
                    "        if ($w -gt 50 -and $h -gt 50) { $targetHwnd = $p.MainWindowHandle; $rect = $r; break } "
                    "      } "
                    "    } "
                    "  }} "
                    "}; "
                    "if ($targetHwnd -ne [IntPtr]::Zero -and $rect -ne $null) { "
                    "  $w = [Math]::Max(10, $rect.Right - $rect.Left); $h = [Math]::Max(10, $rect.Bottom - $rect.Top); "
                    "  $bmp = New-Object System.Drawing.Bitmap($w, $h); "
                    "  $g = [System.Drawing.Graphics]::FromImage($bmp); "
                    "  $g.CopyFromScreen($rect.Left, $rect.Top, 0, 0, (New-Object System.Drawing.Size($w, $h))); "
                    "  $bmp.Save('" + filepath_escaped + "', [System.Drawing.Imaging.ImageFormat]::Png); "
                    "  $g.Dispose(); $bmp.Dispose(); "
                    "} else { "
                    "  $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
                    "  $bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height); "
                    "  $g = [System.Drawing.Graphics]::FromImage($bmp); "
                    "  $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size); "
                    "  $bmp.Save('" + filepath_escaped + "', [System.Drawing.Imaging.ImageFormat]::Png); "
                    "  $g.Dispose(); $bmp.Dispose(); "
                    "}"
                )

                result = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-NonInteractive",
                     "-Command", ps_cmd],
                    capture_output=True, text=True, timeout=15,
                )

                if result.returncode == 0 and os.path.isfile(filepath):
                    self._captured_files.append(filepath)
                    log.info("Screenshot %d → %s", idx, filename)
                    idx += 1
                else:
                    log.warning(
                        "Screenshot %d failed: %s",
                        idx,
                        (result.stderr or "")[:200],
                    )
            except Exception as exc:
                log.warning("Screenshot error: %s", exc)

            # Wait for next interval, checking stop_event frequently
            self._stop_event.wait(timeout=self._interval)

    def collect(self) -> Dict[str, Any]:
        """Return the list of captured screenshot files."""
        image_exts = (".png", ".jpg", ".jpeg", ".bmp")
        try:
            on_disk = [
                os.path.join(self.output_dir, f)
                for f in sorted(os.listdir(self.output_dir))
                if f.lower().endswith(image_exts)
            ]
        except FileNotFoundError:
            on_disk = []

        all_files = sorted(set(self._captured_files + on_disk))

        if all_files:
            log.info("Screenshots: %d files", len(all_files))
            return {"collector": self.name, "status": "ok", "files": all_files}

        log.info("No screenshots captured")
        return {"collector": self.name, "status": "no_data", "files": []}


class TcpvconCollector(BaseCollector):
    """Snapshot active TCP/UDP connections using tcpvcon64.

    Captures the network connection state at the moment of collection.
    Useful for detecting connections opened by the executed sample.
    """

    name = "tcpvcon"

    _SEARCH_PATHS = [
        r"C:\IsoLens\tools\tcpvcon64.exe",
        r"C:\IsoLens\tools\tcpvcon.exe",
        r"C:\Tools\tcpvcon64.exe",
    ]

    def _find_exe(self) -> Optional[str]:
        for p in self._SEARCH_PATHS:
            if os.path.isfile(p):
                return p
        return None

    def is_available(self) -> bool:
        return self._find_exe() is not None

    def collect(self) -> Dict[str, Any]:
        exe = self._find_exe()
        if not exe:
            log.warning("tcpvcon not found — skipping")
            return {"collector": self.name, "status": "unavailable", "files": []}

        output_file = os.path.join(self.output_dir, "tcpvcon_snapshot.csv")
        try:
            result = subprocess.run(
                [exe, "-accepteula", "-a", "-c"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                header = lines[0] if lines else ""
                sample_lower = (self._sample_proc or "").lower()
                filtered = [
                    l for l in lines[1:] if sample_lower and sample_lower in l.lower()
                ]
                if filtered:
                    output_lines = [header] + filtered
                else:
                    # Filter out local loopback and agent port 9090
                    output_lines = [header] + [
                        l for l in lines[1:] if not (":9090" in l or "127.0.0.1" in l)
                    ]
                with open(output_file, "w", encoding="utf-8") as fh:
                    fh.write("\n".join(output_lines))
                log.info("tcpvcon → %s (%d connections)",
                         output_file, max(0, len(output_lines) - 1))
                return {"collector": self.name, "status": "ok",
                        "files": [output_file]}
            log.warning("tcpvcon returned no data")
            return {"collector": self.name, "status": "no_data", "files": []}
        except Exception as exc:
            log.error("tcpvcon failed: %s", exc)
            return {"collector": self.name, "status": "error",
                    "error": str(exc), "files": []}


class HandleCollector(BaseCollector):
    """Snapshot open file and registry handles using handle64.

    Captures all handles held by running processes at the moment of
    collection.  Helps identify files/registry keys accessed by the sample.
    """

    name = "handle"

    _SEARCH_PATHS = [
        r"C:\IsoLens\tools\handle64.exe",
        r"C:\IsoLens\tools\handle.exe",
        r"C:\Tools\handle64.exe",
    ]

    def _find_exe(self) -> Optional[str]:
        for p in self._SEARCH_PATHS:
            if os.path.isfile(p):
                return p
        return None

    def is_available(self) -> bool:
        return self._find_exe() is not None

    def collect(self) -> Dict[str, Any]:
        exe = self._find_exe()
        if not exe:
            log.warning("handle64 not found — skipping")
            return {"collector": self.name, "status": "unavailable", "files": []}

        output_file = os.path.join(self.output_dir, "handle_snapshot.txt")
        try:
            cmd = [exe, "-accepteula"]
            if self._sample_proc:
                cmd.extend(["-p", self._sample_proc])
            else:
                cmd.append("-u")
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=30)
            stdout = result.stdout.strip()
            # If -p <sample> returned no process (e.g. sample already exited), fallback to system handles
            if (result.returncode != 0 or not stdout or "No matching processes" in stdout) and self._sample_proc:
                log.info("handle -p %s returned no data; capturing open system handles fallback...", self._sample_proc)
                fb_cmd = [exe, "-accepteula"]
                result = subprocess.run(fb_cmd, capture_output=True, text=True, timeout=20)
                stdout = result.stdout.strip()

            if stdout:
                with open(output_file, "w", encoding="utf-8") as fh:
                    fh.write(stdout)
                log.info("handle snapshot → %s (%d bytes)", output_file, len(stdout))
                return {"collector": self.name, "status": "ok",
                        "files": [output_file]}
            log.warning("handle64 returned no data")
            return {"collector": self.name, "status": "no_data", "files": []}
        except Exception as exc:
            log.error("handle failed: %s", exc)
            return {"collector": self.name, "status": "error",
                    "error": str(exc), "files": []}


# ═══════════════════════════════════════════════════════════════════════════
# Agent Core
# ═══════════════════════════════════════════════════════════════════════════

class IsoLensAgent:
    """Orchestrates sample execution and artifact collection.

    Parameters
    ----------
    share_path : str
        Path to the VirtualBox shared folder (e.g. ``\\\\VBOXSVR\\SandboxShare``).
    workdir : str
        Local directory for storing samples and collected artifacts.
    """

    def __init__(self, share_path: str, workdir: str) -> None:
        self.share_path = share_path
        self.workdir = workdir
        self.artifacts_dir = os.path.join(workdir, "artifacts")
        self.samples_dir = os.path.join(workdir, "samples")
        self.state = AgentState()

        os.makedirs(self.artifacts_dir, exist_ok=True)
        os.makedirs(self.samples_dir, exist_ok=True)

        # Initialise collectors
        self.collectors: List[BaseCollector] = [
            SysmonCollector(workdir),
            ProcmonCollector(workdir),
            ScreenshotCollector(workdir),
            TcpvconCollector(workdir),
            HandleCollector(workdir),
        ]

        log.info("Agent initialised  share=%s  workdir=%s", share_path, workdir)
        log.info(
            "Collectors: %s",
            ", ".join(c.name for c in self.collectors),
        )

    # -- introspection --

    def get_collector_info(self) -> List[Dict[str, Any]]:
        """Return name + availability of each collector."""
        return [
            {"name": c.name, "available": c.is_available()}
            for c in self.collectors
        ]

    def list_artifacts(self) -> List[str]:
        """Enumerate all files under the artifacts directory."""
        result: List[str] = []
        if not os.path.isdir(self.artifacts_dir):
            return result
        for root, _dirs, files in os.walk(self.artifacts_dir):
            for fname in files:
                rel = os.path.relpath(
                    os.path.join(root, fname), self.artifacts_dir
                )
                result.append(rel)
        return result

    def ensure_share_path(self) -> str:
        """Verify the shared folder path is online and accessible, re-connecting if needed."""
        try:
            if os.path.isdir(self.share_path):
                return self.share_path
        except Exception:
            pass
        log.warning("Share path %s inaccessible; re-resolving...", self.share_path)
        resolved = resolve_share_path(self.share_path, retries=5, delay=0.5)
        if os.path.isdir(resolved):
            self.share_path = resolved
            log.info("Share path re-resolved to: %s", self.share_path)
        return self.share_path

    # -- execution --

    def execute_sample(
        self, filename: str, timeout: int = 60,
        screenshot_interval: int = 5,
    ) -> Dict[str, Any]:
        """Execute a sample from the shared folder.

        Workflow:
          1. Copy sample from shared folder to local samples dir
          2. Clear Sysmon logs for a clean baseline
          3. Execute the sample (simulate double-click)
          4. Capture screenshots at *screenshot_interval* seconds
          5. Wait for the configured timeout
          6. Run all artifact collectors
          7. Package and export results back to the shared folder
        """
        if self.state.status == AgentState.EXECUTING:
            # State was already set by the HTTP handler — this is expected.
            pass
        else:
            self.state.set_executing(filename)

        self.ensure_share_path()
        sample_src = os.path.join(self.share_path, filename)
        if not os.path.isfile(sample_src):
            # Re-resolve share in case connection was refreshed or drive changed
            self.ensure_share_path()
            sample_src = os.path.join(self.share_path, filename)

        if not os.path.isfile(sample_src):
            self.state.set_error("Sample not found: " + filename)
            return {
                "error": "Sample not found in shared folder: " + filename,
                "status": "not_found",
            }

        log.info("── Execution start: %s (timeout=%ds) ──", filename, timeout)

        try:
            # 0. Cleanup previous artifacts and kill any existing instances
            log.info("Cleaning up artifacts from previous runs...")
            self.cleanup()
            
            sample_basename = os.path.basename(filename)
            try:
                subprocess.run(
                    ["taskkill", "/f", "/im", sample_basename],
                    capture_output=True,
                    timeout=10,
                )
                time.sleep(1)
            except Exception:
                pass  # OK if no matching process exists

            # 1. Copy sample locally
            sample_dst = os.path.join(self.samples_dir, filename)
            shutil.copy2(sample_src, sample_dst)
            log.info("Sample copied → %s", sample_dst)

            # 2. Clear Sysmon logs for a clean baseline
            log.info("Clearing Sysmon logs for clean baseline...")
            try:
                subprocess.run(
                    ["wevtutil", "cl", "Microsoft-Windows-Sysmon/Operational"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                log.info("Sysmon logs cleared")
            except Exception as exc:
                log.warning("Failed to clear Sysmon logs: %s", exc)

            # 2b. Start Procmon fresh so it captures execution behaviour
            log.info("Starting Procmon for behavioural capture...")
            try:
                procmon_exe = None
                for _p in ProcmonCollector._SEARCH_PATHS:
                    if os.path.isfile(_p):
                        procmon_exe = _p
                        break
                if procmon_exe:
                    procmon_pml = os.path.join(
                        self.artifacts_dir, "procmon", "procmon.pml"
                    )
                    os.makedirs(os.path.dirname(procmon_pml), exist_ok=True)
                    if os.path.isfile(procmon_pml):
                        try:
                            os.remove(procmon_pml)
                        except OSError as exc:
                            log.warning("Could not remove stale Procmon backing file: %s", exc)
                    # Kill any leftover Procmon instances first
                    subprocess.run(
                        ["taskkill", "/f", "/im", os.path.basename(procmon_exe)],
                        capture_output=True, timeout=10,
                    )
                    time.sleep(1)
                    subprocess.Popen(
                        [
                            procmon_exe,
                            "/AcceptEula", "/Quiet", "/Minimized",
                            "/BackingFile", procmon_pml,
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    log.info("Procmon started → %s", procmon_pml)
                    time.sleep(3)  # give Procmon time to initialise
                else:
                    log.warning("Procmon executable not found — skipping")
            except Exception as exc:
                log.warning("Failed to start Procmon: %s", exc)

            # 3. Execute sample in the interactive session
            #    Using schtasks /it so GUI windows appear on the desktop
            #    (visible to VBoxManage screenshots from the host).
            log.info("Executing sample: %s", sample_dst)
            schtasks_ok = False
            try:
                task_name = "IsoLensExec"
                subprocess.run(
                    ["schtasks", "/delete", "/tn", task_name, "/f"],
                    capture_output=True, timeout=10,
                )
                tr_cmd = 'cmd /c start "" "{path}"'.format(path=sample_dst)
                create_res = subprocess.run(
                    ["schtasks", "/create", "/tn", task_name,
                     "/tr", tr_cmd, "/sc", "once", "/st", "00:00",
                     "/f", "/it"],
                    capture_output=True, text=True, timeout=15,
                )
                if create_res.returncode == 0:
                    run_res = subprocess.run(
                        ["schtasks", "/run", "/tn", task_name],
                        capture_output=True, text=True, timeout=15,
                    )
                    if run_res.returncode == 0:
                        schtasks_ok = True
                        log.info("Sample launched via schtasks (interactive session)")
                    else:
                        log.warning("schtasks /run failed: %s",
                                    run_res.stderr[:200] if run_res.stderr else "")
                else:
                    log.warning("schtasks /create failed: %s",
                                create_res.stderr[:200] if create_res.stderr else "")
            except Exception as exc:
                log.warning("schtasks launch failed: %s", exc)

            if not schtasks_ok:
                log.info("Falling back to cmd /c start (session 0)")
                try:
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", sample_dst],
                        creationflags=getattr(
                            subprocess, "CREATE_NEW_PROCESS_GROUP", 0
                        ),
                    )
                    log.info("Sample launched via 'cmd /c start'")
                except Exception as exc:
                    log.warning(
                        "cmd /c start failed (%s), trying os.startfile...", exc
                    )
                    if hasattr(os, "startfile"):
                        os.startfile(sample_dst)  # type: ignore[attr-defined]
                    else:
                        log.warning(
                            "Non-Windows platform — skipping actual execution "
                            "(agent is designed for Windows VMs)"
                        )

            # 3b. Start screenshot capture (captures GUI as it appears)
            screenshot_c = None
            for _c in self.collectors:
                if _c.name == "screenshots" and hasattr(_c, "start_capture"):
                    screenshot_c = _c
                    break
            if screenshot_c:
                screenshot_c.start_capture(
                    interval=screenshot_interval, sample_name=filename
                )

            # 4. Wait for behaviour timeout
            log.info("Waiting %ds for behaviour collection...", timeout)
            time.sleep(timeout)

            # 4b. Stop captures (flush data before collecting)
            if screenshot_c:
                screenshot_c.stop_capture()

            # 5. Collect artifacts (sample-filtered)
            self.state.set_collecting()
            collection = self._run_collectors(sample_name=filename)

            # 6. Package & export
            package = self._package_results(filename, timeout, collection)

            self.state.set_idle()
            log.info("── Execution complete: %s ──", filename)

            return {
                "status": "complete",
                "sample": filename,
                "timeout": timeout,
                "collection": collection,
                "package": package,
            }

        except Exception as exc:
            self.state.set_error(str(exc))
            log.error("Execution failed: %s", exc)
            return {"status": "failed", "error": str(exc)}

    # -- collection (without execution) --

    def collect_only(self) -> Dict[str, Any]:
        """Run all collectors without executing any sample."""
        if self.state.status == AgentState.EXECUTING:
            return {"error": "Cannot collect while executing"}

        self.state.set_collecting()
        results = self._run_collectors()
        self.state.set_idle()
        return {"collection": results}

    # -- cleanup --

    def cleanup(self) -> None:
        """Remove all collected artifacts.

        Uses ``shutil.rmtree`` with ``ignore_errors`` so that files locked
        by running tools (e.g. Procmon .pml) do not crash the handler.
        """
        if os.path.isdir(self.artifacts_dir):
            shutil.rmtree(self.artifacts_dir, ignore_errors=True)
            os.makedirs(self.artifacts_dir, exist_ok=True)
        log.info("Artifacts cleaned up")

    # -- internal helpers --

    def _run_collectors(self, sample_name: Optional[str] = None) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for collector in self.collectors:
            log.info("Running collector: %s", collector.name)
            os.makedirs(collector.output_dir, exist_ok=True)
            if sample_name:
                collector.set_sample(sample_name)
            try:
                results.append(collector.collect())
            except Exception as exc:
                log.error("Collector %s failed: %s", collector.name, exc)
                results.append({
                    "collector": collector.name,
                    "status": "error",
                    "error": str(exc),
                    "files": [],
                })
        return results

    def _package_results(
        self,
        sample_name: str,
        timeout: int,
        collection: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Zip collected artifacts and copy the archive to the shared folder."""
        ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
        base = os.path.splitext(sample_name)[0]
        zip_name = "results_{base}_{ts}.zip".format(base=base, ts=ts)
        zip_path = os.path.join(self.workdir, zip_name)

        # Build the concise analysis summary (primary AI input)
        summary_path = self._build_analysis_summary(
            sample_name, timeout, collection
        )

        # Gather every file the collectors reported
        all_files: List[str] = []
        for entry in collection:
            all_files.extend(entry.get("files", []))

        # Write a metadata sidecar
        meta_path = os.path.join(self.artifacts_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "sample": sample_name,
                    "timestamp": ts,
                    "agent_version": AGENT_VERSION,
                    "collectors": collection,
                },
                fh,
                indent=2,
            )
        all_files.append(meta_path)
        all_files.append(summary_path)

        if not all_files:
            log.info("No artifacts to package")
            return None

        # Build zip — skip huge raw PML / raw Procmon CSV / PCAP (summaries suffice, tcpvcon CSV kept)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fpath in all_files:
                fname = os.path.basename(fpath).lower()
                if os.path.isfile(fpath) and not (
                    fname.endswith(".pml")
                    or fname.endswith(".pcap")
                    or fname == "procmon.csv"
                ):
                    arcname = os.path.relpath(fpath, self.workdir)
                    zf.write(fpath, arcname)

        # Copy to shared folder
        self.ensure_share_path()
        share_dest = os.path.join(self.share_path, zip_name)
        try:
            shutil.copy2(zip_path, share_dest)
            log.info("Results package → %s", share_dest)
        except OSError as exc:
            log.warning("Initial copy to %s failed: %s. Refreshing share...", share_dest, exc)
            self.ensure_share_path()
            share_dest = os.path.join(self.share_path, zip_name)
            try:
                shutil.copy2(zip_path, share_dest)
                log.info("Results package → %s (after refresh)", share_dest)
            except OSError as exc2:
                log.error("Failed to copy package to share after refresh: %s", exc2)

        return zip_name

    def _build_analysis_summary(
        self,
        sample_name: str,
        timeout: int,
        collection: List[Dict[str, Any]],
    ) -> str:
        """Aggregate all collector outputs into one concise AI-friendly JSON."""
        summary: Dict[str, Any] = {
            "sample": sample_name,
            "analysis_timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "execution_timeout_sec": timeout,
            "agent_version": AGENT_VERSION,
        }

        for entry in collection:
            name = entry.get("collector", "")
            for fpath in entry.get("files", []):
                if fpath.endswith("_summary.json"):
                    try:
                        with open(fpath, "r", encoding="utf-8") as fh:
                            summary[name] = json.load(fh)
                    except Exception as exc:
                        summary[name] = {"read_error": str(exc)}
                elif fpath.endswith(".csv") and name == "tcpvcon":
                    try:
                        with open(fpath, "r", encoding="utf-8") as fh:
                            summary["tcpvcon"] = {"raw": fh.read()[:20000]}
                    except Exception:
                        pass
                elif fpath.endswith(".txt") and name == "handle":
                    try:
                        with open(fpath, "r", encoding="utf-8") as fh:
                            txt = fh.read()
                            if len(txt) > 30000:
                                txt = txt[:30000] + "\n...(truncated)"
                            summary["handle"] = {"snapshot": txt}
                    except Exception:
                        pass

            # Record screenshot info (files are PNGs, not JSON summaries)
            if name == "screenshots" and entry.get("files"):
                summary["screenshots"] = {
                    "count": len(entry["files"]),
                    "files": [os.path.basename(f) for f in entry["files"]],
                }

        out_path = os.path.join(self.artifacts_dir, "analysis_summary.json")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
        log.info("Analysis summary → %s", out_path)
        return out_path


# ═══════════════════════════════════════════════════════════════════════════
# HTTP Handler
# ═══════════════════════════════════════════════════════════════════════════

class AgentHTTPHandler(BaseHTTPRequestHandler):
    """Minimal JSON API handler for the agent."""

    # These class attributes are set dynamically by create_server()
    agent: IsoLensAgent
    shutdown_event: threading.Event

    # Redirect default logging into our logger
    def log_message(self, fmt: str, *args: Any) -> None:
        log.info("HTTP  %s", fmt % args)

    # -- helpers --

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def _ok(self, data: Any) -> None:
        self._send_json({"status": "ok", "data": data})

    def _err(self, msg: str, code: int = 400) -> None:
        self._send_json({"status": "error", "error": msg}, code)

    # -- routing --

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/api/artifact?") or self.path.startswith("/api/artifact/"):
            self._get_artifact_content()
            return

        routes: Dict[str, Any] = {
            "/api/status": self._get_status,
            "/api/collectors": self._get_collectors,
            "/api/artifacts": self._get_artifacts,
        }
        handler = routes.get(self.path)
        if handler:
            try:
                handler()
            except Exception as exc:
                log.exception("GET %s handler error", self.path)
                self._err(f"Internal error: {exc}", 500)
        else:
            self._err("Not found", 404)

    def _get_artifact_content(self) -> None:
        """Download or read a specific artifact file."""
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        rel_path = qs.get("file", [""])[0]
        if not rel_path:
            self._err("Missing 'file' parameter", 400)
            return
        safe_rel = os.path.normpath(rel_path).lstrip("/\\")
        cand1 = os.path.join(self.agent.artifacts_dir, safe_rel)
        cand2 = os.path.join(self.agent.workdir, safe_rel)
        target = cand1 if os.path.isfile(cand1) else cand2
        if not os.path.isfile(target):
            self._err(f"Artifact not found: {rel_path}", 404)
            return
        try:
            with open(target, "rb") as fh:
                data = fh.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            self._err(f"Failed to read file: {exc}", 500)

    def do_POST(self) -> None:  # noqa: N802
        routes: Dict[str, Any] = {
            "/api/execute": self._post_execute,
            "/api/collect": self._post_collect,
            "/api/cleanup": self._post_cleanup,
            "/api/shutdown": self._post_shutdown,
        }
        handler = routes.get(self.path)
        if handler:
            try:
                handler()
            except Exception as exc:
                log.exception("POST %s handler error", self.path)
                self._err(f"Internal error: {exc}", 500)
        else:
            self._err("Not found", 404)

    # -- GET handlers --

    def _get_status(self) -> None:
        data = self.agent.state.to_dict()
        data["agent_version"] = AGENT_VERSION
        data["platform"] = platform.platform()
        data["collectors"] = self.agent.get_collector_info()
        self._ok(data)

    def _get_collectors(self) -> None:
        self._ok({"collectors": self.agent.get_collector_info()})

    def _get_artifacts(self) -> None:
        arts = self.agent.list_artifacts()
        self._ok({"artifacts": arts, "count": len(arts)})

    # -- POST handlers --

    def _post_execute(self) -> None:
        if self.agent.state.status == AgentState.EXECUTING:
            self._err("Agent is already executing a sample", 409)
            return

        body = self._read_body()
        filename = body.get("filename")
        timeout = body.get("timeout", 60)
        screenshot_interval = body.get("screenshot_interval", 5)

        if not filename:
            self._err("Missing required field: 'filename'")
            return

        # Execute in background thread so the HTTP server stays responsive
        # Set state BEFORE starting thread to prevent race with polling.
        self.agent.state.set_executing(filename)

        def _bg() -> None:
            result = self.agent.execute_sample(
                filename, timeout=timeout,
                screenshot_interval=screenshot_interval,
            )
            log.info(
                "Background execution finished: %s",
                json.dumps(result, indent=2, default=str),
            )

        threading.Thread(target=_bg, daemon=True).start()

        self._ok({
            "message": "Execution started for '{f}'".format(f=filename),
            "timeout": timeout,
        })

    def _post_collect(self) -> None:
        if self.agent.state.status == AgentState.EXECUTING:
            self._err("Cannot collect while executing", 409)
            return
        result = self.agent.collect_only()
        self._ok(result)

    def _post_cleanup(self) -> None:
        self.agent.cleanup()
        self._ok({"message": "Artifacts cleaned up"})

    def _post_shutdown(self) -> None:
        self._ok({"message": "Agent shutting down"})
        self.shutdown_event.set()


# ═══════════════════════════════════════════════════════════════════════════
# Server Factory
# ═══════════════════════════════════════════════════════════════════════════

def create_server(
    agent: IsoLensAgent,
    host: str = "0.0.0.0",
    port: int = 9090,
) -> HTTPServer:
    """Build an HTTPServer bound to *host:port* with the given agent."""
    shutdown_event = threading.Event()

    # Dynamically create a handler subclass with agent & event attached
    handler = type(
        "BoundAgentHandler",
        (AgentHTTPHandler,),
        {"agent": agent, "shutdown_event": shutdown_event},
    )

    server = _NoFQDNHTTPServer((host, port), handler)
    server.shutdown_event = shutdown_event  # type: ignore[attr-defined]
    return server


# ═══════════════════════════════════════════════════════════════════════════
# CLI & Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="IsoLens Guest Agent — sandbox VM HTTP service",
    )
    p.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind address (default: 0.0.0.0)",
    )
    p.add_argument(
        "--port",
        type=int,
        default=9090,
        help="Bind port (default: 9090)",
    )
    p.add_argument(
        "--share",
        default=r"\\VBOXSVR\SandboxShare",
        help=r"VirtualBox shared folder UNC path "
             r"(default: \\VBOXSVR\SandboxShare)",
    )
    p.add_argument(
        "--workdir",
        default=r"C:\IsoLens",
        help=r"Local working directory (default: C:\IsoLens)",
    )
    return p


def _mount_windows_share(preferred_drive: str = "Z:") -> Optional[str]:
    """Mount or refresh VirtualBox shared folder on Windows across drive letters."""
    if os.name != "nt":
        return None

    # Order of drive letters to try
    preferred = preferred_drive.rstrip(":\\").upper() + ":"
    drives = [preferred]
    for d in ["Z:", "Y:", "X:", "S:", "V:", "W:"]:
        if d not in drives:
            drives.append(d)

    # 1. Quick check: is any drive letter already accessible?
    for drive in drives:
        root = drive + "\\"
        try:
            if os.path.isdir(root):
                return root
        except Exception:
            pass

    # 2. Try net use on candidate drive letters
    for drive in drives:
        root = drive + "\\"
        try:
            res = subprocess.run(
                ["net", "use", drive, r"\\VBoxSvr\SandboxShare", "/persistent:yes"],
                capture_output=True,
                text=True,
                timeout=6,
            )
            if res.returncode == 0 and os.path.isdir(root):
                log.info("Mapped shared folder to %s", root)
                return root
            err_lower = (res.stderr or "").lower()
            if "85" in (res.stderr or "") or "already in use" in err_lower or "conflict" in err_lower:
                subprocess.run(["net", "use", drive, "/delete", "/y"], capture_output=True, timeout=5)
                res2 = subprocess.run(
                    ["net", "use", drive, r"\\VBoxSvr\SandboxShare", "/persistent:yes"],
                    capture_output=True,
                    text=True,
                    timeout=6,
                )
                if res2.returncode == 0 and os.path.isdir(root):
                    log.info("Remapped shared folder to %s after clearing conflict", root)
                    return root
        except Exception as exc:
            log.debug("Error mapping drive %s: %s", drive, exc)

    return None


def resolve_share_path(
    configured_path: Optional[str] = None,
    retries: int = 15,
    delay: float = 1.0,
) -> str:
    """Resolve an accessible shared folder path, checking multiple candidates and retrying.

    VirtualBox shared folders can be mounted as a drive letter (e.g. Z:\\ or Y:\\) or accessed
    via UNC path (e.g. \\\\VBOXSVR\\SandboxShare or \\\\vboxsrv\\SandboxShare). On guest VM
    boot or snapshot restore, the network redirector may take several seconds to initialize,
    or the Z: drive mapping may be disconnected or in conflict (error 85).

    This function tests candidates in order, attempts automatic re-mapping on Windows
    across multiple drive letters, retries until the provider is online, and returns the first verified path.
    """
    candidates: List[str] = []
    if configured_path:
        norm = configured_path.strip().rstrip("/\\")
        if norm.endswith(":") and len(norm) == 2:
            norm = norm + "\\"
        candidates.append(norm)
        if norm != configured_path:
            candidates.append(configured_path)

    # Prioritize drive letters on Windows (UNC paths to VBoxSvr without mapping often fail)
    if os.name == "nt":
        for d in [r"Z:\\", r"Z:", r"Y:\\", r"Y:", r"X:\\", r"X:", r"S:\\", r"S:"]:
            if d not in candidates:
                candidates.append(d)
    else:
        for p in [r"\\VBOXSVR\SandboxShare", r"\\vboxsrv\SandboxShare", r"Z:\\", r"Z:"]:
            if p not in candidates:
                candidates.append(p)

    for attempt in range(1, max(1, retries) + 1):
        for cand in candidates:
            try:
                if os.path.isdir(cand):
                    log.info("Shared folder verified at: %s", cand)
                    return cand
            except Exception as e:
                log.debug("Error probing candidate %s: %s", cand, e)

        # On Windows, try mounting via net use
        if os.name == "nt":
            pref = candidates[0] if candidates else "Z:"
            mounted = _mount_windows_share(preferred_drive=pref)
            if mounted and os.path.isdir(mounted):
                log.info("Shared folder verified after net use: %s", mounted)
                return mounted

        if attempt < retries:
            log.warning(
                "Shared folder not yet accessible (attempt %d/%d). Retrying in %.1fs...",
                attempt,
                retries,
                delay,
            )
            time.sleep(delay)

    fallback = candidates[0] if candidates else (r"Z:\\" if os.name == "nt" else r"\\VBOXSVR\SandboxShare")
    log.warning(
        "Could not verify shared folder after %d attempts; using fallback: %s",
        retries,
        fallback,
    )
    return fallback


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    # Automatically resolve shared folder path (handles Z:, \\VBOXSVR\SandboxShare, and boot retries)
    share_path = resolve_share_path(args.share)
    if not os.path.isdir(share_path):
        log.warning(
            "Shared folder not immediately accessible: %s (requested: %s). "
            "Agent starting HTTP server and will re-resolve share on-demand.",
            share_path,
            args.share,
        )

    os.makedirs(args.workdir, exist_ok=True)

    agent = IsoLensAgent(share_path=share_path, workdir=args.workdir)
    server = create_server(agent, host=args.host, port=args.port)

    log.info("=" * 60)
    log.info("  IsoLens Agent v%s", AGENT_VERSION)
    log.info("  Listening on  http://%s:%d", args.host, args.port)
    log.info("  Shared folder %s", share_path)
    log.info("  Working dir   %s", args.workdir)
    log.info("=" * 60)

    # Run in a thread so we can monitor the shutdown event
    srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
    srv_thread.start()

    try:
        while not server.shutdown_event.is_set():  # type: ignore[attr-defined]
            time.sleep(0.5)
    except KeyboardInterrupt:
        log.info("Interrupted — shutting down")

    server.shutdown()
    log.info("Agent stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
