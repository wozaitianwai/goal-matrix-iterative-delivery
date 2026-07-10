# Loop Configuration - Goal Matrix Delivery

This repository keeps one manual package-triage loop for plugin readiness.

## Active Loops

| Pattern | Cadence | Status | Prompt |
| --- | --- | --- | --- |
| package-triage | manual or daily | L2 local / L3 remote-enforced | Run `python3 scripts/loop_audit.py --root . --json`; update `STATE.md`; remote verifier must require `L3 remote-ci-activity`. |

## Loop Engineering Completion Matrix

G23-G36 are Done: readiness matrix, verifier skill, workflow checks, remote CI evidence, gap register, shared verifier, release/install readback, and cache drift checks are all represented by local tests plus `scripts/loop_audit.py --root . --json`.

## Readiness Levels

| Level | Meaning | Required signals |
| --- | --- | --- |
| L1 | report-only | state file, loop config, budget, run log, triage prompt |
| L2 | assisted-with-verifier | L1 plus completion matrix and packaged independent verifier |
| L3 | remote-ci-activity | L2 plus GitHub remote, workflow checks, and trusted GitHub Actions context matching the checked-out HEAD |

## Engineering Gap Register

| Gap | Current state | Missing for loop-engineering parity | Next action |
| --- | --- | --- | --- |
| remote-ci | GitHub Actions current-run context is required; run-log readback is informational only | None for L3 remote CI evidence | Resolved: CI runs `loop_verify.py --require-level L3` against its checked-out SHA; recorded run URLs/statuses cannot promote local audits. |
| maker-checker | Branch/worktree verifier path exists | None for maker-checker separation evidence | Resolved: keep branch/worktree/verifier evidence in `loop-run-log.md` |
| run-evidence | `loop-run-log.md` has repeated timestamped runs with outcomes and audit signal `repeatedRunEvidence=true` | None for repeated local run evidence | Resolved: keep two or more JSON-line run records with outcomes |
| distribution | Pushed source validates and installs from release source | None for pushed-source distribution verification | Resolved: keep clone/install/doctor evidence in `loop-run-log.md` |
| connectors | GitHub connector readback works for `wozaitianwai/goal-matrix-iterative-delivery`; write tools exist but no PR/issue/comment/release action is requested | None for current loop; connector writes need explicit user-approved PR/issue/comment/release task | Resolved: defer connector writes until an acting remote task exists |
| governance | `scripts/check_governance.py` is wired into `scripts/loop_verify.py` and CI to block sensitive paths or publish actions without approval | None for local/CI governance gate evidence | Resolved: keep policy, tests, and verifier output together |

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

No unresolved loop-engineering gaps remain in the current matrix.
