# Goal Matrix Engineering Protocol

This project uses Goal Matrix Iterative Delivery. Before implementation, establish initialization type, policy constraints, truth source, active goal, and development flow.

## Loop stage chain

Use this loop:

```text
project_initialization -> work_classification -> design -> design_gate -> execute -> review_gate -> checkpoint -> design_iteration
```

Design gates return to design when clarity, policy, truth source, or verification is unclear. Review gates return to execute when checks fail, checkpoint when verified, or blocked when reviewer evidence is missing.

## Initialization types

- `new-project`: define user, success criteria, boundaries, first spec, first goal.
- `iteration`: record existing behavior, changed surfaces, non-breakage boundaries, regression checks.
- `bugfix`: reproduce failure, state root cause, define failing check, verify fix.
- `legacy-baseline`: inventory structure, commands, data/config boundaries, risks, protected paths.

## Project policy

Read `.goal-matrix/project-policy.json` when present. Immutable paths are blocked. Approval-required paths need explicit approval evidence before editing.

## Active goal contract

Every small goal must state: Active goal, Initialization type, Policy impact, Touched paths, Delivery boundary, Skipped, Truth source, Verification, Development flow.

## Development flow

Use: inspect -> failing check -> implement -> verify -> checkpoint.

## Skill and plugin routing

- Clarify/design: use `brainstorming` to resolve unclear intent before implementation.
- Planning: use `writing-plans` for multi-step work that needs checkpointable tasks.
- Behavior change: use `test-driven-development` before implementation.
- Failure investigation: use `systematic-debugging` before fixes.
- Completion claim: use `verification-before-completion` before saying done.
- Publication: use `finishing-a-development-branch` before merge, squash, PR, cleanup, or push.
- Do not add a new dependency, service, or plugin layer unless the active goal needs it.

## Truth source

Use tests, build output, logs, API responses, database rows, browser state, config, or documented manual reproduction. UI-only success is insufficient.

## Visible Codex goal

Instruction adapters cannot create a visible Codex goal. If work runs inside Codex and a visible Codex goal is needed, the agent must call `create_goal`; otherwise keep the active goal explicit in text and `.goal-matrix`.

## Checkpoint

Completion requires verification, truth-source evidence, updated matrix/status, and a Next loop handoff.
