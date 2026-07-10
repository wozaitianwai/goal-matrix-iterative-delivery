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
COMMIT_APPROVAL_TRAILER = "goal-matrix-approval:"


class GovernanceRangeError(ValueError):
    pass


def git_lines(root, *args):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        return []
    return [line for line in result.stdout.splitlines() if line]


def git_output(root, *args):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
    )
    return result.stdout if result.returncode == 0 else ""


def git_text(root, ref, path):
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:{path}"],
        text=True,
        capture_output=True,
    )
    return result.stdout if result.returncode == 0 else None


def has_worktree_changes(root):
    if git_lines(root, "diff", "--name-only", "HEAD", "--"):
        return True
    return bool(git_lines(root, "ls-files", "--others", "--exclude-standard"))


def changed_files(root, base=None, head=None):
    if base or head:
        head = head or "HEAD"
        base = base or f"{head}^"
        result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-only", base, head, "--"],
            text=True,
            capture_output=True,
        )
        if result.returncode:
            detail = result.stderr.strip() or "git diff failed"
            raise GovernanceRangeError(f"invalid governance diff range {base}..{head}: {detail}")
        return [line for line in result.stdout.splitlines() if line]
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


def message_has_approval_trailer(root, ref):
    message = git_output(root, "log", "-1", "--pretty=%B", ref)
    for line in message.splitlines():
        key, _, value = line.partition(":")
        if f"{key.lower()}:" == COMMIT_APPROVAL_TRAILER and value.strip():
            return True
    return False


def commit_has_approval_trailer(root, policy, base=None, head=None):
    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true":
        return False
    actor = os.environ.get("GITHUB_ACTOR", "").casefold()
    trusted_actors = {
        str(item).casefold() for item in policy.get("approvalActors", []) if str(item).strip()
    }
    if not actor or actor not in trusted_actors:
        return False
    if not head and has_worktree_changes(root):
        return False
    head = head or "HEAD"
    if message_has_approval_trailer(root, head):
        return True
    parents = git_lines(root, "rev-list", "--parents", "-n", "1", head)
    base_sha = git_output(root, "rev-parse", base).strip() if base else ""
    parts = parents[0].split() if len(parents) == 1 else []
    return len(parts) == 3 and parts[1] == base_sha and message_has_approval_trailer(root, parts[2])


def path_text(root, path, ref=None):
    if ref:
        return git_text(root, ref, path)
    file_path = root / path
    return file_path.read_text(encoding="utf-8") if file_path.is_file() else None


def package_version_only_bump(root, path, base=None, head=None):
    if path != "package.json":
        return False
    previous_ref = base or ("HEAD" if path in git_lines(root, "diff", "--name-only", "HEAD", "--") else "HEAD^")
    previous = json_text(git_text(root, previous_ref, path))
    current = json_text(path_text(root, path, head))
    if not previous or not current:
        return False
    version = current.get("version")
    previous_without_version = {key: value for key, value in previous.items() if key != "version"}
    current_without_version = {key: value for key, value in current.items() if key != "version"}
    if not version or previous.get("version") == version or previous_without_version != current_without_version:
        return False
    manifest = json_text(path_text(root, ".codex-plugin/plugin.json", head))
    changelog = path_text(root, "CHANGELOG.md", head) or ""
    return manifest.get("version") == version and version in changelog


def has_approval(root, policy, base=None, head=None):
    value = os.environ.get(policy.get("approvalEnv", DEFAULT_APPROVAL_ENV), "")
    if value.lower() in {"1", "true", "yes", "approved"}:
        return True
    return commit_has_approval_trailer(root, policy, base, head)


def approval_source(root, policy, base=None, head=None):
    value = os.environ.get(policy.get("approvalEnv", DEFAULT_APPROVAL_ENV), "")
    if value.lower() in {"1", "true", "yes", "approved"}:
        return policy.get("approvalEnv", DEFAULT_APPROVAL_ENV)
    if commit_has_approval_trailer(root, policy, base, head):
        return "trusted GitHub actor plus Goal-Matrix-Approval commit trailer"
    return f"{policy.get('approvalEnv', DEFAULT_APPROVAL_ENV)} or trusted GitHub actor attestation"


def load_policy(root):
    path = root / "loop-governance.json"
    if not path.is_file():
        raise SystemExit("missing loop-governance.json")
    return json.loads(path.read_text(encoding="utf-8"))


def publish_action_changed(root, path, patterns, head=None):
    if not fnmatch.fnmatch(path, PUBLISH_WORKFLOW_GLOB):
        return False
    text = path_text(root, path, head)
    if text is None:
        return False
    text = text.lower()
    return any(pattern.lower() in text for pattern in patterns)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--base", default=os.environ.get("GOAL_MATRIX_BASE_SHA", ""))
    parser.add_argument("--head", default=os.environ.get("GOAL_MATRIX_HEAD_SHA", ""))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    policy = load_policy(root)
    base = args.base or None
    head = args.head or None
    try:
        paths = changed_files(root, base, head)
    except GovernanceRangeError as exc:
        print(exc, file=sys.stderr)
        return 2
    approved = has_approval(root, policy, base, head)
    source = approval_source(root, policy, base, head)
    problems = []

    for path in paths:
        if matches(path, policy.get("blockedPaths", [])):
            problems.append(f"{path} is blocked by governance policy")
        if (
            matches(path, policy.get("approvalRequiredPaths", []))
            and not approved
            and not package_version_only_bump(root, path, base, head)
        ):
            problems.append(f"{path} requires approval via {source}")
        if publish_action_changed(root, path, policy.get("publishActionPatterns", []), head) and not approved:
            problems.append(f"{path} publish action requires approval")

    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
