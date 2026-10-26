#!/usr/bin/env python3
"""
TEST_30_gui_integration.py - Standalone test for GUI Screen Analysis & Laya Triage Integration.

Verifies:
  1. run_gui_analyzer_on_report() evaluates screenshots from report directory and generates artifacts/gui/gui_analysis.json.
  2. Threat analyzer (_load_metadata) ingests GUI screen analysis and formats extortion/scam alerts.
  3. Gateway endpoint GET /api/analysis/report/{id}/gui returns structured findings.
  4. Gateway endpoint GET /api/analysis/report/{id}/data contains 'gui' analysis payload.
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.modules.gui_analyzer import run_gui_analyzer_on_report, GUIAnalyzer
from core.threatintelligence.threat_analyzer import _load_metadata
from fastapi.testclient import TestClient
from core.gateway.app import app

def create_mock_ransomware_screenshot(output_path: Path):
    """Generate a mock screenshot simulating a ransomware lockscreen."""
    img = Image.new("RGB", (640, 480), color=(140, 20, 20))
    draw = ImageDraw.Draw(img)
    # Draw simple window bar
    draw.rectangle([0, 0, 640, 30], fill=(50, 50, 50))
    draw.text((10, 8), "WanaCrypt0r 2.0 - Decryptor", fill=(255, 255, 255))
    # Draw extortion text body
    extortion_msg = (
        "Ooops, your files have been encrypted!\n"
        "All your important files (photos, documents, databases) are encrypted.\n"
        "To recover your files, pay 300 USD in Bitcoin to our wallet address.\n"
        "Time left: 71:59:45. After countdown expires, price will double."
    )
    draw.text((20, 60), extortion_msg, fill=(255, 255, 255))
    img.save(str(output_path), "PNG")


def run_test():
    test_name = "TEST_30_gui_integration"
    about = "GUI Screen Analyzer Integration: Automated Window OCR/Triage, Artifact Generation, and Threat Intel Ingestion"

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_dir = Path(temp_dir) / "test_report_gui"
            ss_dir = report_dir / "artifacts" / "screenshots"
            ss_dir.mkdir(parents=True)

            mock_ss_file = ss_dir / "screenshot_001_window.png"
            create_mock_ransomware_screenshot(mock_ss_file)
            mock_txt_file = ss_dir / "screenshot_001_window.txt"
            mock_txt_file.write_text(
                "Ooops, your files have been encrypted!\n"
                "All your important files (photos, documents, databases) are encrypted.\n"
                "To recover your files, pay 300 USD in Bitcoin to our wallet address.\n"
                "Time left: 71:59:45. After countdown expires, price will double."
            )

            # 1. Run GUI analyzer on report directory
            gui_res = run_gui_analyzer_on_report(report_dir, sample_name="wanacry.exe", save_artifact=True)

            artifact_path = report_dir / "artifacts" / "gui" / "gui_analysis.json"
            if not artifact_path.is_file():
                print(f"[{test_name}] FAIL")
                print(f"About: {about}")
                print(f"Reason: Expected artifact {artifact_path} was not created.")
                sys.exit(1)

            with open(artifact_path, "r", encoding="utf-8") as f:
                saved_artifact = json.load(f)

            if saved_artifact.get("total_screenshots") != 1:
                print(f"[{test_name}] FAIL")
                print(f"About: {about}")
                print(f"Reason: Expected 1 evaluated screenshot, found {saved_artifact.get('total_screenshots')}")
                sys.exit(1)

            if not saved_artifact.get("has_malicious_gui"):
                print(f"[{test_name}] FAIL")
                print(f"About: {about}")
                print(f"Reason: Expected has_malicious_gui=True for ransomware extortion note.")
                sys.exit(1)

            # 2. Test Threat Analyzer _load_metadata ingestion
            meta_str, success = _load_metadata(str(report_dir))
            if not success or "gui_screen_analysis" not in meta_str:
                print(f"[{test_name}] FAIL")
                print(f"About: {about}")
                print("Reason: Threat analyzer _load_metadata did not ingest gui_screen_analysis.")
                print("Output:", meta_str)
                sys.exit(1)

            # 3. Test Gateway Endpoints using temporary report override
            # We copy report_dir into core/storage/reports/_test_gui_integration
            live_reports_dir = PROJECT_ROOT / "core" / "storage" / "reports"
            dest_test_dir = live_reports_dir / "_test_gui_integration"
            if dest_test_dir.exists():
                shutil.rmtree(dest_test_dir)
            shutil.copytree(report_dir, dest_test_dir)

            try:
                client = TestClient(app)

                # Test GET /api/analysis/report/{id}/gui
                resp_gui = client.get("/api/analysis/report/_test_gui_integration/gui")
                if resp_gui.status_code != 200:
                    print(f"[{test_name}] FAIL")
                    print(f"About: {about}")
                    print(f"Reason: GET /api/analysis/report/_test_gui_integration/gui returned HTTP {resp_gui.status_code}")
                    sys.exit(1)
                gui_api_data = resp_gui.json().get("data", {})
                if gui_api_data.get("sample") != "wanacry.exe":
                    print(f"[{test_name}] FAIL")
                    print(f"About: {about}")
                    print("Reason: Mismatched sample in API output:", gui_api_data)
                    sys.exit(1)

                # Test GET /api/analysis/report/{id}/data
                resp_data = client.get("/api/analysis/report/_test_gui_integration/data")
                if resp_data.status_code != 200:
                    print(f"[{test_name}] FAIL")
                    print(f"About: {about}")
                    print(f"Reason: GET /api/analysis/report/_test_gui_integration/data returned HTTP {resp_data.status_code}")
                    sys.exit(1)
                full_data = resp_data.json().get("data", {})
                if "gui" not in full_data or full_data["gui"] is None:
                    print(f"[{test_name}] FAIL")
                    print(f"About: {about}")
                    print("Reason: 'gui' key missing in GET /data response")
                    sys.exit(1)

            finally:
                if dest_test_dir.exists():
                    shutil.rmtree(dest_test_dir)

            output_summary = {
                "artifact_saved": "gui_analysis.json",
                "total_screenshots": saved_artifact.get("total_screenshots"),
                "has_malicious_gui": saved_artifact.get("has_malicious_gui"),
                "highest_threat_type": saved_artifact.get("highest_threat_type"),
                "max_confidence": saved_artifact.get("max_confidence"),
                "threat_analyzer_ingestion": "PASS",
                "gateway_gui_endpoint": "PASS",
                "gateway_data_endpoint": "PASS"
            }

            print(f"[{test_name}] PASS")
            print(f"About: {about}")
            print(f"Output:\n{json.dumps(output_summary, indent=2)}")

    except Exception as exc:
        print(f"[{test_name}] FAIL")
        print(f"About: {about}")
        print(f"Reason: Unexpected exception: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_test()
