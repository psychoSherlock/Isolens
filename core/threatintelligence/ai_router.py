"""AI Model Router for Threat Intelligence.

Implements an intelligent 3-tier cascade fallback mechanism for AI analysis:
  1. Tier 1 (Primary): NVIDIA NIM API (OpenAI-compatible via https://integrate.api.nvidia.com/v1)
  2. Tier 2 (Fallback): Google Gemini API (latest Flash model via Generative Language API)
  3. Tier 3 (Final): GitHub Copilot SDK (local authenticated session with gpt-5-mini)

If Tier 1 fails (rate limit, quota exceeded, network error, or invalid key),
the router automatically cascades to Tier 2. If Tier 2 fails, it falls back
to Tier 3.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from .copilot_agents import ThreatIntelAgent, list_default_agents
from .copilot_service import ThreatIntelCopilotService

# Load .env if present
try:
    from dotenv import load_dotenv

    _project_root = Path(__file__).resolve().parents[2]
    env_path = _project_root / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass

log = logging.getLogger("isolens.ai_router")

# ---------------------------------------------------------------------------
# Provider Constants & Defaults
# ---------------------------------------------------------------------------
PROVIDER_NVIDIA = "nvidia-nim"
PROVIDER_GEMINI = "google-gemini"
PROVIDER_COPILOT = "copilot"
PROVIDER_LOCAL = "local-ollama"

DEFAULT_PROVIDER_CHAIN = [PROVIDER_NVIDIA, PROVIDER_GEMINI, PROVIDER_COPILOT]

DEFAULT_NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"

DEFAULT_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"

DEFAULT_LOCAL_URL = "http://10.42.0.88:11434"
DEFAULT_LOCAL_MODEL = "llama3.1:8b"
NVIDIA_NIM_TIMEOUT_SECONDS = 120.0


class ThreatIntelAIRouter:
    """Multi-provider AI Router with automatic failover across NVIDIA NIM, Gemini, and Copilot."""

    def __init__(
        self,
        *,
        working_directory: Optional[str] = None,
        github_token: Optional[str] = None,
        nvidia_api_key: Optional[str] = None,
        nvidia_model: Optional[str] = None,
        nvidia_base_url: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        gemini_model: Optional[str] = None,
        local_model_url: Optional[str] = None,
        local_model: Optional[str] = None,
        provider_chain: Optional[List[str]] = None,
    ) -> None:
        self.working_directory = working_directory
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")

        # NVIDIA NIM Settings
        self.nvidia_api_key = (
            nvidia_api_key
            or os.getenv("NVIDIA_API_KEY")
            or os.getenv("NIM_API_KEY")
            or ""
        ).strip()
        self.nvidia_model = (
            nvidia_model
            or os.getenv("NVIDIA_NIM_MODEL")
            or DEFAULT_NVIDIA_MODEL
        ).strip()
        self.nvidia_base_url = (
            nvidia_base_url
            or os.getenv("NVIDIA_BASE_URL")
            or DEFAULT_NVIDIA_BASE_URL
        ).rstrip("/")

        # Google Gemini Settings
        self.gemini_api_key = (
            gemini_api_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or ""
        ).strip()
        self.gemini_model = (
            gemini_model
            or os.getenv("GEMINI_MODEL")
            or DEFAULT_GEMINI_MODEL
        ).strip()
        self.gemini_base_url = DEFAULT_GEMINI_BASE_URL.rstrip("/")

        # Local / LAN Model Settings (Ollama API compatible)
        self.local_model_url = (
            local_model_url
            or os.getenv("LOCAL_MODEL_URL")
            or os.getenv("OLLAMA_BASE_URL")
            or DEFAULT_LOCAL_URL
        ).rstrip("/")
        self.local_model = (
            local_model
            or os.getenv("LOCAL_MODEL_NAME")
            or os.getenv("OLLAMA_MODEL")
            or DEFAULT_LOCAL_MODEL
        ).strip()

        # Chain sequence (explicit argument > AI_PROVIDER_CHAIN env > DEFAULT_PROVIDER_CHAIN)
        if provider_chain is not None:
            self.provider_chain = list(provider_chain)
        else:
            env_chain = os.getenv("AI_PROVIDER_CHAIN")
            if env_chain:
                self.provider_chain = [p.strip() for p in env_chain.split(",") if p.strip()]
            else:
                self.provider_chain = list(DEFAULT_PROVIDER_CHAIN)

        self._agents = list_default_agents()
        self._copilot_service: Optional[ThreatIntelCopilotService] = None

    @property
    def model(self) -> str:
        """Return a string identifying the active primary model and fallback configuration."""
        configured = []
        if self.nvidia_api_key:
            configured.append(f"NVIDIA({self.nvidia_model})")
        if self.gemini_api_key:
            configured.append(f"Gemini({self.gemini_model})")
        copilot_m = os.getenv("COPILOT_MODEL", "gpt-4.1")
        configured.append(f"Copilot({copilot_m})")
        if self.local_model_url:
            configured.append(f"Local({self.local_model}@{self.local_model_url})")

        return " -> ".join(configured)

    def list_agents(self) -> List[ThreatIntelAgent]:
        """List locally configured agent profiles."""
        return list(self._agents)

    def get_provider_status(self) -> Dict[str, Any]:
        """Inspect and return the availability of all AI providers."""
        copilot_m = os.getenv("COPILOT_MODEL", "gpt-4.1")
        return {
            "nvidia_nim": {
                "configured": bool(self.nvidia_api_key),
                "model": self.nvidia_model,
                "base_url": self.nvidia_base_url,
                "priority": 1,
            },
            "google_gemini": {
                "configured": bool(self.gemini_api_key),
                "model": self.gemini_model,
                "priority": 2,
            },
            "github_copilot": {
                "configured": True,  # Uses local copilot auth or token
                "model": copilot_m,
                "priority": 3,
            },
            "local_ollama": {
                "configured": bool(self.local_model_url),
                "model": self.local_model,
                "url": self.local_model_url,
                "priority": 4,
            },
            "active_chain": self.provider_chain,
        }

    # -----------------------------------------------------------------------
    # Provider Callers
    # -----------------------------------------------------------------------

    async def _call_nvidia_nim(
        self, agent: ThreatIntelAgent, prompt: str, timeout: float = 120.0
    ) -> str:
        """Call NVIDIA NIM via OpenAI-compatible chat completions API."""
        if not self.nvidia_api_key:
            raise ValueError("NVIDIA API key not configured (set NVIDIA_API_KEY or NIM_API_KEY).")

        url = f"{self.nvidia_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.nvidia_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "model": self.nvidia_model,
            "messages": [
                {"role": "system", "content": agent.prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                err_text = resp.text[:400]
                raise RuntimeError(
                    f"NVIDIA NIM API error {resp.status_code}: {err_text}"
                )
            data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            raise ValueError("NVIDIA NIM returned response with empty choices.")

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise ValueError("NVIDIA NIM returned empty message content.")

        return str(content)

    async def _call_gemini(
        self, agent: ThreatIntelAgent, prompt: str, timeout: float = 120.0
    ) -> str:
        """Call Google Gemini API using the latest Flash model."""
        if not self.gemini_api_key:
            raise ValueError("Gemini API key not configured (set GEMINI_API_KEY or GOOGLE_API_KEY).")

        url = f"{self.gemini_base_url}/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {
                "parts": [{"text": agent.prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 4096,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                err_text = resp.text[:400]
                raise RuntimeError(
                    f"Google Gemini API error {resp.status_code}: {err_text}"
                )
            data = resp.json()

        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Google Gemini returned response with empty candidates.")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise ValueError("Google Gemini returned response with empty content parts.")

        content = parts[0].get("text", "")
        if not content:
            raise ValueError("Google Gemini returned empty text content.")

        return str(content)

    async def _call_copilot(
        self, agent: ThreatIntelAgent, prompt: str, timeout: float = 120.0
    ) -> str:
        """Call GitHub Copilot SDK service as final fallback."""
        if self._copilot_service is None:
            self._copilot_service = ThreatIntelCopilotService(
                working_directory=self.working_directory,
                github_token=self.github_token,
            )

        resp = await self._copilot_service.chat(
            agent_name=agent.name,
            prompt=prompt,
            timeout=timeout,
        )
        content = resp.get("response", "")
        if not content:
            raise ValueError("Copilot returned empty response.")
        return str(content)

    async def _call_local_ollama(
        self, agent: ThreatIntelAgent, prompt: str, timeout: float = 60.0
    ) -> str:
        """Call locally or LAN-hosted Ollama model (e.g. at 10.42.0.88:11434)."""
        url = f"{self.local_model_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.local_model,
            "messages": [
                {"role": "system", "content": agent.prompt},
                {"role": "user", "content": prompt},
            ],
            "format": "json",
            "stream": False,
        }
        client_timeout = httpx.Timeout(timeout=timeout, connect=4.0)
        async with httpx.AsyncClient(timeout=client_timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Local Ollama model error {resp.status_code}: {resp.text[:300]}"
                )
            data = resp.json()

        content = data.get("message", {}).get("content", "")
        if not content:
            raise ValueError("Local Ollama model returned empty content.")
        return str(content)

    # -----------------------------------------------------------------------
    # Main Chat Router Interface
    # -----------------------------------------------------------------------

    async def chat(
        self,
        *,
        agent_name: str,
        prompt: str,
        timeout: float = 120.0,
    ) -> Dict[str, Any]:
        """Dispatch a prompt to the specified agent with 3-tier cascade fallback.

        1. Tier 1: NVIDIA NIM
        2. Tier 2: Google Gemini Flash
        3. Tier 3: GitHub Copilot SDK

        Returns:
            Dict containing agent name, response, provider used, and model info.
        """
        if not prompt.strip():
            raise ValueError("Prompt must not be empty.")

        agent = next((item for item in self._agents if item.name == agent_name), None)
        if agent is None:
            supported = ", ".join(a.name for a in self._agents)
            raise ValueError(f"Unknown agent '{agent_name}'. Supported agents: {supported}")

        errors: List[str] = []

        for provider in self.provider_chain:
            t0 = time.time()
            try:
                if provider == PROVIDER_NVIDIA:
                    if not self.nvidia_api_key:
                        log.debug("NVIDIA NIM skipped: No API key configured.")
                        continue
                    log.info("Routing request for '%s' to NVIDIA NIM (%s)...", agent_name, self.nvidia_model)
                    try:
                        response_text = await asyncio.wait_for(
                            self._call_nvidia_nim(
                                agent,
                                prompt,
                                timeout=NVIDIA_NIM_TIMEOUT_SECONDS,
                            ),
                            timeout=NVIDIA_NIM_TIMEOUT_SECONDS,
                        )
                    except (asyncio.TimeoutError, httpx.TimeoutException) as exc:
                        raise TimeoutError(
                            f"NVIDIA NIM request timed out after {NVIDIA_NIM_TIMEOUT_SECONDS:.0f} seconds"
                        ) from exc
                    elapsed = round(time.time() - t0, 2)
                    log.info("NVIDIA NIM successfully handled '%s' in %.2fs", agent_name, elapsed)
                    return {
                        "agent": agent.name,
                        "agent_display_name": agent.display_name,
                        "prompt": prompt,
                        "response": response_text,
                        "provider": PROVIDER_NVIDIA,
                        "model": self.nvidia_model,
                        "latency_sec": elapsed,
                    }

                elif provider == PROVIDER_GEMINI:
                    if not self.gemini_api_key:
                        log.debug("Google Gemini skipped: No API key configured.")
                        continue
                    log.info("Routing request for '%s' to Google Gemini (%s)...", agent_name, self.gemini_model)
                    response_text = await self._call_gemini(agent, prompt, timeout=timeout)
                    elapsed = round(time.time() - t0, 2)
                    log.info("Google Gemini successfully handled '%s' in %.2fs", agent_name, elapsed)
                    return {
                        "agent": agent.name,
                        "agent_display_name": agent.display_name,
                        "prompt": prompt,
                        "response": response_text,
                        "provider": PROVIDER_GEMINI,
                        "model": self.gemini_model,
                        "latency_sec": elapsed,
                    }

                elif provider == PROVIDER_COPILOT:
                    copilot_m = os.getenv("COPILOT_MODEL", "gpt-4.1")
                    log.info("Routing request for '%s' to GitHub Copilot (%s)...", agent_name, copilot_m)
                    response_text = await self._call_copilot(agent, prompt, timeout=timeout)
                    elapsed = round(time.time() - t0, 2)
                    log.info("GitHub Copilot successfully handled '%s' in %.2fs", agent_name, elapsed)
                    return {
                        "agent": agent.name,
                        "agent_display_name": agent.display_name,
                        "prompt": prompt,
                        "response": response_text,
                        "provider": PROVIDER_COPILOT,
                        "model": copilot_m,
                        "latency_sec": elapsed,
                    }

                elif provider == PROVIDER_LOCAL:
                    log.info("Routing request for '%s' to Local/LAN Model (%s at %s)...", agent_name, self.local_model, self.local_model_url)
                    response_text = await self._call_local_ollama(agent, prompt, timeout=timeout)
                    elapsed = round(time.time() - t0, 2)
                    log.info("Local/LAN model successfully handled '%s' in %.2fs", agent_name, elapsed)
                    return {
                        "agent": agent.name,
                        "agent_display_name": agent.display_name,
                        "prompt": prompt,
                        "response": response_text,
                        "provider": PROVIDER_LOCAL,
                        "model": self.local_model,
                        "latency_sec": elapsed,
                    }

            except Exception as exc:
                err_msg = f"{provider} failed ({type(exc).__name__}): {exc!r}"
                log.warning(
                    "[AIRouter] %s. Cascading to next provider in chain...",
                    err_msg,
                    exc_info=True,
                )
                errors.append(err_msg)

        # If all providers failed or no keys were configured
        error_summary = " | ".join(errors) if errors else "No AI providers were configured or available."
        raise RuntimeError(f"All AI providers in chain failed: {error_summary}")
