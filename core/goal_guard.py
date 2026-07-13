#!/usr/bin/env python3
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

try:
    from goal_gate import audit, audit_project, completion_gate, gate_decision, gate_input
    from goal_native_hook import inspect_native_pre_push_hook, native_pre_push_hook_path
    from goal_policy import policy_gate, read_project_policy
    from goal_projection import (
        active_goal_id,
        split_goal_projections,
    )
    from goal_publish import git_output, publish_gate
    from goal_state import (
        INITIALIZATION_TYPES,
        active_goal_contract_problems,
        active_goal_title,
        audit_active_goal_contract,
        fast_lane_available,
        first_pending_goal,
        goal_matrix_summary,
        has_pending_active_goal,
        load_state_json,
        next_action_payload,
        next_goal_id,
        pending_goal_after_active,
        read_active_goal,
        read_active_goal_value,
        read_goal_matrix,
        read_next_loop,
        state_goal_matrix_available,
        status_goal_matrix_summary,
        subagent_candidates,
        visible_status_goals,
        write_state_json,
    )
    from goal_verification import (
        is_metadata_only_verification,
        normalized_verification,
        resolve_guard_verify_command,
        verification_requires_shell,
        verification_is_metadata_status,
        write_checkpoint_evidence,
    )
except ImportError:
    from core.goal_gate import audit, audit_project, completion_gate, gate_decision, gate_input
    from core.goal_native_hook import inspect_native_pre_push_hook, native_pre_push_hook_path
    from core.goal_policy import policy_gate, read_project_policy
    from core.goal_projection import (
        active_goal_id,
        split_goal_projections,
    )
    from core.goal_publish import git_output, publish_gate
    from core.goal_state import (
        INITIALIZATION_TYPES,
        active_goal_contract_problems,
        active_goal_title,
        audit_active_goal_contract,
        fast_lane_available,
        first_pending_goal,
        goal_matrix_summary,
        has_pending_active_goal,
        load_state_json,
        next_action_payload,
        next_goal_id,
        pending_goal_after_active,
        read_active_goal,
        read_active_goal_value,
        read_goal_matrix,
        read_next_loop,
        state_goal_matrix_available,
        status_goal_matrix_summary,
        subagent_candidates,
        visible_status_goals,
        write_state_json,
    )
    from core.goal_verification import (
        is_metadata_only_verification,
        normalized_verification,
        resolve_guard_verify_command,
        verification_requires_shell,
        verification_is_metadata_status,
        write_checkpoint_evidence,
    )


NARROW_TRIGGER_PATTERNS = (
    r"\bgoal[- ]?matrix\b",
    r"\b(active|child)\s+goal\b",
    r"目标矩阵|goal.*(矩阵|迭代)|迭代\s*goal",
    r"\bcheckpoint\b|小步提交",
    r"\b(verification|verify|verifier)\b|验证证据|truth[- ]source|真源",
    r"\b(publish|push|squash|merge)\b|推送|压缩|合并",
    r"loop[- ]engineering|循环工程|自动循环|自我进化|自进化|self[- ]evolution",
    r"continuous iteration|连续迭代|迭代交付|single active slice|active slice",
)

STRICT_TRIGGER_PATTERNS = NARROW_TRIGGER_PATTERNS + (
    r"\bgoal\b",
    "目标",
    "矩阵",
    "迭代",
    "child goal",
    "active goal",
    "工程化",
    "开发流程",
    "高频",
    "习惯",
    "真源",
    "日志",
    "数据库",
    "浏览器",
    "排障",
    "修复",
    "实现",
    "草案",
    "需求",
    "设计",
    "讨论",
    "不清晰",
    "模糊",
    "插件",
    "plugin",
    "loop-engineering",
    "loop engineering",
    "循环工程",
    "自动循环",
    "自我进化",
    "自进化",
    "self-evolution",
    "continuous iteration",
    "连续迭代",
    "小步提交",
    "合并",
    "推送",
    "commit",
    "push",
    "squash",
    "merge",
)

TEMPLATE_FILES = (
    ("project-context.md", "project-context.md"),
    ("checks.md", "checks.md"),
    ("decisions.md", "decisions.md"),
    ("loop-note.md", "loop-note.md"),
    ("notifications.json", "notifications.json"),
    ("goal-matrix.md", "goals/goal-matrix.md"),
    ("active-goal.md", "goals/active-goal.md"),
)
GITIGNORE_LINES = (
    ".goal-matrix/notifications.local.json",
)
LOOP_STAGES = (
    "project_initialization",
    "work_classification",
    "design",
    "design_gate",
    "execute",
    "review_gate",
    "checkpoint",
    "design_iteration",
)

PLUGIN_NAME = "goal-matrix-iterative-delivery"
MARKETPLACE_NAME = "goal-matrix-github"
PLUGIN_ID = f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"

LOOP_CONTEXT = """Loop engineering:
- Cycle: project initialization status -> Repo active goal -> failing check -> minimal change -> verification -> checkpoint commit -> Repo next loop.
- self-evolution run: continue only through pending goals already recorded in state; never synthesize work when no pending goal remains.
- checkpoint commit: make small local commits only after a verified child goal.
- push policy: preserve verified checkpoint commits; publish only from a clean, integrated branch with closed goals and checkpoint evidence.
- final push requires final verification evidence and a clear branch/history state.
"""

PHASE_BOUNDARIES = {
    "clarify": "ask blocking questions before implementation; do not create code or commits yet.",
    "goal_matrix": "split the draft into a goal matrix with truth source and verification for each row.",
    "execute": "one Repo active goal only; inspect -> failing check -> minimal change -> verify.",
    "verify": "run the named truth-source check before claiming progress.",
    "checkpoint": "commit only verified child-goal work and keep the Repo next loop explicit.",
    "history": "keep verified checkpoint history readable and publish only from a clean, integrated branch.",
}

BASE_CONTEXT = """GOAL MATRIX DELIVERY ACTIVE

Execution discipline:
- Read local instructions before editing; expose one Repo active goal; use systematic-debugging for failures and verification-before-completion before claims.

Scope control:
- Reuse existing code, prefer deletion/stdlib, and ship one bounded child goal. Fast Lane applies only to a trivial edit with no Repo active goal and focused verification.

Fusion workflow:
Intake -> Matrix -> Repo active goal -> Development flow -> Execute -> Verify -> Checkpoint
- Intake names scope, risk, and truth source; Development flow is inspect -> failing check -> minimal fix -> verify -> checkpoint.

""" + LOOP_CONTEXT + """

Initialization governance:
- Supported initialization types: new-project, iteration, bugfix, legacy-baseline.
- Project policy source: .goal-matrix/project-policy.json.
- Immutable paths are blocked; Policy impact is none, approval-required, or blocked; every Repo active goal names paths, boundary, truth source, verification, and Development flow.

User operating habits:
- A read-only request permits no writes; start from the named truth source; when scope narrowed, answer that scope first; UI-only evidence is insufficient.

Work routing:
- Product/UI: verify browser plus backing data. Data/API: inspect real responses and rows. Operations: inspect process/config and rollback. Plugin/skill: test hook output directly.

Skill/plugin routing:
- Use brainstorming, writing-plans, test-driven-development, systematic-debugging, verification-before-completion, and finishing-a-development-branch at their named lifecycle boundaries.

Codex visible goal runtime:
- Hooks inject context only; they cannot create the visible Codex goal by themselves.
- If a goal-like prompt needs a visible Codex goal and create_goal is available, call create_goal once before work.

First response contract:
- First substantive response must show a goal matrix or Repo active-goal block before freeform discussion, including for clarify/design or read-only work.

Goal self-correction:
- Repair a missing goal matrix before edits; Repo active goal must include Delivery boundary, Skipped, truth source, Verification, and Development flow; split broad work and keep recoverable blockers open.

Lifecycle CLI:
- goal_guard.py classify; goal_guard.py init; goal_guard.py start; goal_guard.py checkpoint; goal_guard.py status; goal_guard.py gate; goal_guard.py policy-gate; goal_guard.py publish-gate; goal_guard.py audit.
"""

PROMPT_CONTEXT = BASE_CONTEXT + """
Minimum Repo active-goal block:
Repo active goal: G<n> - <name>
Initialization type: <new-project|iteration|bugfix|legacy-baseline>
Policy impact: <none|approval-required|blocked>
Touched paths: <paths or patterns>
Delivery boundary: <what changes now>
Skipped: <what is intentionally not built>
Truth source: <authoritative evidence>
Verification: <smallest real check>
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
"""


def emit(event, context):
    payload = {
        "systemMessage": "GOAL-MATRIX:ACTIVE",
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": context,
        },
    }
    print(json.dumps(payload, ensure_ascii=False))


def prompt_from_stdin():
    raw = sys.stdin.read().lstrip("\ufeff").strip()
    return prompt_text(raw)


def prompt_text(raw):
    if not raw:
        return ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    return str(data.get("prompt", ""))


def read_plugin_governance(root):
    root = Path(root)
    if not (root / ".codex-plugin" / "plugin.json").is_file():
        return {}
    governance_path = root / "loop-governance.json"
    if not governance_path.is_file():
        return {}
    try:
        governance = json.loads(governance_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return governance if isinstance(governance, dict) else {}


def strict_triggering_enabled(root):
    policy = read_project_policy(root)
    trigger_mode = str(policy.get("triggerMode", "")).lower()
    return policy.get("strictMode") is True or trigger_mode == "strict"


def wants_goal_guard(prompt, root=None):
    lowered = prompt.lower()
    patterns = STRICT_TRIGGER_PATTERNS if root is not None and strict_triggering_enabled(root) else NARROW_TRIGGER_PATTERNS
    return any(re.search(pattern, lowered) for pattern in patterns)


def classify_loop_phase(prompt):
    lowered = prompt.lower()
    if re.search(r"不清晰|模糊|讨论|clarify|unclear|草案|draft", lowered):
        return "clarify"
    if re.search(r"推送|push|squash|merge|合并|压缩", lowered):
        return "history"
    if re.search(r"checkpoint|小步提交|提交|commit", lowered):
        return "checkpoint"
    if re.search(r"验证|验收|测试|verify|test|build", lowered):
        return "verify"
    if re.search(r"执行|实现|修复|开始|execute|implement|fix", lowered):
        return "execute"
    if re.search(r"拆分|矩阵|目标|goal|matrix", lowered):
        return "goal_matrix"
    return "clarify"


def phase_context(prompt):
    phase = classify_loop_phase(prompt)
    return f"""
Loop phase: {phase}
- Boundary: {PHASE_BOUNDARIES[phase]}
"""


def write_if_missing(path, text):
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def ensure_gitignore_lines(root):
    path = Path(root) / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    lines = existing.splitlines()
    changed = False
    for line in GITIGNORE_LINES:
        if line not in lines:
            if existing and not existing.endswith("\n"):
                existing += "\n"
            existing += line + "\n"
            changed = True
    if changed:
        path.write_text(existing, encoding="utf-8")
    return changed


def ensure_project_baseline(root, initialization_type):
    root = Path(root)
    matrix_dir = root / ".goal-matrix"
    template_dir = Path(__file__).resolve().parent / "templates"
    created = []
    skipped = []

    matrix_dir.mkdir(parents=True, exist_ok=True)
    (matrix_dir / "specs").mkdir(parents=True, exist_ok=True)
    (matrix_dir / "goals").mkdir(parents=True, exist_ok=True)

    policy_path = matrix_dir / "project-policy.json"
    if policy_path.exists():
        skipped.append(".goal-matrix/project-policy.json")
    else:
        policy = json.loads((template_dir / "project-policy.json").read_text(encoding="utf-8"))
        policy["initializationType"] = initialization_type
        policy_text = json.dumps(policy, ensure_ascii=False, indent=2) + "\n"
        write_if_missing(policy_path, policy_text)
        created.append(".goal-matrix/project-policy.json")

    for template_name, relative_dest in TEMPLATE_FILES:
        dest = matrix_dir / relative_dest
        source = template_dir / template_name
        if write_if_missing(dest, source.read_text(encoding="utf-8")):
            created.append(f".goal-matrix/{relative_dest}")
        else:
            skipped.append(f".goal-matrix/{relative_dest}")

    if ensure_gitignore_lines(root):
        created.append(".gitignore notification ignore")
    else:
        skipped.append(".gitignore notification ignore")

    problems = audit_project(root)
    return created, skipped, problems


def init_project(root, initialization_type):
    created, skipped, problems = ensure_project_baseline(root, initialization_type)
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1

    print(f"initialized .goal-matrix at {root}")
    if created:
        print("created:")
        for path in created:
            print(f"- {path}")
    if skipped:
        print("skipped existing:")
        for path in skipped:
            print(f"- {path}")
    return 0


def status_payload(root):
    root = Path(root)
    problems = audit_project(root)
    active_goal = read_active_goal(root)
    goals = read_goal_matrix(root)
    return {
        "root": str(root),
        "initialized": not problems,
        "auditProblems": problems,
        "activeGoal": active_goal,
        "nextLoop": read_next_loop(root, active_goal),
        "nextAction": next_action_payload(root, goals, active_goal),
        "subagentCandidates": subagent_candidates(goals, active_goal),
        "goalMatrix": status_goal_matrix_summary(root, goals, active_goal),
        "loopStages": list(LOOP_STAGES),
    }


def status_project(root):
    payload = status_payload(root)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["initialized"] else 1


def first_prompt_line(text):
    text = prompt_text(text.lstrip("\ufeff").strip())
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:80]
    return "Start next goal"


def structured_start_contract(text):
    try:
        value = json.loads(text.lstrip("\ufeff").strip())
    except (json.JSONDecodeError, TypeError):
        return None, []
    if not isinstance(value, dict) or "userOutcome" not in value:
        return None, []

    touched_paths = value.get("touchedPaths")
    if isinstance(touched_paths, list) and all(isinstance(path, str) for path in touched_paths):
        touched_paths = ", ".join(path.strip() for path in touched_paths if path.strip())
    verification = value.get("verification")
    if isinstance(verification, str):
        verification = normalized_verification(verification)
    contract = {
        "userOutcome": value.get("userOutcome"),
        "engineeringSlice": value.get("engineeringSlice"),
        "initializationType": value.get("initializationType"),
        "policyImpact": value.get("policyImpact"),
        "touchedPaths": touched_paths,
        "deliveryBoundary": value.get("deliveryBoundary"),
        "skipped": value.get("skipped"),
        "truthSource": value.get("truthSource"),
        "verification": verification,
        "developmentFlow": value.get("developmentFlow"),
        "contractComplete": True,
        "dependencies": value.get("dependencies", "none"),
        "risk": value.get("risk", "medium"),
        "parallelSafety": value.get("parallelSafety", "main thread only"),
        "status": "Pending",
    }
    return contract, active_goal_contract_problems(contract)


def prune_project(root, keep_done):
    root = Path(root)
    if keep_done < 0:
        print("--keep-done must be >= 0", file=sys.stderr)
        return 2
    problems = audit_project(root)
    policy_only_problems = [
        problem
        for problem in problems
        if not problem.startswith("Done goal ")
        and not problem.startswith("invalid state projection: ")
        and not problem.startswith("goal matrix projection drift: ")
        and not problem.startswith("archive projection drift: ")
        and not problem.startswith("active goal projection drift:")
    ]
    if policy_only_problems:
        for problem in policy_only_problems:
            print(problem, file=sys.stderr)
        return 1

    goals = read_goal_matrix(root)
    active_goal = read_active_goal(root)
    visible, archived = split_goal_projections(goals, active_goal, keep_done)
    write_state_json(root, goals=goals, active_goal=active_goal, keep_done=keep_done)
    print(
        json.dumps(
            {
                "visible": len(visible),
                "archived": len(archived),
                "archive": ".goal-matrix/goals/archive.md",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def broad_prompt_items(prompt):
    items = []
    for line in prompt_text(prompt).splitlines():
        line = line.strip()
        if not line or line.endswith(":"):
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^\d+[.)]\s+", "", line)
        match = re.match(r"^(P[0-2])\s*[:：-]?\s*(.+)$", line, re.IGNORECASE)
        if match:
            risk, title = match.groups()
            items.append({"title": title.strip()[:80], "risk": risk.upper()})
    return items if len(items) >= 2 else []


def doctor_runtime_hints(root):
    return {
        "visibleGoalRequiresCreateGoal": True,
        "hookCanCreateCodexGoal": False,
        "checkpointPromotesNextGoal": True,
        "runtimeContinuesWhilePendingGoalsExist": True,
        "completionWhenNoPendingGoal": True,
        "continuationMode": "checkpoint_promotes_existing_pending_goal",
        "minimalFixPath": "load the plugin marketplace/cache for hooks, then call Codex create_goal for visible goals",
    }


def goal_id_after(goal_id, offset):
    match = re.match(r"G(\d+)$", goal_id)
    return f"G{int(match.group(1)) + offset}" if match else f"{goal_id}.{offset}"


def start_project(root, prompt):
    root = Path(root)
    goals = [
        goal
        for goal in read_goal_matrix(root)
        if not (goal.get("id") == "G0" and goal.get("userOutcome") == "Initialize project governance")
    ]
    active_goal = read_active_goal(root)
    if has_pending_active_goal(goals, active_goal):
        print(json.dumps({"activeGoal": active_goal, "root": str(root)}, ensure_ascii=False, indent=2))
        return 0

    problems = audit_project(root)
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    contract, contract_problems = structured_start_contract(prompt)
    if contract_problems:
        for problem in contract_problems:
            print(f"invalid start contract: {problem}", file=sys.stderr)
        return 2

    goals_dir = root / ".goal-matrix" / "goals"
    goals_dir.mkdir(parents=True, exist_ok=True)

    goal_id = next_goal_id(goals)
    if contract:
        goal = {"id": goal_id, **contract}
        active_goal = active_goal_title(goal)
        goals.append(goal)
        write_state_json(root, goals=goals, active_goal=active_goal)
        print(json.dumps({"activeGoal": active_goal, "root": str(root), "structured": True}, ensure_ascii=False, indent=2))
        return 0

    items = broad_prompt_items(prompt)
    if items:
        scheduler_title = "Schedule broad prompt delivery"
        scheduler_slice = "Classify dependency order and review child outputs before checkpoint"
        boundary = "scheduler/acceptance active goal for a broad prompt; classify dependencies, parallel safety, and verify each child goal before checkpoint"
        skipped = "subagent dispatch and child implementation"
        active_goal = f"{goal_id} - {scheduler_title}"
        scheduler_goal = {
            "id": goal_id,
            "userOutcome": scheduler_title,
            "engineeringSlice": scheduler_slice,
            "truthSource": "start command status readback",
            "verification": "`python3 core/goal_guard.py audit --root .`",
            "initializationType": "iteration",
            "policyImpact": "none",
            "touchedPaths": ".goal-matrix/goals/goal-matrix.md, .goal-matrix/goals/active-goal.md",
            "deliveryBoundary": boundary,
            "skipped": skipped,
            "developmentFlow": "inspect -> failing check -> implement -> verify -> checkpoint",
            "contractComplete": True,
            "dependencies": "none",
            "risk": "medium",
            "parallelSafety": "main thread only",
            "status": "Pending",
        }
        goals.append(scheduler_goal)
        planned = []
        for index, item in enumerate(items, start=1):
            child_id = goal_id_after(goal_id, index)
            planned.append(child_id)
            goals.append(
                {
                    "id": child_id,
                    "userOutcome": item["title"],
                    "engineeringSlice": item.get("engineering_slice", f"Subagent candidate: {item['title']}"),
                    "truthSource": item.get("truth_source", "item-specific truth source"),
                    "verification": item.get("verification", "item-specific verification"),
                    "dependencies": goal_id,
                    "risk": item["risk"],
                    "parallelSafety": "independent if touched paths do not overlap",
                    "status": "Pending",
                }
            )
        write_state_json(root, goals=goals, active_goal=active_goal)
        print(json.dumps({"activeGoal": active_goal, "root": str(root), "plannedChildGoals": planned}, ensure_ascii=False, indent=2))
        return 0

    title = first_prompt_line(prompt)
    active_goal = f"{goal_id} - {title}"

    goal = {
        "id": goal_id,
        "userOutcome": title,
        "engineeringSlice": "Start one bounded child goal",
        "truthSource": "`.goal-matrix` status",
        "verification": "`python3 core/goal_guard.py status --root .`",
        "initializationType": "iteration",
        "policyImpact": "none",
        "touchedPaths": "TBD",
        "deliveryBoundary": "one bounded child goal from the current prompt",
        "skipped": "unrelated work",
        "developmentFlow": "inspect -> failing check -> implement -> verify -> checkpoint",
        "contractComplete": False,
        "status": "Pending",
    }
    goals.append(goal)
    write_state_json(root, goals=goals, active_goal=active_goal)
    print(json.dumps({"activeGoal": active_goal, "root": str(root)}, ensure_ascii=False, indent=2))
    return 0


def checkpoint_project(root, verify_command, if_active=False):
    root = Path(root)
    if not verify_command:
        print("missing verification command after --", file=sys.stderr)
        return 2
    if is_metadata_only_verification(verify_command):
        print("metadata-only verification command is not allowed for checkpoint", file=sys.stderr)
        return 2
    active_goal = read_active_goal(root)
    if not active_goal or (if_active and not has_pending_active_goal(read_goal_matrix(root), active_goal)):
        if if_active:
            return 0
        print("missing active goal", file=sys.stderr)
        return 1
    contract_problems = audit_active_goal_contract(root)
    if contract_problems:
        for problem in contract_problems:
            print(f"checkpoint blocked: {problem}", file=sys.stderr)
        return 1

    result = subprocess.run(verify_command, cwd=root, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="", file=sys.stderr)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode:
        return result.returncode

    goal_id = active_goal_id(active_goal)
    goals = [dict(goal) for goal in read_goal_matrix(root)]
    completed = next((goal for goal in goals if goal.get("id") == goal_id), None)
    if not completed:
        print(f"active goal {goal_id} is missing from state.json", file=sys.stderr)
        return 1
    evidence_path = write_checkpoint_evidence(root, goal_id, active_goal, verify_command, result)
    completed["verification"] = f"`{shlex.join(map(str, verify_command))}`"
    completed["status"] = "Done"
    next_goal = first_pending_goal(goals)
    next_active_goal = None
    if next_goal:
        next_active_goal = active_goal_title(next_goal)
    write_state_json(root, goals=goals, active_goal=next_active_goal)
    print(
        json.dumps(
            {
                "completedGoal": active_goal,
                "nextActiveGoal": next_active_goal,
                "verification": verify_command,
                "evidence": str(evidence_path.relative_to(root)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def active_verify(root):
    root = Path(root)
    if not read_active_goal(root):
        if fast_lane_available(root):
            dirty = git_output(root, "status", "--porcelain")
            if dirty.returncode == 0 and dirty.stdout.strip():
                print("active verification blocked: Fast Lane requires focused verification evidence", file=sys.stderr)
                return 1
            return 0
        print("active verification blocked: no active goal", file=sys.stderr)
        return 1
    if state_goal_matrix_available(root):
        active_id = active_goal_id(read_active_goal(root))
        goal = next((item for item in read_goal_matrix(root) if item.get("id") == active_id), None)
        verification = normalized_verification(goal.get("verification", "")) if goal else ""
    else:
        verification = read_active_goal_value(root, "Verification")
    if not verification:
        print("active verification blocked: missing Verification field", file=sys.stderr)
        return 1
    try:
        verify_command = shlex.split(verification)
    except ValueError as exc:
        print(f"active verification blocked: cannot parse Verification field: {exc}", file=sys.stderr)
        return 1
    if verification_is_metadata_status(verification):
        print("active verification blocked: metadata-only verification is not allowed", file=sys.stderr)
        return 1
    if verification_requires_shell(verification):
        return subprocess.run(verification, cwd=root, text=True, shell=True).returncode
    verify_command = resolve_guard_verify_command(root, verify_command)
    return subprocess.run(verify_command, cwd=root, text=True).returncode


def toml_block(text, header):
    match = re.search(rf"^\[{re.escape(header)}\]\s*$(.*?)(?=^\[|\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def toml_block_enabled(text, header):
    return bool(re.search(r"^\s*enabled\s*=\s*true\s*$", toml_block(text, header), re.MULTILINE))


def doctor_project(root, fix=False):
    root = Path(root)
    fix_result = {"applied": False, "created": [], "skipped": [], "problems": []}
    if fix:
        created, skipped, problems = ensure_project_baseline(root, "iteration")
        fix_result = {
            "applied": bool(created),
            "created": created,
            "skipped": skipped,
            "problems": problems,
        }

    plugin_root = Path(__file__).resolve().parents[1]
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    version = manifest.get("version", "0.1.0")
    adapter_skill = plugin_root / "adapters" / "codex" / "skills" / "goal-matrix-iterative-delivery" / "SKILL.md"
    verifier_skill = plugin_root / "adapters" / "codex" / "skills" / "loop-verifier" / "SKILL.md"
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    codex_config = codex_home / "config.toml"
    codex_config_text = codex_config.read_text(encoding="utf-8") if codex_config.is_file() else ""
    cache_path = codex_home / "plugins" / "cache" / MARKETPLACE_NAME / PLUGIN_NAME / str(version)
    hook_state_keys = re.findall(r'^\[hooks\.state\."([^"]+)"\]', codex_config_text, re.MULTILINE)
    installed_skill = codex_home / "skills" / "goal-matrix-iterative-delivery" / "SKILL.md"
    installed_verifier_skill = codex_home / "skills" / "loop-verifier" / "SKILL.md"
    installed_exists = installed_skill.is_file()
    installed_verifier_exists = installed_verifier_skill.is_file()
    source = {
        "pluginRoot": str(plugin_root),
        "manifestPath": str(manifest_path),
        "adapterSkillPath": str(adapter_skill),
        "codexConfigPath": str(codex_config),
        "codexMarketplaceConfigured": f"[marketplaces.{MARKETPLACE_NAME}]" in codex_config_text,
        "codexPluginEnabled": toml_block_enabled(codex_config_text, f'plugins."{PLUGIN_ID}"'),
        "codexCachePath": str(cache_path),
        "codexCacheHasManifest": (cache_path / ".codex-plugin" / "plugin.json").is_file(),
        "codexHookTrusted": any(PLUGIN_ID in key for key in hook_state_keys),
        "installedSkillPath": str(installed_skill),
        "installedSkillExists": installed_exists,
        "installedSkillMatchesAdapter": (
            installed_exists
            and installed_skill.read_text(encoding="utf-8") == adapter_skill.read_text(encoding="utf-8")
        ),
        "installedVerifierSkillPath": str(installed_verifier_skill),
        "installedVerifierSkillExists": installed_verifier_exists,
        "installedVerifierSkillMatchesAdapter": (
            installed_verifier_exists
            and installed_verifier_skill.read_text(encoding="utf-8") == verifier_skill.read_text(encoding="utf-8")
        ),
    }
    runtime = doctor_runtime_hints(root)
    pre_push = native_pre_push_hook_path(root)
    hook_state = inspect_native_pre_push_hook(pre_push, plugin_root / "core" / "goal_guard.py")
    native_hooks = {
        "prePushHookPath": str(pre_push),
        "prePushHookInstalled": hook_state["current"],
        "prePushHookExists": hook_state["exists"],
        "prePushHookManaged": hook_state["managed"],
        "prePushHookState": hook_state["state"],
        "prePushHookExecutable": hook_state["executable"],
        "prePushHookGuardPath": hook_state["guardPath"],
        "expectedGuardPath": hook_state["expectedGuardPath"],
        "refreshRequired": hook_state["refreshRequired"],
        "installCommand": f"python3 scripts/install_adapter.py codex --target {shlex.quote(str(root))} --install-git-hook",
    }
    print(
        json.dumps(
            {
                "resume": status_payload(root),
                "source": source,
                "runtime": runtime,
                "nativeHooks": native_hooks,
                "fix": fix_result,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def runtime_publish_patterns(root):
    patterns = []
    for source in (read_project_policy(root), read_plugin_governance(root)):
        for pattern in source.get("publishActionPatterns", []):
            if pattern and pattern not in patterns:
                patterns.append(pattern)
    return patterns


def classify_work(prompt):
    lowered = prompt.lower()
    if re.search(r"bug|失败|报错|修复|fix|broken|failure|failed", lowered):
        init_type = "bugfix"
        first_gate = "review_gate"
    elif re.search(r"新项目|从零|立项|new project|greenfield|create project", lowered):
        init_type = "new-project"
        first_gate = "design_gate"
    elif re.search(r"遗留|接手|legacy|unknown|baseline|不清楚", lowered):
        init_type = "legacy-baseline"
        first_gate = "design_gate"
    else:
        init_type = "iteration"
        first_gate = "design_gate"
    payload = {
        "initializationType": init_type,
        "firstStage": "project_initialization",
        "firstGate": first_gate,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def project_status_context(root):
    root = Path(root)
    policy_path = root / ".goal-matrix" / "project-policy.json"
    active_goal = read_active_goal(root)
    next_loop = read_next_loop(root, active_goal)
    goals = read_goal_matrix(root)
    matrix = goal_matrix_summary(goals, active_goal)
    display_goals = visible_status_goals(root, goals, active_goal)
    child_goal_status = ", ".join(f"{goal['id']}={goal['status']}" for goal in display_goals[:8])
    if len(display_goals) > 8:
        child_goal_status += f", +{len(display_goals) - 8} visible more"
    archive_status = f"; {len(display_goals)} visible, {len(goals) - len(display_goals)} archived" if display_goals is not goals else ""
    matrix_status = (
        f"{matrix['total']} child goals; {matrix['done']} done; {matrix['pending']} pending"
        + archive_status
        + (f": {child_goal_status}" if child_goal_status else "")
    )

    if not policy_path.is_file():
        status = (
            "missing .goal-matrix/project-policy.json; first loop action: "
            "choose initialization type and create required docs from core/templates/."
        )
    else:
        problems = audit_project(root)
        status = (
            "initialized: .goal-matrix policy and required docs present."
            if not problems
            else "initialized with audit problems: " + "; ".join(problems[:5])
        )

    return f"""
Project initialization status:
- cwd: {root}
- {status}
- Repo active goal: {active_goal or "none"}
- Repo next loop: {next_loop or "none"}
- Goal matrix: {matrix_status}
"""


def hook(event):
    if event == "SessionStart":
        emit(event, BASE_CONTEXT + project_status_context(Path.cwd()))
        return 0

    if event == "UserPromptSubmit":
        prompt = prompt_from_stdin()
        if wants_goal_guard(prompt, Path.cwd()):
            emit(event, PROMPT_CONTEXT + phase_context(prompt) + project_status_context(Path.cwd()))
        return 0

    if event == "Stop":
        print("{}")
        return 0

    return 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    hook_parser = sub.add_parser("hook")
    hook_parser.add_argument("event")
    audit_parser = sub.add_parser("audit")
    audit_parser.add_argument("--root")
    init_parser = sub.add_parser("init")
    init_parser.add_argument("--root", default=".")
    start_parser = sub.add_parser("start")
    start_parser.add_argument("--root", default=".")
    checkpoint_parser = sub.add_parser("checkpoint")
    checkpoint_parser.add_argument("--root", default=".")
    checkpoint_parser.add_argument("--if-active", action="store_true")
    checkpoint_parser.add_argument("verify_command", nargs=argparse.REMAINDER)
    init_parser.add_argument("--type", choices=INITIALIZATION_TYPES, default="new-project")
    status_parser = sub.add_parser("status")
    status_parser.add_argument("--root", default=".")
    prune_parser = sub.add_parser("prune")
    prune_parser.add_argument("--root", default=".")
    prune_parser.add_argument("--keep-done", type=int, default=10)
    active_verify_parser = sub.add_parser("active-verify")
    active_verify_parser.add_argument("--root", default=".")
    doctor_parser = sub.add_parser("doctor")
    doctor_parser.add_argument("--root", default=".")
    doctor_parser.add_argument("--fix", action="store_true")
    publish_gate_parser = sub.add_parser("publish-gate")
    publish_gate_parser.add_argument("--root", default=".")
    publish_gate_parser.add_argument("--hook", action="store_true")
    completion_gate_parser = sub.add_parser("completion-gate")
    completion_gate_parser.add_argument("--root", default=".")
    policy_gate_parser = sub.add_parser("policy-gate")
    policy_gate_parser.add_argument("--root", default=".")
    policy_gate_parser.add_argument("--hook", action="store_true")
    policy_gate_parser.add_argument("--debug", action="store_true")
    gate_parser = sub.add_parser("gate")
    gate_parser.add_argument("--phase", choices=("design_gate", "review_gate"), required=True)
    gate_parser.add_argument("--root", default=".")
    gate_parser.add_argument("--file")
    gate_parser.add_argument("--verify", nargs=argparse.REMAINDER)
    sub.add_parser("classify")
    args = parser.parse_args()

    if args.cmd == "hook":
        return hook(args.event)
    if args.cmd == "init":
        return init_project(args.root, args.type)
    if args.cmd == "start":
        return start_project(args.root, sys.stdin.read())
    if args.cmd == "checkpoint":
        verify_command = args.verify_command[1:] if args.verify_command[:1] == ["--"] else args.verify_command
        return checkpoint_project(args.root, verify_command, args.if_active)
    if args.cmd == "status":
        return status_project(args.root)
    if args.cmd == "prune":
        return prune_project(args.root, args.keep_done)
    if args.cmd == "active-verify":
        return active_verify(args.root)
    if args.cmd == "doctor":
        return doctor_project(args.root, args.fix)
    if args.cmd == "publish-gate":
        return publish_gate(
            args.root,
            hook_mode=args.hook,
            goals=read_goal_matrix(args.root),
            active_goal=read_active_goal(args.root),
            publish_patterns=runtime_publish_patterns(args.root),
        )
    if args.cmd == "completion-gate":
        return completion_gate(args.root)
    if args.cmd == "policy-gate":
        return policy_gate(
            args.root,
            args.hook,
            args.debug,
            active_goal_id(read_active_goal(args.root)),
        )
    if args.cmd == "gate":
        verify_command = args.verify[1:] if args.verify and args.verify[:1] == ["--"] else args.verify
        return gate_decision(args.phase, gate_input(args.root, args.file), verify_command, args.root)
    if args.cmd == "classify":
        return classify_work(sys.stdin.read())

    text = sys.stdin.read()
    problems = []
    if args.root:
        problems.extend(audit_project(args.root))
    # Text audit is heuristic; replace it with assistant-output hooks
    # if Codex exposes a stable completion event.
    if text.strip() or not args.root:
        problems.extend(audit(text))
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
