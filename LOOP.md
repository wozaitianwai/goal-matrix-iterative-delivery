# Loop Configuration - Goal Matrix Delivery

This repository is moving from plugin packaging toward loop-engineering parity.

## Active Loops

| Pattern | Cadence | Status | Prompt |
| --- | --- | --- | --- |
| package-triage | manual or daily | L2 assisted-with-verifier | Run `python3 scripts/loop_audit.py --root . --json`; update `STATE.md`; verifier must reject completion without evidence. |

## Loop Engineering Completion Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G23 | The repo says exactly what "loop-engineering complete" means | Add L1/L2/L3 readiness matrix and audit signals | `LOOP.md`, audit JSON | `python3 scripts/loop_audit.py --root . --json` | Done |
| G24 | Completion claims get a second check | Package a `loop-verifier` skill and require it in readiness audit | Codex skill path, audit JSON | `python3 tests/test_goal_guard.py -k loop_verifier` | Done |
| G25 | GitHub can block regressions | Add audit/package workflow file; run it after remote exists | `.github/workflows`, Actions run | GitHub check run | Local gate done; blocked: no remote run |
| G26 | Publish path is real, not imagined | Create remote, push consolidated history, open PR/release only after verification | `git remote -v`, GitHub PR/release | remote readback | Blocked: no GitHub repo |
| G27 | L3 has operating evidence | Run scheduled/manual loop and append evidence to run log | `loop-run-log.md`, CI logs | audit shows L3 | Pending after G25-G26 |
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
| L3 | remote-ci-activity | L2 plus GitHub remote, workflow checks, and repeated loop activity |

## Engineering Gap Register

| Gap | Current state | Missing for loop-engineering parity | Next action |
| --- | --- | --- | --- |
| remote-ci | Workflow file has push/PR/schedule triggers; `git remote -v` is empty, so no CI readback | GitHub remote and Actions run evidence | Add remote, push, read check result |
| maker-checker | Packaged verifier and one-command check exist; worktree isolation still waits for PR/push | Separate worktree or fresh verifier run before PR/push | Add when remote branch exists |
| run-evidence | Manual run log exists; no `remote-ci-readback` evidence | Remote workflow pass recorded in run log | Append evidence after GitHub Actions passes |
| distribution | Plugin validates locally; global install, doctor, and local Codex cache cover all Codex skills; no pushed repo, PR, release, or remote install readback | Consolidated history, remote push, release/install readback | G26 after GitHub repo exists |
| connectors | GitHub/MCP write path is not configured | Minimal read/comment permissions before any acting loop | Defer until remote exists |
| governance | Human gates exist; denylist/allowlist is still prose only | CI-enforced gates for sensitive paths and publish actions | Add with CI workflow |

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

Add a GitHub remote, push, and read back the workflow result.
