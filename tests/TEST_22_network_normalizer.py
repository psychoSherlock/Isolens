#!/usr/bin/env python3
"""
TEST_22_network_normalizer.py - Verification of Network Telemetry Normalization & Noise Filtering.

Validates:
 1. Windows OS & local multicast domain noise filtering accuracy.
 2. Loopback, multicast, link-local, and host-agent IP filtering.
 3. DNS query normalization and process attribution.
 4. HTTP request normalization and NCSI/agent noise exclusion.
 5. Procmon & Sysmon socket connection parsing.
 6. End-to-end unified network telemetry aggregation and IOC extraction.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.modules.network_normalizer import (
    is_noise_domain,
    is_noise_ip,
    is_noise_port,
    parse_endpoint,
    normalize_dns_queries,
    normalize_http_requests,
    normalize_connections,
    normalize_network_telemetry,
)


def run_checks():
    results = {}
    passed = 0
    failed = 0

    def check(name, condition, details=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"[TEST_22_network_normalizer:{name}] PASS")
            print(f"  About: {name}")
            print(f"  Output: {details}\n")
            results[name] = True
        else:
            failed += 1
            print(f"[TEST_22_network_normalizer:{name}] FAIL")
            print(f"  About: {name}")
            print(f"  Output: {details}\n")
            results[name] = False

    # Check 1: Domain noise filtering
    c1 = (
        is_noise_domain("www.msftconnecttest.com")
        and is_noise_domain("v10.events.data.microsoft.com")
        and is_noise_domain("wpad")
        and is_noise_domain("ocsp.digicert.com")
        and is_noise_domain("printer.local")
        and is_noise_domain("ctldl.windowsupdate.com")
        and not is_noise_domain("c2-beacon.darkweb.xyz")
        and not is_noise_domain("evil-trojan.su")
        and not is_noise_domain("microsoft.com.attacker.net")
    )
    check("domain_noise_filtering", c1, "Verified OS telemetry, NCSI, WPAD, CRL domains filtered; C2 domains preserved")

    # Check 2: IP noise filtering
    c2 = (
        is_noise_ip("127.0.0.1")
        and is_noise_ip("224.0.0.251")
        and is_noise_ip("169.254.10.20")
        and is_noise_ip("192.168.56.1")     # Host management
        and is_noise_ip("192.168.56.105")   # Guest agent VM
        and not is_noise_ip("192.0.2.123")  # TEST-NET-1 C2
        and not is_noise_ip("198.51.100.45")
        and not is_noise_ip("8.8.8.8")
    )
    check("ip_noise_filtering", c2, "Verified loopback, multicast, link-local, and host-only subnet filtered")

    # Check 3: DNS query normalization
    mock_dns = [
        "dns.msftncsi.com",
        "time.windows.com",
        "wpad",
        {
            "QueryName": "malicious-c2.xyz",
            "QueryResults": "192.0.2.123;192.0.2.124",
            "Image": "C:\\samples\\malware.exe",
            "ProcessId": 3412,
            "TimeCreated": "2026-10-17T12:00:01Z",
        },
        "malicious-c2.xyz", # Duplicate
    ]
    clean_dns, noise_dns = normalize_dns_queries(mock_dns, sample_proc="malware.exe")
    c3 = (
        len(clean_dns) == 1
        and len(noise_dns) == 3
        and clean_dns[0]["domain"] == "malicious-c2.xyz"
        and clean_dns[0]["resolved_ips"] == ["192.0.2.123", "192.0.2.124"]
        and clean_dns[0]["pid"] == 3412
    )
    check("dns_query_normalization", c3, f"Clean DNS: {len(clean_dns)}, Filtered Noise DNS: {len(noise_dns)}")

    # Check 4: HTTP request normalization
    mock_http = [
        {"host": "www.msftconnecttest.com", "uri": "/connecttest.txt", "method": "GET", "port": 80},
        {"host": "192.168.56.105", "uri": "/api/status", "method": "GET", "port": 9090}, # Agent management traffic
        {"host": "malicious-c2.xyz", "uri": "/gate.php?id=beacon", "method": "POST", "port": 80, "user_agent": "CustomAgent"},
    ]
    clean_http, noise_http = normalize_http_requests(mock_http, sample_proc="malware.exe")
    c4 = (
        len(clean_http) == 1
        and len(noise_http) == 2
        and clean_http[0]["host"] == "malicious-c2.xyz"
        and clean_http[0]["method"] == "POST"
        and clean_http[0]["url"] == "http://malicious-c2.xyz/gate.php?id=beacon"
    )
    check("http_request_normalization", c4, f"Clean HTTP: {len(clean_http)}, Filtered Noise HTTP: {len(noise_http)}")

    # Check 5: Procmon & Sysmon connection parsing
    mock_conns = [
        {"path": "WindowsSandbox:65283 -> 192.0.2.123:http", "image": "malware.exe"},
        {"src": "192.168.56.105:49152", "dst": "192.0.2.123:80", "dst_host": "malicious-c2.xyz", "proto": "tcp"},
        {"src": "192.168.56.105:49153", "dst": "192.168.56.1:9090", "proto": "tcp"}, # Host management
    ]
    clean_conns, noise_conns = normalize_connections(mock_conns, sample_proc="malware.exe")
    c5 = (
        len(clean_conns) == 1
        and len(noise_conns) == 1
        and clean_conns[0]["dst_ip"] == "192.0.2.123"
        and clean_conns[0]["dst_port"] == 80
        and clean_conns[0]["proto"] == "TCP"
    )
    check("connection_parsing_and_filtering", c5, f"Clean Conns: {len(clean_conns)}, Noise Conns: {len(noise_conns)}")

    # Check 6: Master telemetry aggregation & IOC output
    sysmon_mock = {
        "sample_process": "malware.exe",
        "dns_queries": ["time.windows.com", "c2-beacon.net"],
        "network_connections": [{"src": "192.168.56.105:1234", "dst": "198.51.100.99:443", "proto": "tcp"}],
    }
    procmon_mock = {
        "sample_process": "malware.exe",
        "network_activity": [{"path": "WindowsSandbox:5000 -> 198.51.100.99:443"}],
    }
    net_mock = {
        "http_requests": [{"host": "c2-beacon.net", "uri": "/login", "method": "GET", "port": 80}],
    }

    full_result = normalize_network_telemetry(
        sysmon_summary=sysmon_mock,
        procmon_summary=procmon_mock,
        network_summary=net_mock,
        sample_proc="malware.exe",
    )

    s = full_result["summary"]
    iocs = full_result["iocs"]

    c6 = (
        s["sample_process"] == "malware.exe"
        and s["clean_dns_count"] == 1
        and s["filtered_noise_dns"] == 1
        and s["clean_http_count"] == 1
        and s["clean_connections_count"] == 1
        and "c2-beacon.net" in iocs["domains"]
        and "198.51.100.99" in iocs["ips"]
        and "http://c2-beacon.net/login" in iocs["urls"]
    )
    check("master_telemetry_aggregation", c6, f"Aggregated IOCs: {iocs}")

    print("=" * 60)
    print(f"TEST_22_network_normalizer: {passed} PASS, {failed} FAIL")
    print("=" * 60)

    if failed > 0:
        print("[TEST_22_network_normalizer] FAIL")
        sys.exit(1)
    else:
        print("[TEST_22_network_normalizer] PASS")
        print("About: Network Telemetry Normalizer and Noise Filter verification")
        print("Output:")
        print(json.dumps({"passed": passed, "failed": failed}, indent=2))
        sys.exit(0)


if __name__ == "__main__":
    run_checks()
