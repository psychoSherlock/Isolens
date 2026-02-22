"""VirtualBox controller utilities for IsoLens."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CommandResult:
    cmd: List[str]
    returncode: int
    stdout: str
    stderr: str

    def to_dict(self) -> dict:
        return {
            "cmd": self.cmd,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


class VBoxManageClient:
    """Thin wrapper around VBoxManage commands.

    Designed for both programmatic use and CLI execution.
    """

    def __init__(
        self,
        vboxmanage_path: str = "VBoxManage",
        dry_run: bool = False,
        raise_on_error: bool = True,
    ):
        self.vboxmanage_path = vboxmanage_path
        self.dry_run = dry_run
        self.raise_on_error = raise_on_error

    def _run(
        self,
        args: List[str],
        *,
        check: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> CommandResult:
        cmd = [self.vboxmanage_path] + args
        if self.dry_run:
            return CommandResult(cmd=cmd, returncode=0, stdout="", stderr="")

        if check is None:
            check = self.raise_on_error

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        result = CommandResult(
            cmd=cmd,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
        if check and proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "VBoxManage command failed")
        return result

    def list_vms(self) -> CommandResult:
        return self._run(["list", "vms"])

    def list_running_vms(self) -> CommandResult:
        return self._run(["list", "runningvms"])

    def show_vm_info(self, vm: str, machinereadable: bool = False) -> CommandResult:
        args = ["showvminfo", vm]
        if machinereadable:
            args.append("--machinereadable")
        return self._run(args)

    def start_vm(self, vm: str, headless: bool = False) -> CommandResult:
        args = ["startvm", vm]
        if headless:
            args += ["--type", "headless"]
        return self._run(args)

    def control_vm(self, vm: str, action: str) -> CommandResult:
        return self._run(["controlvm", vm, action])

    def poweroff_vm(self, vm: str) -> CommandResult:
        return self.control_vm(vm, "poweroff")

    def savestate_vm(self, vm: str) -> CommandResult:
        return self.control_vm(vm, "savestate")

    def pause_vm(self, vm: str) -> CommandResult:
        return self.control_vm(vm, "pause")

    def resume_vm(self, vm: str) -> CommandResult:
        return self.control_vm(vm, "resume")

    def reset_vm(self, vm: str) -> CommandResult:
        return self.control_vm(vm, "reset")

    def shutdown_vm(self, vm: str, force: bool = False) -> CommandResult:
        args = ["controlvm", vm, "shutdown"]
        if force:
            args.append("--force")
        return self._run(args)

    def snapshot_take(self, vm: str, name: str) -> CommandResult:
        return self._run(["snapshot", vm, "take", name])

    def snapshot_restore(self, vm: str, name: str) -> CommandResult:
        return self._run(["snapshot", vm, "restore", name])

    def snapshot_restore_current(self, vm: str) -> CommandResult:
        return self._run(["snapshot", vm, "restorecurrent"])


def _print_result(result: CommandResult, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="IsoLens VirtualBox controller (VBoxManage wrapper)",
    )
    parser.add_argument(
        "--vboxmanage",
        default="VBoxManage",
        help="Path to VBoxManage binary",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing VBoxManage",
    )
    parser.add_argument(
        "--no-raise",
        action="store_true",
        help="Do not raise on non-zero VBoxManage exit codes",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON results",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all VMs")
    sub.add_parser("list-running", help="List running VMs")

    info = sub.add_parser("info", help="Show VM info")
    info.add_argument("--vm", required=True)
    info.add_argument("--machinereadable", action="store_true")

    start = sub.add_parser("start", help="Start VM")
    start.add_argument("--vm", required=True)
    start.add_argument("--headless", action="store_true")

    poweroff = sub.add_parser("poweroff", help="Power off VM")
    poweroff.add_argument("--vm", required=True)

    savestate = sub.add_parser("savestate", help="Save VM state")
    savestate.add_argument("--vm", required=True)

    pause = sub.add_parser("pause", help="Pause VM")
    pause.add_argument("--vm", required=True)

    resume = sub.add_parser("resume", help="Resume VM")
    resume.add_argument("--vm", required=True)

    reset = sub.add_parser("reset", help="Reset VM")
    reset.add_argument("--vm", required=True)

    shutdown = sub.add_parser("shutdown", help="Shutdown VM")
    shutdown.add_argument("--vm", required=True)
    shutdown.add_argument("--force", action="store_true")

    take = sub.add_parser("snapshot-take", help="Take snapshot")
    take.add_argument("--vm", required=True)
    take.add_argument("--name", required=True)

    restore = sub.add_parser("snapshot-restore", help="Restore snapshot")
    restore.add_argument("--vm", required=True)
    restore.add_argument("--name", required=True)

    restore_current = sub.add_parser(
        "snapshot-restore-current",
        help="Restore current snapshot",
    )
    restore_current.add_argument("--vm", required=True)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    client = VBoxManageClient(
        vboxmanage_path=args.vboxmanage,
        dry_run=args.dry_run,
        raise_on_error=not args.no_raise,
    )

    try:
        if args.command == "list":
            result = client.list_vms()
        elif args.command == "list-running":
            result = client.list_running_vms()
        elif args.command == "info":
            result = client.show_vm_info(args.vm, machinereadable=args.machinereadable)
        elif args.command == "start":
            result = client.start_vm(args.vm, headless=args.headless)
        elif args.command == "poweroff":
            result = client.poweroff_vm(args.vm)
        elif args.command == "savestate":
            result = client.savestate_vm(args.vm)
        elif args.command == "pause":
            result = client.pause_vm(args.vm)
        elif args.command == "resume":
            result = client.resume_vm(args.vm)
        elif args.command == "reset":
            result = client.reset_vm(args.vm)
        elif args.command == "shutdown":
            result = client.shutdown_vm(args.vm, force=args.force)
        elif args.command == "snapshot-take":
            result = client.snapshot_take(args.vm, args.name)
        elif args.command == "snapshot-restore":
            result = client.snapshot_restore(args.vm, args.name)
        elif args.command == "snapshot-restore-current":
            result = client.snapshot_restore_current(args.vm)
        else:
            parser.error("Unknown command")
            return 2
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    _print_result(result, as_json=args.json or args.dry_run)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
