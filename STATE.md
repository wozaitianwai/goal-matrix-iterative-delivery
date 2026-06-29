# Loop State - Goal Matrix Delivery

Last run: 2026-06-26T13:47:23Z (G45 connector trigger verification)
Loop paused: false

## High Priority

- Keep the plugin package installable, auditable, and verifier-backed.
- Keep the G28 gap register current before claiming L3 or publishing.
- Keep the local CI gate green before push.
- Use `python3 scripts/loop_verify.py` before checkpoint, push, or release.
- Keep local-only state out of git commits.
- Keep remote CI evidence tied to real GitHub Actions run URLs before claiming L3.
- Verify distribution from pushed source or release/install readback, not local overlay/cache alone.
- Use isolated branch/worktree plus verifier output before claiming maker-checker separation.
- Keep `scripts/check_governance.py` in the local/CI verifier path before push or publish.
- Keep at least two JSON-line run records with `run_id` and `outcome` before claiming repeatable operation.
- Use GitHub connector write tools only for explicit PR/issue/comment/release tasks with user approval.

## Watch List

- Codex hook trust remains a runtime boundary.
- `create_goal` is required for visible Codex goals.
- L2 verifier is packaged; worktree automation is not enabled.
- G25/G26/G27 are complete: private GitHub repo exists, clean history is pushed, and GitHub Actions run `28239087462` passed.
- G41 distribution path is verified from pushed source `b94dcc92102a23d27afb2b0d9a2bb48e56e8d388` using isolated install and doctor readback.
- G42 maker-checker path is verified on branch `codex/g42-maker-checker` in linked worktree with `python3 scripts/loop_verify.py` passing.
- G43 governance policy is machine-owned in `loop-governance.json`; STATE.md does not repeat approval envs, path lists, or publish patterns.
- G44 repeated run evidence is machine-checked by `scripts/loop_audit.py`.
- G45 connector path is explicit: readback works, writes are deferred until an acting remote task exists.
- Audit now reports unresolved gap register items and the next external action.
- CI and local verification share `scripts/loop_verify.py`.
- L3 requires `remote-ci-readback` or `github-check-run` evidence in `loop-run-log.md`.
- Workflow has push, PR, and scheduled triggers; first remote run passed on `main`.
- Public READMEs expose `python3 scripts/loop_verify.py`.
- Global Codex install syncs every packaged Codex skill, including `loop-verifier`.
- Doctor reports installed `loop-verifier` drift.
- Codex plugin cache refreshed to `0.1.0+codex.20260626122349`.

## Recent Noise

- Local `.goal-matrix`, `.agents`, `.codex`, and `plugins` directories are ignored development state.

---
Run log: append entries to `loop-run-log.md`.
