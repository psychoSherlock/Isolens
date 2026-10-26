#!/usr/bin/env python3
"""
TEST_27_gui_analyzer.py - Standalone test for GUI Screen Analyzer & Laya System 1 Triage.

Verifies:
  1. Application window cropping & taskbar exclusion.
  2. Threat keyword detection across extortion, scareware, and benign samples.
  3. Laya System 1 binary decision evaluation.
  4. End-to-end report screenshot analysis & artifact generation.
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.modules.gui_analyzer import (
    crop_application_window,
    detect_suspicious_gui_keywords,
    evaluate_with_laya,
    GUIAnalyzer
)

def run_test():
    test_name = "TEST_27_gui_analyzer"
    about = "GUI Screen Analyzer: Application Window Cropping, OCR Pre-filtering, and Laya System 1 Triage"

    try:
        # 1. Test Window Cropping
        full_desktop = Image.new("RGB", (1024, 768), color=(30, 80, 150)) # Blue desktop
        draw = ImageDraw.Draw(full_desktop)
        # Draw taskbar at bottom
        draw.rectangle([0, 728, 1024, 768], fill=(15, 15, 15))
        # Draw application window in center
        draw.rectangle([150, 100, 850, 600], fill=(245, 245, 245))

        cropped, bbox = crop_application_window(full_desktop)
        assert cropped.size[0] < 1024 or cropped.size[1] < 768, "Taskbar or margin should be cropped"
        assert bbox[3] <= 728, "Taskbar region should be excluded"

        # 2. Test Keyword Detection
        ransom_text = "Oops, your files have been encrypted! Send 300 USD in bitcoin to unlock your private key."
        kw_res = detect_suspicious_gui_keywords(ransom_text)
        assert kw_res["has_keywords"] is True
        assert kw_res["primary_threat_type"] == "ransomware_extortion"
        assert "encrypt" in kw_res["matched_keywords"] or "bitcoin" in kw_res["matched_keywords"]

        scam_text = "Windows Defender Alert: System infected with Trojan. Call toll-free Microsoft support at 1-800-445-0192 immediately."
        scam_kw = detect_suspicious_gui_keywords(scam_text)
        assert scam_kw["has_keywords"] is True
        assert scam_kw["primary_threat_type"] == "tech_support_scam"

        benign_text = "Welcome to Chrome. Manage your bookmarks and downloads across devices."
        benign_kw = detect_suspicious_gui_keywords(benign_text)
        assert benign_kw["has_keywords"] is False

        # 3. Test Laya System 1 Binary Evaluation
        laya_mal = evaluate_with_laya(ransom_text)
        assert laya_mal["is_malicious"] is True
        assert laya_mal["verdict"] == "malicious"
        assert laya_mal["confidence"] >= 0.80

        laya_benign = evaluate_with_laya(benign_text)
        assert laya_benign["is_malicious"] is False
        assert laya_benign["verdict"] == "benign"

        # 4. Test Full Report Analysis & Artifact Generation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            ss_dir = temp_path / "screenshots"
            ss_dir.mkdir(parents=True)

            img1_path = ss_dir / "screenshot_000.png"
            full_desktop.save(img1_path)

            analyzer = GUIAnalyzer()
            # Analyze using provided_text hook to simulate OCR without requiring tesseract binary in environment
            res_single = analyzer.analyze_image(
                img1_path,
                sample_name="lockbit.exe",
                provided_text=ransom_text
            )
            assert res_single["is_malicious"] is True
            assert res_single["threat_type"] == "ransomware_extortion"

            # Batch report execution
            report_summary = analyzer.analyze_report(
                temp_path,
                sample_name="lockbit.exe",
                save_artifact=True
            )
            artifact_file = temp_path / "artifacts" / "gui" / "gui_analysis.json"
            assert artifact_file.is_file(), "Artifact gui_analysis.json must be saved"

            saved_data = json.loads(artifact_file.read_text())
            assert "total_screenshots" in saved_data
            assert "has_malicious_gui" in saved_data
            assert saved_data["total_screenshots"] == 1

        output = {
            "window_cropping": "PASS",
            "bbox": bbox,
            "ransomware_detection": laya_mal,
            "scam_detection": scam_kw["primary_threat_type"],
            "benign_filter": laya_benign["verdict"],
            "artifact_generation": "PASS"
        }

        print(f"[{test_name}] PASS")
        print(f"About: {about}")
        print("Output:")
        print(json.dumps(output, indent=2))
        return 0

    except Exception as exc:
        print(f"[{test_name}] FAIL")
        print(f"About: {about}")
        print(f"Reason: {exc}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_test())
