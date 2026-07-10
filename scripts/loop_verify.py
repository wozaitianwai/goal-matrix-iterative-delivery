#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(os.environ.get("GOAL_MATRIX_VERIFY_ROOT", Path.cwd())).resolve()
CACHE_ROOT = Path(tempfile.gettempdir()) / "goal-matrix-pycache"
ENV = {"PYTHONPYCACHEPREFIX": str(CACHE_ROOT)}
DEFAULT_APPROVAL_ENV = "GOAL_MATRIX_APPROVED"

CHECKS = (
    ("package validation", [sys.executable, "scripts/validate_plugin_package.py", "--root", "."]),
    ("pi-extension tests", ["node", "--test", "pi-extension/test/extension.test.js"]),
    ("python lint", [sys.executable, "scripts/lint_python.py"]),
    (
        "py_compile",
        [
            sys.executable,
            "-m",
            "py_compile",
            "scripts/lint_python.py",
            "core/goal_guard.py",
            "core/goal_native_hook.py",
            "core/goal_policy.py",
            "core/goal_projection.py",
            "core/goal_publish.py",
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


def checks(require_level=None):
    audit_command = [sys.executable, "scripts/loop_audit.py", "--root", ".", "--json"]
    if require_level:
        audit_command.extend(("--require-level", require_level))
    return (("loop audit", audit_command), *CHECKS)


def approval_env_name():
    try:
        policy = json.loads((ROOT / "loop-governance.json").read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT_APPROVAL_ENV
    return policy.get("approvalEnv") or DEFAULT_APPROVAL_ENV


def command_env(name):
    env = {**os.environ, **ENV}
    if name != "governance":
        env.pop(approval_env_name(), None)
        env.pop("GOAL_MATRIX_BASE_SHA", None)
        env.pop("GOAL_MATRIX_HEAD_SHA", None)
    if name == "tests":
        for key in tuple(env):
            if key.startswith("GITHUB_"):
                env.pop(key)
    return env


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-level", choices=("L1", "L2", "L3"))
    args = parser.parse_args(argv)
    for name, command in checks(args.require_level):
        print(f"==> {name}", flush=True)
        result = subprocess.run(command, cwd=ROOT, env=command_env(name))
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
