"""TEST_12: Verify analysis_routes.py has correct imports and serve_report_file fallback."""
import json
import os
import sys
import ast


def main() -> int:
    test_name = "TEST_12_analysis_routes_imports"
    about = "analysis_routes.py has json/csv/io at module level and serve_report_file has artifacts fallback"
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        routes_path = os.path.join(
            root, "core", "gateway", "analysis_routes.py"
        )

        results = {}

        if not os.path.isfile(routes_path):
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: analysis_routes.py does not exist")
            return 1

        with open(routes_path, "r") as f:
            content = f.read()

        # Parse the AST to check top-level imports
        tree = ast.parse(content)

        top_level_imports = set()
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_level_imports.add(node.module)

        results["top_level_imports"] = sorted(top_level_imports)

        # Check that json, csv, io are imported at module level
        required = {"json", "csv", "io"}
        # csv may be imported as 'import csv as csv_mod'
        # Check raw content for these
        has_json = "import json" in content.split("\n")[:30] or any(
            isinstance(n, ast.Import) and any(a.name == "json" for a in n.names)
            for n in ast.iter_child_nodes(tree)
            if isinstance(n, ast.Import)
        )
        has_csv = "import csv" in content
        has_io = "import io" in content

        results["has_module_level_json"] = has_json
        results["has_module_level_csv"] = has_csv
        results["has_module_level_io"] = has_io

        missing = []
        if not has_json:
            missing.append("json")
        if not has_csv:
            missing.append("csv")
        if not has_io:
            missing.append("io")

        if missing:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print(f"Reason: Missing module-level imports: {', '.join(missing)}")
            print(f"Output:\n{json.dumps(results, indent=2)}")
            return 1

        # Check that serve_report_file has artifacts fallback
        has_artifacts_fallback = "artifacts" in content and "serve_report_file" in content
        results["has_artifacts_fallback"] = has_artifacts_fallback

        if not has_artifacts_fallback:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: serve_report_file does not have artifacts directory fallback")
            print(f"Output:\n{json.dumps(results, indent=2)}")
            return 1

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
