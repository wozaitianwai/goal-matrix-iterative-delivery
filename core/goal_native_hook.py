#!/usr/bin/env python3
import os
import re
import shlex
import subprocess
from pathlib import Path


MANAGED_MARKER = "# goal-matrix-managed-pre-push:v1"
GUARD_PATH_PREFIX = "# goal-matrix-guard-path: "
LEGACY_SIGNATURES = (
    "repo_root=$(git rev-parse --show-toplevel)",
    "goal_guard.py",
    "publish-gate",
    "pre-push.goal-matrix.previous",
)


def native_pre_push_hook_path(root):
    root = Path(root).resolve()
    configured = subprocess.run(
        ["git", "-C", str(root), "config", "--path", "--get", "core.hooksPath"],
        text=True,
        capture_output=True,
    )
    if configured.returncode == 0 and configured.stdout.strip():
        hooks_dir = Path(configured.stdout.strip()).expanduser()
        if not hooks_dir.is_absolute():
            hooks_dir = root / hooks_dir
        return hooks_dir.resolve() / "pre-push"

    resolved = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-path", "hooks/pre-push"],
        text=True,
        capture_output=True,
    )
    if resolved.returncode == 0 and resolved.stdout.strip():
        hook = Path(resolved.stdout.strip())
        return hook.resolve() if hook.is_absolute() else (root / hook).resolve()
    return root / ".git" / "hooks" / "pre-push"


def native_pre_push_hook_text(guard_path):
    guard_path = Path(guard_path).resolve()
    quoted_guard = shlex.quote(str(guard_path))
    return f"""#!/bin/sh
{MANAGED_MARKER}
{GUARD_PATH_PREFIX}{guard_path}
set -eu
repo_root=$(git rev-parse --show-toplevel)
goal_guard={quoted_guard}
if [ ! -f "$goal_guard" ]; then
  printf '%s\n' "goal-matrix pre-push hook is stale: $goal_guard is missing; reinstall the native hook" >&2
  exit 1
fi
python3 "$goal_guard" publish-gate --root "$repo_root"
previous_hook="${{0}}.goal-matrix.previous"
if [ -x "$previous_hook" ]; then
  "$previous_hook" "$@"
elif [ -f "$previous_hook" ]; then
  sh "$previous_hook" "$@"
fi
"""


def _managed_guard_path(text):
    for line in text.splitlines():
        if line.startswith(GUARD_PATH_PREFIX):
            return line[len(GUARD_PATH_PREFIX):].strip()
    legacy = re.search(r'''python3\s+["']([^"']*goal_guard\.py)["']\s+publish-gate''', text)
    return legacy.group(1) if legacy else ""


def inspect_native_pre_push_hook(hook_path, expected_guard_path):
    hook_path = Path(hook_path)
    expected_guard = Path(expected_guard_path).resolve()
    exists = hook_path.is_file()
    if not exists:
        state = "absent"
        text = ""
    else:
        text = hook_path.read_text(encoding="utf-8", errors="ignore")
        marker_present = MANAGED_MARKER in text
        legacy_managed = all(signature in text for signature in LEGACY_SIGNATURES)
        managed = marker_present or legacy_managed
        guard_path = _managed_guard_path(text)
        if not managed:
            state = "unmanaged"
        elif not marker_present:
            state = "stale"
        elif guard_path != str(expected_guard):
            state = "stale"
        elif not os.access(hook_path, os.X_OK) or not expected_guard.is_file():
            state = "broken"
        elif text != native_pre_push_hook_text(expected_guard):
            state = "broken"
        else:
            state = "current"

    guard_path = _managed_guard_path(text) if text else ""
    managed = state in {"current", "stale", "broken"}
    return {
        "state": state,
        "exists": exists,
        "managed": managed,
        "executable": exists and os.access(hook_path, os.X_OK),
        "guardPath": guard_path or None,
        "expectedGuardPath": str(expected_guard),
        "current": state == "current",
        "refreshRequired": state in {"stale", "broken"},
    }
