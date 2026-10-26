"""Standalone Copilot SDK service for threat intelligence workflows.

All sessions are forced to use the ``gpt-5-mini`` model regardless of
caller-supplied overrides.  This keeps token cost low and response
latency predictable across all tool-analyst and summarizer agents.
"""

from __future__ import annotations

import os
from typing import Any

from copilot import CopilotClient, PermissionHandler
from copilot.generated.session_events import SessionEvent, SessionEventType

from .copilot_agents import ThreatIntelAgent, list_default_agents

# ─── Enforced model ──────────────────────────────────────────────────────
REQUIRED_MODEL = "gpt-5-mini"


class ThreatIntelCopilotService:
    """Wrapper around ``github-copilot-sdk`` for local threat-intel usage.

    The *model* parameter is intentionally ignored — every session is
    pinned to ``gpt-5-mini`` to ensure consistent behaviour and lower
    token costs across the analysis pipeline.
    """

    def __init__(
        self,
        *,
        model: str | None = None,          # ignored — always gpt-5-mini
        working_directory: str | None = None,
        github_token: str | None = None,
    ) -> None:
        # Always force gpt-5-mini regardless of what was passed
        self.model = REQUIRED_MODEL
        self.working_directory = working_directory
        self.github_token = github_token
        self._agents = list_default_agents()

    def list_agents(self) -> list[ThreatIntelAgent]:
        """List locally configured agent profiles."""
        return list(self._agents)

    async def get_auth_status(self) -> Any:
        """Fetch Copilot authentication state from the SDK client."""
        options: dict[str, Any] = {}
        if self.working_directory:
            options["cwd"] = self.working_directory
        if self.github_token:
            options["github_token"] = self.github_token
        client = CopilotClient(options)
        await client.start()
        try:
            return await client.get_auth_status()
        finally:
            await client.stop()

    async def list_models(self) -> list[Any]:
        """List models exposed by the authenticated Copilot runtime."""
        options: dict[str, Any] = {}
        if self.working_directory:
            options["cwd"] = self.working_directory
        if self.github_token:
            options["github_token"] = self.github_token
        client = CopilotClient(options)
        await client.start()
        try:
            return await client.list_models()
        finally:
            await client.stop()

    async def chat(self, *, agent_name: str, prompt: str, timeout: float = 120.0) -> dict[str, Any]:
        """Send a prompt via Copilot to the selected agent and return the response."""
        if not prompt.strip():
            raise ValueError("Prompt must not be empty.")

        agent = next((item for item in self._agents if item.name == agent_name), None)
        if agent is None:
            supported = ", ".join(a.name for a in self._agents)
            raise ValueError(f"Unknown agent '{agent_name}'. Supported agents: {supported}")

        options: dict[str, Any] = {}
        if self.working_directory:
            options["cwd"] = self.working_directory
        if self.github_token:
            options["github_token"] = self.github_token

        custom_agents = [entry.to_custom_agent_config() for entry in self._agents]
        active_model = os.getenv("COPILOT_MODEL", "gpt-4.1")
        session_config: dict[str, Any] = {
            "model": active_model,
            "on_permission_request": PermissionHandler.approve_all,
            "custom_agents": custom_agents,
            "streaming": False,
        }
        if self.working_directory:
            session_config["working_directory"] = self.working_directory

        command_prompt = build_agent_switch_prompt(agent.name, prompt)

        client = CopilotClient(options)
        await client.start()
        try:
            auth_status = await client.get_auth_status()
            if not auth_status.isAuthenticated and not self.github_token:
                message = auth_status.statusMessage or "Copilot is not authenticated."
                raise RuntimeError(
                    "Copilot authentication required. "
                    "Run `python3 core/threatintelligence/copilot_cli.py auth-status` and sign in first. "
                    f"Status: {message}"
                )

            session = await client.create_session(session_config)
            final_event = None
            history: list[Any] = []
            try:
                import asyncio
                idle_event = asyncio.Event()
                error_event: Exception | None = None
                last_msg: Any = None

                def event_handler(event: Any) -> None:
                    nonlocal last_msg, error_event
                    if event.type == SessionEventType.ASSISTANT_MESSAGE:
                        last_msg = event
                        if getattr(event.data, "content", None):
                            # In non-streaming mode, full response is delivered with ASSISTANT_MESSAGE
                            idle_event.set()
                    elif event.type == SessionEventType.SESSION_IDLE:
                        idle_event.set()
                    elif event.type == SessionEventType.SESSION_ERROR:
                        error_event = Exception(
                            f"Session error: {getattr(event.data, 'message', str(event.data))}"
                        )
                        idle_event.set()

                unsubscribe = session.on(event_handler)
                try:
                    await session.send({"prompt": command_prompt})
                    try:
                        await asyncio.wait_for(idle_event.wait(), timeout=timeout)
                    except TimeoutError:
                        if last_msg is None:
                            raise TimeoutError(f"Timeout after {timeout}s waiting for Copilot response")
                    if error_event and last_msg is None:
                        raise error_event
                    final_event = last_msg
                    try:
                        history = await session.get_messages()
                    except Exception:
                        history = []
                finally:
                    unsubscribe()
            finally:
                await session.destroy()
        finally:
            await client.stop()

        response_text = _extract_assistant_text(final_event, history)
        return {
            "agent": agent.name,
            "agent_display_name": agent.display_name,
            "prompt": prompt,
            "response": response_text,
            "event_count": len(history),
        }


def _extract_assistant_text(final_event: SessionEvent | None, history: list[SessionEvent]) -> str:
    """Extract assistant response text from final event, with history fallback."""
    if final_event and getattr(final_event.data, "content", None):
        return str(final_event.data.content)

    for event in reversed(history):
        if event.type == SessionEventType.ASSISTANT_MESSAGE and getattr(event.data, "content", None):
            return str(event.data.content)

    for event in reversed(history):
        if event.type == SessionEventType.SESSION_ERROR and getattr(event.data, "message", None):
            return f"[session.error] {event.data.message}"

    return ""


def build_agent_switch_prompt(agent_name: str, prompt: str) -> str:
    """Build the slash command prompt used to select an agent and send content."""
    return f"/agent {agent_name}\n{prompt}"
