import fnmatch
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_APPROVAL_ENV = "GOAL_MATRIX_APPROVED"


def load_project_policy(root):
    policy_path = Path(root) / ".goal-matrix" / "project-policy.json"
    if not policy_path.is_file():
        return {}, None
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, f"invalid project policy JSON: {exc.msg}"
    if not isinstance(policy, dict):
        return {}, "invalid project policy: top-level value must be an object"
    if policy.get("version") != 1:
        return {}, "invalid project policy version: expected 1"
    return policy, None


def read_project_policy(root):
    return load_project_policy(root)[0]


def truthy_env(name):
    return os.environ.get(name, "").lower() in {"1", "true", "yes", "approved"}


def hook_payload_data(raw):
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def path_field_hint(key):
    lowered = key.lower()
    return any(token in lowered for token in ("path", "file", "dir", "target", "source", "destination"))


def command_field_hint(key):
    lowered = key.lower()
    return lowered in {"cmd", "command", "shell", "script"} or lowered.endswith("_cmd")


def normalize_policy_path(root, value):
    text = str(value).strip().strip("'\"")
    if not text or "\n" in text:
        return ""
    path = Path(text).expanduser()
    if path.is_absolute():
        try:
            return path.resolve().relative_to(Path(root).resolve()).as_posix()
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def collect_payload_paths(raw, root):
    data = hook_payload_data(raw)
    paths = set()

    def add_path(value):
        normalized = normalize_policy_path(root, value)
        if normalized:
            paths.add(normalized)

    def walk(value, key=""):
        if isinstance(value, str):
            for match in re.finditer(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", value, re.MULTILINE):
                add_path(match.group(1))
            if path_field_hint(key):
                add_path(value)
        elif isinstance(value, list):
            for item in value:
                walk(item, key)
        elif isinstance(value, dict):
            for child_key, item in value.items():
                walk(item, str(child_key))

    walk(data)
    return sorted(paths)


def collect_payload_commands(raw):
    data = hook_payload_data(raw)
    commands = []

    def walk(value, key=""):
        if isinstance(value, str) and command_field_hint(key):
            commands.append(value)
        elif isinstance(value, list) and key.lower() in {"args", "argv"} and all(
            isinstance(item, str) for item in value
        ):
            commands.append(" ".join(value))
        elif isinstance(value, list):
            for item in value:
                walk(item, key)
        elif isinstance(value, dict):
            for child_key, item in value.items():
                walk(item, str(child_key))

    if isinstance(data, str):
        commands.append(data)
    else:
        walk(data)
    return commands


def approval_not_expired(value):
    try:
        expires_at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(timezone.utc)


def collect_payload_approvals(raw):
    data = hook_payload_data(raw)
    approvals = []

    def walk(value, key=""):
        if key.lower() == "approval" and isinstance(value, dict):
            approvals.append(value)
        if isinstance(value, list):
            for item in value:
                walk(item, key)
        elif isinstance(value, dict):
            for child_key, item in value.items():
                walk(item, str(child_key))

    walk(data)
    return approvals


def policy_path_matches(path, patterns):
    return any(
        fnmatch.fnmatch(path, pattern)
        or fnmatch.fnmatch(f"./{path}", pattern)
        or path == pattern.rstrip("/")
        or path.startswith(pattern.rstrip("/") + "/")
        for pattern in patterns
    )


def payload_has_approval(raw, path, active_goal):
    for approval in collect_payload_approvals(raw):
        if not active_goal or str(approval.get("goal", "")).strip() != active_goal:
            continue
        if not approval_not_expired(approval.get("expiresAt", "")):
            continue
        if not str(approval.get("reason", "")).strip():
            continue
        approval_paths = approval.get("paths", [])
        if isinstance(approval_paths, str):
            approval_paths = [approval_paths]
        if policy_path_matches(path, [str(item) for item in approval_paths]):
            return True
    return False


def command_literal_policy_paths(command, root, patterns):
    if not patterns:
        return []
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars="|&;<>()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return []
    paths = set()
    for token in tokens:
        path = normalize_policy_path(root, token)
        if path and policy_path_matches(path, patterns):
            paths.add(path)
    return sorted(paths)


def payload_policy_paths(root, raw, policy):
    patterns = [*policy.get("immutablePaths", []), *policy.get("approvalRequiredPaths", [])]
    paths = set(collect_payload_paths(raw, root))
    for command in collect_payload_commands(raw):
        paths.update(command_literal_policy_paths(command, root, patterns))
    return sorted(paths)


def protected_command_matches(command, protected):
    command_lower = command.lower()
    protected_lower = protected.lower().strip()
    if not protected_lower:
        return False
    if re.search(r"\s", protected_lower):
        return protected_lower in command_lower
    return bool(re.search(rf"(^|[\s;&|()]){re.escape(protected_lower)}($|[\s;&|()])", command_lower))


def policy_gate_problems(root, raw, active_goal=""):
    root = Path(root)
    policy, policy_problem = load_project_policy(root)
    if policy_problem:
        return [policy_problem]
    if not policy:
        return []

    env_approved = truthy_env(policy.get("approvalEnv", DEFAULT_APPROVAL_ENV))
    problems = []
    paths = payload_policy_paths(root, raw, policy)
    for path in paths:
        if policy_path_matches(path, policy.get("immutablePaths", [])):
            problems.append(f"immutable path: {path}")
        if (
            policy_path_matches(path, policy.get("approvalRequiredPaths", []))
            and not env_approved
            and not payload_has_approval(raw, path, active_goal)
        ):
            problems.append(f"{path} requires approval via {policy.get('approvalEnv', DEFAULT_APPROVAL_ENV)}")

    for command in collect_payload_commands(raw):
        for protected in policy.get("protectedCommands", []):
            if protected_command_matches(command, protected):
                problems.append(f"protected command: {protected}")
    return problems


def policy_gate_debug(root, raw):
    policy = read_project_policy(root)
    return {"paths": payload_policy_paths(root, raw, policy), "commands": collect_payload_commands(raw)}


def policy_gate(root, hook_mode=False, debug=False, active_goal=""):
    raw = sys.stdin.read()
    if debug:
        print(json.dumps(policy_gate_debug(root, raw), ensure_ascii=False))
    problems = policy_gate_problems(root, raw, active_goal)
    for problem in problems:
        print(f"policy gate blocked: {problem}", file=sys.stderr)
    return 1 if problems else 0
