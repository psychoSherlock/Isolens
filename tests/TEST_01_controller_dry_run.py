import json
import os
import sys


def main() -> int:
    test_name = "TEST_01_controller_dry_run"
    about = "Controller dry-run builds correct VBoxManage command"
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)
        from core.controller import VBoxManageClient

        client = VBoxManageClient(dry_run=True)
        result = client.start_vm("TestVM", headless=True)
        expected = ["VBoxManage", "startvm", "TestVM", "--type", "headless"]
        raw_output = json.dumps(result.to_dict())
        if result.cmd != expected:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print(f"Reason: Expected cmd {expected}, got {result.cmd}")
            print("Output:")
            print(raw_output)
            return 1

        print(f"[{test_name}] PASS")
        print(f"About: {about}")
        print("Output:")
        print(raw_output)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[{test_name}] FAIL")
        print(f"About: {about}")
        print(f"Reason: {exc}")
        print("Output:")
        print("")
        return 1


if __name__ == "__main__":
    sys.exit(main())
