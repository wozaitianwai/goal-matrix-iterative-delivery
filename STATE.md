# Loop State - Goal Matrix Delivery

Last run: 2026-07-10 (scheme A local remediation; machine goal status is in `.goal-matrix/state.json`)
Loop paused: false

## High Priority

- Keep the plugin package installable, auditable, and verifier-backed.
- Use `python3 scripts/loop_verify.py` before checkpoint, push, or release.
- Keep local-only state out of git commits.
- Require current-head PR and CI evidence before claiming remote enforcement.

## Watch List

- Codex hook trust remains a runtime boundary.
- `create_goal` is required for visible Codex goals.
- STATE.md is a human operational note; machine goal status stays in `.goal-matrix/state.json`.
- LOOP.md holds the stable loop contract; run evidence stays in `loop-run-log.md`.
- The marketplace is the only global plugin installation path; `install_adapter.py` is project-only.

## Recent Noise

- Local `.goal-matrix`, `.agents`, `.codex`, and `plugins` directories are ignored development state.

---
Run log: append entries to `loop-run-log.md`.
