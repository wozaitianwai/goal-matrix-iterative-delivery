# Loop State - Goal Matrix Delivery

Last run: 2026-06-30T00:00:00Z (G121 plugin surface slimming in progress)
Loop paused: false

## High Priority

- Keep the plugin package installable, auditable, and verifier-backed.
- Use `python3 scripts/loop_verify.py` before checkpoint, push, or release.
- Keep the G28 gap register current before claiming L3 or publishing.
- Keep local-only state out of git commits.
- Keep release, install, and CI claims tied to real readback evidence.

## Watch List

- Codex hook trust remains a runtime boundary.
- `create_goal` is required for visible Codex goals.
- STATE.md is a human-readable current-state note; machine policy stays in JSON.
- LOOP.md holds the stable loop contract; run evidence stays in `loop-run-log.md`.
- G121 intentionally skips hook/runtime simplification.

## Recent Noise

- Local `.goal-matrix`, `.agents`, `.codex`, and `plugins` directories are ignored development state.

---
Run log: append entries to `loop-run-log.md`.
