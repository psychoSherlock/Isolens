#!/usr/bin/env python3
"""
TEST_23_ai_router.py - Verification of Multi-Provider AI Fallback Router.

Validates:
 1. Router initialization and provider status detection (NVIDIA, Gemini, Copilot).
 2. NVIDIA NIM call dispatch and OpenAI-compatible payload format.
 3. Google Gemini call dispatch and GenerativeLanguage payload format.
 4. Fallback cascade from NVIDIA NIM -> Gemini Flash on error.
 5. Fallback cascade from Gemini Flash -> Copilot on error.
 6. Clean error reporting when all configured providers fail.
 7. Integration with ThreatAnalyzer and provider tracking in report schema.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.threatintelligence.ai_router import (
    DEFAULT_PROVIDER_CHAIN,
    NVIDIA_NIM_TIMEOUT_SECONDS,
    PROVIDER_COPILOT,
    PROVIDER_GEMINI,
    PROVIDER_NVIDIA,
    ThreatIntelAIRouter,
)
from core.threatintelligence.copilot_agents import get_agent_by_name
from core.threatintelligence.threat_analyzer import ThreatAnalysisReport, ThreatAnalyzer, ToolAnalysisResult


def run_checks():
    results = {}
    passed = 0
    failed = 0

    def check(name, condition, details=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"[TEST_23_ai_router:{name}] PASS")
            print(f"  About: {name}")
            print(f"  Output: {details}\n")
            results[name] = True
        else:
            failed += 1
            print(f"[TEST_23_ai_router:{name}] FAIL")
            print(f"  About: {name}")
            print(f"  Output: {details}\n")
            results[name] = False

    # Check 1: Router initialization and provider status detection
    router = ThreatIntelAIRouter(
        nvidia_api_key="test-nv-key",
        gemini_api_key="test-gemini-key",
        nvidia_model="meta/llama-3.3-70b-instruct",
        gemini_model="gemini-2.0-flash",
        provider_chain=DEFAULT_PROVIDER_CHAIN,
    )
    status = router.get_provider_status()
    c1 = (
        status["nvidia_nim"]["configured"] is True
        and status["nvidia_nim"]["model"] == "meta/llama-3.3-70b-instruct"
        and status["google_gemini"]["configured"] is True
        and status["google_gemini"]["model"] == "gemini-2.0-flash"
        and status["github_copilot"]["configured"] is True
        and router.provider_chain == DEFAULT_PROVIDER_CHAIN
    )
    check("router_initialization_and_status", c1, f"Provider status: {status}")

    # Check 2: Tier 1 (NVIDIA NIM) call execution
    mock_nv_response = MagicMock()
    mock_nv_response.status_code = 200
    mock_nv_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "tool": "sysmon",
                        "verdict": "malicious",
                        "confidence": 95,
                        "findings": [{"severity": "high", "indicator": "Injection", "description": "Process hollowing"}],
                        "iocs": [],
                        "summary": "Malicious activity detected by NVIDIA NIM",
                    })
                }
            }
        ]
    }

    async def _test_nvidia_success():
        observed_timeouts = []
        original_wait_for = asyncio.wait_for

        async def _spy_wait_for(awaitable, *, timeout):
            observed_timeouts.append(timeout)
            return await original_wait_for(awaitable, timeout=timeout)

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_nv_response
            with patch("core.threatintelligence.ai_router.asyncio.wait_for", new=_spy_wait_for):
                res = await router.chat(
                    agent_name="sysmon-analyzer",
                    prompt="Test sysmon prompt data",
                )
            # Verify URL and authorization header
            call_url = mock_post.call_args[0][0]
            call_headers = mock_post.call_args[1]["headers"]
            call_json = mock_post.call_args[1]["json"]
            c2_url = "integrate.api.nvidia.com" in call_url
            c2_auth = call_headers.get("Authorization") == "Bearer test-nv-key"
            c2_model = call_json.get("model") == "meta/llama-3.3-70b-instruct"
            c2_provider = res.get("provider") == PROVIDER_NVIDIA
            c2_timeout = observed_timeouts == [NVIDIA_NIM_TIMEOUT_SECONDS]
            return c2_url and c2_auth and c2_model and c2_provider and c2_timeout, {
                "provider": res.get("provider"),
                "model": res.get("model"),
                "nvidia_timeout_seconds": observed_timeouts,
            }

    ok2, res2 = asyncio.run(_test_nvidia_success())
    check("tier1_nvidia_nim_dispatch", ok2, f"NVIDIA NIM response: provider={res2.get('provider')}, model={res2.get('model')}")

    # Check 3: Tier 2 (Google Gemini) fallback when NVIDIA fails
    mock_gemini_response = MagicMock()
    mock_gemini_response.status_code = 200
    mock_gemini_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "tool": "procmon",
                                "verdict": "suspicious",
                                "confidence": 80,
                                "findings": [],
                                "iocs": [],
                                "summary": "Suspicious activity detected by Gemini Flash",
                            })
                        }
                    ]
                }
            }
        ]
    }

    async def _test_gemini_fallback():
        with patch.object(router, "_call_nvidia_nim", side_effect=RuntimeError("NVIDIA 429 Rate Limit Exceeded")), \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_gemini_post:
            mock_gemini_post.return_value = mock_gemini_response
            res = await router.chat(
                agent_name="procmon-analyzer",
                prompt="Test procmon prompt data",
            )
            call_url = mock_gemini_post.call_args[0][0]
            c3_url = "generativelanguage.googleapis.com" in call_url and "gemini-2.0-flash" in call_url
            c3_provider = res.get("provider") == PROVIDER_GEMINI
            return c3_url and c3_provider, res

    ok3, res3 = asyncio.run(_test_gemini_fallback())
    check("tier2_gemini_fallback_on_nvidia_failure", ok3, f"Gemini response: provider={res3.get('provider')}, model={res3.get('model')}")

    async def _test_nvidia_timeout_fallback():
        with patch.object(router, "_call_nvidia_nim", new_callable=AsyncMock) as mock_nvidia, \
             patch.object(router, "_call_gemini", new_callable=AsyncMock) as mock_gemini:
            mock_nvidia.side_effect = asyncio.TimeoutError()
            mock_gemini.return_value = json.dumps({"tool": "metadata", "verdict": "clean"})
            res = await router.chat(
                agent_name="metadata-analyzer",
                prompt="Test metadata prompt data",
            )
            return (
                res.get("provider") == PROVIDER_GEMINI
                and mock_gemini.called
                and mock_nvidia.await_args.kwargs.get("timeout") == NVIDIA_NIM_TIMEOUT_SECONDS
            ), res

    ok_timeout, res_timeout = asyncio.run(_test_nvidia_timeout_fallback())
    check(
        "nvidia_timeout_uses_two_minute_deadline_then_falls_back",
        ok_timeout,
        f"Fallback provider={res_timeout.get('provider')}; NVIDIA deadline={NVIDIA_NIM_TIMEOUT_SECONDS:.0f}s",
    )

    # Check 4: Tier 3 (Copilot) fallback when both NVIDIA and Gemini fail
    async def _test_copilot_fallback():
        with patch.object(router, "_call_nvidia_nim", side_effect=RuntimeError("NVIDIA 401 Unauthorized")), \
             patch.object(router, "_call_gemini", side_effect=RuntimeError("Gemini Quota Exceeded")), \
             patch.object(router, "_call_copilot", new_callable=AsyncMock) as mock_copilot:
            mock_copilot.return_value = json.dumps({
                "tool": "network",
                "verdict": "malicious",
                "confidence": 90,
                "findings": [],
                "iocs": [],
                "summary": "Handled via Copilot fallback",
            })
            res = await router.chat(
                agent_name="network-analyzer",
                prompt="Test network prompt data",
            )
            c4_called = mock_copilot.called
            c4_provider = res.get("provider") == PROVIDER_COPILOT
            return c4_called and c4_provider, res

    ok4, res4 = asyncio.run(_test_copilot_fallback())
    check("tier3_copilot_fallback_on_dual_failure", ok4, f"Copilot fallback response: provider={res4.get('provider')}")

    # Check 5: Error raised when all providers fail
    async def _test_all_fail():
        with patch.object(router, "_call_nvidia_nim", side_effect=RuntimeError("NV Error")), \
             patch.object(router, "_call_gemini", side_effect=RuntimeError("Gemini Error")), \
             patch.object(router, "_call_copilot", side_effect=RuntimeError("Copilot Error")):
            try:
                await router.chat(agent_name="sysmon-analyzer", prompt="Prompt")
                return False, "Did not raise"
            except RuntimeError as exc:
                return "All AI providers in chain failed" in str(exc), str(exc)

    ok5, err5 = asyncio.run(_test_all_fail())
    check("all_providers_failure_handling", ok5, f"Caught expected RuntimeError: {err5}")

    # Check 6: ThreatAnalyzer default integration
    analyzer = ThreatAnalyzer()
    service = analyzer._get_service()
    c6 = isinstance(service, ThreatIntelAIRouter)
    check("threat_analyzer_uses_ai_router", c6, f"ThreatAnalyzer default service type: {type(service).__name__}")

    # Check 7: Report schema includes provider attribute
    tr = ToolAnalysisResult(tool="sysmon", agent_name="sysmon-analyzer", provider=PROVIDER_NVIDIA)
    tr_dict = tr.to_dict()
    rep = ThreatAnalysisReport(analysis_id="test_id", provider=PROVIDER_GEMINI, model="gemini-2.0-flash")
    rep_dict = rep.to_dict()
    c7 = (
        tr_dict.get("provider") == PROVIDER_NVIDIA
        and rep_dict.get("provider") == PROVIDER_GEMINI
        and rep_dict.get("model") == "gemini-2.0-flash"
    )
    check("report_schema_provider_tracking", c7, f"ToolResult provider: {tr_dict.get('provider')}, Report provider: {rep_dict.get('provider')}")

    print("=" * 60)
    print(f"TEST_23_ai_router: {passed} PASS, {failed} FAIL")
    print("=" * 60)

    if failed > 0:
        print("[TEST_23_ai_router] FAIL")
        sys.exit(1)
    else:
        print("[TEST_23_ai_router] PASS")
        print("About: Multi-provider AI fallback router (NVIDIA NIM -> Gemini Flash -> Copilot)")
        print("Output:")
        print(json.dumps({"passed": passed, "failed": failed}, indent=2))
        sys.exit(0)


if __name__ == "__main__":
    run_checks()
