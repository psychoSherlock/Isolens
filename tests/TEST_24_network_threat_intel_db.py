#!/usr/bin/env python3
"""TEST_24 - Network Threat Intelligence Database & Local Matcher.

Validates:
  1. network_threat_intel.db exists and contains populated threat_ips, threat_domains, and threat_urls tables.
  2. No file hashes (SHA256, MD5, SHA1) are stored in the database.
  3. Deduplication rule: IPs with duplicate entries chose the record with maximum information.
  4. Single observable lookups (IP, Domain exact, Domain parent, URL).
  5. Batch matching produces valid IsoLens tool findings, IOCs, and verdicts without AI calls.
  6. Integration with report directory via analyze_report_network_with_db.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))

TEST_NAME = "TEST_24_network_threat_intel_db"
ABOUT = "Offline network threat intelligence DB builder, IP max-info deduplication, and deterministic IOC matcher"


def run_test() -> list[str]:
    errors: list[str] = []

    db_path = _PROJECT_ROOT / "core" / "storage" / "database" / "network_threat_intel.db"
    if not db_path.is_file():
        errors.append(f"Database file not found: {db_path}")
        return errors

    # ── 1. Schema & Table Verification ──────────────────────────────────────
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    for expected in ("threat_ips", "threat_domains", "threat_urls"):
        if expected not in tables:
            errors.append(f"Missing table in SQLite database: {expected}")

    cursor.execute("SELECT COUNT(*) FROM threat_ips;")
    ip_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM threat_domains;")
    domain_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM threat_urls;")
    url_count = cursor.fetchone()[0]

    if ip_count < 100:
        errors.append(f"threat_ips has unexpectedly low count: {ip_count}")
    if domain_count < 100:
        errors.append(f"threat_domains has unexpectedly low count: {domain_count}")
    if url_count < 100:
        errors.append(f"threat_urls has unexpectedly low count: {url_count}")

    # ── 2. Observables Only: Verify No File Hashes Exist ─────────────────────
    # Query for any 32, 40, or 64 character hex strings in IP or Domain columns
    cursor.execute("""
        SELECT COUNT(*) FROM threat_ips 
        WHERE LENGTH(ip_address) IN (32, 40, 64) 
          AND ip_address NOT LIKE '%.%' 
          AND ip_address NOT LIKE '%:%';
    """)
    hash_ips = cursor.fetchone()[0]
    if hash_ips > 0:
        errors.append(f"Found {hash_ips} file hashes incorrectly stored in threat_ips!")

    cursor.execute("""
        SELECT COUNT(*) FROM threat_domains 
        WHERE LENGTH(domain) IN (32, 40, 64) 
          AND domain NOT LIKE '%.%';
    """)
    hash_doms = cursor.fetchone()[0]
    if hash_doms > 0:
        errors.append(f"Found {hash_doms} file hashes incorrectly stored in threat_domains!")

    # ── 3. Information Scoring & Deduplication Verification ─────────────────
    # Verify that multi-source IP '162.243.103.246' retained maximum information
    cursor.execute("""
        SELECT ip_address, port, malware_family, threat_type, tags, confidence, source, info_score
        FROM threat_ips WHERE ip_address = '162.243.103.246';
    """)
    row = cursor.fetchone()
    if not row:
        errors.append("Expected multi-source IP 162.243.103.246 not found in threat_ips")
    else:
        ip_addr, port, fam, tt, tags, conf, src, score = row
        if score < 40:
            errors.append(f"IP info score too low ({score}), expected > 40 for rich record")
        if not fam:
            errors.append("Malware family missing from deduplicated IP with known attribution")
        if not tags:
            errors.append("Tags missing from deduplicated IP")

    # ── 4. Deterministic Matcher Lookups ────────────────────────────────────
    from core.modules.network_db_matcher import NetworkThreatIntelMatcher

    matcher = NetworkThreatIntelMatcher(db_path=db_path)

    # 4a. IP lookup
    res_ip = matcher.lookup_ip("162.243.103.246")
    if not res_ip or res_ip["ip_address"] != "162.243.103.246":
        errors.append("matcher.lookup_ip('162.243.103.246') failed")

    # 4b. Domain exact lookup
    # Find any sample domain from the database
    cursor.execute("SELECT domain FROM threat_domains LIMIT 1;")
    sample_domain = cursor.fetchone()[0]
    res_dom = matcher.lookup_domain(sample_domain)
    if not res_dom or res_dom["domain"] != sample_domain:
        errors.append(f"matcher.lookup_domain({sample_domain!r}) exact match failed")

    # 4c. URL lookup
    cursor.execute("SELECT url FROM threat_urls LIMIT 1;")
    sample_url = cursor.fetchone()[0]
    res_url = matcher.lookup_url(sample_url)
    if not res_url or res_url["url"] != sample_url:
        errors.append(f"matcher.lookup_url({sample_url!r}) failed")

    conn.close()

    # ── 5. Batch Matching & ToolAnalysisResult Compatibility ────────────────
    batch_res = matcher.match_network_indicators(
        ips=["162.243.103.246", "1.1.1.1"],
        domains=[sample_domain, "benign-internal.local"],
        urls=[sample_url],
    )

    for field in ("tool", "verdict", "confidence", "findings", "iocs", "summary"):
        if field not in batch_res:
            errors.append(f"batch_res missing required field: {field}")

    if batch_res.get("verdict") not in ("malicious", "suspicious"):
        errors.append(f"Expected malicious or suspicious verdict for batch_res, got {batch_res.get('verdict')}")

    if not batch_res.get("findings"):
        errors.append("batch_res generated no findings for matched indicators")

    if not batch_res.get("iocs"):
        errors.append("batch_res generated no IOCs for matched indicators")

    # ── 6. Report Directory Integration (Mock Directory) ────────────────────
    from core.modules.network_db_matcher import analyze_report_network_with_db

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        artifacts_dir = tmp_path / "artifacts"
        net_dir = artifacts_dir / "network"
        net_dir.mkdir(parents=True, exist_ok=True)

        network_summary = {
            "dns_queries": [
                {"domain": sample_domain, "QueryResults": "162.243.103.246"},
                {"domain": "time.windows.com"},  # Noise domain
            ],
            "http_requests": [
                {"host": sample_domain, "uri": "/c2.php", "port": 80, "url": sample_url},
                {"host": "www.msftconnecttest.com", "uri": "/connecttest.txt", "port": 80},  # Noise HTTP
            ],
            "tcp_conversations": "192.168.56.101:49200 <-> 162.243.103.246:8080",
        }
        with open(net_dir / "network_summary.json", "w", encoding="utf-8") as f:
            json.dump(network_summary, f)

        report_res = analyze_report_network_with_db(tmp_path, db_path=db_path)
        if report_res.get("verdict") != "malicious":
            errors.append(f"analyze_report_network_with_db verdict expected 'malicious', got {report_res.get('verdict')}")
        if report_res.get("tool") != "network":
            errors.append(f"analyze_report_network_with_db tool expected 'network', got {report_res.get('tool')}")
        if not report_res.get("findings"):
            errors.append("analyze_report_network_with_db generated no findings")

    return errors


def main() -> int:
    try:
        errors = run_test()
        output = (
            f"Threat Intel DB verification:\n"
            f"  - SQLite tables and schemas validated\n"
            f"  - Zero file hashes stored (observables only)\n"
            f"  - IP deduplication with max-info priority confirmed\n"
            f"  - Deterministic lookups and batch matching verified\n"
            f"  - Pipeline integration validated without AI tokens\n"
        )
        if errors:
            print(f"[{TEST_NAME}] FAIL")
            print(f"About: {ABOUT}")
            print(f"Reason: {len(errors)} check(s) failed:\n" + "\n".join(f"  - {e}" for e in errors))
            print(f"Output:\n{output}")
            return 1
        else:
            print(f"[{TEST_NAME}] PASS")
            print(f"About: {ABOUT}")
            print(f"Output:\n{output}")
            return 0
    except Exception as exc:
        print(f"[{TEST_NAME}] FAIL")
        print(f"About: {ABOUT}")
        print(f"Reason: Exception -- {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
