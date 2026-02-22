import json
import os
import sys


def main() -> int:
    test_name = "TEST_05_gateway_main_module"
    about = "Gateway __main__ exposes CLI parser and main without side effects"
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)

        import core.gateway.__main__ as gateway_main

        parser = gateway_main.build_arg_parser()
        args = parser.parse_args([])
        raw_output = {
            "host": args.host,
            "port": args.port,
            "reload": args.reload,
            "log_level": args.log_level,
        }

        if args.host != "127.0.0.1" or args.port != 8000:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print("Reason: Default args mismatch")
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
