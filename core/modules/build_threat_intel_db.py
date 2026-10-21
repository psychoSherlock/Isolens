"""build_threat_intel_db.py - Network Threat Intelligence Database Builder.

Streams open-source threat intelligence blacklists (ThreatFox, URLhaus, Feodo Tracker,
Compromised IPs) into a centralized, indexed SQLite database for fast, offline,
zero-cost deterministic network IOC matching in IsoLens.

Core Principles:
1. STREAMING ONLY: Never reads large files into memory as a whole.
2. OBSERVABLES ONLY: Discards file hashes (SHA256/MD5/SHA1); stores only IPs, Domains, URLs.
3. INFORMATION-DENSITY IP DEDUPLICATION: When duplicate IPs appear across or within datasets,
   evaluates an information score (family, tags, port, threat type, status, confidence)
   and selects the record with maximum intelligence.
"""

from __future__ import annotations

import csv
import ipaddress
import logging
import os
import sqlite3
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, Optional, Set, Tuple

log = logging.getLogger("isolens.build_threat_intel_db")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = _PROJECT_ROOT / "core" / "storage" / "database" / "network_threat_intel.db"
DEFAULT_FEEDS_DIR = _PROJECT_ROOT / "data" / "blacklists" / "network"


def is_valid_ip(val: str) -> bool:
    """Check if string is a valid IPv4 or IPv6 address."""
    if not val:
        return False
    clean = val.strip().strip("[]")
    try:
        ipaddress.ip_address(clean)
        return True
    except ValueError:
        return False


def clean_domain(val: str) -> str:
    """Normalize a domain string, removing ports, protocol prefixes, and trailing slashes."""
    if not val:
        return ""
    d = val.strip().lower()
    if d.startswith("http://") or d.startswith("https://"):
        try:
            parsed = urllib.parse.urlparse(d)
            d = parsed.hostname or ""
        except Exception:
            pass
    if ":" in d:
        d = d.split(":")[0]
    return d.strip().strip(".").strip("/")


def merge_tags(tags_a: str, tags_b: str) -> str:
    """Combine comma-separated tags uniquely."""
    tag_set: Set[str] = set()
    for t in (tags_a or "").split(","):
        clean = t.strip()
        if clean and clean.lower() not in ("none", "unknown", "null"):
            tag_set.add(clean)
    for t in (tags_b or "").split(","):
        clean = t.strip()
        if clean and clean.lower() not in ("none", "unknown", "null"):
            tag_set.add(clean)
    return ",".join(sorted(tag_set))


def calculate_ip_info_score(rec: Dict[str, Any]) -> int:
    """Score record richness to determine which dataset record has the maximum information."""
    score = 0
    # 1. Specific Malware family known (+25)
    fam = (rec.get("malware_family") or "").strip().lower()
    if fam and fam not in ("unknown", "unknown malware", "none", "null", ""):
        score += 25

    # 2. Informative tags (+10 base, +2 per tag up to +10)
    tags = [
        t.strip()
        for t in (rec.get("tags") or "").split(",")
        if t.strip() and t.strip().lower() not in ("none", "unknown", "null")
    ]
    if tags:
        score += 10 + min(len(tags), 5) * 2

    # 3. Known destination port (+10)
    port = rec.get("port")
    try:
        if port is not None and int(port) > 0:
            score += 10
    except (ValueError, TypeError):
        pass

    # 4. Specific threat type (+10)
    tt = (rec.get("threat_type") or "").strip().lower()
    if tt and tt not in ("unknown", "none", "null", ""):
        score += 10

    # 5. C2 / active status known (+5)
    status = (rec.get("c2_status") or "").strip().lower()
    if status and status not in ("none", "unknown", ""):
        score += 5

    # 6. Reference link (+5)
    ref = (rec.get("reference") or "").strip()
    if ref and ref.lower() not in ("none", "null", ""):
        score += 5

    # 7. Confidence level (up to +10)
    try:
        conf = int(rec.get("confidence", 0))
        score += min(10, max(0, conf // 10))
    except (ValueError, TypeError):
        pass

    return score


class ThreatIntelDBBuilder:
    """Builds and indexes the SQLite network threat intelligence database."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH, feeds_dir: Path | str = DEFAULT_FEEDS_DIR):
        self.db_path = Path(db_path)
        self.feeds_dir = Path(feeds_dir)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def init_database(self, conn: sqlite3.Connection) -> None:
        """Create tables and indexes."""
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS threat_ips (
                ip_address TEXT PRIMARY KEY,
                port INTEGER,
                malware_family TEXT,
                threat_type TEXT,
                tags TEXT,
                confidence INTEGER,
                c2_status TEXT,
                source TEXT,
                first_seen TEXT,
                last_seen TEXT,
                reference TEXT,
                info_score INTEGER
            );

            CREATE TABLE IF NOT EXISTS threat_domains (
                domain TEXT PRIMARY KEY,
                malware_family TEXT,
                threat_type TEXT,
                tags TEXT,
                confidence INTEGER,
                source TEXT,
                first_seen TEXT,
                last_seen TEXT,
                reference TEXT
            );

            CREATE TABLE IF NOT EXISTS threat_urls (
                url TEXT PRIMARY KEY,
                host TEXT,
                port INTEGER,
                malware_family TEXT,
                threat_type TEXT,
                tags TEXT,
                status TEXT,
                source TEXT,
                first_seen TEXT,
                last_seen TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_threat_urls_host ON threat_urls(host);
            CREATE INDEX IF NOT EXISTS idx_threat_ips_family ON threat_ips(malware_family);
            CREATE INDEX IF NOT EXISTS idx_threat_domains_family ON threat_domains(malware_family);
        """)
        conn.commit()

    # ── Feed Stream Parsers (Line by Line) ───────────────────────────────────

    def stream_threatfox(self, path: Path) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """Stream ThreatFox CSV line-by-line, discarding hashes and extracting network IOCs."""
        if not path.is_file():
            log.warning("ThreatFox file not found: %s", path)
            return

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or not row[0] or row[0].startswith("#"):
                    continue
                if len(row) < 13:
                    continue

                # Strip whitespace and quotes
                row = [col.strip().strip('"') for col in row]
                first_seen = row[0]
                ioc_val = row[2]
                ioc_type = row[3].lower()
                threat_type = row[4]
                fk_malware = row[5]
                malware_alias = row[6]
                malware_printable = row[7]
                last_seen = row[8]
                conf = 0
                try:
                    conf = int(row[9])
                except (ValueError, TypeError):
                    pass
                reference = row[11]
                tags = row[12]

                # Drop hashes completely!
                if "hash" in ioc_type or ioc_type in ("sha256_hash", "md5_hash", "sha1_hash"):
                    continue

                family = malware_printable
                if not family or family.lower() in ("unknown malware", "none", "unknown"):
                    family = fk_malware if fk_malware and fk_malware.lower() != "none" else ""

                all_tags = merge_tags(tags, malware_alias if malware_alias and malware_alias.lower() != "none" else "")

                if ioc_type == "ip:port" or (":" in ioc_val and not ioc_val.startswith("http")):
                    parts = ioc_val.rsplit(":", 1)
                    ip_str = parts[0].strip("[]")
                    port = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                    if is_valid_ip(ip_str):
                        yield "ip", {
                            "ip_address": ip_str,
                            "port": port,
                            "malware_family": family,
                            "threat_type": threat_type,
                            "tags": all_tags,
                            "confidence": conf,
                            "c2_status": "active",
                            "source": "threatfox",
                            "first_seen": first_seen,
                            "last_seen": last_seen,
                            "reference": reference,
                        }
                elif ioc_type == "domain":
                    dom = clean_domain(ioc_val)
                    if dom:
                        yield "domain", {
                            "domain": dom,
                            "malware_family": family,
                            "threat_type": threat_type,
                            "tags": all_tags,
                            "confidence": conf,
                            "source": "threatfox",
                            "first_seen": first_seen,
                            "last_seen": last_seen,
                            "reference": reference,
                        }
                elif ioc_type == "url":
                    parsed = urllib.parse.urlparse(ioc_val)
                    host = parsed.hostname or ""
                    port = parsed.port or (443 if parsed.scheme == "https" else 80)
                    yield "url", {
                        "url": ioc_val,
                        "host": host,
                        "port": port,
                        "malware_family": family,
                        "threat_type": threat_type,
                        "tags": all_tags,
                        "status": "active",
                        "source": "threatfox",
                        "first_seen": first_seen,
                        "last_seen": last_seen,
                    }
                    if is_valid_ip(host):
                        yield "ip", {
                            "ip_address": host,
                            "port": port,
                            "malware_family": family,
                            "threat_type": threat_type,
                            "tags": all_tags,
                            "confidence": conf,
                            "c2_status": "active",
                            "source": "threatfox",
                            "first_seen": first_seen,
                            "last_seen": last_seen,
                            "reference": reference,
                        }
                    elif host:
                        dom = clean_domain(host)
                        if dom:
                            yield "domain", {
                                "domain": dom,
                                "malware_family": family,
                                "threat_type": threat_type,
                                "tags": all_tags,
                                "confidence": conf,
                                "source": "threatfox",
                                "first_seen": first_seen,
                                "last_seen": last_seen,
                                "reference": reference,
                            }

    def stream_urlhaus(self, path: Path) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """Stream URLhaus CSV line-by-line, extracting malicious URLs, hosts, and tags."""
        if not path.is_file():
            log.warning("URLhaus file not found: %s", path)
            return

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or not row[0] or row[0].startswith("#"):
                    continue
                if len(row) < 8:
                    continue

                row = [col.strip().strip('"') for col in row]
                dateadded = row[1]
                url_str = row[2]
                url_status = row[3]
                last_online = row[4]
                threat = row[5]
                tags = row[6]
                ref = row[7]

                try:
                    parsed = urllib.parse.urlparse(url_str)
                    host = parsed.hostname or ""
                    port = parsed.port or (443 if parsed.scheme == "https" else 80)
                except Exception:
                    host = ""
                    port = 80

                # Determine potential malware family from tags (e.g. 'Mozi', 'Mirai', 'RedLine')
                fam = ""
                tag_list = [t.strip() for t in tags.split(",") if t.strip() and t.strip().lower() != "none"]
                for t in tag_list:
                    if t.lower() not in ("32-bit", "64-bit", "arm", "mips", "elf", "sh", "bin", "exe", "x86"):
                        fam = t
                        break

                clean_tags = ",".join(tag_list)

                yield "url", {
                    "url": url_str,
                    "host": host,
                    "port": port,
                    "malware_family": fam,
                    "threat_type": threat,
                    "tags": clean_tags,
                    "status": url_status,
                    "source": "urlhaus",
                    "first_seen": dateadded,
                    "last_seen": last_online,
                }

                if is_valid_ip(host):
                    yield "ip", {
                        "ip_address": host,
                        "port": port,
                        "malware_family": fam,
                        "threat_type": threat,
                        "tags": clean_tags,
                        "confidence": 85 if url_status == "online" else 60,
                        "c2_status": url_status,
                        "source": "urlhaus",
                        "first_seen": dateadded,
                        "last_seen": last_online,
                        "reference": ref,
                    }
                elif host:
                    dom = clean_domain(host)
                    if dom:
                        yield "domain", {
                            "domain": dom,
                            "malware_family": fam,
                            "threat_type": threat,
                            "tags": clean_tags,
                            "confidence": 85 if url_status == "online" else 60,
                            "source": "urlhaus",
                            "first_seen": dateadded,
                            "last_seen": last_online,
                            "reference": ref,
                        }

    def stream_feodotracker(self, path: Path) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """Stream Feodo Tracker CSV line-by-line for high-fidelity botnet C2 IP records."""
        if not path.is_file():
            log.warning("Feodo Tracker file not found: %s", path)
            return

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or not row[0] or row[0].startswith("#"):
                    continue
                if len(row) < 6:
                    continue

                row = [col.strip().strip('"') for col in row]
                first_seen = row[0]
                dst_ip = row[1]
                try:
                    port = int(row[2])
                except (ValueError, TypeError):
                    port = 0
                status = row[3]
                last_online = row[4]
                malware = row[5]

                if is_valid_ip(dst_ip):
                    yield "ip", {
                        "ip_address": dst_ip,
                        "port": port,
                        "malware_family": malware,
                        "threat_type": "botnet_c2",
                        "tags": f"{malware},c2,feodotracker",
                        "confidence": 100,
                        "c2_status": status,
                        "source": "feodotracker",
                        "first_seen": first_seen,
                        "last_seen": last_online,
                        "reference": "https://feodotracker.abuse.ch/",
                    }

    def stream_compromised_ips(self, path: Path) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """Stream compromised IPs line-by-line."""
        if not path.is_file():
            log.warning("Compromised IPs file not found: %s", path)
            return

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                ip_str = line.strip()
                if not ip_str or ip_str.startswith("#"):
                    continue
                if is_valid_ip(ip_str):
                    yield "ip", {
                        "ip_address": ip_str,
                        "port": 0,
                        "malware_family": "",
                        "threat_type": "compromised_host",
                        "tags": "compromised,scanner",
                        "confidence": 70,
                        "c2_status": "unknown",
                        "source": "compromised_list",
                        "first_seen": "",
                        "last_seen": "",
                        "reference": "",
                    }

    # ── Database Ingestion with Maximum Information Deduplication ────────────

    def build(self) -> Dict[str, int]:
        """Process all feeds and build the final indexed database."""
        conn = sqlite3.connect(self.db_path)
        self.init_database(conn)
        cursor = conn.cursor()

        stats = {
            "ips_ingested": 0,
            "ips_updated_max_info": 0,
            "domains_ingested": 0,
            "urls_ingested": 0,
        }

        # In-memory dictionary for IP deduplication and max info tracking
        # Key: ip_address -> Dict with record values and 'info_score'
        ip_registry: Dict[str, Dict[str, Any]] = {}

        def _process_ip_candidate(rec: Dict[str, Any]) -> None:
            ip = rec["ip_address"]
            score = calculate_ip_info_score(rec)
            rec["info_score"] = score

            if ip not in ip_registry:
                ip_registry[ip] = rec
                stats["ips_ingested"] += 1
            else:
                existing = ip_registry[ip]
                # Merge tags regardless so we don't lose aliases/context
                merged_tags = merge_tags(existing.get("tags", ""), rec.get("tags", ""))

                if score > existing["info_score"]:
                    # New record has MAXIMUM INFORMATION: replace record
                    rec["tags"] = merged_tags
                    # Preserve port or reference if existing had it and new didn't
                    if not rec.get("port") and existing.get("port"):
                        rec["port"] = existing["port"]
                    if not rec.get("reference") and existing.get("reference"):
                        rec["reference"] = existing["reference"]
                    ip_registry[ip] = rec
                    stats["ips_updated_max_info"] += 1
                else:
                    # Existing record had higher or equal info density: keep existing, update merged tags
                    existing["tags"] = merged_tags
                    # Backfill any missing field
                    if not existing.get("port") and rec.get("port"):
                        existing["port"] = rec["port"]
                    if not existing.get("reference") and rec.get("reference"):
                        existing["reference"] = rec["reference"]

        # 1. Process Compromised IPs (Base baseline)
        log.info("Streaming compromised IPs...")
        for _, rec in self.stream_compromised_ips(self.feeds_dir / "compromised-ips.txt"):
            _process_ip_candidate(rec)

        # 2. Process Feodo Tracker (High fidelity C2)
        log.info("Streaming Feodo Tracker C2 blocklist...")
        for _, rec in self.stream_feodotracker(self.feeds_dir / "ipblocklist.csv"):
            _process_ip_candidate(rec)

        # 3. Process URLhaus (URLs, hosts, tags)
        log.info("Streaming URLhaus feeds...")
        url_batch: list[Tuple] = []
        domain_dict: Dict[str, Dict[str, Any]] = {}

        for kind, rec in self.stream_urlhaus(self.feeds_dir / "urlhaus_full.csv"):
            if kind == "ip":
                _process_ip_candidate(rec)
            elif kind == "domain":
                d = rec["domain"]
                if d not in domain_dict:
                    domain_dict[d] = rec
                else:
                    domain_dict[d]["tags"] = merge_tags(domain_dict[d]["tags"], rec["tags"])
            elif kind == "url":
                url_batch.append((
                    rec["url"], rec["host"], rec["port"], rec["malware_family"],
                    rec["threat_type"], rec["tags"], rec["status"], rec["source"],
                    rec["first_seen"], rec["last_seen"],
                ))
                if len(url_batch) >= 10000:
                    cursor.executemany("""
                        INSERT OR REPLACE INTO threat_urls
                        (url, host, port, malware_family, threat_type, tags, status, source, first_seen, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, url_batch)
                    conn.commit()
                    stats["urls_ingested"] += len(url_batch)
                    url_batch.clear()

        # 4. Process ThreatFox (IPs, Domains, URLs)
        log.info("Streaming ThreatFox IOCs...")
        for kind, rec in self.stream_threatfox(self.feeds_dir / "threatfox_full.csv"):
            if kind == "ip":
                _process_ip_candidate(rec)
            elif kind == "domain":
                d = rec["domain"]
                if d not in domain_dict:
                    domain_dict[d] = rec
                else:
                    ex = domain_dict[d]
                    ex["tags"] = merge_tags(ex["tags"], rec["tags"])
                    if not ex.get("malware_family") and rec.get("malware_family"):
                        ex["malware_family"] = rec["malware_family"]
                    if rec.get("confidence", 0) > ex.get("confidence", 0):
                        ex["confidence"] = rec["confidence"]
            elif kind == "url":
                url_batch.append((
                    rec["url"], rec["host"], rec["port"], rec["malware_family"],
                    rec["threat_type"], rec["tags"], rec["status"], rec["source"],
                    rec["first_seen"], rec["last_seen"],
                ))
                if len(url_batch) >= 10000:
                    cursor.executemany("""
                        INSERT OR REPLACE INTO threat_urls
                        (url, host, port, malware_family, threat_type, tags, status, source, first_seen, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, url_batch)
                    conn.commit()
                    stats["urls_ingested"] += len(url_batch)
                    url_batch.clear()

        if url_batch:
            cursor.executemany("""
                INSERT OR REPLACE INTO threat_urls
                (url, host, port, malware_family, threat_type, tags, status, source, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, url_batch)
            conn.commit()
            stats["urls_ingested"] += len(url_batch)
            url_batch.clear()

        # Batch insert all deduplicated IPs
        log.info("Inserting %d deduplicated IPs into SQLite...", len(ip_registry))
        ip_batch = [
            (
                r["ip_address"], r.get("port", 0), r.get("malware_family", ""),
                r.get("threat_type", ""), r.get("tags", ""), r.get("confidence", 0),
                r.get("c2_status", ""), r.get("source", ""), r.get("first_seen", ""),
                r.get("last_seen", ""), r.get("reference", ""), r.get("info_score", 0),
            )
            for r in ip_registry.values()
        ]

        for i in range(0, len(ip_batch), 10000):
            cursor.executemany("""
                INSERT OR REPLACE INTO threat_ips
                (ip_address, port, malware_family, threat_type, tags, confidence, c2_status, source, first_seen, last_seen, reference, info_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ip_batch[i:i + 10000])
            conn.commit()

        # Batch insert all domains
        log.info("Inserting %d threat domains into SQLite...", len(domain_dict))
        dom_batch = [
            (
                r["domain"], r.get("malware_family", ""), r.get("threat_type", ""),
                r.get("tags", ""), r.get("confidence", 0), r.get("source", ""),
                r.get("first_seen", ""), r.get("last_seen", ""), r.get("reference", ""),
            )
            for r in domain_dict.values()
        ]
        for i in range(0, len(dom_batch), 10000):
            cursor.executemany("""
                INSERT OR REPLACE INTO threat_domains
                (domain, malware_family, threat_type, tags, confidence, source, first_seen, last_seen, reference)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, dom_batch[i:i + 10000])
            conn.commit()
            stats["domains_ingested"] += len(dom_batch[i:i + 10000])

        cursor.execute("VACUUM;")
        conn.close()

        log.info("Threat intelligence database built successfully: %s", self.db_path)
        log.info("Stats: %s", stats)
        return stats


if __name__ == "__main__":
    builder = ThreatIntelDBBuilder()
    builder.build()
