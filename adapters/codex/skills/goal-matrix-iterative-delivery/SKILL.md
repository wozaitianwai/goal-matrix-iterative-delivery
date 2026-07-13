---
name: goal-matrix-iterative-delivery
description: Use when the user asks for goal matrix delivery, child goals, iterative execution, engineering constraints, hooks, or goal self-correction.
---

# Goal Matrix Iterative Delivery

Codex adapter for the Goal Matrix Engineering Protocol. Keep the whole user objective visible in Codex, do the smallest useful repo slice, verify it against a real truth source, then checkpoint.

## Core Invariants

- `core/protocol.md` is the portable source of truth.
- Every task declares Initialization types, Project policy impact, Active goal contract (the Repo active goal contract in Codex), Development flow, Truth source, and Checkpoint plan before edits.
- Prefer existing project code, stdlib, and host behavior before new machinery.
- Read-only requests stay read-only.

## Skill and plugin routing

- Clarify/design: use `brainstorming` to resolve unclear intent before implementation.
- Planning: use `writing-plans` for multi-step work that needs checkpointable tasks.
- Behavior change: use `test-driven-development` before implementation.
- Failure investigation: use `systematic-debugging` before fixes.
- Completion claim: use `verification-before-completion` before saying done.
- Publication: use `finishing-a-development-branch` before merge, squash, PR, cleanup, or push.
- Do not add a new dependency, service, or plugin layer unless the Repo active goal needs it.

## Goal Lifecycles

- The visible Codex goal is the whole user objective. Read it with `get_goal`; call `create_goal` once when no visible goal exists.
- Call `update_goal(status=complete)` only after all repo work and final verification for the whole user objective are complete.
- The Repo active goal is the current `.goal-matrix` `G<n>` slice. Manage it with `goal_guard.py status`, `goal_guard.py start`, and `goal_guard.py checkpoint`.
- The visible Codex goal and Repo active goal names need not match.
- A repo checkpoint does not complete the visible Codex goal.
- The first substantive response after this skill is active must show a goal matrix or Repo active-goal block before freeform discussion.
- In clarify/design or read-only work, show the lightweight matrix/Repo active-goal draft first, then continue with discussion.

## Repo Active Loop

Use this chain:

```text
project_initialization -> work_classification -> design -> design_gate -> execute -> review_gate -> checkpoint -> design_iteration
```

Before editing, state:

```text
Repo active goal: G<n> - <name>
Initialization type: <new-project|iteration|bugfix|legacy-baseline>
Policy impact: <none|approval-required|blocked>
Touched paths: <paths or patterns>
Delivery boundary: <what changes now>
Skipped: <what is intentionally not built>
Truth source: <authoritative evidence>
Verification: <smallest real check>
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
```

Call `goal_guard.py start` with structured JSON containing the complete contract fields above. Plain text input creates a blocked draft; do not execute or checkpoint it.

## Loop Engineering

Engineering pass:

```text
project initialization status -> Repo active goal -> failing check -> minimal change -> verification -> checkpoint commit -> Repo next loop
```

- A self-evolution run continues only through pending goals already recorded in state; when none remains, report complete instead of synthesizing a backlog.
- Recoverable external prerequisites, such as token, cookies, login, or service restart, keep the Repo active goal open with a concrete next action instead of becoming a blocked goal.
- Fast Lane is available only for trivial typo, copy, or single-function edits with no Repo active goal; keep path/publish policy and focused verification, but skip goal-matrix checkpointing.
- Before push, preserve verified checkpoint commits and require a clean, integrated branch with closed goals and checkpoint evidence.
- Final push needs final verification evidence and a clear branch/history state.

## Hook Workflow

- `SessionStart`: show initialization status and loop policy.
- `UserPromptSubmit`: classify the request into `clarify`, `goal_matrix`, `execute`, `verify`, `checkpoint`, or `history`.
- `PreToolUse`: run policy and publish gates without injecting model context after a successful tool call.
- `Stop`: run the completion gate; on success emit only an empty JSON object and no model context.
- Completion needs `Repo next loop:` (`Next loop` in the portable protocol) with the next pending goal, the still-open Repo active goal's next action, or no remaining goal.

## User Habits

- If the user requests read-only work, do not edit files or run write commands.
- Start from the named truth source: logs, database rows, API responses, browser state, config, or test output.
- When the user narrows scope, answer that scope first.
- Do not treat UI refresh or optimistic state as success without source-of-truth evidence.
- Prefer existing routes, docs, scripts, migration logs, and project commands over new surfaces.
- If conflicts are discussed and the user declares one side authoritative, align to that side first.

## Matrix Shape

```markdown
| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G0 | Stabilize current state | Preserve existing behavior | Repo/docs/tests | Existing checks pass | Pending |
| G1 | First visible improvement | Smallest useful slice | API/DB/UI/log/test | Focused check | Pending |
```

Keep each development flow concrete:

- `inspect`: files, docs, callers, logs, or current behavior to read first.
- `failing check`: the one test/script/manual reproduction that should fail or reveal the gap.
- `implement`: the smallest code/doc/config change allowed by this goal.
- `verify`: exact command or truth-source readback.
- `checkpoint`: matrix/status/doc update and skipped scope.

## Work Routing

- Product/UI: verify browser behavior and backing API/data state.
- Data/API: inspect real request/response, database rows, logs, and config.
- Operations: check process state, resource pressure, service config, and rollback boundary.
- Plugin/skill work: keep trigger text generic and test hook output directly.

## Self-Correction

Before edits and before the final answer, audit the current plan or summary:

- Missing matrix: create or repair it.
- Missing Repo active-goal block or development flow: stop and add it.
- Broad Repo active goal: split it, then do the smallest useful slice.
- No truth source: name the authoritative evidence before proceeding.
- No verification evidence: do not claim completion.
- New abstraction/service/queue/UI surface: skip unless the Repo active goal needs it now.

Local draft check:

```bash
python3 core/goal_guard.py audit < draft.md
```

## Default Finish

```text
Completed G<n>: <result>. Verified with <check>. Skipped <scope>; add it when <trigger>.
```
