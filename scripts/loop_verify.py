#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CHECKS = (
    ("loop audit", [sys.executable, "scripts/loop_audit.py", "--root", ".", "--json"]),
    ("package validation", [sys.executable, "scripts/validate_plugin_package.py", "--root", "."]),
    (
        "py_compile",
        [
            sys.executable,
            "-m",
            "py_compile",
            "core/goal_guard.py",
            "scripts/install_adapter.py",
            "scripts/validate_plugin_package.py",
            "scripts/loop_audit.py",
            "scripts/loop_verify.py",
            "tests/test_goal_guard.py",
        ],
    ),
    ("tests", [sys.executable, "tests/test_goal_guard.py"]),
    ("git diff --check", ["git", "diff", "--check"]),
)


def main():
    for name, command in CHECKS:
        print(f"==> {name}", flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
