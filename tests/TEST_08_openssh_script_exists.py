import os

def test_openssh_script_exists():
    script_path = "SandboxShare/install_openssh.ps1"
    print(f"Checking for {script_path}...")
    if os.path.exists(script_path):
        print(f"[TEST_08_openssh_script_exists] PASS")
        print(f"About: Verify OpenSSH installation script exists in SandboxShare")
        print(f"Output: File found at {script_path}")
    else:
        print(f"[TEST_08_openssh_script_exists] FAIL")
        print(f"About: Verify OpenSSH installation script exists in SandboxShare")
        print(f"Reason: File NOT found at {script_path}")
        exit(1)

if __name__ == "__main__":
    test_openssh_script_exists()
