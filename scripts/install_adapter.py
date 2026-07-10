#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "goal-matrix-iterative-delivery"


def init_goal_matrix(target, init_type):
    from core.goal_guard import init_project

    return init_project(target, init_type)


def sync_codex_global():
    source = ROOT / "adapters" / "codex" / "skills"
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    destination = codex_home / "skills"
    for src in source.rglob("*"):
        rel = src.relative_to(source)
        dst = destination / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return destination


def install_native_pre_push_hook(target):
    from core.goal_native_hook import (
        inspect_native_pre_push_hook,
        native_pre_push_hook_path,
        native_pre_push_hook_text,
    )

    inside = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--git-dir"],
        text=True,
        capture_output=True,
    )
    if inside.returncode:
        raise SystemExit("--install-git-hook requires an initialized git repository")
    hook = native_pre_push_hook_path(target)
    previous = hook.with_name("pre-push.goal-matrix.previous")
    guard_path = ROOT / "core" / "goal_guard.py"
    state = inspect_native_pre_push_hook(hook, guard_path)
    if state["current"]:
        return hook
    if state["exists"] and not state["managed"]:
        if previous.exists():
            raise SystemExit(f"{hook} and {previous} already exist; restore or merge the hook manually")
        hook.rename(previous)
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(native_pre_push_hook_text(guard_path), encoding="utf-8")
    hook.chmod(0o755)
    return hook


def install_project(tool, target, init_type, install_git_hook=False):
    target.mkdir(parents=True, exist_ok=True)
    messages = []
    messages.append("codex project scope initializes .goal-matrix only; install the Codex plugin globally for hooks")
    rc = init_goal_matrix(target, init_type)
    messages.append(f"initialized .goal-matrix for {target}")
    if install_git_hook:
        hook = install_native_pre_push_hook(target)
        messages.append(f"installed native pre-push hook at {hook}")
    print("\n".join(messages))
    return rc


def main():
    parser = argparse.ArgumentParser(description="Install one Goal Matrix adapter into a target project.")
    parser.add_argument("tool", choices=("codex",))
    parser.add_argument("--scope", default="project", choices=("project", "global"), help="Install into one project or global Codex.")
    parser.add_argument("--target", help="Target project root. Required for --scope project.")
    parser.add_argument("--type", default="iteration", choices=("new-project", "iteration", "bugfix", "legacy-baseline"))
    parser.add_argument("--install-git-hook", action="store_true", help="Also install a native git pre-push hook for publish-gate.")
    args = parser.parse_args()

    if args.scope == "global":
        if args.tool != "codex":
            parser.error("--scope global is only supported for codex")
        destination = sync_codex_global()
        print(f"installed Codex skill to {destination}")
        print("global install does not edit Codex config or marketplace files")
        return 0

    if not args.target:
        parser.error("--target is required for --scope project")
    return install_project(args.tool, Path(args.target).resolve(), args.type, args.install_git_hook)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    sys.exit(main())
