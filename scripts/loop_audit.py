#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


REQUIRED = {
    "stateFile": ("STATE.md", ("Last run:", "High Priority", "Watch List")),
    "loopConfig": ("LOOP.md", ("Active Loops", "Human Gates", "Budget")),
    "budgetDoc": ("loop-budget.md", ("Max tokens", "Kill Switch")),
    "runLog": ("loop-run-log.md", ("Recent Runs", "outcome")),
}

LEVELS = {
    "L1": "report-only",
    "L2": "assisted-with-verifier",
    "L3": "remote-ci-activity",
}

RUN_LOG_LINE_LIMIT = 500
STATUS_OUTPUT_CHAR_LIMIT = 40000
HOOK_OUTPUT_CHAR_LIMIT = 12000
DEFAULT_APPROVAL_ENV = "GOAL_MATRIX_APPROVED"
GOVERNANCE_STATE_HINTS = ("governance", "approval", "publish", "policy", "gate", "protected", "blocked")
MACHINE_ENV_RE = re.compile(r"\b[A-Z][A-Z0-9_]*(?:APPROVED|APPROVAL|GOVERNANCE|PUBLISH)[A-Z0-9_]*\b")
VERSION_RE = re.compile(r"\b\d+\.\d+\.\d+(?:[+.-][A-Za-z0-9.-]+)?\b")


def has_phrases(root, rel, phrases):
    path = root / rel
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return all(phrase in text for phrase in phrases)


def has_github_remote(root):
    result = subprocess.run(
        ["git", "-C", str(root), "config", "--get-regexp", r"^remote\..*\.url$"],
        text=True,
        capture_output=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def unresolved_gaps(root):
    path = root / "LOOP.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    gaps = []
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        name = cells[0]
        next_action = cells[3]
        if name in {"Gap", "---"}:
            continue
        if next_action.lower().startswith("resolved:"):
            continue
        if name in {"remote-ci", "maker-checker", "run-evidence", "distribution", "connectors", "governance"}:
            gaps.append(name)
    return gaps


def has_remote_run_evidence(root):
    path = root / "loop-run-log.md"
    if not path.is_file():
        return False
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        is_remote_ci = (
            record.get("pattern") == "github-check-run"
            or record.get("outcome") == "remote-ci-readback"
        )
        is_success = record.get("run_status") == "completed" and record.get("run_conclusion") == "success"
        has_readback = bool(record.get("run_url")) and bool(record.get("head_sha"))
        if is_remote_ci and is_success and has_readback:
            return True
    return False


def has_repeated_run_evidence(root):
    path = root / "loop-run-log.md"
    if not path.is_file():
        return False
    count = 0
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and record.get("run_id") and record.get("outcome"):
            count += 1
    return count >= 2


def run_log_line_count(root):
    path = root / "loop-run-log.md"
    if not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def command_output_chars(root, args, input_text=""):
    guard = root / "core" / "goal_guard.py"
    if not guard.is_file():
        return 0
    try:
        result = subprocess.run(
            [sys.executable, str(guard), *args],
            input=input_text,
            text=True,
            capture_output=True,
            cwd=root,
            timeout=5,
        )
    except Exception:
        return 0
    return len(result.stdout) if result.returncode == 0 else 0


def friction_budget(root):
    status_chars = command_output_chars(root, ["status", "--root", "."])
    hook_prompt = json.dumps({"prompt": "goal matrix friction budget"})
    hook_chars = max(
        command_output_chars(root, ["hook", "SessionStart"]),
        command_output_chars(root, ["hook", "UserPromptSubmit"], hook_prompt),
    )
    return {
        "statusOutputChars": status_chars,
        "statusOutputCharLimit": STATUS_OUTPUT_CHAR_LIMIT,
        "hookOutputChars": hook_chars,
        "hookOutputCharLimit": HOOK_OUTPUT_CHAR_LIMIT,
    }


def load_governance_policy(root):
    path = root / "loop-governance.json"
    if not path.is_file():
        return {}
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return policy if isinstance(policy, dict) else {}


def load_json_version(root, rel):
    path = root / rel
    if not path.is_file():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    return str(data.get("version", "")) if isinstance(data, dict) else ""


def state_version_mentions(root):
    path = root / "STATE.md"
    if not path.is_file():
        return []
    versions = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        lowered = line.lower()
        if not any(token in lowered for token in ("plugin", "cache", "version")):
            continue
        versions.update(VERSION_RE.findall(line))
    return sorted(versions)


def policy_string_values(value):
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(policy_string_values(item))
        return values
    if isinstance(value, dict):
        values = []
        for item in value.values():
            values.extend(policy_string_values(item))
        return values
    return []


def state_governance_machine_values(root, policy):
    path = root / "STATE.md"
    if not path.is_file():
        return []
    policy_values = sorted(set(policy_string_values(policy)), key=len, reverse=True)
    machine_values = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        lowered = line.lower()
        if not any(hint in lowered for hint in GOVERNANCE_STATE_HINTS):
            continue
        for value in policy_values:
            if value in line:
                machine_values.add(value)
        machine_values.update(MACHINE_ENV_RE.findall(line))
    return sorted(machine_values)


def audit(root):
    root = Path(root).resolve()
    signals = {name: has_phrases(root, rel, phrases) for name, (rel, phrases) in REQUIRED.items()}
    signals["triage"] = "package-triage" in (root / "LOOP.md").read_text(encoding="utf-8", errors="ignore") if (root / "LOOP.md").is_file() else False
    signals["completionMatrix"] = has_phrases(
        root,
        "LOOP.md",
        ("Loop Engineering Completion Matrix", "Readiness Levels", "remote-ci-activity"),
    )
    signals["verifier"] = has_phrases(
        root,
        "adapters/codex/skills/loop-verifier/SKILL.md",
        ("independent verifier", "truth source", "reject completion"),
    ) or (root / ".codex" / "agents" / "verifier.toml").is_file()
    gaps = unresolved_gaps(root)
    signals["gapRegister"] = bool(gaps)
    signals["githubRemote"] = has_github_remote(root)
    signals["githubWorkflows"] = (root / ".github" / "workflows").is_dir()
    signals["remoteRunEvidence"] = has_remote_run_evidence(root)
    signals["repeatedRunEvidence"] = has_repeated_run_evidence(root)
    run_log_lines = run_log_line_count(root)
    signals["runLogNeedsSummary"] = run_log_lines > RUN_LOG_LINE_LIMIT
    friction = friction_budget(root)
    signals["frictionBudgetExceeded"] = (
        friction["statusOutputChars"] > friction["statusOutputCharLimit"]
        or friction["hookOutputChars"] > friction["hookOutputCharLimit"]
    )
    governance_policy = load_governance_policy(root)
    policy_approval_env = governance_policy.get("approvalEnv", DEFAULT_APPROVAL_ENV) if governance_policy else ""
    state_machine_values = state_governance_machine_values(root, governance_policy)
    state_approval_env = next((value for value in state_machine_values if "APPROV" in value), None)
    repo_versions = {
        "package": load_json_version(root, "package.json"),
        "plugin": load_json_version(root, ".codex-plugin/plugin.json"),
    }
    repo_version_values = {value for value in repo_versions.values() if value}
    state_versions = state_version_mentions(root)
    stale_state_versions = sorted(version for version in state_versions if version not in repo_version_values)
    signals["stateGovernanceDuplication"] = bool(state_machine_values)
    signals["stateGovernanceDrift"] = signals["stateGovernanceDuplication"]
    signals["stateVersionDrift"] = bool(stale_state_versions) or (
        bool(repo_versions["package"] and repo_versions["plugin"]) and repo_versions["package"] != repo_versions["plugin"]
    )

    score = 10
    score += 18 if signals["stateFile"] else 0
    score += 9 if signals["loopConfig"] else 0
    score += 3 if signals["budgetDoc"] else 0
    score += 3 if signals["runLog"] else 0
    score += 5 if signals["triage"] else 0
    score += 8 if signals["completionMatrix"] else 0
    score += 14 if signals["verifier"] else 0
    score += 6 if signals["githubRemote"] else 0
    score += 6 if signals["githubWorkflows"] else 0

    if (
        score >= 78
        and signals["verifier"]
        and signals["githubRemote"]
        and signals["githubWorkflows"]
        and signals["remoteRunEvidence"]
    ):
        level = "L3"
    elif score >= 58 and signals["verifier"]:
        level = "L2"
    elif score >= 38 and signals["stateFile"]:
        level = "L1"
    else:
        level = "L0"

    recommendations = []
    blocked = []
    if not signals["verifier"]:
        recommendations.append("Add a separate verifier before L2.")
    if not signals["completionMatrix"]:
        recommendations.append("Document the completion matrix before claiming loop-engineering parity.")
    if not signals["githubRemote"]:
        blocked.append("GitHub remote is missing; G25/G26 cannot be completed.")
    if not signals["githubWorkflows"]:
        recommendations.append("Add CI/audit workflow after GitHub remote exists.")
        blocked.append("GitHub workflow evidence is missing; L3 cannot be claimed.")
    if signals["githubRemote"] and signals["githubWorkflows"] and not signals["remoteRunEvidence"]:
        blocked.append("Remote workflow run evidence is missing; L3 cannot be claimed.")
    if not all(signals[name] for name in REQUIRED):
        recommendations.append("Restore missing L1 spine files.")
    if signals["runLogNeedsSummary"]:
        blocked.append(
            f"loop-run-log.md exceeds {RUN_LOG_LINE_LIMIT} lines; run a summary/pruning goal before continuing."
        )
        recommendations.append("Summarize or prune loop-run-log.md before the next long loop.")
    if signals["stateGovernanceDuplication"]:
        blocked.append("STATE.md repeats machine governance values from loop-governance.json.")
        recommendations.append("Keep machine-owned governance values only in loop-governance.json; keep STATE.md human-only.")
    if signals["stateVersionDrift"]:
        blocked.append("STATE.md mentions stale plugin version or package/plugin versions diverge.")
        recommendations.append("Update STATE.md plugin cache/version readback after package or plugin version changes.")
    if signals["frictionBudgetExceeded"]:
        blocked.append("Loop friction budget exceeded; slim status or hook output before adding more loop surface.")
        recommendations.append("Prefer compact status or quieter hooks before adding new lifecycle machinery.")

    assessment = {
        "L0": "Loop spine incomplete.",
        "L1": "L1 report-only spine present.",
        "L2": "L2 assisted loop present; remote CI is still blocked.",
        "L3": "L3 remote CI loop evidence present.",
    }[level]

    if not gaps:
        next_action = "No unresolved loop-engineering gaps."
    elif not signals["githubRemote"]:
        next_action = "Add GitHub remote, push, and read back the workflow result."
    elif not signals["remoteRunEvidence"]:
        next_action = "Append remote-ci-readback evidence after the workflow passes."
    else:
        next_action = "Review L3 evidence and continue unresolved gap register."

    return {
        "target": str(root),
        "score": min(score, 100),
        "level": level,
        "levels": LEVELS,
        "runLogLineCount": run_log_lines,
        "runLogLineLimit": RUN_LOG_LINE_LIMIT,
        "stateGovernanceApprovalEnv": state_approval_env,
        "stateGovernanceMachineValues": state_machine_values,
        "stateVersionMentions": state_versions,
        "repoVersions": repo_versions,
        "governanceApprovalEnv": policy_approval_env,
        "frictionBudget": friction,
        "assessment": assessment,
        "signals": signals,
        "unresolvedGaps": gaps,
        "nextAction": next_action,
        "blocked": blocked,
        "recommendations": recommendations,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = audit(args.root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Loop readiness: {result['level']} ({result['score']}/100)")
        for item in result["recommendations"]:
            print(f"- {item}")
    return 0 if result["score"] >= 38 else 2


if __name__ == "__main__":
    raise SystemExit(main())
