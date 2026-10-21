"""Threat intelligence integrations.

Exports
-------
- ``ai_router``        – Multi-provider AI router with fallback cascade (NVIDIA NIM -> Gemini -> Copilot)
- ``copilot_agents``   – Per-tool and summarizer agent definitions
- ``copilot_service``  – Copilot SDK wrapper (gpt-5-mini enforced)
- ``threat_analyzer``  – Multi-agent AI analysis pipeline
"""

from .ai_router import (
    DEFAULT_PROVIDER_CHAIN,
    PROVIDER_COPILOT,
    PROVIDER_GEMINI,
    PROVIDER_NVIDIA,
    ThreatIntelAIRouter,
)

