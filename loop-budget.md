# Loop Budget - Goal Matrix Delivery

## Daily Limits

| Loop | Max runs/day | Max tokens/day | Max sub-agent spawns/run |
| --- | --- | --- | --- |
| Package Triage | 1 | 100k | 0 |

## Kill Switch

Set `Loop paused: true` in `STATE.md`.

## On Budget Exceed

1. Stop the current loop.
2. Append an `escalated` entry to `loop-run-log.md`.
3. Ask for human approval before continuing.

## L2 Gate

Do not enable auto-fix, worktree execution, or scheduled workflows until a verifier and remote CI target exist.
