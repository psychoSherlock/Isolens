#!/usr/bin/env python3
"""
IsoLens Deterministic Risk Scoring Engine.

Computes an objective, explainable, and multi-layered risk score (0-100)
by synthesizing findings from all sandbox analysis submodules:
  1. Deterministic Network Threat Intel DB matching (C2, malware drops, malicious IPs)
  2. Static YARA pattern matching & capability detection (packers, evasion, ransomware)
  3. Sequential BiLSTM behavioral inference from Procmon chronological API calls
  4. GUI application screen threat triage with Laya System 1 model (extortion, scareware)
  5. Normalized host behavior, sensitive file/registry access & MITRE ATT&CK mappings
  6. Sysmon process telemetry & LOLBin execution detection
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

log = logging.getLogger("isolens.risk_scorer")


def _read_json_file(path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    p = Path(path)
    if p.is_file():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            log.debug("Failed to read JSON %s: %s", path, exc)
    return None


class DeterministicRiskScorer:
    """Calculates an explainable 0-100 risk score and threat level from report artifacts."""

    def __init__(self) -> None:
        pass

    def evaluate_report(self, report_dir: Union[str, Path]) -> Dict[str, Any]:
        """Load structured artifacts from report_dir and compute the unified score."""
        rdir = Path(report_dir)
        artifacts_dir = rdir / "artifacts"

        # 1. Load artifacts
        manifest = _read_json_file(rdir / "analysis_manifest.json")
        yara_data = _read_json_file(artifacts_dir / "yara" / "yara_summary.json")
        lstm_data = _read_json_file(artifacts_dir / "lstm" / "lstm_prediction.json")
        behav_data = _read_json_file(artifacts_dir / "behavior" / "behavior_summary.json")
        gui_data = _read_json_file(artifacts_dir / "gui" / "gui_analysis.json")
        network_data = _read_json_file(artifacts_dir / "network" / "network_summary.json")
        sysmon_data = _read_json_file(artifacts_dir / "sysmon" / "sysmon_summary.json")

        breakdown: List[Dict[str, Any]] = []
        mitre_detected: List[Dict[str, str]] = []

        # ── 1. Network Threat Intelligence DB Matching ──────────────────────
        network_pts = 0
        try:
            from core.modules.network_db_matcher import analyze_report_network_with_db
            db_res = analyze_report_network_with_db(rdir)
            if db_res.get("verdict") == "malicious":
                findings = db_res.get("findings", [])
                c2_or_drop = any(
                    f.get("threat_type") in ("c2", "malware_download", "botnet", "ransomware")
                    for f in findings
                )
                pts = 40 if c2_or_drop else 30
                network_pts = pts
                breakdown.append({
                    "layer": "Network Threat Intelligence",
                    "points": pts,
                    "confidence": db_res.get("confidence", 0.95),
                    "summary": f"Deterministic match in offline Threat DB: {len(findings)} malicious indicator(s) identified.",
                    "details": [f.get("indicator") for f in findings[:5]]
                })
            elif db_res.get("verdict") == "suspicious":
                network_pts = 15
                breakdown.append({
                    "layer": "Network Threat Intelligence",
                    "points": 15,
                    "confidence": db_res.get("confidence", 0.70),
                    "summary": "Suspicious network indicator(s) identified in Threat DB.",
                    "details": db_res.get("findings", [])
                })
        except Exception as exc:
            log.debug("Network DB lookup skipped in risk scoring: %s", exc)

        # ── 2. Static YARA Capability & Signatures ───────────────────────────
        if yara_data and yara_data.get("matched_rules_count", 0) > 0:
            count = yara_data.get("matched_rules_count", 0)
            level = yara_data.get("threat_level", "low").lower()
            matches = yara_data.get("matches", [])
            rule_names = [m.get("rule_name") for m in matches]

            if level in ("critical", "high") or count >= 2:
                pts = 25
            elif level == "medium":
                pts = 15
            else:
                pts = 5

            breakdown.append({
                "layer": "Static YARA Signatures",
                "points": pts,
                "confidence": 0.90,
                "summary": f"Matched {count} signature rule(s) (threat level: {level}).",
                "details": rule_names
            })
            for m in yara_data.get("mitre_attack", []):
                mitre_detected.append(m)

        # ── 3. Sequential BiLSTM Behavioral Inference ───────────────────────
        if lstm_data and "verdict" in lstm_data:
            verdict = lstm_data.get("verdict", "").lower()
            p_malware = float(lstm_data.get("p_malware", 0.0))
            conf = float(lstm_data.get("confidence", 0.0))

            if p_malware >= 0.85 or (verdict == "malware" and conf >= 85):
                pts = 25
                breakdown.append({
                    "layer": "Sequential BiLSTM",
                    "points": pts,
                    "confidence": round(conf / 100.0, 3) if conf > 1 else conf,
                    "summary": f"Chronological API sequence classified as malicious (p_malware={p_malware:.3f}).",
                    "details": {
                        "peak_window": lstm_data.get("peak_window_range"),
                        "sequence_length": lstm_data.get("total_sequence_length", lstm_data.get("sequence_length", 0))
                    }
                })
            elif p_malware >= 0.60 or verdict == "malware":
                pts = 15
                breakdown.append({
                    "layer": "Sequential BiLSTM",
                    "points": pts,
                    "confidence": round(conf / 100.0, 3) if conf > 1 else conf,
                    "summary": f"Suspicious chronological API behavior pattern (p_malware={p_malware:.3f}).",
                    "details": {"p_malware": p_malware}
                })

        # ── 4. GUI Screen Threat Triage (Laya System 1) ───────────────────────
        if gui_data and gui_data.get("has_malicious_gui"):
            threat_type = gui_data.get("highest_threat_type", "malicious")
            conf = float(gui_data.get("max_confidence", 0.85))
            if threat_type == "ransomware_extortion":
                pts = 25
                desc = "Ransomware extortion note / lockscreen detected in application window."
            elif threat_type in ("tech_support_scam", "fake_antivirus"):
                pts = 20
                desc = f"Scareware / {threat_type.replace('_', ' ')} warning displayed in window."
            elif threat_type in ("phishing_login", "social_engineering"):
                pts = 15
                desc = f"Credential harvesting / {threat_type.replace('_', ' ')} detected in GUI."
            else:
                pts = 15
                desc = "Malicious user-facing dialog detected by System 1 screen triage."

            breakdown.append({
                "layer": "GUI Screen Threat Triage",
                "points": pts,
                "confidence": conf,
                "summary": desc,
                "details": {
                    "threat_type": threat_type,
                    "flagged_count": gui_data.get("flagged_count", 1)
                }
            })

        # ── 5. Behavioral Normalization & Host MITRE ATT&CK ─────────────────
        if behav_data:
            summary = behav_data.get("summary", {})
            mitre_list = behav_data.get("mitre_attack", [])
            for m in mitre_list:
                mitre_detected.append(m)

            behav_pts = 0
            behav_reasons = []

            # Defense Evasion / Tampering
            tamper_keys = summary.get("total_defense_tampering_keys", 0)
            deleted_files = summary.get("total_files_deleted", 0)
            if tamper_keys > 0 or deleted_files > 0:
                behav_pts += 20
                behav_reasons.append(
                    f"Defense evasion: {tamper_keys} security tampering key(s), {deleted_files} file deletion(s)."
                )

            # Persistence
            pers_keys = summary.get("total_persistence_keys", 0)
            if pers_keys > 0:
                behav_pts += 15
                behav_reasons.append(f"Persistence established via {pers_keys} registry Run/Startup key(s).")

            # Sensitive Credential File Access
            sens_reads = summary.get("total_sensitive_reads", 0)
            if sens_reads > 0:
                behav_pts += 15
                behav_reasons.append(f"Credential/identity reconnaissance: {sens_reads} sensitive target access(es).")

            if behav_pts > 0:
                breakdown.append({
                    "layer": "Host Behavior & MITRE Techniques",
                    "points": min(35, behav_pts),
                    "confidence": 0.95,
                    "summary": " ".join(behav_reasons),
                    "details": {
                        "techniques": [m.get("id") for m in mitre_list if m.get("id")]
                    }
                })

        # ── 6. Sysmon Process & Injection Telemetry ──────────────────────────
        if sysmon_data:
            summary = sysmon_data.get("summary", {})
            injections = summary.get("process_injection_count", 0)
            lolbins = summary.get("lolbin_count", 0)

            sysmon_pts = 0
            sysmon_notes = []
            if injections > 0:
                sysmon_pts += 25
                sysmon_notes.append(f"Process injection / hollow detected ({injections} event(s)).")
            if lolbins > 0:
                sysmon_pts += 15
                sysmon_notes.append(f"Living-off-the-land binary (LOLBin) execution ({lolbins} event(s)).")

            if sysmon_pts > 0:
                breakdown.append({
                    "layer": "Sysmon Telemetry",
                    "points": min(30, sysmon_pts),
                    "confidence": 0.95,
                    "summary": " ".join(sysmon_notes),
                    "details": summary
                })

        # ── 7. Unified Score & Level Calculation ─────────────────────────────
        raw_score = sum(b.get("points", 0) for b in breakdown)
        risk_score = min(100, max(0, raw_score))

        if risk_score >= 80:
            threat_level = "Critical"
        elif risk_score >= 60:
            threat_level = "High"
        elif risk_score >= 35:
            threat_level = "Medium"
        elif risk_score >= 15:
            threat_level = "Low"
        else:
            threat_level = "Benign"

        # Deduplicate MITRE techniques
        unique_mitre = []
        seen_mitre_ids = set()
        for m in mitre_detected:
            tid = m.get("id")
            if tid and tid not in seen_mitre_ids:
                seen_mitre_ids.add(tid)
                unique_mitre.append(m)

        return {
            "risk_score": risk_score,
            "threat_level": threat_level,
            "max_score": 100,
            "raw_sum": raw_score,
            "total_layers_flagged": len(breakdown),
            "breakdown": breakdown,
            "mitre_attack": unique_mitre,
            "sample_name": (manifest or {}).get("sample_name", "unknown"),
            "engine": "isolens_deterministic_risk_v1"
        }

    def evaluate_and_save(
        self,
        report_dir: Union[str, Path],
        save_artifact: bool = True
    ) -> Dict[str, Any]:
        """Compute score and save to artifacts/risk/risk_score.json."""
        result = self.evaluate_report(report_dir)
        if save_artifact:
            rdir = Path(report_dir)
            out_dir = rdir / "artifacts" / "risk"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "risk_score.json"
            out_path.write_text(json.dumps(result, indent=2))
            log.info("Saved deterministic risk score to %s (score=%d, level=%s)", out_path, result["risk_score"], result["threat_level"])
        return result


def run_risk_scorer_on_report(
    report_dir: Union[str, Path],
    save_artifact: bool = True
) -> Dict[str, Any]:
    """Top-level convenience helper for orchestrator and gateway."""
    scorer = DeterministicRiskScorer()
    return scorer.evaluate_and_save(report_dir, save_artifact=save_artifact)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="IsoLens Unified Deterministic Risk Scorer")
    parser.add_argument("--report", required=True, help="Path to report directory")
    args = parser.parse_args()

    result = run_risk_scorer_on_report(args.report, save_artifact=True)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
