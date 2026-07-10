import json
import re
from pathlib import Path

try:
    from goal_projection import (
        active_goal_id,
        active_goal_projection,
        projection_keep_done,
        read_goal_matrix_markdown,
        render_goal_matrix,
        split_goal_projections,
        write_goal_projections,
    )
    from goal_verification import (
        active_goal_iteration_commands,
        normalized_verification,
        verification_is_metadata_status,
    )
except ImportError:
    from core.goal_projection import (
        active_goal_id,
        active_goal_projection,
        projection_keep_done,
        read_goal_matrix_markdown,
        render_goal_matrix,
        split_goal_projections,
        write_goal_projections,
    )
    from core.goal_verification import (
        active_goal_iteration_commands,
        normalized_verification,
        verification_is_metadata_status,
    )


INITIALIZATION_TYPES = ("new-project", "iteration", "bugfix", "legacy-baseline")
UNSET = object()


def load_state_json(root):
    path = Path(root) / ".goal-matrix" / "state.json"
    if not path.is_file():
        return {}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return state if isinstance(state, dict) else {}


def read_active_goal_markdown(root):
    path = Path(root) / ".goal-matrix" / "goals" / "active-goal.md"
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"Active goal:\s*(.+)", line)
        if match:
            value = match.group(1).strip()
            return None if value.lower() == "none" else value
    return None


def read_active_goal(root):
    state = load_state_json(root)
    if "activeGoal" in state:
        value = state.get("activeGoal")
        return value if value else None
    return read_active_goal_markdown(root)


def read_active_goal_value(root, field):
    path = Path(root) / ".goal-matrix" / "goals" / "active-goal.md"
    if not path.is_file():
        return ""
    pattern = re.compile(rf"^{re.escape(field)}:\s*(.+)$", re.IGNORECASE)
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip("`")
    return ""


def fast_lane_available(root):
    active_path = Path(root) / ".goal-matrix" / "goals" / "active-goal.md"
    return active_path.is_file() and read_active_goal(root) is None


def read_goal_matrix(root):
    state = load_state_json(root)
    matrix = state.get("goalMatrix")
    if isinstance(matrix, dict) and isinstance(matrix.get("childGoals"), list):
        return [goal for goal in matrix["childGoals"] if isinstance(goal, dict)]
    return read_goal_matrix_markdown(root)


def state_goal_matrix_available(root):
    matrix = load_state_json(root).get("goalMatrix")
    return isinstance(matrix, dict) and isinstance(matrix.get("childGoals"), list)


def audit_active_goal_projection_drift(root):
    if not state_goal_matrix_available(root):
        return []
    state = load_state_json(root)
    active_id = active_goal_id(state.get("activeGoal"))
    goal = next((item for item in read_goal_matrix(root) if item.get("id") == active_id), None) if active_id else None
    if active_id and not goal:
        return [f"active goal projection drift: {active_id} is missing from state.json"]
    path = Path(root) / ".goal-matrix" / "goals" / "active-goal.md"
    if path.is_file() and path.read_text(encoding="utf-8") != active_goal_projection(goal):
        return ["active goal projection drift: active-goal.md differs from state.json"]
    return []


def active_goal_contract_problems(goal):
    required = (
        "userOutcome",
        "engineeringSlice",
        "initializationType",
        "policyImpact",
        "touchedPaths",
        "deliveryBoundary",
        "skipped",
        "truthSource",
        "verification",
        "developmentFlow",
    )
    problems = []
    for field in required:
        value = goal.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"missing {field}")
    if goal.get("initializationType") not in INITIALIZATION_TYPES:
        problems.append("invalid initializationType")
    if goal.get("policyImpact") not in ("none", "approval-required", "blocked"):
        problems.append("invalid policyImpact")
    if str(goal.get("touchedPaths", "")).strip().lower() == "tbd":
        problems.append("touchedPaths cannot be TBD")
    if goal.get("engineeringSlice") == "Start one bounded child goal":
        problems.append("engineeringSlice cannot be the default placeholder")
    verification = goal.get("verification")
    if isinstance(verification, str) and verification_is_metadata_status(verification):
        problems.append("verification cannot be metadata-only status")
    return problems


def audit_active_goal_contract(root):
    if not state_goal_matrix_available(root):
        return []
    active_id = active_goal_id(read_active_goal(root))
    if not active_id:
        return []
    goal = next((item for item in read_goal_matrix(root) if item.get("id") == active_id), None)
    if not goal or "contractComplete" not in goal:
        return []
    if goal.get("contractComplete") is not True:
        return ["active goal contract is incomplete: use structured start input"]
    return [f"active goal contract is invalid: {problem}" for problem in active_goal_contract_problems(goal)]


def audit_visible_done_goal_verification(root):
    problems = []
    for goal in read_goal_matrix_markdown(root):
        if goal.get("status", "").lower() != "done":
            continue
        if verification_is_metadata_status(goal.get("verification", "")):
            problems.append(f"Done goal {goal.get('id', '<unknown>')} verification cannot be metadata-only status")
    return problems


def audit_goal_matrix_projection_drift(root):
    if not state_goal_matrix_available(root):
        return []
    state = load_state_json(root)
    goals = read_goal_matrix(root)
    active_goal = state.get("activeGoal")
    visible, archived = split_goal_projections(goals, active_goal, projection_keep_done(state))
    goals_dir = Path(root) / ".goal-matrix" / "goals"
    problems = []
    expected = (
        ("goal-matrix.md", render_goal_matrix(visible), "goal matrix projection drift"),
        ("archive.md", render_goal_matrix(archived, "Goal Matrix Archive"), "archive projection drift"),
    )
    for filename, projection, label in expected:
        path = goals_dir / filename
        if not path.is_file() or path.read_text(encoding="utf-8") != projection:
            problems.append(f"{label}: {filename} differs from state.json")
    return problems


def next_loop_from_goals(goals, active_goal):
    active_id = active_goal_id(active_goal)
    for goal in goals:
        if goal["status"].lower() != "pending":
            continue
        if active_id and goal["id"] == active_id:
            continue
        return f"{goal['id']} - {goal['userOutcome']}"
    return None


def read_next_loop(root, active_goal):
    return next_loop_from_goals(read_goal_matrix(root), active_goal)


def next_goal_id(goals):
    numbers = []
    for goal in goals:
        match = re.match(r"G(\d+)$", goal["id"])
        if match:
            numbers.append(int(match.group(1)))
    return f"G{max(numbers, default=0) + 1}"


def goal_matrix_summary(goals, active_goal):
    active_id = active_goal_id(active_goal)
    return {
        "total": len(goals),
        "done": sum(1 for goal in goals if goal["status"].lower() == "done"),
        "pending": sum(1 for goal in goals if goal["status"].lower() == "pending"),
        "activeId": active_id,
        "childGoals": goals,
    }


def visible_status_goals(root, goals, active_goal):
    if not state_goal_matrix_available(root):
        return goals
    visible, _ = split_goal_projections(goals, active_goal, projection_keep_done(load_state_json(root)))
    return visible


def status_goal_matrix_summary(root, goals, active_goal):
    summary = goal_matrix_summary(goals, active_goal)
    visible = visible_status_goals(root, goals, active_goal)
    if len(visible) < len(goals):
        summary["childGoals"] = visible
        summary["visible"] = len(visible)
        summary["archived"] = len(goals) - len(visible)
    return summary


def has_pending_active_goal(goals, active_goal):
    active_id = active_goal_id(active_goal)
    return any(goal["id"] == active_id and goal["status"].lower() == "pending" for goal in goals)


def active_goal_title(goal):
    return f"{goal['id']} - {goal['userOutcome']}"


def first_pending_goal(goals):
    for goal in goals:
        if goal["status"].lower() == "pending":
            return goal
    return None


def pending_goal_after_active(goals, active_goal):
    active_id = active_goal_id(active_goal)
    for goal in goals:
        if goal["status"].lower() != "pending":
            continue
        if active_id and goal["id"] == active_id:
            continue
        return goal
    return None


def subagent_candidates(goals, active_goal):
    active_id = active_goal_id(active_goal)
    promoted_goal = None if has_pending_active_goal(goals, active_goal) else pending_goal_after_active(goals, active_goal)
    promoted_id = promoted_goal["id"] if promoted_goal else None
    candidates = []
    for goal in goals:
        if goal["status"].lower() != "pending":
            continue
        if goal["id"] == active_id or goal["id"] == promoted_id:
            continue
        if not goal.get("parallelSafety", "").startswith("independent"):
            continue
        candidates.append(
            {
                "goal": active_goal_title(goal),
                "dependencies": goal.get("dependencies", "none"),
                "risk": goal.get("risk", "medium"),
                "parallelSafety": goal.get("parallelSafety", ""),
            }
        )
    return candidates


def next_action_payload(root, goals, active_goal):
    active_id = active_goal_id(active_goal)
    active = next((goal for goal in goals if goal["id"] == active_id), None)
    if active and active["status"].lower() == "pending":
        if state_goal_matrix_available(root):
            verification = normalized_verification(active.get("verification", ""))
            boundary = active.get("deliveryBoundary", active.get("engineeringSlice", ""))
            truth_source = active.get("truthSource", "")
        else:
            verification = normalized_verification(
                read_active_goal_value(root, "Verification") or active.get("verification", "")
            )
            boundary = read_active_goal_value(root, "Delivery boundary") or active.get("engineeringSlice", "")
            truth_source = read_active_goal_value(root, "Truth source") or active.get("truthSource", "")
        title = active_goal_title(active)
        return {
            "type": "continue_active_goal",
            "goal": title,
            "verification": verification,
            "deliveryBoundary": boundary,
            "truthSource": truth_source,
            "commands": active_goal_iteration_commands(root),
            "continuePrompt": (
                f"Continue active goal {title}. "
                f"Boundary: {boundary}. Truth source: {truth_source}. Verification: {verification}."
            ).strip(),
        }
    next_goal = pending_goal_after_active(goals, active_goal)
    if next_goal:
        title = active_goal_title(next_goal)
        verification = normalized_verification(next_goal.get("verification", ""))
        return {
            "type": "promote_pending_goal",
            "goal": title,
            "verification": verification,
            "truthSource": next_goal.get("truthSource", ""),
            "continuePrompt": f"Start next pending goal {title}. Verification: {verification}.",
        }
    return {"type": "complete", "message": "No pending goal remains."}


def audit_projection_config(root):
    state = load_state_json(root)
    if "projection" not in state:
        return []
    projection = state.get("projection")
    keep_done = projection.get("keepDone") if isinstance(projection, dict) else None
    if not isinstance(keep_done, int) or isinstance(keep_done, bool) or keep_done < 0:
        return ["invalid state projection: projection.keepDone must be a non-negative integer"]
    return []


def write_state_json(root, goals=None, active_goal=UNSET, keep_done=None):
    root = Path(root)
    active_goal = read_active_goal(root) if active_goal is UNSET else active_goal
    goals = read_goal_matrix(root) if goals is None else goals
    keep_done = projection_keep_done(load_state_json(root)) if keep_done is None else keep_done
    path = root / ".goal-matrix" / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "activeGoal": active_goal,
                "nextLoop": next_loop_from_goals(goals, active_goal),
                "nextAction": next_action_payload(root, goals, active_goal),
                "subagentCandidates": subagent_candidates(goals, active_goal),
                "goalMatrix": goal_matrix_summary(goals, active_goal),
                "projection": {"keepDone": keep_done},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_goal_projections(root, goals, active_goal, keep_done)
