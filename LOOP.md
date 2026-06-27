# Loop Configuration - Goal Matrix Delivery

This repository is moving from plugin packaging toward loop-engineering parity.

## Active Loops

| Pattern | Cadence | Status | Prompt |
| --- | --- | --- | --- |
| package-triage | manual or daily | L3 remote-ci-activity | Run `python3 scripts/loop_audit.py --root . --json`; update `STATE.md`; verifier must reject completion without evidence. |

## Loop Engineering Completion Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G23 | The repo says exactly what "loop-engineering complete" means | Add L1/L2/L3 readiness matrix and audit signals | `LOOP.md`, audit JSON | `python3 scripts/loop_audit.py --root . --json` | Done |
| G24 | Completion claims get a second check | Package a `loop-verifier` skill and require it in readiness audit | Codex skill path, audit JSON | `python3 tests/test_goal_guard.py -k loop_verifier` | Done |
| G25 | GitHub can block regressions | Add audit/package workflow file; run it after remote exists | `.github/workflows`, Actions run | GitHub check run | Done |
| G26 | Publish path is real, not imagined | Create remote, push consolidated history, open PR/release only after verification | `git remote -v`, GitHub PR/release | remote readback | Done |
| G27 | L3 has operating evidence | Run scheduled/manual loop and append evidence to run log | `loop-run-log.md`, CI logs | audit shows L3 | Done |
| G28 | The remaining engineering gaps are explicit | Register gaps by category, evidence, and next action | `LOOP.md`, `STATE.md` | `python3 tests/test_goal_guard.py -k gap_register` | Done |
| G29 | The audit output cannot hide unfinished gaps | Report unresolved gap register items and next action in audit JSON | `scripts/loop_audit.py`, audit JSON | `python3 tests/test_goal_guard.py -k unresolved_gap` | Done |
| G30 | Humans and CI use the same verifier | Add one-command local verifier and point CI at it | `scripts/loop_verify.py`, workflow | `python3 scripts/loop_verify.py` | Done |
| G31 | Adding a remote cannot falsely claim L3 | Require remote workflow run evidence before L3 | audit JSON, run log | `python3 tests/test_goal_guard.py -k remote_run_evidence` | Done |
| G32 | The workflow has loop cadence | Add scheduled trigger for future remote loop runs | workflow | `python3 tests/test_goal_guard.py -k loop_cadence` | Done |
| G33 | Users see the one-command verifier | Add `loop_verify.py` to public READMEs | README files | `python3 tests/test_goal_guard.py -k public_readmes` | Done |
| G34 | Global install includes verifier | Sync every Codex skill directory, not only the main skill | installer test | `python3 tests/test_goal_guard.py -k install_adapter_global_codex` | Done |
| G35 | Doctor catches verifier drift | Report installed `loop-verifier` path/existence/match | doctor JSON | `python3 tests/test_goal_guard.py -k verifier_skill_drift` | Done |
| G36 | Codex plugin cache uses the current package | Bump cachebuster, sync local marketplace overlay, reinstall plugin cache | doctor JSON, cache files | `python3 scripts/loop_verify.py` + cache file readback | Done |

## Readiness Levels

| Level | Meaning | Required signals |
| --- | --- | --- |
| L1 | report-only | state file, loop config, budget, run log, triage prompt |
| L2 | assisted-with-verifier | L1 plus completion matrix and packaged independent verifier |
| L3 | remote-ci-activity | L2 plus GitHub remote, workflow checks, and remote CI readback evidence |

## Engineering Gap Register

| Gap | Current state | Missing for loop-engineering parity | Next action |
| --- | --- | --- | --- |
| remote-ci | GitHub remote exists and Actions run `28239087462` passed for `b94dcc92102a23d27afb2b0d9a2bb48e56e8d388` | None for L3 remote CI evidence | Resolved: keep run URL/status in `loop-run-log.md` |
| maker-checker | Branch `codex/g42-maker-checker` ran in linked worktree and `python3 scripts/loop_verify.py` passed for commit `51134ff` | None for maker-checker separation evidence | Resolved: keep branch/worktree/verifier evidence in `loop-run-log.md` |
| run-evidence | `loop-run-log.md` has repeated timestamped runs with outcomes and audit signal `repeatedRunEvidence=true` | None for repeated local run evidence | Resolved: keep two or more JSON-line run records with outcomes |
| distribution | Pushed source `b94dcc92102a23d27afb2b0d9a2bb48e56e8d388` validates and installs into isolated `CODEX_HOME`; doctor matched installed skills to cloned source | None for pushed-source distribution verification | Resolved: keep clone/install/doctor evidence in `loop-run-log.md` |
| connectors | GitHub connector readback works for `wozaitianwai/goal-matrix-iterative-delivery`; write tools exist but no PR/issue/comment/release action is requested | None for current loop; connector writes need explicit user-approved PR/issue/comment/release task | Resolved: defer connector writes until an acting remote task exists |
| governance | `scripts/check_governance.py` is wired into `scripts/loop_verify.py` and CI to block sensitive paths or publish actions without approval | None for local/CI governance gate evidence | Resolved: keep policy, tests, and verifier output together |

## Scope

- Watch plugin package readiness, adapter drift, installed Codex skill drift, and release blockers.
- Do not auto-edit source files during L1.
- Do not auto-push or publish without explicit human approval.

## Human Gates

- Any write to global Codex config or marketplace files.
- Any hook trust change.
- Any GitHub remote creation, push, release, or npm publication.
- Any auto-fix, workflow automation, or remote publication.

## Worktrees

- L1 does not require worktrees.
- L2 fix attempts must use one isolated worktree per fix and a separate verifier before PR or merge.

## Budget

- Max runs/day: 1 manual package triage run.
- Max tokens/day: 100k.
- Max sub-agent spawns/run: 0 in L1.
- Kill switch: set `Loop paused: true` in `STATE.md`.

## Observability

- `STATE.md` is the current state spine.
- `loop-run-log.md` records every loop run.
- `loop-budget.md` records cost limits and pause rules.

## Next Loop

No unresolved loop-engineering gaps remain in the current matrix.
