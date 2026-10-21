"""yara_scanner.py - YARA Static Pattern & Signature Detection Module.

Scans uploaded binaries and sandbox artifacts against curated YARA rulesets
(packers, sandbox evasion, ransomware commands, credential dumpers, infostealers)
to provide instant signature-based threat detection and MITRE ATT&CK attribution.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

log = logging.getLogger("isolens.yara_scanner")

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES_DIR = _PROJECT_ROOT / "core" / "storage" / "yara_rules"

# Try importing the official yara engine
try:
    import yara  # type: ignore
    _YARA_AVAILABLE = True
except ImportError:
    _YARA_AVAILABLE = False
    log.warning("yara-python not installed; fallback pattern scanner will be used")


class YaraScanner:
    """Manages compilation and scanning of YARA rules against target files."""

    def __init__(self, rules_dir: Path | str = DEFAULT_RULES_DIR) -> None:
        self.rules_dir = Path(rules_dir)
        self._compiled_rules: Optional[Any] = None
        self._fallback_rules: List[Dict[str, Any]] = []
        self._load_rules()

    def _load_rules(self) -> None:
        """Load and compile all .yar files in the rules directory."""
        if not self.rules_dir.is_dir():
            log.warning("YARA rules directory does not exist: %s", self.rules_dir)
            return

        yar_files = sorted(list(self.rules_dir.glob("*.yar")))
        if not yar_files:
            log.warning("No .yar files found in: %s", self.rules_dir)
            return

        if _YARA_AVAILABLE:
            filepaths = {f"ns_{i}": str(p.resolve()) for i, p in enumerate(yar_files)}
            try:
                self._compiled_rules = yara.compile(filepaths=filepaths)
                log.info("Compiled %d YARA ruleset(s) with yara-python", len(yar_files))
            except Exception as exc:
                log.error("Failed to compile YARA rules with yara-python: %s", exc)
                self._compiled_rules = None

        # Build fallback regex/string scanner in case yara-python is unavailable
        self._build_fallback_rules(yar_files)

    def _build_fallback_rules(self, yar_files: List[Path]) -> None:
        """Lightweight regex/literal rule extractor for fallback matching."""
        rule_re = re.compile(
            r'rule\s+(\w+)\s*\{([^}]+)\}',
            re.DOTALL
        )
        meta_desc_re = re.compile(r'description\s*=\s*"([^"]+)"')
        meta_sev_re = re.compile(r'severity\s*=\s*"([^"]+)"')
        meta_cat_re = re.compile(r'category\s*=\s*"([^"]+)"')
        meta_mitre_re = re.compile(r'mitre_technique\s*=\s*"([^"]+)"')
        string_re = re.compile(r'\$\w+\s*=\s*"([^"]+)"')

        for yf in yar_files:
            try:
                text = yf.read_text(encoding="utf-8", errors="replace")
                for match in rule_re.finditer(text):
                    rname = match.group(1)
                    body = match.group(2)
                    desc_m = meta_desc_re.search(body)
                    sev_m = meta_sev_re.search(body)
                    cat_m = meta_cat_re.search(body)
                    mitre_m = meta_mitre_re.search(body)
                    strs = string_re.findall(body)

                    self._fallback_rules.append({
                        "name": rname,
                        "description": desc_m.group(1) if desc_m else "",
                        "severity": sev_m.group(1) if sev_m else "medium",
                        "category": cat_m.group(1) if cat_m else "general",
                        "mitre_technique": mitre_m.group(1) if mitre_m else "",
                        "strings": [s.encode("utf-8") for s in strs],
                    })
            except Exception as exc:
                log.warning("Could not parse fallback rule file %s: %s", yf, exc)

    def scan_bytes(self, data: bytes, filename: str = "sample") -> Dict[str, Any]:
        """Scan a byte buffer against compiled YARA rules."""
        matches_out: List[Dict[str, Any]] = []
        tags_set: Set[str] = set()
        highest_severity = "none"

        severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1, "none": 0}

        def _update_sev(sev: str) -> None:
            nonlocal highest_severity
            if severity_rank.get(sev.lower(), 0) > severity_rank.get(highest_severity, 0):
                highest_severity = sev.lower()

        # 1. Native yara execution if available
        if self._compiled_rules is not None:
            try:
                yara_matches = self._compiled_rules.match(data=data)
                for ym in yara_matches:
                    meta = ym.meta if hasattr(ym, "meta") else {}
                    sev = meta.get("severity", "medium")
                    cat = meta.get("category", "malware")
                    mitre = meta.get("mitre_technique", "")

                    _update_sev(sev)
                    tags_set.add(cat)
                    if mitre:
                        tags_set.add(mitre)

                    matched_strings = []
                    if hasattr(ym, "strings"):
                        for s in ym.strings:
                            try:
                                sval = s.instances[0].matched_data.decode("utf-8", errors="replace")
                                matched_strings.append(sval[:80])
                            except Exception:
                                pass

                    matches_out.append({
                        "rule": ym.rule,
                        "category": cat,
                        "severity": sev,
                        "mitre_technique": mitre,
                        "description": meta.get("description", ""),
                        "tags": list(ym.tags) if hasattr(ym, "tags") else [],
                        "matched_strings": matched_strings[:10],
                    })
            except Exception as exc:
                log.error("YARA match error: %s", exc)

        # 2. Fallback execution if native yara was not compiled
        elif self._fallback_rules:
            data_lower = data.lower()
            for r in self._fallback_rules:
                matched_strs = [
                    s.decode("utf-8", errors="replace")
                    for s in r["strings"]
                    if s.lower() in data_lower
                ]
                if matched_strs:
                    _update_sev(r["severity"])
                    tags_set.add(r["category"])
                    if r.get("mitre_technique"):
                        tags_set.add(r["mitre_technique"])
                    matches_out.append({
                        "rule": r["name"],
                        "category": r["category"],
                        "severity": r["severity"],
                        "mitre_technique": r["mitre_technique"],
                        "description": r["description"],
                        "tags": [r["category"]],
                        "matched_strings": matched_strs[:10],
                    })

        # Generate MITRE list
        mitre_list: List[Dict[str, str]] = []
        for m in matches_out:
            tid = m.get("mitre_technique")
            if tid and not any(x["id"] == tid for x in mitre_list):
                mitre_list.append({
                    "id": tid,
                    "name": m.get("rule", "").replace("_", " "),
                    "description": m.get("description", ""),
                })

        return {
            "status": "ok",
            "scanned_file": filename,
            "engine": "yara-python" if self._compiled_rules is not None else "fallback_regex",
            "matched_rules_count": len(matches_out),
            "threat_level": highest_severity,
            "tags": sorted(list(tags_set)),
            "matches": matches_out,
            "mitre_attack": mitre_list,
        }

    def scan_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Scan a target file on the local filesystem."""
        p = Path(file_path)
        if not p.is_file():
            return {
                "status": "error",
                "error": f"File not found: {file_path}",
                "matched_rules_count": 0,
                "matches": [],
                "threat_level": "none",
                "tags": [],
            }

        try:
            with open(p, "rb") as fh:
                data = fh.read()
            return self.scan_bytes(data, filename=p.name)
        except Exception as exc:
            return {
                "status": "error",
                "error": f"Failed to read file: {exc}",
                "matched_rules_count": 0,
                "matches": [],
                "threat_level": "none",
                "tags": [],
            }

    def scan_report_directory(self, report_dir: Union[str, Path]) -> Dict[str, Any]:
        """Look for the archived sample in the report and run YARA scanning."""
        rdir = Path(report_dir)
        manifest_path = rdir / "analysis_manifest.json"
        sample_name = ""

        if manifest_path.is_file():
            try:
                import json
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                    sample_name = manifest.get("sample_name", "")
            except Exception:
                pass

        # Try to find the sample file in storage
        samples_dir = _PROJECT_ROOT / "core" / "storage" / "samples"
        candidates = []
        if sample_name:
            candidates.extend(list(samples_dir.glob(f"*{sample_name}*")))
            candidates.extend(list(rdir.glob(f"*{sample_name}*")))

        for c in candidates:
            if c.is_file():
                return self.scan_file(c)

        # If sample not found directly, check if a cached yara_summary.json exists
        cached_yara = rdir / "artifacts" / "yara" / "yara_summary.json"
        if cached_yara.is_file():
            try:
                import json
                with open(cached_yara, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "status": "no_sample",
            "message": "Sample file not found for YARA scanning",
            "matched_rules_count": 0,
            "matches": [],
            "threat_level": "none",
            "tags": [],
        }


def scan_file_with_yara(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Convenience function to scan a file with default YARA scanner."""
    scanner = YaraScanner()
    return scanner.scan_file(file_path)
