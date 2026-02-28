import json
import os
import sys


def main() -> int:
    test_name = "TEST_10_interface_config"
    about = "Interface Next.js and PostCSS configs are correct for fast dev compilation"
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        interface_dir = os.path.join(root, "core", "interface")

        results = {}

        # 1. next.config.ts must contain optimizePackageImports with react-icons
        next_config_path = os.path.join(interface_dir, "next.config.ts")
        with open(next_config_path, "r") as f:
            next_config_content = f.read()

        has_optimize = "optimizePackageImports" in next_config_content
        has_react_icons = "react-icons" in next_config_content
        results["next_config_has_optimizePackageImports"] = has_optimize
        results["next_config_has_react_icons"] = has_react_icons

        if not has_optimize or not has_react_icons:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: next.config.ts missing optimizePackageImports for react-icons")
            print("Output:")
            print(json.dumps(results))
            return 1

        # 2. package.json must NOT contain @tailwindcss/postcss (Tailwind v4 plugin)
        pkg_path = os.path.join(interface_dir, "package.json")
        with open(pkg_path, "r") as f:
            pkg_data = json.load(f)
        dev_deps = pkg_data.get("devDependencies", {})
        has_tw4_postcss = "@tailwindcss/postcss" in dev_deps
        results["package_json_has_tailwindcss_postcss_v4"] = has_tw4_postcss

        if has_tw4_postcss:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: @tailwindcss/postcss (Tailwind v4) conflicts with tailwindcss v3 and causes infinite compile hang")
            print("Output:")
            print(json.dumps(results))
            return 1

        # 3. postcss.config.mjs (Tailwind v4 style) must NOT exist
        postcss_mjs_path = os.path.join(interface_dir, "postcss.config.mjs")
        postcss_mjs_exists = os.path.exists(postcss_mjs_path)
        results["postcss_config_mjs_exists"] = postcss_mjs_exists

        if postcss_mjs_exists:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: postcss.config.mjs (Tailwind v4) should not coexist with postcss.config.js (Tailwind v3)")
            print("Output:")
            print(json.dumps(results))
            return 1

        # 4. postcss.config.js (Tailwind v3 style) must exist
        postcss_js_path = os.path.join(interface_dir, "postcss.config.js")
        postcss_js_exists = os.path.exists(postcss_js_path)
        results["postcss_config_js_exists"] = postcss_js_exists

        if not postcss_js_exists:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: postcss.config.js (Tailwind v3) must exist")
            print("Output:")
            print(json.dumps(results))
            return 1

        print(f"[{test_name}] PASS")
        print(f"About: {about}")
        print("Output:")
        print(json.dumps(results))
        return 0
    except Exception as exc:  # noqa: BLE001
        import traceback
        print(f"[{test_name}] FAIL")
        print(f"About: {about}")
        print(f"Reason: {exc}")
        print("Output:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
