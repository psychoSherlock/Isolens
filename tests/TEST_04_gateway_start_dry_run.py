import json
import os
import sys


def main() -> int:
    test_name = "TEST_04_gateway_start_dry_run"
    about = "Gateway start endpoint returns dry-run VBoxManage command"
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)

        from core.gateway.api_models import VMStartRequest
        from core.gateway.controller_routes import vm_start

        payload = VMStartRequest(
            vm="TestVM",
            headless=True,
            dry_run=True,
            raise_on_error=True,
        )
        res = vm_start(payload)
        raw_output = res.model_dump()

        if raw_output.get("status") != "ok":
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: Start endpoint returned error status")
            print("Output:")
            print(json.dumps(raw_output))
            return 1

        expected_cmd = ["VBoxManage", "startvm", "TestVM", "--type", "headless"]
        if raw_output.get("data", {}).get("cmd") != expected_cmd:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: Command mismatch")
            print("Output:")
            print(json.dumps(raw_output))
            return 1

        print(f"[{test_name}] PASS")
        print(f"About: {about}")
        print("Output:")
        print(json.dumps(raw_output))
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
