import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

try:
    from goal_policy import collect_payload_commands, protected_command_matches
except ImportError:
    from core.goal_policy import collect_payload_commands, protected_command_matches


def git_output(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
    )


def current_branch(root):
    result = git_output(root, "branch", "--show-current")
    if result.returncode:
        return ""
    return result.stdout.strip()


def publish_state_problems(root, goals, active_goal):
    problems = []
    dirty = git_output(root, "status", "--porcelain")
    if dirty.returncode or dirty.stdout.strip():
        problems.append("uncommitted changes present; commit, stash, or discard them before push")

    if not goals:
        return problems
    if active_goal:
        problems.append(f"active goal still open: {active_goal}")

    done_goals = [goal for goal in goals if goal["status"].lower() == "done"]
    if done_goals:
        latest_done = done_goals[-1]["id"]
        evidence = Path(root) / ".goal-matrix" / "evidence" / f"{latest_done}.log"
        if not evidence.is_file():
            problems.append(f"missing checkpoint evidence: {evidence.relative_to(root)}")
    return problems


def git_ref_exists(root, ref):
    return git_output(root, "rev-parse", "--verify", "--quiet", ref).returncode == 0


def remote_default_ref(root):
    result = git_output(root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    ref = result.stdout.strip() if result.returncode == 0 else ""
    return ref if ref and git_ref_exists(root, ref) else ""


def publish_base_ref(root, branch):
    upstream = git_output(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if upstream.returncode == 0 and upstream.stdout.strip():
        return upstream.stdout.strip()
    candidate = f"origin/{branch}" if branch else ""
    if candidate and git_ref_exists(root, candidate):
        return candidate
    return remote_default_ref(root)


def hook_payload_text(raw):
    if not raw.strip():
        return ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    parts = []

    def walk(value):
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)

    walk(data)
    return "\n".join(parts)


GIT_GLOBAL_OPTIONS_WITH_VALUE = {
    "-C",
    "-c",
    "--config-env",
    "--exec-path",
    "--git-dir",
    "--namespace",
    "--super-prefix",
    "--work-tree",
}

GIT_GLOBAL_OPTIONS_WITH_INLINE_VALUE = tuple(
    f"{option}=" for option in GIT_GLOBAL_OPTIONS_WITH_VALUE if option.startswith("--")
)


def command_is_git_push(command):
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    for index, token in enumerate(tokens):
        if os.path.basename(token) != "git":
            continue
        cursor = index + 1
        while cursor < len(tokens):
            current = tokens[cursor]
            if current == "push":
                return True
            if current == "--":
                return False
            if current in GIT_GLOBAL_OPTIONS_WITH_VALUE:
                cursor += 2
                continue
            if current.startswith(GIT_GLOBAL_OPTIONS_WITH_INLINE_VALUE):
                cursor += 1
                continue
            if current.startswith("-"):
                cursor += 1
                continue
            break
    return False


def hook_is_git_push(raw):
    if any(command_is_git_push(command) for command in collect_payload_commands(raw)):
        return True
    text = hook_payload_text(raw)
    return bool(re.search(r"\bgit\s+push\b", text))


def hook_is_publish_action(raw, publish_patterns):
    if hook_is_git_push(raw):
        return True
    if not publish_patterns:
        return False
    text = hook_payload_text(raw).lower()
    for pattern in publish_patterns:
        pattern_lower = pattern.lower().strip()
        if pattern_lower and pattern_lower in text:
            return True
    return any(
        protected_command_matches(command, pattern)
        for command in collect_payload_commands(raw)
        for pattern in publish_patterns
    )


def publish_gate(root, hook_mode=False, goals=None, active_goal="", publish_patterns=()):
    raw = sys.stdin.read()
    root = Path(root)
    if hook_mode and not hook_is_publish_action(raw, publish_patterns):
        return 0

    inside = git_output(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode:
        print("publish gate blocked: not inside a git worktree", file=sys.stderr)
        return 1

    branch = current_branch(root)
    base_ref = publish_base_ref(root, branch)
    if not base_ref:
        print("publish gate blocked: missing upstream or remote default integration base", file=sys.stderr)
        return 1

    counts = git_output(root, "rev-list", "--left-right", "--count", f"HEAD...{base_ref}")
    if counts.returncode:
        print("publish gate blocked: cannot compare local history with upstream", file=sys.stderr)
        return 1
    _, behind_text = counts.stdout.split()[:2]
    problems = publish_state_problems(root, goals or [], active_goal)
    if int(behind_text):
        problems.append(f"remote history not integrated: {behind_text} commit(s) behind {base_ref}")
    for problem in problems:
        print(f"publish gate blocked: {problem}", file=sys.stderr)
    return 1 if problems else 0
