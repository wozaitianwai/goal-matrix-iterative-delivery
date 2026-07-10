# Governance Remediation Design

## Objective

Close the six verified governance gaps without adding a service, dependency, or second state system. The plugin must tell the truth about what it enforces locally, what only remote CI proves, and which data is authoritative.

## Decisions

### JSON state and Markdown projections

`.goal-matrix/state.json` is authoritative for goal rows, status, active goal, and ordering. Normal commands mutate in-memory JSON state and then render Markdown. Markdown may seed JSON only when no state file exists; it is never merged back during checkpoint or prune. Drift audit also rejects missing active or pending projection rows.

### Runtime path policy

Relative path normalization removes one exact `./` prefix and preserves leading dots. Structured path fields and literal shell tokens are checked against configured path patterns. Dynamic shell expansion remains outside static enforcement and is stated as a threat-model boundary; no general shell parser is added.

### L3 evidence

Local audit reports the strongest completed evidence it can read. A GitHub Actions run may supply current remote activity through trusted runner context (`GITHUB_ACTIONS`, `GITHUB_SHA`, run metadata). CI invokes the verifier with `--require-level L3`; local verification does not impersonate remote CI.

### Governance approval and diff range

A commit trailer is accepted only as a committed attestation from an actor listed in `loop-governance.json` while running in GitHub Actions. It is not accepted from arbitrary PR authors or local clean commits. CI passes explicit base/head SHAs so all commits in a push or PR are checked.

### Package closure

Package validation includes every file directly executed or imported by hooks, installer, audit, governance, and verification, plus initialization templates. Missing runtime files fail validation before installation claims are accepted.

### Human state

`STATE.md` remains human operational context and must not claim a goal is active, pending, or in progress. Machine goal status stays in `.goal-matrix/state.json`; loop audit rejects future duplicated goal-status claims.

## Error Handling

Invalid policy, invalid Git references, stale required evidence, missing runtime files, and projection drift fail closed with a specific message. Missing optional remote context keeps local audit at L2 rather than pretending to be L3.

## Verification

Each finding gets one focused RED/GREEN regression test and checkpoint. Final acceptance runs `python3 scripts/loop_verify.py`, governance readback, status/audit, and the packaged independent loop verifier contract.

## Non-Goals

- No GitHub API client or approval service.
- No cryptographic authorization claim.
- No complete shell-language parser.
- No unrelated `goal_guard.py` decomposition.
- No release, push, tag, or local plugin reinstall in this goal.
