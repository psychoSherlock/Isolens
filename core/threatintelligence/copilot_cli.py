"""CLI entrypoint for the standalone threat intelligence Copilot integration."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    # Allow direct execution: python3 core/threatintelligence/copilot_cli.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from core.threatintelligence.copilot_service import (  # type: ignore
        ThreatIntelCopilotService,
        build_agent_switch_prompt,
    )
else:
    from .copilot_service import ThreatIntelCopilotService, build_agent_switch_prompt


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Threat intelligence Copilot SDK CLI")
    parser.add_argument("--model", default=None, help="Optional model ID to use")
    parser.add_argument(
        "--github-token",
        default=os.getenv("GITHUB_TOKEN"),
        help="Optional GitHub token (defaults to GITHUB_TOKEN env)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("auth-status", help="Show Copilot authentication status")
    subparsers.add_parser("list-agents", help="List local selectable agent profiles")
    subparsers.add_parser("list-models", help="List models available in Copilot runtime")

    chat_parser = subparsers.add_parser("chat", help="Chat with a selected agent")
    chat_parser.add_argument("--agent", required=True, help="Agent name from list-agents")
    chat_parser.add_argument("--prompt", default=None, help="Single prompt to send")
    chat_parser.add_argument("--timeout", type=float, default=120.0, help="Wait timeout in seconds")
    chat_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive REPL mode for the selected agent",
    )
    chat_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be sent without calling Copilot",
    )

    return parser


async def _run_async(args: argparse.Namespace) -> int:
    service = ThreatIntelCopilotService(
        model=args.model,
        working_directory=str(Path.cwd()),
        github_token=args.github_token,
    )

    if args.command == "auth-status":
        status = await service.get_auth_status()
        print(json.dumps(status.to_dict(), indent=2))
        return 0

    if args.command == "list-agents":
        payload = [
            {
                "name": agent.name,
                "display_name": agent.display_name,
                "description": agent.description,
            }
            for agent in service.list_agents()
        ]
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "list-models":
        models = await service.list_models()
        print(json.dumps([model.to_dict() for model in models], indent=2))
        return 0

    if args.command == "chat":
        if args.dry_run:
            preview = {
                "agent": args.agent,
                "command_prompt": build_agent_switch_prompt(args.agent, args.prompt or "<interactive>"),
                "model": args.model,
                "interactive": bool(args.interactive),
                "timeout": args.timeout,
            }
            print(json.dumps(preview, indent=2))
            return 0

        if args.interactive:
            print(f"Interactive mode started for agent '{args.agent}'. Type 'exit' to quit.")
            while True:
                user_prompt = input("> ").strip()
                if not user_prompt:
                    continue
                if user_prompt.lower() in {"exit", "quit"}:
                    return 0
                result = await service.chat(agent_name=args.agent, prompt=user_prompt, timeout=args.timeout)
                print(result["response"])
            
        if not args.prompt:
            raise ValueError("--prompt is required when --interactive is not set")

        result = await service.chat(agent_name=args.agent, prompt=args.prompt, timeout=args.timeout)
        print(json.dumps(result, indent=2))
        return 0

    raise ValueError(f"Unsupported command: {args.command}")


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        return asyncio.run(_run_async(args))
    except KeyboardInterrupt:
        return 130
    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
