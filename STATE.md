# Loop State - Goal Matrix Delivery

Last run: 2026-06-26T11:03:38Z (manual G36 plugin cache refresh)
Loop paused: false

## High Priority

- Keep the plugin package installable, auditable, and verifier-backed.
- Keep the G28 gap register current before claiming L3 or publishing.
- Keep the local CI gate green before push.
- Use `python3 scripts/loop_verify.py` before checkpoint, push, or release.
- Keep local-only state out of git commits.
- Create a GitHub remote before any push or release workflow.

## Watch List

- Codex hook trust remains a runtime boundary.
- `create_goal` is required for visible Codex goals.
- L2 verifier is packaged; worktree automation is not enabled.
- G25 local workflow is present; G25 remote run and G26 remain blocked until a GitHub repo or remote URL exists.
- Audit now reports unresolved gap register items and the next external action.
- CI and local verification share `scripts/loop_verify.py`.
- L3 requires `remote-ci-readback` or `github-check-run` evidence in `loop-run-log.md`.
- Workflow has push, PR, and scheduled triggers, but no remote run exists yet.
- Public READMEs expose `python3 scripts/loop_verify.py`.
- Global Codex install syncs every packaged Codex skill, including `loop-verifier`.
- Doctor reports installed `loop-verifier` drift.
- Codex plugin cache refreshed to `0.1.0+codex.20260626105959`.

## Recent Noise

- Local `.goal-matrix`, `.agents`, `.codex`, and `plugins` directories are ignored development state.

---
Run log: append entries to `loop-run-log.md`.
