#!/usr/bin/env python3
import argparse
import os
import shutil
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


def install_project(tool, target, init_type):
    target.mkdir(parents=True, exist_ok=True)
    messages = []
    messages.append("codex project scope initializes .goal-matrix only; install the Codex plugin globally for hooks")
    rc = init_goal_matrix(target, init_type)
    messages.append(f"initialized .goal-matrix for {target}")
    print("\n".join(messages))
    return rc


def main():
    parser = argparse.ArgumentParser(description="Install one Goal Matrix adapter into a target project.")
    parser.add_argument("tool", choices=("codex",))
    parser.add_argument("--scope", default="project", choices=("project", "global"), help="Install into one project or global Codex.")
    parser.add_argument("--target", help="Target project root. Required for --scope project.")
    parser.add_argument("--type", default="iteration", choices=("new-project", "iteration", "bugfix", "legacy-baseline"))
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
    return install_project(args.tool, Path(args.target).resolve(), args.type)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    sys.exit(main())
