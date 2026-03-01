"""Threat Analyzer — multi-agent AI analysis pipeline for IsoLens reports.

Reads collector artifacts from an analysis report directory, dispatches
each tool's data to a specialized Copilot agent, collects their structured
JSON responses, then feeds everything to the *threat-summarizer* agent for
a final risk score and executive summary.

Architecture
────────────
  report_dir/
    artifacts/
      sysmon/sysmon_summary.json    → sysmon-analyzer agent
      procmon/procmon_summary.json  → procmon-analyzer agent
      network/network_summary.json  → network-analyzer agent
      handle/handle_snapshot.txt    → handle-analyzer agent
      tcpvcon/tcpvcon_snapshot.csv  → tcpvcon-analyzer agent
      metadata.json                 → metadata-analyzer agent

  All per-tool JSON responses      → threat-summarizer agent
                                   → final threat_report JSON

Results are saved to ``report_dir/ai_analysis/``.
"""

from __future__ import annotations

import asyncio
import csv
import datetime
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("isolens.threat_analyzer")

# ─── Default paths ────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORTS_DIR = _PROJECT_ROOT / "core" / "storage" / "reports"

# Maximum characters of raw data to send per tool (keeps tokens in check)
MAX_TOOL_PAYLOAD_CHARS = 6000


# ─── Data classes ─────────────────────────────────────────────────────────

@dataclass
class ToolAnalysisResult:
    """Result from a single tool-specific agent."""

    tool: str
    agent_name: str
    raw_response: str = ""
    verdict: str = "inconclusive"
    confidence: int = 0
    findings_count: int = 0
    iocs_count: int = 0
    summary: str = ""
    findings: List[Dict[str, str]] = field(default_factory=list)
    iocs: List[Dict[str, str]] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "agent_name": self.agent_name,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "findings_count": self.findings_count,
            "iocs_count": self.iocs_count,
            "summary": self.summary,
            "findings": self.findings,
            "iocs": self.iocs,
            "raw_response": self.raw_response,
            "error": self.error,
        }


@dataclass
class ThreatAnalysisReport:
    """Final AI-driven threat analysis for an IsoLens report."""

    analysis_id: str
    model: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "pending"          # pending | running | complete | failed
    error: Optional[str] = None
    tool_results: List[ToolAnalysisResult] = field(default_factory=list)
    # Final summary fields (parsed from threat-summarizer JSON)
    risk_score: int = 0
    threat_level: str = "none"
    malware_type: str = "unknown"
    malware_family: str = "unknown"
    platform: str = "unknown"
    classification_confidence: int = 0
    executive_summary: str = ""
    detailed_analysis: str = ""
    key_findings: List[Dict[str, str]] = field(default_factory=list)
    iocs: List[Dict[str, str]] = field(default_factory=list)
    mitre_attack: List[Dict[str, str]] = field(default_factory=list)
    recommendations: List[Dict[str, str]] = field(default_factory=list)
    raw_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "model": self.model,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "error": self.error,
            "risk_score": self.risk_score,
            "threat_level": self.threat_level,
            "classification": {
                "malware_type": self.malware_type,
                "malware_family": self.malware_family,
                "platform": self.platform,
                "confidence": self.classification_confidence,
            },
            "executive_summary": self.executive_summary,
            "detailed_analysis": self.detailed_analysis,
            "key_findings": self.key_findings,
            "iocs": self.iocs,
            "mitre_attack": self.mitre_attack,
            "recommendations": self.recommendations,
            "tool_results": [r.to_dict() for r in self.tool_results],
            "raw_summary": self.raw_summary,
        }


# ─── Helper: read collector data ─────────────────────────────────────────

def _read_json(path: str) -> Optional[dict]:
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _read_text(path: str, max_chars: int = MAX_TOOL_PAYLOAD_CHARS) -> Optional[str]:
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read(max_chars)
        except Exception:
            return None
    return None


def _read_csv_as_text(path: str, max_rows: int = 200) -> Optional[str]:
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                lines = []
                for i, row in enumerate(reader):
                    if i >= max_rows:
                        lines.append(f"... truncated ({i}+ rows)")
                        break
                    lines.append(",".join(row))
                return "\n".join(lines)
        except Exception:
            return None
    return None


def _truncate_json(data: Any, max_chars: int = MAX_TOOL_PAYLOAD_CHARS) -> str:
    """Serialize JSON data and truncate to stay within token budget."""
    raw = json.dumps(data, indent=None, default=str)
    if len(raw) > max_chars:
        return raw[:max_chars] + "\n... [truncated]"
    return raw


# ─── Helper: parse JSON responses ─────────────────────────────────────────

def _clean_json_response(raw: str) -> str:
    """Strip markdown fences and whitespace around the JSON response."""
    text = raw.strip()
    # Remove ```json ... ``` wrappers some models add despite instructions
    if text.startswith("```"):
        first_nl = text.find("\n")
        if first_nl > 0:
            text = text[first_nl + 1:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    # Try to extract JSON object if there's prose around it
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start >= 0 and brace_end > brace_start:
        text = text[brace_start:brace_end + 1]
    return text


def _normalize_tool_findings(items: list) -> List[Dict]:
    """Ensure per-tool findings are {severity, indicator, description}."""
    out = []
    for item in items:
        if isinstance(item, dict):
            out.append({
                "severity": str(item.get("severity", "medium")),
                "indicator": str(item.get("indicator", "")),
                "description": str(item.get("description", "")),
            })
        elif isinstance(item, str):
            out.append({"severity": "medium", "indicator": item[:80], "description": item})
    return out


def _normalize_tool_iocs(items: list) -> List[Dict]:
    """Ensure per-tool IOCs are {type, value}."""
    out = []
    for item in items:
        if isinstance(item, dict):
            out.append({
                "type": str(item.get("type", "unknown")),
                "value": str(item.get("value", "")),
            })
        elif isinstance(item, str):
            out.append({"type": "unknown", "value": item})
    return out


def _parse_tool_json(raw_json: str, result: ToolAnalysisResult) -> None:
    """Parse a tool analysis JSON response into the result dataclass."""
    try:
        data = json.loads(raw_json)
        result.verdict = str(data.get("verdict", "inconclusive")).strip().lower()
        try:
            result.confidence = int(data.get("confidence", 0))
        except (ValueError, TypeError):
            result.confidence = 0
        result.summary = str(data.get("summary", "")).strip()
        findings = data.get("findings", [])
        if isinstance(findings, list):
            result.findings = _normalize_tool_findings(findings)
            result.findings_count = len(result.findings)
        iocs = data.get("iocs", [])
        if isinstance(iocs, list):
            result.iocs = _normalize_tool_iocs(iocs)
            result.iocs_count = len(result.iocs)
    except json.JSONDecodeError as exc:
        # Fallback: agent returned prose instead of JSON — wrap it
        log.warning("Failed to parse tool JSON for %s: %s", result.tool, exc)
        if raw_json.strip():
            result.summary = raw_json.strip()[:2000]
            result.verdict = _infer_verdict_from_text(raw_json)
            result.confidence = 40  # lower confidence for non-JSON
            result.error = f"JSON parse error: {exc}"
        else:
            result.error = f"JSON parse error: {exc}"


def _infer_verdict_from_text(text: str) -> str:
    """Best-effort verdict from plain text when JSON parsing fails."""
    lower = text.lower()
    if any(w in lower for w in ("malicious", "malware", "trojan", "ransomware", "backdoor")):
        return "malicious"
    if any(w in lower for w in ("suspicious", "anomal", "unusual", "concerning")):
        return "suspicious"
    if any(w in lower for w in ("benign", "clean", "legitimate", "safe")):
        return "benign"
    return "inconclusive"


def _normalize_findings(items: list) -> List[Dict]:
    """Ensure each finding is {source, severity, description}."""
    out = []
    for item in items:
        if isinstance(item, dict):
            out.append({
                "source": str(item.get("source", "")),
                "severity": str(item.get("severity", "medium")),
                "description": str(item.get("description", item.get("text", ""))),
            })
        elif isinstance(item, str):
            out.append({"source": "", "severity": "medium", "description": item})
    return out


def _normalize_iocs(items: list) -> List[Dict]:
    """Ensure each IOC is {type, severity, value}."""
    out = []
    for item in items:
        if isinstance(item, dict):
            out.append({
                "type": str(item.get("type", "unknown")),
                "severity": str(item.get("severity", "medium")),
                "value": str(item.get("value", "")),
            })
        elif isinstance(item, str):
            out.append({"type": "unknown", "severity": "medium", "value": item})
    return out


def _normalize_mitre(items: list) -> List[Dict]:
    """Ensure each MITRE technique is {id, name, tactic, description}."""
    out = []
    for item in items:
        if isinstance(item, dict):
            out.append({
                "id": str(item.get("id", item.get("technique_id", ""))),
                "name": str(item.get("name", "")),
                "tactic": str(item.get("tactic", "")),
                "description": str(item.get("description", "")),
            })
        elif isinstance(item, str):
            out.append({"id": "", "name": item, "tactic": "", "description": ""})
    return out


def _normalize_recommendations(items: list) -> List[Dict]:
    """Ensure each recommendation is {priority, action}."""
    out = []
    for item in items:
        if isinstance(item, dict):
            out.append({
                "priority": str(item.get("priority", "medium")),
                "action": str(item.get("action", item.get("text", ""))),
            })
        elif isinstance(item, str):
            out.append({"priority": "medium", "action": item})
    return out


def _parse_summary_json(raw_json: str, report: ThreatAnalysisReport) -> None:
    """Parse a threat_report JSON response into the report dataclass."""
    try:
        data = json.loads(raw_json)
        try:
            report.risk_score = int(data.get("risk_score", 0))
        except (ValueError, TypeError):
            report.risk_score = 0
        report.threat_level = str(data.get("threat_level", "none")).strip().lower()

        classification = data.get("classification", {})
        if isinstance(classification, dict):
            report.malware_type = str(classification.get("malware_type", "unknown")).strip()
            report.malware_family = str(classification.get("malware_family", "unknown")).strip()
            report.platform = str(classification.get("platform", "unknown")).strip()
            try:
                report.classification_confidence = int(classification.get("confidence", 0))
            except (ValueError, TypeError):
                report.classification_confidence = 0
        elif isinstance(classification, str):
            # Model returned a flat string classification
            report.malware_type = classification.strip()
            report.classification_confidence = 50

        report.executive_summary = str(data.get("executive_summary", "")).strip()
        report.detailed_analysis = str(data.get("detailed_analysis", "")).strip()

        # Store structured arrays — normalize shapes for UI
        kf = data.get("key_findings", [])
        report.key_findings = _normalize_findings(kf if isinstance(kf, list) else [])
        iocs = data.get("iocs", [])
        report.iocs = _normalize_iocs(iocs if isinstance(iocs, list) else [])
        mitre = data.get("mitre_attack", [])
        report.mitre_attack = _normalize_mitre(mitre if isinstance(mitre, list) else [])
        recs = data.get("recommendations", [])
        report.recommendations = _normalize_recommendations(recs if isinstance(recs, list) else [])

    except json.JSONDecodeError as exc:
        # Fallback: summarizer returned prose — use it as executive summary
        log.warning("Failed to parse summary JSON: %s", exc)
        if raw_json.strip():
            report.executive_summary = raw_json.strip()[:3000]
            report.detailed_analysis = raw_json.strip()
            # Infer risk from tool results already parsed
            verdicts = [tr.verdict for tr in report.tool_results if tr.verdict != "inconclusive"]
            mal_count = sum(1 for v in verdicts if v == "malicious")
            sus_count = sum(1 for v in verdicts if v == "suspicious")
            if mal_count > 0:
                report.risk_score = min(85, 50 + mal_count * 15)
                report.threat_level = "high" if report.risk_score >= 70 else "medium"
            elif sus_count > 0:
                report.risk_score = min(65, 30 + sus_count * 15)
                report.threat_level = "medium"
            else:
                report.risk_score = 20
                report.threat_level = "low"
            report.error = None  # mark as usable despite JSON failure
        else:
            report.error = f"Summary JSON parse error: {exc}"
        log.warning("Failed to parse summary JSON: %s", exc)


# ─── Collector → Agent mapping ────────────────────────────────────────────

# Maps agent name → function(report_dir) → (payload_text, has_data)
def _load_sysmon(report_dir: str) -> tuple[str, bool]:
    data = _read_json(os.path.join(report_dir, "artifacts", "sysmon", "sysmon_summary.json"))
    if not data:
        return "No Sysmon data was collected for this analysis.", False
    return _truncate_json(data), True


def _load_procmon(report_dir: str) -> tuple[str, bool]:
    data = _read_json(os.path.join(report_dir, "artifacts", "procmon", "procmon_summary.json"))
    if not data:
        return "No Procmon data was collected for this analysis.", False
    return _truncate_json(data), True


def _load_network(report_dir: str) -> tuple[str, bool]:
    data = _read_json(os.path.join(report_dir, "artifacts", "network", "network_summary.json"))
    if not data:
        return "No network capture data was collected for this analysis.", False
    return _truncate_json(data), True


def _load_handle(report_dir: str) -> tuple[str, bool]:
    text = _read_text(os.path.join(report_dir, "artifacts", "handle", "handle_snapshot.txt"))
    if not text or not text.strip():
        return "No handle snapshot data was collected for this analysis.", False
    return text, True


def _load_tcpvcon(report_dir: str) -> tuple[str, bool]:
    text = _read_csv_as_text(os.path.join(report_dir, "artifacts", "tcpvcon", "tcpvcon_snapshot.csv"))
    if not text or not text.strip():
        return "No TCPVcon data was collected for this analysis.", False
    return text, True


def _load_metadata(report_dir: str) -> tuple[str, bool]:
    data = _read_json(os.path.join(report_dir, "artifacts", "metadata.json"))
    manifest = _read_json(os.path.join(report_dir, "analysis_manifest.json"))
    combined: dict[str, Any] = {}
    if manifest:
        combined["manifest"] = {
            "sample_name": manifest.get("sample_name"),
            "status": manifest.get("status"),
            "started_at": manifest.get("started_at"),
            "completed_at": manifest.get("completed_at"),
            "timeout": manifest.get("timeout"),
            "sysmon_events": manifest.get("sysmon_events"),
            "files_collected_count": len(manifest.get("files_collected", [])),
        }
    if data:
        combined["metadata"] = data
    if not combined:
        return "No metadata available for this analysis.", False
    return _truncate_json(combined), True


# Agent name → loader function
TOOL_LOADERS: Dict[str, Any] = {
    "sysmon-analyzer": _load_sysmon,
    "procmon-analyzer": _load_procmon,
    "network-analyzer": _load_network,
    "handle-analyzer": _load_handle,
    "tcpvcon-analyzer": _load_tcpvcon,
    "metadata-analyzer": _load_metadata,
}


# ─── Main analyzer class ─────────────────────────────────────────────────

class ThreatAnalyzer:
    """Orchestrates the multi-agent AI analysis pipeline.

    Parameters
    ----------
    reports_dir : str
        Root directory containing all analysis reports.
    copilot_service : ThreatIntelCopilotService | None
        Pre-configured Copilot service.  If *None*, one is created lazily.
    """

    def __init__(
        self,
        reports_dir: str | None = None,
        copilot_service: Any = None,
    ) -> None:
        self.reports_dir = reports_dir or str(DEFAULT_REPORTS_DIR)
        self._service = copilot_service

    def _get_service(self) -> Any:
        if self._service is None:
            from .copilot_service import ThreatIntelCopilotService
            self._service = ThreatIntelCopilotService(
                working_directory=str(_PROJECT_ROOT),
            )
        return self._service

    # ── Public API ────────────────────────────────────────────────────

    async def analyze_report(self, analysis_id: str) -> ThreatAnalysisReport:
        """Run the full AI analysis pipeline on an existing report.

        1. Load each collector's data from the report directory.
        2. Send each payload to its specialized agent.
        3. Collect all JSON responses.
        4. Feed them to the *threat-summarizer* agent.
        5. Parse the final JSON and save everything.

        Returns the populated ``ThreatAnalysisReport``.
        """
        report = ThreatAnalysisReport(
            analysis_id=analysis_id,
            started_at=datetime.datetime.utcnow().isoformat() + "Z",
        )

        report_dir = os.path.join(self.reports_dir, analysis_id)
        if not os.path.isdir(report_dir):
            report.status = "failed"
            report.error = f"Report directory not found: {analysis_id}"
            return report

        service = self._get_service()
        report.model = service.model
        report.status = "running"

        # ── Phase 1: Per-tool analysis (parallel) ─────────────────────
        tool_responses: Dict[str, str] = {}

        from .copilot_agents import get_tool_agents

        # Prepare all tasks — agents WITH data run in parallel
        async def _run_tool_agent(
            agent_def: Any, tool_name: str, payload_text: str,
        ) -> ToolAnalysisResult:
            result = ToolAnalysisResult(
                tool=tool_name, agent_name=agent_def.name,
            )
            prompt = (
                f"Analyze the following {tool_name} data from a malware sandbox execution.\n"
                f"Sample file: {self._get_sample_name(report_dir)}\n\n"
                f"--- BEGIN {tool_name.upper()} DATA ---\n"
                f"{payload_text}\n"
                f"--- END {tool_name.upper()} DATA ---\n\n"
                f"IMPORTANT: Respond with ONLY a valid JSON object. "
                f"First character must be '{{'. Last character must be '}}'. "
                f"Use the exact keys: tool, verdict, confidence, findings, iocs, summary."
            )
            try:
                log.info("Calling agent %s …", agent_def.name)
                resp = await service.chat(
                    agent_name=agent_def.name,
                    prompt=prompt,
                    timeout=120.0,
                )
                raw = _clean_json_response(resp.get("response", ""))
                result.raw_response = raw
                _parse_tool_json(raw, result)
                log.info(
                    "Agent %s → verdict=%s confidence=%d findings=%d",
                    agent_def.name, result.verdict, result.confidence, result.findings_count,
                )
            except Exception as exc:
                result.error = str(exc)
                fallback = {
                    "tool": tool_name,
                    "verdict": "inconclusive",
                    "confidence": 0,
                    "findings": [],
                    "iocs": [],
                    "summary": f"Agent error: {exc}",
                }
                result.raw_response = json.dumps(fallback)
                log.error("Agent %s failed: %s", agent_def.name, exc)
            return result

        parallel_tasks = []
        no_data_results: list[ToolAnalysisResult] = []

        for agent_def in get_tool_agents():
            loader = TOOL_LOADERS.get(agent_def.name)
            if loader is None:
                continue

            payload_text, has_data = loader(report_dir)
            tool_name = agent_def.name.replace("-analyzer", "")

            if not has_data:
                result = ToolAnalysisResult(
                    tool=tool_name, agent_name=agent_def.name,
                )
                result.verdict = "inconclusive"
                result.summary = f"No {tool_name} data was available for analysis."
                fallback = {
                    "tool": tool_name,
                    "verdict": "inconclusive",
                    "confidence": 0,
                    "findings": [],
                    "iocs": [],
                    "summary": f"No data collected by {tool_name} collector.",
                }
                result.raw_response = json.dumps(fallback)
                tool_responses[tool_name] = result.raw_response
                no_data_results.append(result)
                log.info("Skipped %s (no data)", agent_def.name)
                continue

            parallel_tasks.append((agent_def, tool_name, payload_text))

        # Run all agents WITH data in parallel
        if parallel_tasks:
            log.info("Running %d tool agents in parallel …", len(parallel_tasks))
            coroutines = [
                _run_tool_agent(ad, tn, pt) for ad, tn, pt in parallel_tasks
            ]
            parallel_results = await asyncio.gather(*coroutines, return_exceptions=True)
            for i, res in enumerate(parallel_results):
                if isinstance(res, Exception):
                    ad, tn, _ = parallel_tasks[i]
                    result = ToolAnalysisResult(
                        tool=tn, agent_name=ad.name,
                        error=str(res),
                    )
                    fallback = {
                        "tool": tn,
                        "verdict": "inconclusive",
                        "confidence": 0,
                        "findings": [],
                        "iocs": [],
                        "summary": f"Agent error: {res}",
                    }
                    result.raw_response = json.dumps(fallback)
                    tool_responses[tn] = result.raw_response
                    report.tool_results.append(result)
                else:
                    tool_responses[res.tool] = res.raw_response
                    report.tool_results.append(res)

        # Add no-data results
        report.tool_results.extend(no_data_results)

        # ── Phase 2: Final summary ────────────────────────────────────
        summary_input_parts = [
            f"Sample: {self._get_sample_name(report_dir)}",
            "",
            "Below are the analysis outputs from each specialized tool analyst.",
            "Synthesize them into a final threat report.",
            "",
        ]
        for tool_name, json_text in tool_responses.items():
            summary_input_parts.append(f"--- {tool_name.upper()} ANALYSIS ---")
            summary_input_parts.append(json_text)
            summary_input_parts.append("")

        summary_input_parts.append(
            "IMPORTANT: Respond with ONLY a valid JSON object. "
            "First character must be '{'. Last character must be '}'. "
            "Use the exact keys from the schema: risk_score, threat_level, classification, "
            "executive_summary, key_findings, iocs, mitre_attack, recommendations, detailed_analysis."
        )
        summary_prompt = "\n".join(summary_input_parts)

        try:
            log.info("Calling threat-summarizer agent …")
            resp = await service.chat(
                agent_name="threat-summarizer",
                prompt=summary_prompt,
                timeout=120.0,
            )
            raw_summary = _clean_json_response(resp.get("response", ""))
            report.raw_summary = raw_summary
            _parse_summary_json(raw_summary, report)
            log.info(
                "Threat summary → risk=%d level=%s type=%s",
                report.risk_score, report.threat_level, report.malware_type,
            )
        except Exception as exc:
            report.error = f"Summarizer failed: {exc}"
            log.error("Threat summarizer failed: %s", exc)

        # ── Finalize ──────────────────────────────────────────────────
        report.completed_at = datetime.datetime.utcnow().isoformat() + "Z"
        report.status = "complete" if not report.error else "failed"

        # Save results
        self._save_results(report_dir, report)

        return report

    def get_ai_report(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Load a previously saved AI analysis report from disk."""
        report_dir = os.path.join(self.reports_dir, analysis_id)
        ai_path = os.path.join(report_dir, "ai_analysis", "ai_report.json")
        if os.path.isfile(ai_path):
            try:
                with open(ai_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    # ── Internals ─────────────────────────────────────────────────────

    def _get_sample_name(self, report_dir: str) -> str:
        manifest = _read_json(os.path.join(report_dir, "analysis_manifest.json"))
        if manifest:
            return manifest.get("sample_name", "unknown")
        return "unknown"

    def _save_results(self, report_dir: str, report: ThreatAnalysisReport) -> None:
        """Persist the AI analysis to the report directory."""
        ai_dir = os.path.join(report_dir, "ai_analysis")
        os.makedirs(ai_dir, exist_ok=True)

        # Full JSON report
        report_path = os.path.join(ai_dir, "ai_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, default=str)

        # Individual tool JSON responses
        for result in report.tool_results:
            tool_path = os.path.join(ai_dir, f"{result.tool}_analysis.json")
            with open(tool_path, "w", encoding="utf-8") as f:
                f.write(result.raw_response)

        # Summary JSON
        if report.raw_summary:
            summary_path = os.path.join(ai_dir, "threat_report.json")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(report.raw_summary)

        log.info("AI analysis saved to %s", ai_dir)
