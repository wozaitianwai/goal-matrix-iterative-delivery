#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(os.environ.get("GOAL_MATRIX_VERIFY_ROOT", Path.cwd())).resolve()
CACHE_ROOT = Path(tempfile.gettempdir()) / "goal-matrix-pycache"
ENV = {"PYTHONPYCACHEPREFIX": str(CACHE_ROOT)}

CHECKS = (
    ("loop audit", [sys.executable, "scripts/loop_audit.py", "--root", ".", "--json"]),
    ("package validation", [sys.executable, "scripts/validate_plugin_package.py", "--root", "."]),
    ("pi-extension tests", ["node", "--test", "pi-extension/test/extension.test.js"]),
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
            "scripts/check_governance.py",
            "scripts/loop_verify.py",
            "tests/test_goal_guard.py",
        ],
    ),
    ("tests", [sys.executable, "tests/test_goal_guard.py"]),
    ("governance", [sys.executable, "scripts/check_governance.py", "--root", "."]),
    ("git diff --check", ["git", "diff", "--check"]),
)


def main():
    for name, command in CHECKS:
        print(f"==> {name}", flush=True)
        result = subprocess.run(command, cwd=ROOT, env={**os.environ, **ENV})
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
