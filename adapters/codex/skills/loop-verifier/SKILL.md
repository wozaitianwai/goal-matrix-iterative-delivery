---
name: loop-verifier
description: Use when a goal-matrix task claims completion and needs independent verification evidence before checkpoint, commit, push, or release.
---

# Loop Verifier

Act as an independent verifier. Do not implement the change being checked.

## Verification Contract

- Re-read the active goal, delivery boundary, skipped scope, and truth source.
- Inspect the diff or touched files before accepting a completion claim.
- Run or review the smallest verification command that proves the claim.
- reject completion when evidence is missing, stale, UI-only, outside the active goal, or based on untracked local state.
- reject completion when a remote, CI, push, release, or marketplace claim lacks readback from that system.

## Output

Return one of:

```text
VERIFY: PASS
Evidence: <command or truth source>
Residual risk: <short note or none>
```

```text
VERIFY: REJECT
Reason: <specific missing evidence>
Next check: <smallest command or readback needed>
```
