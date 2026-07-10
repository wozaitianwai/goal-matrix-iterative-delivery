import json
import re
import subprocess
import sys
from pathlib import Path

try:
    from goal_policy import load_project_policy
    from goal_publish import git_output
    from goal_state import (
        INITIALIZATION_TYPES,
        audit_active_goal_contract,
        audit_active_goal_projection_drift,
        audit_goal_matrix_projection_drift,
        audit_projection_config,
        audit_visible_done_goal_verification,
        fast_lane_available,
        read_active_goal,
        read_goal_matrix,
    )
except ImportError:
    from core.goal_policy import load_project_policy
    from core.goal_publish import git_output
    from core.goal_state import (
        INITIALIZATION_TYPES,
        audit_active_goal_contract,
        audit_active_goal_projection_drift,
        audit_goal_matrix_projection_drift,
        audit_projection_config,
        audit_visible_done_goal_verification,
        fast_lane_available,
        read_active_goal,
        read_goal_matrix,
    )


POLICY_LIST_FIELDS = (
    "immutablePaths",
    "approvalRequiredPaths",
    "protectedCommands",
    "truthSources",
    "requiredDocs",
    "completionRequires",
)
REQUIRED_DOCS = (
    "project-context.md",
    "checks.md",
    "goals/goal-matrix.md",
    "goals/active-goal.md",
)
REQUIRED_COMPLETION = ("verification", "truthSource", "checkpoint")


def audit(text):
    problems = []
    lowered = text.lower()

    if "| goal |" not in lowered or "truth source" not in lowered or "verification" not in lowered:
        problems.append("missing goal matrix columns: Goal, Truth source, Verification")

    for label in (
        "Active goal:",
        "Initialization type:",
        "Policy impact:",
        "Touched paths:",
        "Delivery boundary:",
        "Skipped:",
        "Truth source:",
        "Verification:",
        "Development flow:",
    ):
        if label.lower() not in lowered:
            problems.append(f"missing active-goal field: {label}")

    if len(re.findall(r"^active goal:", lowered, re.MULTILINE)) > 1:
        problems.append("one active goal only: split or defer extra active goals")

    unclear_draft = re.search(r"draft requirement:|草案|不清晰|模糊|unclear", lowered)
    clarity_decision = re.search(r"^clarity decision:\s*\S", lowered, re.MULTILINE)
    if unclear_draft and not clarity_decision:
        problems.append("missing clarity decision: resolve blocking questions before goal execution")

    init_match = re.search(r"^initialization type:\s*(\S+)", lowered, re.MULTILINE)
    if init_match and init_match.group(1) not in INITIALIZATION_TYPES:
        problems.append("unsupported Initialization type: use new-project, iteration, bugfix, or legacy-baseline")

    policy_match = re.search(r"^policy impact:\s*(.+)$", lowered, re.MULTILINE)
    if policy_match:
        policy_impact = policy_match.group(1).strip()
        if policy_impact == "blocked":
            problems.append("Policy impact is blocked: do not proceed")
        if policy_impact == "approval-required" and not re.search(
            r"approval:|approved by|user approved|用户确认|已确认|批准",
            lowered,
        ):
            problems.append("Policy impact requires approval evidence")

    completion = re.search(r"\b(completed|complete|done|fixed|implemented)\b|完成|已完成", lowered)
    evidence = re.search(r"verified with|verified:|验收|验证.*(通过|pass)|tests? pass|build pass", lowered)
    if completion and not evidence:
        problems.append("missing completion evidence: use `Verified with ...` or state the blocker")
    checkpoint = re.search(r"checkpoint updated|status updated|matrix updated|更新状态|更新矩阵", lowered)
    if completion and not checkpoint:
        problems.append("missing checkpoint evidence: update matrix/status before completion")
    next_loop = re.search(r"^next loop:\s*\S", lowered, re.MULTILINE)
    if completion and not next_loop:
        problems.append("missing next loop handoff: add `Next loop: ...`")

    active_block = "\n".join(
        line for line in lowered.splitlines() if line.startswith(("active goal:", "delivery boundary:", "skipped:"))
    )
    broad_goal = re.search(r"(全部|完整|整套|全量|whole|entire|everything|all\b|platform|重构)", active_block)
    small_slice = re.search(r"最小|切片|本轮|只|one |single|smallest|bounded|slice", active_block)
    if broad_goal and not small_slice:
        problems.append("active goal too broad: split it into one bounded child goal")

    ui_only = re.search(r"ui refresh|optimistic|looks good|看起来|刷新正常", lowered)
    source_evidence = re.search(
        r"verified with|api response|database|db readback|postgres|sqlite|log readback|pytest|test|build|落库|真实",
        lowered,
    )
    if completion and ui_only and not source_evidence:
        problems.append("UI-only evidence is insufficient: verify against API/DB/log/test truth source")

    push_claim = re.search(r"\b(push|pushed|pushing)\b|推送", lowered)
    final_verification = re.search(r"final verification|verified with|最终验证|最终验收|验证.*(通过|pass)", lowered)
    if push_claim and not final_verification:
        problems.append("missing final verification before push")
    return problems


def audit_project(root):
    problems = []
    root = Path(root)
    policy_path = root / ".goal-matrix" / "project-policy.json"
    if not policy_path.is_file():
        return ["missing project policy: .goal-matrix/project-policy.json"]

    policy, policy_problem = load_project_policy(root)
    if policy_problem:
        return [policy_problem]
    if policy.get("initializationType") not in INITIALIZATION_TYPES:
        problems.append("invalid project policy initializationType")

    trigger_mode = policy.get("triggerMode", "narrow")
    if trigger_mode not in ("narrow", "strict"):
        problems.append("invalid project policy triggerMode: expected narrow or strict")
    if "strictMode" in policy and not isinstance(policy.get("strictMode"), bool):
        problems.append("invalid project policy strictMode: expected boolean")

    for field in POLICY_LIST_FIELDS:
        values = policy.get(field)
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            problems.append(f"invalid project policy field: {field} must be a list of strings")

    required_docs = policy.get("requiredDocs", [])
    if isinstance(required_docs, list):
        for doc in REQUIRED_DOCS:
            if doc not in required_docs:
                problems.append(f"project policy missing required doc entry: {doc}")
        for doc in required_docs:
            if isinstance(doc, str) and not (root / ".goal-matrix" / doc).is_file():
                problems.append(f"missing required doc: .goal-matrix/{doc}")

    completion = policy.get("completionRequires", [])
    if isinstance(completion, list):
        for item in REQUIRED_COMPLETION:
            if item not in completion:
                problems.append(f"project policy missing completion requirement: {item}")

    problems.extend(audit_projection_config(root))
    problems.extend(audit_goal_matrix_projection_drift(root))
    problems.extend(audit_active_goal_projection_drift(root))
    problems.extend(audit_active_goal_contract(root))
    problems.extend(audit_visible_done_goal_verification(root))
    return problems


def gate_input(root, file_path):
    text = sys.stdin.read()
    if text.strip():
        return text
    path = Path(file_path) if file_path else Path(root) / ".goal-matrix" / "loop-note.md"
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def completion_gate(root):
    root = Path(root)
    if not (root / ".goal-matrix" / "project-policy.json").is_file():
        return 0

    problems = audit_project(root)
    active_goal = read_active_goal(root)
    pending_goals = [goal for goal in read_goal_matrix(root) if goal.get("status", "").lower() != "done"]
    if active_goal:
        problems.append(f"active goal still open: {active_goal}; run checkpoint explicitly")
    elif pending_goals:
        problems.append(f"pending goal remains: {pending_goals[0].get('id', 'unknown')}")

    dirty = git_output(root, "status", "--porcelain")
    if dirty.returncode == 0 and dirty.stdout.strip() and not active_goal:
        note = gate_input(root, None).lower()
        focused = re.search(r"^focused verification:\s*\S", note, re.MULTILINE)
        verified = re.search(r"^verified with:\s*\S", note, re.MULTILINE)
        if not (focused and verified):
            problems.append("Fast Lane requires focused verification evidence")

    for problem in dict.fromkeys(problems):
        print(f"completion gate blocked: {problem}", file=sys.stderr)
    return 1 if problems else 0


def emit_gate(next_step, reason):
    print(json.dumps({"next": next_step, "reason": reason}, ensure_ascii=False, indent=2))
    return 0 if next_step == "checkpoint" else 1


def gate_decision(phase, text, verify_command=None, root="."):
    lowered = text.lower()
    has_clarity = re.search(r"^clarity decision:\s*\S", lowered, re.MULTILINE)
    has_policy = "policy impact:" in lowered
    has_truth = "truth source:" in lowered
    has_verification_plan = "verification:" in lowered
    has_verification_evidence = re.search(
        r"verified with|verified:|tests? pass|build pass|验证.*(通过|pass)", lowered
    )
    reviewer_values = re.findall(r"^reviewer:\s*(.+)$", lowered, re.MULTILINE)
    review_changes = any(
        re.search(r"\b(changes requested|requested changes|fail|failed|reject)\b", value)
        for value in reviewer_values
    )
    review_approved = any(re.search(r"\b(approved|pass|passed|ok)\b", value) for value in reviewer_values)

    if phase == "design_gate":
        if not has_clarity:
            return emit_gate("design", "missing clarity decision")
        if not (has_policy and has_truth and has_verification_plan):
            return emit_gate("design", "missing policy, truth source, or verification plan")
        return emit_gate("execute", "design gate passed")

    if phase == "review_gate":
        if review_changes:
            return emit_gate("execute", "review requested changes")
        if fast_lane_available(root) and not review_approved:
            if re.search(r"^focused verification:\s*\S", lowered, re.MULTILINE) and re.search(
                r"^verified with:\s*\S", lowered, re.MULTILINE
            ):
                return emit_gate("checkpoint", "Fast Lane: focused verification evidence present")
            if not verify_command:
                return emit_gate("execute", "Fast Lane requires focused verification")
            result = subprocess.run(verify_command, cwd=Path(root), text=True, capture_output=True)
            if result.returncode:
                reason = (
                    result.stderr.strip().splitlines()[-1]
                    if result.stderr.strip()
                    else "Fast Lane verification command failed"
                )
                return emit_gate("execute", reason.removeprefix("active verification blocked: "))
            return emit_gate("checkpoint", "Fast Lane: focused verification passed")
        if review_approved:
            if not verify_command:
                return emit_gate("execute", "missing machine verification command")
            result = subprocess.run(verify_command, cwd=Path(root), text=True, capture_output=True)
            if result.returncode:
                return emit_gate("execute", "verification command failed")
            return emit_gate("checkpoint", "review gate passed")
        if not has_verification_evidence:
            return emit_gate("execute", "missing verification evidence")
        return emit_gate("execute", "missing reviewer decision; keep active goal open")
    return emit_gate("blocked", "unsupported gate phase")
