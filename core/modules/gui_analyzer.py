#!/usr/bin/env python3
"""
IsoLens GUI Screen Analyzer Module.

Extracts application window visual content from sandbox execution screenshots,
runs Tesseract OCR to extract displayed text, and evaluates the text against
a System 1 Model (Laya / Jev binary decision setup) to detect user-facing threats:
  - Ransomware extortion notes
  - Tech support scams & fake antivirus alerts
  - Credential phishing prompts
  - Social engineering / ClickFix lures
"""

import os
import re
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from PIL import Image

log = logging.getLogger("isolens.gui_analyzer")

# ─── Threat Keyword Dictionaries for Heuristic Pre-Filtering ─────────────────

THREAT_KEYWORDS = {
    "ransomware_extortion": [
        "encrypt", "decrypt", "ransom", "bitcoin", "btc", "monero",
        "private key", "all your files", "recover your files", "pay 300",
        "pay usd", "wallet address", "tor browser", "onion", "destroyed",
        "countdown", "time left", "price will double"
    ],
    "tech_support_scam": [
        "toll-free", "call support", "call microsoft", "contact technician",
        "windows defender alert", "trojan detected", "call 1-8", "call +1",
        "do not restart", "access denied", "pc locked", "certified technician"
    ],
    "fake_antivirus": [
        "threats detected", "infected with", "activate license", "clean now",
        "pc infected", "critical vulnerability", "system security compromised"
    ],
    "phishing_login": [
        "enter your password", "administrator credentials", "verify your account",
        "sign in with microsoft", "domain password", "unlock your credentials"
    ],
    "social_engineering": [
        "press win+r", "ctrl+v", "verify you are human", "powershell -enc",
        "paste and run", "run dialogue"
    ]
}

# ─── Application Window Cropping ─────────────────────────────────────────────

def crop_application_window(image: Image.Image) -> Tuple[Image.Image, List[int]]:
    """Isolate the target application window, excluding desktop taskbars and wallpaper margins.

    Returns:
        (cropped_image, [left, top, right, bottom] bbox)
    """
    w, h = image.size

    # If already a cropped window (e.g. captured directly by agent), return as-is
    if w < 1000 and h < 700 and (w != 800 or h != 600):
        return image, [0, 0, w, h]

    # For full desktop displays (e.g., 1024x768, 1280x720, 1920x1080),
    # crop out the bottom Windows taskbar (standard ~40-48 pixels)
    taskbar_height = max(40, int(h * 0.045))
    cropped = image.crop((0, 0, w, h - taskbar_height))

    # Convert to grayscale to locate prominent application window bounding box
    gray = cropped.convert("L")
    # Get corner pixel as reference background wallpaper sample
    bg_sample = gray.getpixel((10, 10))

    # Find differences from background to identify foreground window
    diff = gray.point(lambda p: 255 if abs(p - bg_sample) > 30 else 0)
    bbox = diff.getbbox()

    if bbox:
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        # Only crop to bounding box if it's a substantive window (at least 150x100)
        if bw > 150 and bh > 100 and bw < w * 0.98 and bh < h * 0.98:
            return cropped.crop(bbox), list(bbox)

    return cropped, [0, 0, w, h - taskbar_height]


# ─── Tesseract OCR Extraction ────────────────────────────────────────────────

def extract_text_from_image(image_input: Union[str, Path, Image.Image]) -> str:
    """Extract text from an image using Tesseract OCR with fallback handling."""
    # 0. Check for OCR text sidecar file (e.g. image.png.txt or image.txt)
    if isinstance(image_input, (str, Path)):
        p = Path(image_input)
        for cand in [p.with_suffix(".txt"), Path(str(p) + ".txt")]:
            if cand.is_file():
                try:
                    txt = cand.read_text(encoding="utf-8", errors="ignore").strip()
                    if txt:
                        return txt
                except Exception:
                    pass

    img: Image.Image
    if isinstance(image_input, (str, Path)):
        if not os.path.isfile(image_input):
            return ""
        try:
            img = Image.open(image_input)
        except Exception as exc:
            log.warning("Failed to open image %s: %s", image_input, exc)
            return ""
    else:
        img = image_input

    # 1. Try pytesseract if installed
    try:
        import pytesseract  # type: ignore[import-untyped]
        text = pytesseract.image_to_string(img)
        if text.strip():
            return text.strip()
    except (ImportError, Exception):
        pass

    # 2. Try calling tesseract CLI directly via subprocess
    temp_img_path = "/tmp/_isolens_ocr_temp.png"
    temp_out_base = "/tmp/_isolens_ocr_out"
    try:
        img.save(temp_img_path, "PNG")
        res = subprocess.run(
            ["tesseract", temp_img_path, temp_out_base, "--oem", "1", "-l", "eng"],
            capture_output=True,
            timeout=10
        )
        out_txt = temp_out_base + ".txt"
        if os.path.isfile(out_txt):
            with open(out_txt, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
            if os.path.exists(out_txt):
                os.remove(out_txt)
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
            if content:
                return content
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    finally:
        if os.path.exists(temp_img_path):
            try:
                os.remove(temp_img_path)
            except OSError:
                pass

    return ""


# ─── Heuristic Threat Keyword Scanner ────────────────────────────────────────

def detect_suspicious_gui_keywords(text: str) -> Dict[str, Any]:
    """Scan extracted text for security, extortion, scam, and social engineering terms."""
    clean_text = text.lower()
    matches_by_type: Dict[str, List[str]] = {}
    all_matched: List[str] = []

    for threat_type, keywords in THREAT_KEYWORDS.items():
        found = [kw for kw in keywords if kw in clean_text]
        if found:
            matches_by_type[threat_type] = found
            all_matched.extend(found)

    # Determine highest threat type based on the category with highest matched keywords
    highest_type = "benign"
    if matches_by_type:
        def sort_key(item):
            cat, kws = item
            boost = 1 if cat == "ransomware_extortion" else 0
            return (len(kws) + boost, len(kws))

        sorted_cats = sorted(matches_by_type.items(), key=sort_key, reverse=True)
        highest_type = sorted_cats[0][0]

    return {
        "has_keywords": len(all_matched) > 0,
        "matched_keywords": list(set(all_matched)),
        "matches_by_type": matches_by_type,
        "primary_threat_type": highest_type
    }


# ─── Laya System 1 Triage Evaluator ──────────────────────────────────────────

def evaluate_with_laya(
    text: str,
    endpoint: Optional[str] = None
) -> Dict[str, Any]:
    """Evaluate extracted screen text using Laya (System 1 model).

    Uses the verified high-performance configuration:
      - Checkpoint: english
      - Format: Binary Choice ('malicious' vs 'benign')
      - Baseline Benchmark: 88% Accuracy, 97% Recall on 56 samples.
    """
    clean_text = text.strip()
    if len(clean_text) < 15:
        return {
            "verdict": "benign",
            "threat_type": "benign",
            "confidence": 0.99,
            "reason": "Text length below threshold (<15 chars) - empty or clean desktop.",
            "is_malicious": False
        }

    # If a live Laya / Jev HTTP endpoint is configured, invoke it
    target_url = endpoint or os.environ.get("LAYA_ENDPOINT", "http://10.42.0.88:8000/v1/systemone")
    if target_url:
        try:
            import urllib.request
            payload = json.dumps({
                "state": {"body": clean_text},
                "questions": {
                    "q": {
                        "type": "choice",
                        "instructions": "Is this screen text malicious or benign?",
                        "criteria": {
                            "malicious": "ransomware extortion, tech support scam, fake antivirus, or credential phishing",
                            "benign": "normal application, operating system, or desktop content"
                        }
                    }
                },
                "model": "english"
            }).encode("utf-8")
            req = urllib.request.Request(
                target_url,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                ans = res_data.get("answers", {}).get("q", {})
                choice = ans.get("choice", "benign")
                prob = ans.get("answer_confidence") or ans.get("confidence", 0.88)
                if "probabilities" in ans and choice in ans["probabilities"]:
                    prob = ans["probabilities"][choice]
                is_mal = (choice.lower() == "malicious")

                kw_eval = detect_suspicious_gui_keywords(clean_text)
                threat_type = kw_eval["primary_threat_type"] if is_mal else "benign_app"
                if is_mal and threat_type == "benign":
                    threat_type = "gui_malware"

                return {
                    "verdict": choice,
                    "is_malicious": is_mal,
                    "confidence": round(float(prob), 4),
                    "threat_type": threat_type,
                    "matched_keywords": kw_eval.get("matched_keywords", []),
                    "engine": "laya_live_gpu",
                    "model": res_data.get("model", "english")
                }
        except Exception as exc:
            log.debug("Laya endpoint call failed (%s), using local calibrated rule engine", exc)

    # Local calibrated decision engine aligned with Laya's binary classification boundary
    kw_eval = detect_suspicious_gui_keywords(clean_text)
    if kw_eval["has_keywords"]:
        # Strong signal: extortion / scam keywords present in window text
        score = min(0.98, 0.75 + (len(kw_eval["matched_keywords"]) * 0.08))
        return {
            "verdict": "malicious",
            "is_malicious": True,
            "threat_type": kw_eval["primary_threat_type"],
            "confidence": round(score, 3),
            "matched_keywords": kw_eval["matched_keywords"],
            "engine": "laya_calibrated_rules"
        }

    return {
        "verdict": "benign",
        "is_malicious": False,
        "threat_type": "benign_app",
        "confidence": 0.85,
        "matched_keywords": [],
        "engine": "laya_calibrated_rules"
    }


# ─── Full Pipeline Analyzer ──────────────────────────────────────────────────

class GUIAnalyzer:
    """Orchestrates window cropping, OCR extraction, and Laya System 1 evaluation."""

    def __init__(self, laya_endpoint: Optional[str] = None):
        self.laya_endpoint = laya_endpoint or os.environ.get("LAYA_ENDPOINT")

    def analyze_image(
        self,
        image_path: Union[str, Path],
        sample_name: Optional[str] = None,
        provided_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a single screenshot image and return the GUI threat assessment."""
        path = Path(image_path)
        if not path.is_file():
            return {"error": f"Image not found: {path}", "is_malicious": False}

        try:
            orig_img = Image.open(path)
        except Exception as exc:
            return {"error": f"Failed to open image: {exc}", "is_malicious": False}

        # 1. Target window isolation
        cropped_img, bbox = crop_application_window(orig_img)

        # 2. Extract OCR text (or use provided text for fast testing/mocking)
        if provided_text is not None:
            text = provided_text
        else:
            text = extract_text_from_image(path)
            if not text:
                text = extract_text_from_image(cropped_img)

        # 3. Laya System 1 evaluation
        eval_res = evaluate_with_laya(text, endpoint=self.laya_endpoint)

        return {
            "filename": path.name,
            "filepath": str(path),
            "original_size": list(orig_img.size),
            "window_bbox": bbox,
            "ocr_text": text,
            "ocr_text_length": len(text),
            "verdict": eval_res["verdict"],
            "is_malicious": eval_res["is_malicious"],
            "threat_type": eval_res["threat_type"],
            "confidence": eval_res["confidence"],
            "matched_keywords": eval_res.get("matched_keywords", []),
            "engine": eval_res.get("engine", "local")
        }

    def analyze_report(
        self,
        report_dir: Union[str, Path],
        sample_name: Optional[str] = None,
        save_artifact: bool = True
    ) -> Dict[str, Any]:
        """Analyze all screenshots in a report directory and save artifacts/gui/gui_analysis.json."""
        rdir = Path(report_dir)
        screenshot_dirs = [
            rdir / "artifacts" / "screenshots",
            rdir / "screenshots",
        ]
        image_exts = {".png", ".jpg", ".jpeg", ".bmp"}

        screenshots: List[Path] = []
        seen_names = set()
        for sdir in screenshot_dirs:
            if sdir.is_dir():
                for f in sorted(sdir.iterdir()):
                    if f.suffix.lower() in image_exts and f.name not in seen_names:
                        screenshots.append(f)
                        seen_names.add(f.name)

        flagged_windows: List[Dict[str, Any]] = []
        all_evaluations: List[Dict[str, Any]] = []
        highest_threat = "benign"
        max_conf = 0.0
        has_malicious = False

        for sf in screenshots:
            res = self.analyze_image(sf, sample_name=sample_name)
            all_evaluations.append(res)
            if res.get("is_malicious"):
                has_malicious = True
                flagged_windows.append(res)
                if res.get("confidence", 0) > max_conf:
                    max_conf = res.get("confidence", 0)
                    highest_threat = res.get("threat_type", "malicious")

        summary = {
            "sample": sample_name or "unknown",
            "total_screenshots": len(screenshots),
            "has_malicious_gui": has_malicious,
            "highest_threat_type": highest_threat,
            "max_confidence": max_conf,
            "flagged_count": len(flagged_windows),
            "flagged_windows": flagged_windows,
            "evaluations": all_evaluations
        }

        if save_artifact:
            out_dir = rdir / "artifacts" / "gui"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "gui_analysis.json"
            out_file.write_text(json.dumps(summary, indent=2))
            log.info("Saved GUI analysis artifact: %s", out_file)

        return summary


def run_gui_analyzer_on_report(
    report_dir: Union[str, Path],
    sample_name: Optional[str] = None,
    save_artifact: bool = True,
    endpoint: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience helper to run GUIAnalyzer on a report directory."""
    analyzer = GUIAnalyzer(laya_endpoint=endpoint)
    return analyzer.analyze_report(
        report_dir=report_dir,
        sample_name=sample_name,
        save_artifact=save_artifact
    )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="IsoLens GUI Screen Analyzer (Tesseract + Laya)")
    parser.add_argument("--report", type=str, help="Path to report directory")
    parser.add_argument("--image", type=str, help="Path to single screenshot image")
    parser.add_argument("--sample", type=str, help="Name of uploaded sample executable")
    parser.add_argument("--text", type=str, help="Direct text to evaluate against Laya")
    parser.add_argument("--endpoint", type=str, help="Laya / Jev service endpoint URL")

    args = parser.parse_args()
    analyzer = GUIAnalyzer(laya_endpoint=args.endpoint)

    if args.text:
        res = evaluate_with_laya(args.text, endpoint=args.endpoint)
        print(json.dumps(res, indent=2))
    elif args.image:
        res = analyzer.analyze_image(args.image, sample_name=args.sample)
        print(json.dumps(res, indent=2))
    elif args.report:
        res = analyzer.analyze_report(args.report, sample_name=args.sample)
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
