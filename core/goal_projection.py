from pathlib import Path

try:
    from goal_verification import normalized_verification
except ImportError:
    from core.goal_verification import normalized_verification


DEFAULT_KEEP_DONE = 10
GOAL_MATRIX_HEADER = "| Goal | User outcome | Engineering slice | Truth source | Verification | Status |"
GOAL_MATRIX_SEPARATOR = "| --- | --- | --- | --- | --- | --- |"
EXTENDED_GOAL_MATRIX_HEADER = (
    "| Goal | User outcome | Engineering slice | Truth source | Verification | Dependencies | Risk | Parallel safety | Status |"
)
EXTENDED_GOAL_MATRIX_SEPARATOR = "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"


def active_goal_id(active_goal):
    return active_goal.split(" - ", 1)[0] if active_goal else None


def markdown_table_cell(value):
    return " ".join(str(value).splitlines()).replace("\\", "\\\\").replace("|", "\\|")


def markdown_table_row(cells):
    return "| " + " | ".join(markdown_table_cell(cell) for cell in cells) + " |"


def split_markdown_table_row(line):
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    cells = []
    current = []
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if escaped:
        current.append("\\")
    cells.append("".join(current).strip())
    return cells


def read_goal_matrix_markdown(root, filename="goal-matrix.md"):
    path = Path(root) / ".goal-matrix" / "goals" / filename
    if not path.is_file():
        return []
    goals = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = split_markdown_table_row(line)
        if len(cells) < 6 or cells[0] in ("Goal", "---"):
            continue
        goal = {
            "id": cells[0],
            "userOutcome": cells[1],
            "engineeringSlice": cells[2],
            "truthSource": cells[3],
            "verification": cells[4],
            "status": cells[8] if len(cells) >= 9 else cells[5],
        }
        if len(cells) >= 9:
            goal.update({"dependencies": cells[5], "risk": cells[6], "parallelSafety": cells[7]})
        goals.append(goal)
    return goals


def active_goal_projection(goal=None):
    if goal is None:
        return """# Active Goal

Active goal: none
Initialization type: iteration
Policy impact: none
Touched paths: none
Delivery boundary: no active goal
Skipped: none
Truth source: `.goal-matrix` status
Verification: python3 core/goal_guard.py status --root .
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
"""
    return f"""# Active Goal

Active goal: {goal['id']} - {goal['userOutcome']}
Initialization type: {goal.get('initializationType', 'iteration')}
Policy impact: {goal.get('policyImpact', 'none')}
Touched paths: {goal.get('touchedPaths', 'TBD')}
Delivery boundary: {goal.get('deliveryBoundary', goal.get('engineeringSlice', ''))}
Skipped: {goal.get('skipped', 'other pending goals')}
Truth source: {goal.get('truthSource', '')}
Verification: {normalized_verification(goal.get('verification', ''))}
Development flow: {goal.get('developmentFlow', 'inspect -> failing check -> implement -> verify -> checkpoint')}
"""


def projection_keep_done(state):
    projection = state.get("projection") if isinstance(state, dict) else None
    keep_done = projection.get("keepDone") if isinstance(projection, dict) else DEFAULT_KEEP_DONE
    return (
        keep_done
        if isinstance(keep_done, int) and not isinstance(keep_done, bool) and keep_done >= 0
        else DEFAULT_KEEP_DONE
    )


def render_goal_matrix(goals, title="Goal Matrix"):
    extended = any(any(goal.get(field) for field in ("dependencies", "risk", "parallelSafety")) for goal in goals)
    header = EXTENDED_GOAL_MATRIX_HEADER if extended else GOAL_MATRIX_HEADER
    separator = EXTENDED_GOAL_MATRIX_SEPARATOR if extended else GOAL_MATRIX_SEPARATOR
    lines = [f"# {title}", "", header, separator]
    for goal in goals:
        cells = [
            goal.get("id", ""),
            goal.get("userOutcome", ""),
            goal.get("engineeringSlice", ""),
            goal.get("truthSource", ""),
            goal.get("verification", ""),
        ]
        if extended:
            cells.extend(
                [
                    goal.get("dependencies", "none"),
                    goal.get("risk", "medium"),
                    goal.get("parallelSafety", "main thread only"),
                ]
            )
        cells.append(goal.get("status", "Pending"))
        lines.append(markdown_table_row(cells))
    return "\n".join(lines) + "\n"


def split_goal_projections(goals, active_goal, keep_done):
    active_id = active_goal_id(active_goal)
    done_goals = [goal for goal in goals if goal.get("status", "").lower() == "done"]
    recent_done_ids = {goal.get("id") for goal in done_goals[-keep_done:]} if keep_done else set()
    visible = []
    archived = []
    for goal in goals:
        goal_id = goal.get("id")
        if goal.get("status", "").lower() != "done" or goal_id == active_id or goal_id in recent_done_ids:
            visible.append(goal)
        else:
            archived.append(goal)
    return visible, archived


def write_goal_projections(root, goals, active_goal, keep_done):
    goals_dir = Path(root) / ".goal-matrix" / "goals"
    goals_dir.mkdir(parents=True, exist_ok=True)
    visible, archived = split_goal_projections(goals, active_goal, keep_done)
    (goals_dir / "goal-matrix.md").write_text(render_goal_matrix(visible), encoding="utf-8")
    (goals_dir / "archive.md").write_text(render_goal_matrix(archived, "Goal Matrix Archive"), encoding="utf-8")
    active_id = active_goal_id(active_goal)
    active = next((goal for goal in goals if goal.get("id") == active_id), None) if active_id else None
    (goals_dir / "active-goal.md").write_text(active_goal_projection(active), encoding="utf-8")
