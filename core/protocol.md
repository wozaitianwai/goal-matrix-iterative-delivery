# Goal Matrix Engineering Protocol

This is the portable source of truth for Goal Matrix Iterative Delivery. Host adapters may package or inject it, but they must not fork the workflow.

## Core Rule

Every project starts by declaring its initialization type, policy constraints, truth sources, and active goal before implementation.

## Loop stage chain

The loop runs through a fixed stage chain:

```text
project_initialization -> work_classification -> design -> design_gate -> execute -> review_gate -> checkpoint -> design_iteration
```

- `project_initialization`: create or read `.goal-matrix` policy, context, checks, matrix, and active goal.
- `work_classification`: classify the work as new project, iteration, bugfix, or legacy baseline.
- `design`: turn the requirement into a goal matrix and one active goal.
- `design_gate`: clarify or return to design when intent, scope, policy, truth source, or verification is unclear.
- `execute`: make the smallest change inside the active-goal boundary.
- `review_gate`: inspect checks, reviewer findings, and evidence; return to design or execute when they fail.
- `checkpoint`: update state and commit only verified child-goal work.
- `design_iteration`: hand off the next pending goal, a hard blocker, or no remaining goal.

The practical backbone is state on disk. `.goal-matrix` records what was tried, what passed, what remains open, and what resumes after a restart. Automations, worktrees, connectors, and sub-agents are optional extensions; add them only when state, gates, and checks are already reliable.

The review gate separates maker and checker responsibilities. The agent that implements a slice should not be the only evidence that the slice is done; tests, audit output, reviewer findings, or a separate review pass must be able to send the loop back to `design` or `execute`.

Use the shared guard for a minimal gate decision:

```bash
python3 core/goal_guard.py gate --phase design_gate < loop-note.md
python3 core/goal_guard.py gate --phase review_gate < loop-note.md
python3 core/goal_guard.py gate --phase review_gate --root /path/to/project
```

`design_gate` returns `design` when clarity, policy, truth source, or verification plan is missing; otherwise it returns `execute`. `review_gate` returns `execute` for failed review, missing verification, or missing reviewer decision, and returns `checkpoint` for verified approved work.

When stdin is empty, `gate --root` reads `.goal-matrix/loop-note.md`.

## Initialization types

- `new-project`: define target user, success criteria, technical boundaries, first spec, and first goal.
- `iteration`: record current behavior, changed surfaces, non-breakage boundaries, and regression checks.
- `bugfix`: reproduce the failure, state root-cause hypothesis, create or name a failing check, and verify the fix.
- `legacy-baseline`: inventory structure, commands, data/config boundaries, risks, and protected paths before changes.

## Project policy

`.goal-matrix/project-policy.json` is the machine-readable hard-constraint source. It defines initialization type, immutable paths, approval-required paths, protected commands, truth sources, required docs, and completion requirements.

## Project initialization

Use the shared guard to create the baseline files for a target project:

```bash
printf '新项目立项...' | python3 core/goal_guard.py classify
python3 core/goal_guard.py init --root /path/to/project --type iteration
printf '修复下一个有边界的目标' | python3 core/goal_guard.py start --root /path/to/project
python3 core/goal_guard.py checkpoint --root /path/to/project -- python3 scripts/loop_verify.py
```

The command creates missing `.goal-matrix` files from `core/templates/`, creates `specs/` and `goals/`, writes the requested initialization type into a new policy file, and does not overwrite existing project files.

After initialization, fill `.goal-matrix/project-context.md` with the project charter, work classification, and lifecycle support cycle. This is the project立项 record: idea source, user/operator, success criteria, support horizon, retirement trigger, work type, risk, primary surface, approval needs, and the stage-by-stage support loop.

## Active goal contract

```text
Active goal: G<n> - <name>
Initialization type: <new-project|iteration|bugfix|legacy-baseline>
Policy impact: <none|approval-required|blocked>
Touched paths: <paths or patterns>
Delivery boundary: <this slice only>
Skipped: <explicitly not doing>
Truth source: <authoritative evidence>
Verification: <smallest real check>
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
```

## Development flow

Each small goal must carry its own flow:

- inspect: read project instructions, docs, likely touched files, callers, logs, or current behavior.
- failing check: define the smallest test, script, reproduction, or truth-source readback that proves the gap.
- implement: make the smallest allowed change inside the delivery boundary.
- verify: run the named check or read back the authoritative truth source.
- checkpoint: update goal state, decisions, and skipped scope.

## Skill and plugin routing

Supporting skills and plugins are selected by loop phase, not by habit or novelty:

| Phase | Route to | Boundary |
| --- | --- | --- |
| clarify/design | `brainstorming` | Resolve unclear intent or design before implementation. |
| implementation planning | `writing-plans` | Create testable, checkpointable tasks for multi-step work. |
| behavior change | `test-driven-development` | Write or name the failing check before implementation. |
| failure investigation | `systematic-debugging` | Reproduce, inspect, isolate root cause, fix once, verify. |
| completion claim | `verification-before-completion` | Run the named truth-source check before saying done. |
| publication | `finishing-a-development-branch` | Decide merge, squash, PR, cleanup, or push only after final verification. |

Prefer the most specific existing project, host, or plugin capability that enforces the active loop boundary. Do not add a new dependency, service, or plugin layer unless the current active goal needs it.

## Loop engineering

Every engineering pass is a closed loop:

```text
project initialization status -> active goal -> failing check -> minimal change -> verification -> checkpoint commit -> next loop
```

Use small local checkpoint commits after verified child goals. Before pushing, squash or merge fragmented local commits into readable history unless the user asks to preserve every checkpoint. Hook-capable hosts must run `goal_guard.py publish-gate` before `git push` so this policy can fail closed.

Keep `loop-run-log.md` bounded. When `scripts/loop_audit.py` reports `runLogNeedsSummary`, run a summary/pruning child goal before continuing long-loop work.

Treat `.goal-matrix/project-policy.json` as the target project runtime policy source for path, command, and publish-action gates. Treat `loop-governance.json` as plugin repository autonomy for this repo's own CI/static governance checks. `STATE.md` is human-readable only and must not repeat approval envs, protected paths, or publish patterns. If human state copies machine-owned policy values, `scripts/loop_audit.py` must flag `stateGovernanceDuplication`.

Payload approvals for approval-required paths must be scoped to the active goal, target path, future expiry, and a reason. Environment approval remains an explicit local emergency override only.

After `start` or `checkpoint`, `.goal-matrix/state.json` is the canonical machine state for active goal and goal-matrix status. Markdown goal files remain a human-readable projection and fallback for legacy state.

`.goal-matrix/goals/archive.md` is an immutable read-only snapshot produced by prune; it is not part of drift detection and is not a trusted source of current goal state.

Fast Lane is allowed only when the project is initialized, there is no active goal, and the request is a trivial typo, copy, or single-function edit. Keep policy-gate and publish-gate enforcement, require focused verification before completion, and skip goal-matrix checkpointing. Protected paths, publish actions, unclear scope, or multi-file behavior changes return to the normal loop.

Broad prompt handling: first generate a pending matrix with scope, truth source, verification, dependencies, risk, and parallel-safety metadata. Keep one scheduler/acceptance active goal in the main thread; optional subagents may only produce candidates or investigations. The main thread reviews outputs, runs the real verification, and checkpoints child goals one at a time.

A self-evolution run still exposes only one active child goal at a time, but it does not stop after one verified checkpoint when more pending goals exist. After checkpoint, promote the next pending goal and keep executing. Stop only at budget, blocker, or no pending goal.

## Hook phase gates

Hook-capable hosts should wire the same loop with thin lifecycle hooks:

| Hook | Phase boundary |
| --- | --- |
| `SessionStart` | Show project initialization status and loop policy. |
| `UserPromptSubmit` | Classify the prompt as `clarify`, `goal_matrix`, `execute`, `verify`, `checkpoint`, or `history`; do not run `start` or write `.goal-matrix` state by default. UserPromptSubmit 不会运行 `start`。 |
| `PreToolUse` | Permit one loop step only after active goal and policy boundary are known; block `git push` when publish history is fragmented. |
| `PostToolUse` | Tie tool output back to the active goal truth source or next step. |
| `Stop` | Require verification, checkpoint/status evidence, and push history policy before completion. |

Unclear drafts require a `Clarity decision:` note before execution. A loop may expose only one `Active goal:` at a time.

Completion requires a `Next loop:` handoff: select the next pending goal, keep the active goal open with a concrete next action when prerequisites are recoverable, or state that no goal remains.

## Truth source

Use real evidence: tests, build output, logs, API responses, database rows, browser state, config, or documented manual reproduction.

UI refresh, optimistic state, or "looks good" is not enough without a backing truth source.

## Checkpoint

Completion requires verification, truth-source evidence, and an updated matrix/status note. If verification cannot run because of a recoverable external prerequisite, such as token, cookies, login, or service restart, state the next action and keep the goal open.

## Adapter rule

Adapters are thin. Codex and future hook-capable hosts must carry these same invariants.
