# Threat Intelligence Copilot SDK Setup

This integration is standalone and currently **not** connected to malware execution workflows.

## Install

From project root:

```bash
./.venv/bin/python -m pip install -r requirements.txt
```

## Commands

List auth state:

```bash
python3 core/threatintelligence/copilot_cli.py auth-status
```

List local selectable agents:

```bash
python3 core/threatintelligence/copilot_cli.py list-agents
```

List models from Copilot runtime:

```bash
python3 core/threatintelligence/copilot_cli.py list-models
```

Chat with a selected agent (single prompt):

```bash
python3 core/threatintelligence/copilot_cli.py chat --agent intel-brief --prompt "Summarize TTPs for this report"
```

Chat with a selected agent (interactive):

```bash
python3 core/threatintelligence/copilot_cli.py chat --agent malware-triage --interactive
```

Dry run preview (no Copilot call):

```bash
python3 core/threatintelligence/copilot_cli.py chat --agent ioc-analyst --prompt "extract IOCs" --dry-run
```

## Notes

- The CLI uses the SDK package `github-copilot-sdk`.
- If not authenticated, run `auth-status` and complete sign-in flow for your environment.
- Optional token support: set `GITHUB_TOKEN` or pass `--github-token`.
