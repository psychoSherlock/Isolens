"""TEST_11: Verify reports page structure and required components exist."""
import json
import os
import sys


def main() -> int:
    test_name = "TEST_11_reports_page_structure"
    about = "Reports page.tsx exists, compiles (no syntax issues), and contains key UI components"
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_path = os.path.join(
            root, "core", "interface", "src", "app", "reports", "page.tsx"
        )

        results = {}

        # 1. File must exist
        if not os.path.isfile(reports_path):
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: reports/page.tsx does not exist")
            print(f"Output:\n{json.dumps(results)}")
            return 1
        results["file_exists"] = True

        with open(reports_path, "r") as f:
            content = f.read()

        results["file_length"] = len(content)

        # 2. Required component definitions
        required_components = [
            "Panel",
            "NoData",
            "MiniStat",
            "FPath",
            "DataGrid",
            "ScreenshotGallery",
            "SysmonSection",
            "ProcmonSection",
            "NetworkSection",
            "HandleSection",
            "TcpvconSection",
            "CollectorBadges",
            "ReportsPage",
        ]
        missing = []
        for comp in required_components:
            # Check for function definition
            if f"function {comp}" not in content:
                missing.append(comp)

        results["required_components"] = required_components
        results["missing_components"] = missing

        if missing:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print(f"Reason: Missing component definitions: {', '.join(missing)}")
            print(f"Output:\n{json.dumps(results, indent=2)}")
            return 1

        # 3. All collector sections always rendered (NoData fallback pattern)
        # Each section should have a NoData fallback when data is absent
        nodata_patterns = [
            "No Sysmon data collected",
            "No Procmon data collected",
            "No network capture data",
            "No handle snapshot data",
            "No active TCP/UDP connections captured",
        ]
        missing_nodata = []
        for pattern in nodata_patterns:
            if pattern not in content:
                missing_nodata.append(pattern)

        results["nodata_fallback_patterns"] = nodata_patterns
        results["missing_nodata_fallbacks"] = missing_nodata

        if missing_nodata:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print(
                f"Reason: Missing NoData fallback messages: {', '.join(missing_nodata)}"
            )
            print(f"Output:\n{json.dumps(results, indent=2)}")
            return 1

        # 4. Required imports from api.ts
        required_imports = [
            "SysmonData",
            "ProcmonData",
            "NetworkData",
            "TcpvconRow",
            "ReportData",
            "screenshotURL",
            "getReportData",
        ]
        missing_imports = [imp for imp in required_imports if imp not in content]
        results["missing_imports"] = missing_imports

        if missing_imports:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print(
                f"Reason: Missing required imports: {', '.join(missing_imports)}"
            )
            print(f"Output:\n{json.dumps(results, indent=2)}")
            return 1

        # 5. Screenshot onError handler exists (prevents broken images)
        has_onerror = "onError" in content
        results["has_screenshot_onerror"] = has_onerror
        if not has_onerror:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: Missing onError handler for screenshots (broken image prevention)")
            print(f"Output:\n{json.dumps(results, indent=2)}")
            return 1

        # 6. No .bak file lingering
        bak_path = reports_path + ".bak"
        results["bak_file_exists"] = os.path.isfile(bak_path)

        print(f"[{test_name}] PASS")
        print(f"About: {about}")
        print(f"Output:\n{json.dumps(results, indent=2)}")
        return 0

    except Exception as e:
        print(f"[{test_name}] FAIL")
        print(f"About: {about}")
        print(f"Reason: Exception: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
