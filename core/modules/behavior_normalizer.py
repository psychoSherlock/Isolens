"""behavior_normalizer.py - File & Registry Behavioral Normalization Module.

Normalizes heterogeneous filesystem and registry events from Procmon and Sysmon,
filters out benign Windows OS noise, categorizes operations into structured
security buckets (created, written, read, deleted, persistence, defense tampering),
and extracts behavioral Indicators of Compromise (IOCs) and MITRE ATT&CK mappings.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

log = logging.getLogger("isolens.behavior_normalizer")

# ---------------------------------------------------------------------------
# Sensitive Target Definitions & Heuristics
# ---------------------------------------------------------------------------

# Sensitive file path patterns indicating user data, credentials, or staged malware
SENSITIVE_FILE_PATTERNS = (
    r"\desktop",
    r"\documents",
    r"\downloads",
    r"\pictures",
    r"\videos",
    r"\user data",
    r"\mozilla\firefox",
    r"\opera software",
    r"\.ssh",
    r"\.aws",
    r"\.azure",
    r"\.kube",
    r"\.git-credentials",
    r"\bitcoin",
    r"\ethereum",
    r"\exodus",
    r"\atomic",
    r"\electrum",
    "wallet.dat",
    r"\config\sam",
    r"\config\system",
    r"\config\security",
    r"\drivers\etc\hosts",
    r"\1password",
    r"\bitwarden",
    r"\keepass",
    ".kdbx",
    ".key",
    ".pem",
    ".rdp",
    ".ovpn",
    r"\appdata\local\temp",
    r"\appdata\roaming",
    r"\samples",
)

# Benign system file directories filtered out from general read listings
BENIGN_SYSTEM_PREFIXES = (
    r"c:\windows\system32",
    r"c:\windows\syswow64",
    r"c:\windows\microsoft.net",
    r"c:\windows\assembly",
    r"c:\windows\winsxs",
    r"c:\windows\globalization",
    r"c:\windows\fonts",
    r"c:\windows\prefetch",
)

# Registry persistence targets (MITRE T1547)
PERSISTENCE_REG_PATTERNS = (
    r"\currentversion\run",
    r"\currentversion\runonce",
    r"\startupapproved",
    r"\winlogon\shell",
    r"\winlogon\userinit",
    r"\currentversion\windows\load",
    r"\currentversion\windows\run",
    r"\environment\userinitmprlogonscript",
    r"\currentcontrolset\services",
)

# Registry security defense tampering targets (MITRE T1562)
DEFENSE_TAMPERING_REG_PATTERNS = (
    r"\windows defender",
    r"\antivirusproduct",
    r"\firewallpolicy",
    r"\securityhealth",
    r"\policies\system\enablelua",
    r"\policies\system\disableregistrytools",
    r"\policies\system\disablestartupapplications",
    r"\policies\microsoft\windows defender",
)

# Registry reconnaissance / system discovery targets (MITRE T1082)
RECON_REG_PATTERNS = (
    r"\systembiosversion",
    r"\videobiosversion",
    r"\centralprocessor",
    r"\cryptography\machineguid",
    r"\software\microsoft\windows nt\currentversion",
    r"\internet settings\proxyserver",
)


# ---------------------------------------------------------------------------
# Classification & Normalization Helpers
# ---------------------------------------------------------------------------

def is_sensitive_file(path: str) -> bool:
    """Check if file path targets user data, credentials, or sensitive directories."""
    if not path:
        return False
    lower = path.lower()
    return any(p in lower for p in SENSITIVE_FILE_PATTERNS)


def is_benign_system_file(path: str) -> bool:
    """Check if path is a standard Windows OS / framework runtime file."""
    if not path:
        return False
    lower = path.lower()
    return any(lower.startswith(p) for p in BENIGN_SYSTEM_PREFIXES)


def classify_registry_key(key: str) -> Dict[str, bool]:
    """Classify a registry key into behavioral categories."""
    lower = (key or "").lower()
    return {
        "is_persistence": any(p in lower for p in PERSISTENCE_REG_PATTERNS),
        "is_defense_tampering": any(p in lower for p in DEFENSE_TAMPERING_REG_PATTERNS),
        "is_recon": any(p in lower for p in RECON_REG_PATTERNS),
    }


# ---------------------------------------------------------------------------
# Main Behavior Normalization Pipeline
# ---------------------------------------------------------------------------

def normalize_behavior_artifacts(
    procmon_summary: Optional[Dict[str, Any]] = None,
    sysmon_summary: Optional[Dict[str, Any]] = None,
    sample_name: str = "",
) -> Dict[str, Any]:
    """Aggregate, filter, and normalize file and registry activity from Procmon and Sysmon.

    Returns:
        Structured dictionary containing categorized file operations, registry operations,
        MITRE ATT&CK technique inferences, and notable behavioral findings.
    """
    proc_name = sample_name
    if not proc_name:
        if procmon_summary and procmon_summary.get("sample_process"):
            proc_name = procmon_summary["sample_process"]
        elif sysmon_summary and sysmon_summary.get("sample_process"):
            proc_name = sysmon_summary["sample_process"]

    # ── 1. File Activity Categorization ─────────────────────────────────────
    created_files: Set[str] = set()
    written_files: Set[str] = set()
    sensitive_reads: Set[str] = set()
    general_reads: Set[str] = set()
    deleted_files: Set[str] = set()

    # From Procmon
    if procmon_summary and "file_activity" in procmon_summary:
        fa = procmon_summary["file_activity"]
        notable = fa.get("notable", {})

        for p in notable.get("CreateFile", []):
            if p:
                created_files.add(p)
        for p in notable.get("WriteFile", []):
            if p:
                written_files.add(p)
        for p in (
            notable.get("SetDisposition", [])
            + notable.get("SetDispositionInformationFile", [])
            + notable.get("DeleteFile", [])
        ):
            if p:
                deleted_files.add(p)

        # Reads
        for p in notable.get("ReadFile", []):
            if is_sensitive_file(p):
                sensitive_reads.add(p)
            elif not is_benign_system_file(p):
                general_reads.add(p)

        for p in fa.get("sensitive_reads", []):
            sensitive_reads.add(p)

    # From Sysmon
    if sysmon_summary:
        for f in sysmon_summary.get("files_created", []):
            if f:
                created_files.add(f)

    # ── 2. Registry Activity Categorization ─────────────────────────────────
    modified_reg: Set[str] = set()
    created_reg_keys: Set[str] = set()
    deleted_reg_keys: Set[str] = set()
    sensitive_reg_queries: Set[str] = set()
    general_reg_queries: Set[str] = set()

    persistence_keys: Set[str] = set()
    defense_tampering_keys: Set[str] = set()
    recon_queries: Set[str] = set()

    # From Procmon
    if procmon_summary and "registry_activity" in procmon_summary:
        ra = procmon_summary["registry_activity"]
        rnotable = ra.get("notable", {})

        for k in rnotable.get("RegSetValue", []):
            if k:
                modified_reg.add(k)
                cls = classify_registry_key(k)
                if cls["is_persistence"]:
                    persistence_keys.add(k)
                if cls["is_defense_tampering"]:
                    defense_tampering_keys.add(k)

        for k in rnotable.get("RegCreateKey", []):
            if k:
                created_reg_keys.add(k)
                cls = classify_registry_key(k)
                if cls["is_persistence"]:
                    persistence_keys.add(k)

        for k in rnotable.get("RegDeleteKey", []) + rnotable.get("RegDeleteValue", []):
            if k:
                deleted_reg_keys.add(k)
                cls = classify_registry_key(k)
                if cls["is_defense_tampering"]:
                    defense_tampering_keys.add(k)

        for k in rnotable.get("RegQueryValue", []) + ra.get("sensitive_queries", []):
            if k:
                cls = classify_registry_key(k)
                if cls["is_persistence"]:
                    persistence_keys.add(k)
                if cls["is_defense_tampering"]:
                    defense_tampering_keys.add(k)
                if cls["is_recon"]:
                    recon_queries.add(k)
                if cls["is_persistence"] or cls["is_defense_tampering"] or cls["is_recon"]:
                    sensitive_reg_queries.add(k)
                else:
                    general_reg_queries.add(k)

    # From Sysmon
    if sysmon_summary and "registry_events" in sysmon_summary:
        for ev in sysmon_summary["registry_events"]:
            k = ev.get("key", "")
            if not k:
                continue
            t = ev.get("type", "")
            if "Set" in t:
                modified_reg.add(k)
            elif "Create" in t:
                created_reg_keys.add(k)
            elif "Delete" in t:
                deleted_reg_keys.add(k)

            cls = classify_registry_key(k)
            if cls["is_persistence"]:
                persistence_keys.add(k)
            if cls["is_defense_tampering"]:
                defense_tampering_keys.add(k)

    # ── 3. MITRE ATT&CK Mapping ─────────────────────────────────────────────
    mitre_techniques: List[Dict[str, str]] = []

    if persistence_keys:
        mitre_techniques.append({
            "id": "T1547.001",
            "name": "Boot or Logon Autostart Execution: Registry Run Keys / Startup Folder",
            "tactic": "Persistence",
            "description": f"Modified or queried startup persistence registry keys ({len(persistence_keys)} target(s)).",
        })

    if defense_tampering_keys:
        mitre_techniques.append({
            "id": "T1562.001",
            "name": "Impair Defenses: Disable or Modify Tools",
            "tactic": "Defense Evasion",
            "description": f"Accessed or modified security/antivirus settings ({len(defense_tampering_keys)} target(s)).",
        })

    if sensitive_reads:
        mitre_techniques.append({
            "id": "T1005",
            "name": "Data from Local System",
            "tactic": "Collection",
            "description": f"Read sensitive files from user directories, credentials, or staged storage ({len(sensitive_reads)} target(s)).",
        })

    if recon_queries:
        mitre_techniques.append({
            "id": "T1082",
            "name": "System Information Discovery",
            "tactic": "Discovery",
            "description": f"Queried system identifiers, hardware specs, or cryptography machine GUID ({len(recon_queries)} target(s)).",
        })

    if deleted_files:
        mitre_techniques.append({
            "id": "T1070.004",
            "name": "Indicator Removal on Host: File Deletion",
            "tactic": "Defense Evasion",
            "description": f"Deleted {len(deleted_files)} file(s) during or after execution.",
        })

    # ── 4. Structured Output Assembly ───────────────────────────────────────
    return {
        "sample_process": proc_name,
        "summary": {
            "total_files_created": len(created_files),
            "total_files_written": len(written_files),
            "total_sensitive_reads": len(sensitive_reads),
            "total_general_reads": len(general_reads),
            "total_files_deleted": len(deleted_files),
            "total_registry_modified": len(modified_reg),
            "total_registry_created": len(created_reg_keys),
            "total_registry_deleted": len(deleted_reg_keys),
            "total_persistence_keys": len(persistence_keys),
            "total_defense_tampering_keys": len(defense_tampering_keys),
        },
        "files": {
            "created": sorted(list(created_files))[:80],
            "written": sorted(list(written_files))[:80],
            "sensitive_reads": sorted(list(sensitive_reads))[:80],
            "general_reads": sorted(list(general_reads))[:50],
            "deleted": sorted(list(deleted_files))[:50],
        },
        "registry": {
            "persistence_keys": sorted(list(persistence_keys)),
            "defense_tampering_keys": sorted(list(defense_tampering_keys)),
            "sensitive_queries": sorted(list(sensitive_reg_queries))[:80],
            "general_queries": sorted(list(general_reg_queries))[:50],
            "modified": sorted(list(modified_reg))[:80],
            "created": sorted(list(created_reg_keys))[:50],
            "deleted": sorted(list(deleted_reg_keys))[:50],
        },
        "mitre_attack": mitre_techniques,
    }


def normalize_report_behavior(report_dir: Union[str, Path]) -> Dict[str, Any]:
    """Load Procmon and Sysmon summaries from an analysis report directory and normalize behavior."""
    rdir = Path(report_dir)
    artifacts = rdir / "artifacts" if (rdir / "artifacts").is_dir() else rdir

    procmon_path = artifacts / "procmon" / "procmon_summary.json"
    sysmon_path = artifacts / "sysmon" / "sysmon_summary.json"

    procmon_data = None
    if procmon_path.is_file():
        try:
            with open(procmon_path, "r", encoding="utf-8") as f:
                procmon_data = json.load(f)
        except Exception:
            pass

    sysmon_data = None
    if sysmon_path.is_file():
        try:
            with open(sysmon_path, "r", encoding="utf-8") as f:
                sysmon_data = json.load(f)
        except Exception:
            pass

    return normalize_behavior_artifacts(
        procmon_summary=procmon_data,
        sysmon_summary=sysmon_data,
    )


def run_behavior_normalizer_on_report(
    report_dir: Union[str, Path],
    save_artifact: bool = True,
) -> Dict[str, Any]:
    """Execute behavioral normalization on a report directory and optionally save

    artifacts/behavior/behavior_summary.json.
    """
    result = normalize_report_behavior(report_dir)
    if save_artifact:
        rdir = Path(report_dir)
        out_dir = rdir / "artifacts" / "behavior"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "behavior_summary.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        log.info("Saved behavior summary artifact: %s", out_file)
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="IsoLens Filesystem & Registry Behavioral Normalizer")
    parser.add_argument("--report", type=str, required=True, help="Path to analysis report directory")
    parser.add_argument("--save", action="store_true", help="Save artifacts/behavior/behavior_summary.json")

    args = parser.parse_args()
    res = run_behavior_normalizer_on_report(args.report, save_artifact=args.save)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
