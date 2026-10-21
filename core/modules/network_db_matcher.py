"""network_db_matcher.py - Deterministic Network Threat Intelligence Matcher.

Queries the local SQLite network threat intelligence database (ThreatFox, URLhaus,
Feodo Tracker, Compromised IPs) for exact and hierarchical IOC matches. Replaces
expensive AI LLM queries with 100% deterministic, high-speed, local lookups.
"""

from __future__ import annotations

import logging
import sqlite3
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

log = logging.getLogger("isolens.network_db_matcher")

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = _PROJECT_ROOT / "core" / "storage" / "database" / "network_threat_intel.db"


class NetworkThreatIntelMatcher:
    """Fast, local matcher for IPs, Domains, and URLs against network threat intelligence."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)

    def _get_connection(self) -> Optional[sqlite3.Connection]:
        if not self.db_path.is_file():
            log.warning("Threat intelligence database not found at %s", self.db_path)
            return None
        try:
            # Open SQLite in read-only mode for speed and concurrency
            uri = f"file:{self.db_path.resolve()}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.OperationalError:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    # ── Single Observable Lookups ───────────────────────────────────────────

    def lookup_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """Query threat intelligence database for a specific IP address."""
        if not ip:
            return None
        clean_ip = ip.strip().strip("[]").split(":")[0]
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ip_address, port, malware_family, threat_type, tags,
                       confidence, c2_status, source, first_seen, last_seen, reference
                FROM threat_ips
                WHERE ip_address = ?
                """,
                (clean_ip,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def lookup_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Query threat intelligence database for a domain or its parent domain."""
        if not domain:
            return None
        clean_dom = domain.strip().lower().strip(".")
        if ":" in clean_dom:
            clean_dom = clean_dom.split(":")[0]

        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            # 1. Exact match
            cursor.execute(
                """
                SELECT domain, malware_family, threat_type, tags,
                       confidence, source, first_seen, last_seen, reference
                FROM threat_domains
                WHERE domain = ?
                """,
                (clean_dom,),
            )
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res["match_type"] = "exact"
                return res

            # 2. Check parent domains (e.g. c2.sub.evil.com -> evil.com)
            parts = clean_dom.split(".")
            if len(parts) > 2:
                for i in range(1, len(parts) - 1):
                    parent = ".".join(parts[i:])
                    cursor.execute(
                        """
                        SELECT domain, malware_family, threat_type, tags,
                               confidence, source, first_seen, last_seen, reference
                        FROM threat_domains
                        WHERE domain = ?
                        """,
                        (parent,),
                    )
                    row = cursor.fetchone()
                    if row:
                        res = dict(row)
                        res["match_type"] = f"parent_domain ({parent})"
                        return res

            return None
        finally:
            conn.close()

    def lookup_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Query threat intelligence database for a malicious URL."""
        if not url:
            return None
        clean_url = url.strip()
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            # Exact match or normalized trailing slash
            cursor.execute(
                """
                SELECT url, host, port, malware_family, threat_type, tags,
                       status, source, first_seen, last_seen
                FROM threat_urls
                WHERE url = ? OR url = ?
                """,
                (clean_url, clean_url.rstrip("/")),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    # ── Batch Analysis Pipeline ─────────────────────────────────────────────

    def match_network_indicators(
        self,
        domains: Optional[List[str]] = None,
        ips: Optional[List[str]] = None,
        urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Match collected network observables against threat intelligence database.

        Returns:
            Structured dictionary matching the IsoLens ToolAnalysisResult schema:
            {
                "tool": "network",
                "verdict": "malicious|suspicious|benign|inconclusive",
                "confidence": 0-100,
                "findings": [...],
                "iocs": [...],
                "summary": "...",
                "matched_counts": {...},
                "malware_families": [...],
            }
        """
        domains = domains or []
        ips = ips or []
        urls = urls or []

        matched_ips: List[Dict[str, Any]] = []
        matched_domains: List[Dict[str, Any]] = []
        matched_urls: List[Dict[str, Any]] = []

        all_families: Set[str] = set()
        all_threat_types: Set[str] = set()
        all_tags: Set[str] = set()

        max_confidence = 0

        # Check IPs
        for ip in ips:
            match = self.lookup_ip(ip)
            if match:
                matched_ips.append(match)
                conf = match.get("confidence") or 80
                max_confidence = max(max_confidence, int(conf))
                fam = match.get("malware_family")
                if fam and fam.lower() not in ("unknown", "none", ""):
                    all_families.add(fam)
                if match.get("threat_type"):
                    all_threat_types.add(match["threat_type"])
                for t in (match.get("tags") or "").split(","):
                    if t.strip() and t.strip().lower() not in ("none", "unknown"):
                        all_tags.add(t.strip())

        # Check Domains
        for dom in domains:
            match = self.lookup_domain(dom)
            if match:
                matched_domains.append(match)
                conf = match.get("confidence") or 80
                max_confidence = max(max_confidence, int(conf))
                fam = match.get("malware_family")
                if fam and fam.lower() not in ("unknown", "none", ""):
                    all_families.add(fam)
                if match.get("threat_type"):
                    all_threat_types.add(match["threat_type"])
                for t in (match.get("tags") or "").split(","):
                    if t.strip() and t.strip().lower() not in ("none", "unknown"):
                        all_tags.add(t.strip())

        # Check URLs
        for u in urls:
            match = self.lookup_url(u)
            if match:
                matched_urls.append(match)
                max_confidence = max(max_confidence, 90)
                fam = match.get("malware_family")
                if fam and fam.lower() not in ("unknown", "none", ""):
                    all_families.add(fam)
                if match.get("threat_type"):
                    all_threat_types.add(match["threat_type"])
                for t in (match.get("tags") or "").split(","):
                    if t.strip() and t.strip().lower() not in ("none", "unknown"):
                        all_tags.add(t.strip())

        # Determine Verdict
        total_matches = len(matched_ips) + len(matched_domains) + len(matched_urls)
        total_queried = len(ips) + len(domains) + len(urls)

        if total_queried == 0:
            verdict = "inconclusive"
            summary = "No external network connections, DNS queries, or HTTP requests observed."
        elif total_matches > 0:
            # Check if matches are confirmed malicious C2 / malware download or just scanner/compromised
            has_c2_or_malware = bool(all_families) or any(
                "c2" in (m.get("threat_type") or "").lower()
                or "botnet" in (m.get("threat_type") or "").lower()
                or "malware" in (m.get("threat_type") or "").lower()
                for m in matched_ips + matched_domains + matched_urls
            )
            verdict = "malicious" if has_c2_or_malware else "suspicious"
            fam_str = f" attributed to [{', '.join(sorted(all_families))}]" if all_families else ""
            summary = (
                f"Identified {total_matches} known malicious network indicator(s){fam_str}. "
                f"Matched {len(matched_ips)} IP(s), {len(matched_domains)} domain(s), and {len(matched_urls)} URL(s) "
                f"against threat intelligence feeds."
            )
        else:
            verdict = "benign"
            max_confidence = 85
            summary = (
                f"Observed network activity ({len(domains)} domain queries, {len(ips)} remote connection endpoints) "
                f"did not match any known malicious indicators in threat intelligence feeds."
            )

        # Generate Structured Findings
        findings: List[Dict[str, str]] = []
        for m in matched_ips:
            ip_val = m["ip_address"]
            port_str = f":{m['port']}" if m.get("port") else ""
            fam = m.get("malware_family") or "Unclassified malware"
            tt = m.get("threat_type") or "malicious_ip"
            src = m.get("source") or "threat_intel"
            findings.append({
                "severity": "high" if "c2" in tt.lower() or "botnet" in tt.lower() else "medium",
                "indicator": f"{ip_val}{port_str}",
                "description": f"Known {tt.replace('_', ' ')} associated with {fam} (Source: {src}, Confidence: {m.get('confidence', 80)}%).",
            })

        for m in matched_domains:
            dom_val = m["domain"]
            fam = m.get("malware_family") or "Unclassified malware"
            tt = m.get("threat_type") or "malicious_domain"
            src = m.get("source") or "threat_intel"
            match_t = m.get("match_type", "exact")
            findings.append({
                "severity": "high",
                "indicator": dom_val,
                "description": f"Known malicious domain ({match_t}) associated with {fam} (Source: {src}).",
            })

        for m in matched_urls:
            url_val = m["url"]
            fam = m.get("malware_family") or "Malware payload"
            findings.append({
                "severity": "high",
                "indicator": url_val[:120],
                "description": f"Known malware download URL ({fam}). Status: {m.get('status', 'active')}.",
            })

        # Generate IOCs list
        iocs: List[Dict[str, str]] = []
        for m in matched_ips:
            iocs.append({"type": "network", "value": m["ip_address"]})
        for m in matched_domains:
            iocs.append({"type": "dns", "value": m["domain"]})
        for m in matched_urls:
            iocs.append({"type": "url", "value": m["url"]})

        return {
            "tool": "network",
            "verdict": verdict,
            "confidence": max_confidence,
            "summary": summary,
            "findings": findings[:15],
            "iocs": iocs[:25],
            "details": {
                "matched_ips_count": len(matched_ips),
                "matched_domains_count": len(matched_domains),
                "matched_urls_count": len(matched_urls),
                "malware_families": sorted(list(all_families)),
                "threat_types": sorted(list(all_threat_types)),
                "tags": sorted(list(all_tags)),
            },
        }


def analyze_report_network_with_db(
    report_dir: Union[str, Path],
    db_path: Path | str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """Ingest network artifacts from a report directory and perform deterministic DB matching."""
    from core.modules.network_normalizer import normalize_report_directory

    rdir = Path(report_dir)
    if not rdir.is_dir():
        return {
            "tool": "network",
            "verdict": "inconclusive",
            "confidence": 0,
            "summary": f"Report directory not found: {report_dir}",
            "findings": [],
            "iocs": [],
            "details": {},
        }

    norm = normalize_report_directory(rdir)
    iocs = norm.get("iocs", {})
    domains = iocs.get("domains", [])
    ips = iocs.get("ips", [])
    urls = iocs.get("urls", [])

    matcher = NetworkThreatIntelMatcher(db_path=db_path)
    result = matcher.match_network_indicators(domains=domains, ips=ips, urls=urls)

    # If traffic exists but wasn't in DB, include clean counts in details
    result["details"]["total_domains_observed"] = len(domains)
    result["details"]["total_ips_observed"] = len(ips)
    result["details"]["total_urls_observed"] = len(urls)

    return result
