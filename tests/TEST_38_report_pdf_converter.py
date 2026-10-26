#!/usr/bin/env python3
"""Check the report converter's image-reference validation."""

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
converter = root / "MajorProjectReport" / "convert_report.py"
if not converter.is_file():
    if (root / "MajorProjectReport" / "backup" / "convert_report.py").is_file():
        converter = root / "MajorProjectReport" / "backup" / "convert_report.py"
    elif (root / "MajorProjectReport" / "FinalReport" / "ActualReport" / "convert_report.py").is_file():
        converter = root / "MajorProjectReport" / "FinalReport" / "ActualReport" / "convert_report.py"
result = subprocess.run(
    [sys.executable, str(converter), "--check-assets"],
    cwd=converter.parent,
    text=True,
    capture_output=True,
)
raw_output = (result.stdout + result.stderr).strip()
if result.returncode == 0 and "Assets OK:" in result.stdout:
    print("[TEST_38_report_pdf_converter] PASS")
    print("About: Report converter validates every referenced logo and figure")
    print("Output:")
    print(raw_output)
else:
    print("[TEST_38_report_pdf_converter] FAIL")
    print("About: Report converter validates every referenced logo and figure")
    print(f"Reason: converter returned {result.returncode}")
    print("Output:")
    print(raw_output or "<no output>")
    raise SystemExit(1)
