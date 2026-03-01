#!/usr/bin/env python3
"""TEST_15 — Expanded features tests.

Verifies:
  1. Parser extracts expanded VM info fields (vram, chipset, firmware, etc.)
  2. VBoxManageClient has screenshot_vm method
  3. Controller routes has live screenshot endpoint
  4. Analysis routes has clear reports endpoint
  5. api.ts exports vmScreenURL and clearAllReports
  6. Sandbox page has no restore snapshot button
  7. Sandbox page has live preview section
  8. Reports page has clear all button
"""

import json
import os
import re
import sys

TEST_NAME = "TEST_15_expanded_features"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, PROJECT_ROOT)

passed = 0
failed = 0


def report(name, ok, output, reason=""):
    global passed, failed
    tag = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
    print(f"[{TEST_NAME}:{name}] {tag}")
    print(f"  About: {name}")
    if not ok and reason:
        print(f"  Reason: {reason}")
    print(f"  Output: {output}\n")


# ────────────────────────────────────────────────────────────────────
# 1. Parser: expanded fields
# ────────────────────────────────────────────────────────────────────

def test_parser_expanded_fields():
    """parse_showvminfo should extract vram, chipset, firmware, graphics, vrde."""
    from core.modules.vbox_output_parser import parse_showvminfo

    sample = (
        'name="WindowsSandbox"\n'
        'UUID="8e6277b9-72b9-4e35-ba9c-46cf2b24fe87"\n'
        'ostype="Windows 10 (64-bit)"\n'
        'VMState="running"\n'
        'memory=6141\n'
        'cpus=2\n'
        'vram=128\n'
        'chipset="piix3"\n'
        'firmware="BIOS"\n'
        'graphicscontroller="vboxsvga"\n'
        'accelerate3d="off"\n'
        'vrde="on"\n'
        'vrdeport=3389\n'
        'vrdeauthtype="null"\n'
        'nic1="nat"\n'
        'natnet1="nat"\n'
        'macaddress1="080027416E0E"\n'
        'cableconnected1="on"\n'
        'CurrentSnapshotName="Working"\n'
    )
    info = parse_showvminfo(sample)

    checks = {
        "vram_mb": (info.get("vram_mb"), 128),
        "chipset": (info.get("chipset"), "piix3"),
        "firmware": (info.get("firmware"), "BIOS"),
        "graphics_controller": (info.get("graphics_controller"), "vboxsvga"),
        "accelerate_3d": (info.get("accelerate_3d"), False),
        "vrde": (info.get("vrde"), True),
        "vrde_port": (info.get("vrde_port"), 3389),
        "vrde_auth_type": (info.get("vrde_auth_type"), "null"),
    }

    all_ok = True
    details = []
    for key, (got, expected) in checks.items():
        ok = got == expected
        details.append(f"{key}: {'✓' if ok else '✗'} (got={got!r}, expected={expected!r})")
        if not ok:
            all_ok = False

    report(
        "Parser expanded fields",
        all_ok,
        "\n    ".join(details),
        "Some expanded fields missing or wrong",
    )


# ────────────────────────────────────────────────────────────────────
# 2. VBoxManageClient.screenshot_vm method
# ────────────────────────────────────────────────────────────────────

def test_screenshot_vm_method():
    """VBoxManageClient should have a screenshot_vm method."""
    from core.controller.vbox_controller import VBoxManageClient
    has_method = hasattr(VBoxManageClient, "screenshot_vm")
    sig = ""
    if has_method:
        import inspect
        sig = str(inspect.signature(VBoxManageClient.screenshot_vm))
    report(
        "VBoxManageClient.screenshot_vm exists",
        has_method,
        f"has_method={has_method}, signature={sig}",
        "screenshot_vm method not found",
    )


# ────────────────────────────────────────────────────────────────────
# 3. Controller routes: /api/vms/screen endpoint
# ────────────────────────────────────────────────────────────────────

def test_controller_screen_endpoint():
    """controller_routes.py should define vm_live_screenshot endpoint."""
    path = os.path.join(PROJECT_ROOT, "core", "gateway", "controller_routes.py")
    with open(path, "r") as f:
        content = f.read()
    has_decorator = '@router.get("/screen")' in content
    has_function = "def vm_live_screenshot" in content
    ok = has_decorator and has_function
    report(
        "GET /api/vms/screen endpoint",
        ok,
        f"decorator={has_decorator}, function={has_function}",
        "Live screenshot endpoint not found",
    )


# ────────────────────────────────────────────────────────────────────
# 4. Analysis routes: DELETE /api/analysis/reports/clear
# ────────────────────────────────────────────────────────────────────

def test_clear_reports_endpoint():
    """analysis_routes.py should define clear_all_reports endpoint."""
    path = os.path.join(PROJECT_ROOT, "core", "gateway", "analysis_routes.py")
    with open(path, "r") as f:
        content = f.read()
    has_decorator = '@router.delete("/reports/clear"' in content
    has_function = "def clear_all_reports" in content
    ok = has_decorator and has_function
    report(
        "DELETE /api/analysis/reports/clear endpoint",
        ok,
        f"decorator={has_decorator}, function={has_function}",
        "Clear reports endpoint not found",
    )


# ────────────────────────────────────────────────────────────────────
# 5. api.ts: vmScreenURL and clearAllReports exports
# ────────────────────────────────────────────────────────────────────

def test_api_ts_exports():
    """api.ts should export vmScreenURL and clearAllReports functions."""
    path = os.path.join(PROJECT_ROOT, "core", "interface", "src", "lib", "api.ts")
    with open(path, "r") as f:
        content = f.read()
    has_screen = "export function vmScreenURL" in content
    has_clear = "export async function clearAllReports" in content
    ok = has_screen and has_clear
    report(
        "api.ts new exports",
        ok,
        f"vmScreenURL={has_screen}, clearAllReports={has_clear}",
        "Missing api.ts exports",
    )


# ────────────────────────────────────────────────────────────────────
# 6. Sandbox page: no restore snapshot button
# ────────────────────────────────────────────────────────────────────

def test_no_restore_button():
    """sandbox/page.tsx should NOT have Restore Snapshot button."""
    path = os.path.join(
        PROJECT_ROOT, "core", "interface", "src", "app", "sandbox", "page.tsx"
    )
    with open(path, "r") as f:
        content = f.read()
    has_restore_handler = "handleRestore" in content
    has_restore_button = "Restore Snapshot" in content
    has_import = "restoreCurrentSnapshot" in content
    ok = not has_restore_handler and not has_restore_button and not has_import
    report(
        "No restore snapshot in sandbox page",
        ok,
        f"handler={has_restore_handler}, button={has_restore_button}, import={has_import}",
        "Restore snapshot remnants still present",
    )


# ────────────────────────────────────────────────────────────────────
# 7. Sandbox page: live preview section
# ────────────────────────────────────────────────────────────────────

def test_live_preview_section():
    """sandbox/page.tsx should have the live VM preview section."""
    path = os.path.join(
        PROJECT_ROOT, "core", "interface", "src", "app", "sandbox", "page.tsx"
    )
    with open(path, "r") as f:
        content = f.read()
    has_preview_state = "previewEnabled" in content
    has_preview_component = "Live VM Preview" in content
    has_screen_import = "vmScreenURL" in content
    has_live_badge = "LIVE" in content
    ok = has_preview_state and has_preview_component and has_screen_import and has_live_badge
    report(
        "Live VM preview section",
        ok,
        f"state={has_preview_state}, component={has_preview_component}, import={has_screen_import}, badge={has_live_badge}",
        "Live preview section missing or incomplete",
    )


# ────────────────────────────────────────────────────────────────────
# 8. Reports page: clear all button
# ────────────────────────────────────────────────────────────────────

def test_reports_clear_button():
    """reports/page.tsx should have Clear All button with confirmation."""
    path = os.path.join(
        PROJECT_ROOT, "core", "interface", "src", "app", "reports", "page.tsx"
    )
    with open(path, "r") as f:
        content = f.read()
    has_clear_import = "clearAllReports" in content
    has_clear_handler = "handleClearAll" in content
    has_confirm_dialog = "showClearConfirm" in content
    has_delete_button = "Yes, Delete All" in content
    ok = has_clear_import and has_clear_handler and has_confirm_dialog and has_delete_button
    report(
        "Reports clear all button",
        ok,
        f"import={has_clear_import}, handler={has_clear_handler}, confirm={has_confirm_dialog}, button={has_delete_button}",
        "Clear all reports UI missing or incomplete",
    )


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────

def main() -> int:
    test_parser_expanded_fields()
    test_screenshot_vm_method()
    test_controller_screen_endpoint()
    test_clear_reports_endpoint()
    test_api_ts_exports()
    test_no_restore_button()
    test_live_preview_section()
    test_reports_clear_button()

    total = passed + failed
    print(f"\n{'='*60}")
    print(f"[{TEST_NAME}] {passed}/{total} checks passed")
    if failed > 0:
        print(f"[{TEST_NAME}] FAIL — {failed} check(s) failed")
        return 1
    print(f"[{TEST_NAME}] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
