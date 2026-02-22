import json
import os
import sys


def main() -> int:
    test_name = "TEST_03_gateway_ping_version"
    about = "Gateway ping and version endpoints return standard responses"
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)

        from core.gateway.system_routes import ping, version
        from core.gateway.version import VERSION

        ping_res = ping()
        version_res = version()

        raw_output = {
            "ping": ping_res.model_dump(),
            "version": version_res.model_dump(),
        }

        if ping_res.status != "ok":
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: Ping endpoint returned error status")
            print("Output:")
            print(json.dumps(raw_output))
            return 1

        if version_res.data is None or version_res.data.get("version") != VERSION:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: Version mismatch")
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
