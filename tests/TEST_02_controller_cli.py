import json
import os
import subprocess
import sys


def main() -> int:
    test_name = "TEST_02_controller_cli"
    about = "CLI dry-run returns JSON and expected command"
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script = os.path.join(root, "core", "controller", "vbox_controller.py")
        cmd = [
            sys.executable,
            script,
            "--dry-run",
            "start",
            "--vm",
            "TestVM",
            "--headless",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print(f"Reason: CLI returned {proc.returncode}")
            print("Output:")
            print(proc.stdout.rstrip())
            if proc.stderr:
                print(proc.stderr.rstrip())
            return 1

        payload = json.loads(proc.stdout)
        expected = ["VBoxManage", "startvm", "TestVM", "--type", "headless"]
        if payload.get("cmd") != expected:
            print(f"[{test_name}] FAIL")
            print(f"About: {about}")
            print(f"Reason: Expected cmd {expected}, got {payload.get('cmd')}")
            print("Output:")
            print(proc.stdout.rstrip())
            return 1

        print(f"[{test_name}] PASS")
        print(f"About: {about}")
        print("Output:")
        print(proc.stdout.rstrip())
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
