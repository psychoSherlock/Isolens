#!/usr/bin/env python3
"""Check the generated black-and-white IsoLens workflow illustration."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "MajorProjectReport"
if not (REPORT_DIR / "isolens_workflow_bw.png").is_file():
    if (ROOT / "MajorProjectReport" / "backup" / "isolens_workflow_bw.png").is_file():
        REPORT_DIR = ROOT / "MajorProjectReport" / "backup"
    elif (ROOT / "MajorProjectReport" / "FinalReport" / "ActualReport" / "isolens_workflow_bw.png").is_file():
        REPORT_DIR = ROOT / "MajorProjectReport" / "FinalReport" / "ActualReport"
IMAGE = REPORT_DIR / "isolens_workflow_bw.png"
SVG = REPORT_DIR / "isolens_workflow_bw.svg"
HORIZONTAL = REPORT_DIR / "isolens_workflow_bw_horizontal.png"
HORIZONTAL_SVG = REPORT_DIR / "isolens_workflow_bw_horizontal.svg"
print("[TEST_36_report_flow_diagram] About: Generated monochrome project workflow image exists and is readable")
try:
    assert IMAGE.is_file() and SVG.is_file(), "Vertical workflow diagram is missing"
    assert HORIZONTAL.is_file() and HORIZONTAL_SVG.is_file(), "Horizontal workflow diagram is missing"
    with Image.open(HORIZONTAL) as image:
        image.verify()
    with Image.open(HORIZONTAL) as image:
        assert image.width > image.height, f"Horizontal diagram is not landscape: {image.size}"
        horizontal_size = image.size
        image = image.convert("RGB")
        horizontal_colors = image.getcolors(image.width * image.height)
        assert horizontal_colors is not None and all(r == g == b for count, (r, g, b) in horizontal_colors), "Horizontal diagram contains colors"
    with Image.open(IMAGE) as image:
        image.verify()
    with Image.open(IMAGE) as image:
        assert image.width >= 1000 and image.height >= 1000, f"Unexpected image size: {image.size}"
        image = image.convert("RGB")
        colors = image.getcolors(image.width * image.height)
        assert colors is not None
        assert all(r == g == b for count, (r, g, b) in colors), "Image contains non-gray colors"
    print("[TEST_36_report_flow_diagram] PASS")
    print("Output:")
    print({"vertical": [str(IMAGE), str(SVG)], "horizontal": [str(HORIZONTAL), str(HORIZONTAL_SVG)], "horizontal_size": horizontal_size, "horizontal_colors": len(horizontal_colors)})
except Exception as exc:
    print("[TEST_36_report_flow_diagram] FAIL")
    print(f"Reason: {exc}")
    raise
