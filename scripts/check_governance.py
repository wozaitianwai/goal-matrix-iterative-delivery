#!/usr/bin/env python3
import argparse
import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_APPROVAL_ENV = "GOAL_MATRIX_APPROVED"
PUBLISH_WORKFLOW_GLOB = ".github/workflows/*.y*ml"


def git_lines(root, *args):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        return []
    return [line for line in result.stdout.splitlines() if line]


def git_text(root, ref, path):
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:{path}"],
        text=True,
        capture_output=True,
    )
    return result.stdout if result.returncode == 0 else None


def changed_files(root):
    paths = set(git_lines(root, "diff", "--name-only", "HEAD", "--"))
    paths.update(git_lines(root, "ls-files", "--others", "--exclude-standard"))
    if paths:
        return sorted(paths)
    if git_lines(root, "rev-parse", "--verify", "HEAD^"):
        return git_lines(root, "diff", "--name-only", "HEAD^", "HEAD", "--")
    return git_lines(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD")


def json_text(text):
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def matches(path, patterns):
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def package_version_only_bump(root, path):
    if path != "package.json":
        return False
    previous_ref = "HEAD" if path in git_lines(root, "diff", "--name-only", "HEAD", "--") else "HEAD^"
    previous = json_text(git_text(root, previous_ref, path))
    current_path = root / path
    current = json_text(current_path.read_text(encoding="utf-8")) if current_path.is_file() else {}
    if not previous or not current:
        return False
    version = current.get("version")
    previous_without_version = {key: value for key, value in previous.items() if key != "version"}
    current_without_version = {key: value for key, value in current.items() if key != "version"}
    if not version or previous.get("version") == version or previous_without_version != current_without_version:
        return False
    manifest_path = root / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        return False
    manifest = json_text(manifest_path.read_text(encoding="utf-8"))
    changelog = root / "CHANGELOG.md"
    return manifest.get("version") == version and changelog.is_file() and version in changelog.read_text(encoding="utf-8")


def has_approval(policy):
    value = os.environ.get(policy.get("approvalEnv", DEFAULT_APPROVAL_ENV), "")
    return value.lower() in {"1", "true", "yes", "approved"}


def load_policy(root):
    path = root / "loop-governance.json"
    if not path.is_file():
        raise SystemExit("missing loop-governance.json")
    return json.loads(path.read_text(encoding="utf-8"))


def publish_action_changed(root, path, patterns):
    if not fnmatch.fnmatch(path, PUBLISH_WORKFLOW_GLOB):
        return False
    file_path = root / path
    if not file_path.is_file():
        return False
    text = file_path.read_text(encoding="utf-8", errors="ignore").lower()
    return any(pattern.lower() in text for pattern in patterns)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    policy = load_policy(root)
    approved = has_approval(policy)
    problems = []

    for path in changed_files(root):
        if matches(path, policy.get("blockedPaths", [])):
            problems.append(f"{path} is blocked by governance policy")
        if (
            matches(path, policy.get("approvalRequiredPaths", []))
            and not approved
            and not package_version_only_bump(root, path)
        ):
            problems.append(f"{path} requires approval via {policy.get('approvalEnv', DEFAULT_APPROVAL_ENV)}")
        if publish_action_changed(root, path, policy.get("publishActionPatterns", [])) and not approved:
            problems.append(f"{path} publish action requires approval")

    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
