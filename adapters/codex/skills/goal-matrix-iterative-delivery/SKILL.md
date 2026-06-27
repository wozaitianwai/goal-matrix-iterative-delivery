---
name: goal-matrix-iterative-delivery
description: Use when the user asks for goal matrix delivery, child goals, iterative execution, engineering constraints, hooks, or goal self-correction.
---

# Goal Matrix Iterative Delivery

## Overview

Fuse execution discipline, scope control, Codex hooks, and the user's high-frequency operating habits: make the goal visible, execute one child goal, verify against a real truth source, then checkpoint.

This skill is the Codex adapter entry point. The portable source of truth is `core/protocol.md`; host-specific files live under `adapters/`.

## Core Invariants

- Goal Matrix Engineering Protocol
- Initialization types
- Project policy
- Active goal contract
- Development flow
- Truth source
- Checkpoint

## Operating Sources

- Planning gates, TDD/debugging discipline, and verification before completion.
- YAGNI, existing code first, stdlib/native first, and no speculative systems.
- Codex hook-injected reminders at session start and goal-like prompts.
- User habits: truth-source first, scope-narrowing first, read-only requests stay read-only.

## Skill and plugin routing

- Clarify/design: use `brainstorming` to resolve unclear intent before implementation.
- Planning: use `writing-plans` for multi-step work that needs checkpointable tasks.
- Behavior change: use `test-driven-development` before implementation.
- Failure investigation: use `systematic-debugging` before fixes.
- Completion claim: use `verification-before-completion` before saying done.
- Publication: use `finishing-a-development-branch` before merge, squash, PR, cleanup, or push.
- Do not add a new dependency, service, or plugin layer unless the active goal needs it.

## Codex visible goal runtime

- Hooks inject context only; they cannot create the visible Codex goal by themselves.
- If a goal-like prompt needs a visible Codex goal and `create_goal` is available, call `create_goal` once before work.

## Fusion Workflow

Intake -> Matrix -> Active goal -> Development flow -> Execute -> Verify -> Checkpoint

1. Intake: read project instructions, existing docs, likely touched files, and user-named truth sources.
2. Matrix: turn broad work into user outcome, engineering slice, truth source, verification.
3. Active goal: select one child goal and state boundary, skipped scope, and check.
4. Development flow: write the concrete process for this child goal.
5. Execute: trace the real flow, then apply the scope-control ladder.
6. Verify: use a real source: test, build, API/DB/log readback, browser check, or project script.
7. Checkpoint: update matrix/status and report what was skipped.

## Loop Engineering

Run each engineering pass as:

```text
project initialization status -> active goal -> failing check -> minimal change -> verification -> checkpoint commit -> next loop
```

- Show whether `.goal-matrix/project-policy.json` is initialized before the first child goal.
- A self-evolution run keeps one active child goal at a time, but continues after each verified checkpoint by promoting the next pending goal; stop only at budget, blocker, or no pending goal.
- Use small local checkpoint commits only after verified child goals.
- Before push, squash or merge fragmented local commits into readable history unless the user asks to preserve them.
- `PreToolUse` must run `goal_guard.py publish-gate` before `git push` so fragmented history fails closed.
- Final push needs final verification evidence and a clear branch/history state.

## Loop stage chain

```text
project_initialization -> work_classification -> design -> design_gate -> execute -> review_gate -> checkpoint -> design_iteration
```

## Hook Workflow

- `SessionStart`: show initialization status and loop policy.
- `UserPromptSubmit`: classify the request into `clarify`, `goal_matrix`, `execute`, `verify`, `checkpoint`, or `history`.
- `PreToolUse`: keep the next action to one active-goal step and block unsafe publish actions.
- `PostToolUse`: connect tool output to truth source, verification, or next step.
- `Stop`: require verification, checkpoint/status evidence, and push history policy before completion.
- Unclear drafts need `Clarity decision:` before execution, and only one `Active goal:` can be exposed at a time.
- Completion needs `Next loop:` with the next pending goal, a blocked state, or no remaining goal.

## User Habits

- If the user requests read-only work, do not edit files or run write commands.
- Start from the named truth source: logs, database rows, API responses, browser state, config, or test output.
- When the user narrows scope, answer that scope first.
- Do not treat UI refresh or optimistic state as success without source-of-truth evidence.
- Prefer existing routes, docs, scripts, migration logs, and project commands over new surfaces.
- If conflicts are discussed and the user declares one side authoritative, align to that side first.

## Work Routing

- Product/UI: verify browser behavior and the backing API/data state; UI-only success is not enough.
- Data/API: inspect real request/response, database rows, logs, and permission/config boundaries before changing code.
- Operations: check process state, resource pressure, service config, and rollback/cleanup boundaries before fixes.
- Migration/refactor: preserve existing behavior, update the active goal/migration log, and run project-native checks.
- Plugin/skill work: keep trigger text generic, avoid project-specific memories, and test hook output directly.

## Matrix Shape

```markdown
| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G0 | Stabilize current state | Preserve existing behavior | Repo/docs/tests | Existing checks pass | Pending |
| G1 | First visible improvement | Smallest useful slice | API/DB/UI/log/test | Focused check | Pending |
```

## Active Goal Gate

State this before editing:

```text
Active goal: G<n> - <name>
Initialization type: <new-project|iteration|bugfix|legacy-baseline>
Policy impact: <none|approval-required|blocked>
Touched paths: <paths or patterns>
Delivery boundary: <what changes now>
Skipped: <what is intentionally not built>
Truth source: <authoritative evidence>
Verification: <smallest real check>
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
```

Every small goal must carry its own development flow. Keep it concrete:

- `inspect`: files, docs, callers, logs, or current behavior to read first.
- `failing check`: the one test/script/manual reproduction that should fail or reveal the gap.
- `implement`: the smallest code/doc/config change allowed by this goal.
- `verify`: exact command or truth-source readback.
- `checkpoint`: matrix/status/doc update and skipped scope.

## Self-Correction

Before edits and before the final answer, audit the current plan or summary:

- Missing matrix: create or repair it.
- Missing active-goal block or development flow: stop and add it.
- Broad active goal: split it, then do the smallest useful slice.
- No truth source: name the authoritative evidence before proceeding.
- No verification evidence: do not claim completion.
- New abstraction/service/queue/UI surface: skip unless the active goal needs it now.

The plugin hook injects this guard at session start and when goal-like prompts arrive. For a local draft check, run:

```bash
python3 core/goal_guard.py audit < draft.md
```

## Default Finish

```text
Completed G<n>: <result>. Verified with <check>. Skipped <scope>; add it when <trigger>.
```
