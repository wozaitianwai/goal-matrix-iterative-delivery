# Loop Configuration - Goal Matrix Delivery

This repository keeps one CI-backed package-triage loop for plugin readiness.

## Active Loops

| Pattern | Cadence | Status | Prompt |
| --- | --- | --- | --- |
| package-triage | push or pull request | L2 local; L3 only in trusted current-head CI | Run `python3 scripts/loop_audit.py --root . --json`; remote verifier must require `L3 remote-ci-activity`. |

## Loop Engineering Completion Matrix

The machine goal status is read from `.goal-matrix/state.json`; this document does not duplicate G-number status. Local completion evidence comes from `scripts/loop_verify.py`, while L3 requires trusted GitHub Actions context matching the checked-out HEAD. Recorded run-log readback is informational only. A pull request and required-check ruleset are the remaining remote enforcement step.

## Readiness Levels

| Level | Meaning | Required signals |
| --- | --- | --- |
| L1 | report-only | state file, loop config, budget, run log, triage prompt |
| L2 | assisted-with-verifier | L1 plus completion matrix and packaged independent verifier |
| L3 | remote-ci-activity | L2 plus GitHub remote, workflow checks, and trusted GitHub Actions context matching the checked-out HEAD |

## Human Gates

- Any write to global Codex config or marketplace files.
- Any hook trust change.
- Any GitHub remote creation, push, release, or npm publication.
- Any auto-fix, workflow automation, or remote publication.

## Budget

- Max runs/day: 1 manual package triage run.
- Max tokens/day: 100k.
- Max sub-agent spawns/run: 0 in L1.
- Kill switch: set `Loop paused: true` in `STATE.md`.

## Observability

- `STATE.md` records human operational notes and must not claim an active or pending G-number status.
- `.goal-matrix/state.json` is the machine goal-state truth source.
- `loop-run-log.md` records every loop run.
- `loop-budget.md` records cost limits and pause rules.

## Next Loop

Push the current checkpoint branch through a pull request, verify every Python matrix leg, then activate and read back the required-check ruleset for `main`.
