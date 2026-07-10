<p align="center">
  <img src="assets/icon.png" alt="Goal Matrix Delivery icon" width="96" height="96">
</p>

# Goal Matrix Iterative Delivery

> English | [中文](README.zh.md)

Keep Codex work honest: one active slice, one truth source, one proof before handoff.

## Install

Install the GitHub repository as a Codex plugin source:

```bash
codex plugin marketplace add https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git --ref v0.1.11-codex.2
codex plugin add goal-matrix-iterative-delivery@goal-matrix-github
```

Use a tagged release for reproducible installs. The moving development branch is only for unreleased testing.

Trust the plugin hooks in Codex Desktop and restart once.

## Initialize A Project

Create project-local state:

```bash
python3 scripts/install_adapter.py codex --target /path/to/project
```

Optional native push guard:

```bash
python3 scripts/install_adapter.py codex --target /path/to/project --install-git-hook
```

Setup writes `.goal-matrix/` files only. With `--install-git-hook`, an unmanaged native hook is preserved once as the sibling `pre-push.goal-matrix.previous`; rerunning the command refreshes a managed stale/broken wrapper in place. `doctor` reports `absent`, `unmanaged`, `current`, `stale`, or `broken` and never installs the hook implicitly.

## Daily Loop

```bash
python3 core/goal_guard.py start --root . <<'JSON'
{
  "userOutcome": "Fix the next bounded goal",
  "engineeringSlice": "Change one verified behavior",
  "initializationType": "iteration",
  "policyImpact": "none",
  "touchedPaths": ["src/module.py"],
  "deliveryBoundary": "this behavior only",
  "skipped": "unrelated work",
  "truthSource": "tests",
  "verification": "python3 -m unittest",
  "developmentFlow": "inspect -> failing check -> implement -> verify -> checkpoint"
}
JSON
python3 core/goal_guard.py status --root .
python3 core/goal_guard.py checkpoint --root . -- python3 scripts/loop_verify.py
```

Plain text input creates a blocked draft. Use the structured contract above before implementation.

The loop stays small:

```text
initialize -> classify -> design -> execute -> review -> checkpoint -> next loop
```

Broad prompts can create pending child goals, but the main thread still verifies and checkpoints one child goal at a time. Fast Lane is only for trivial typo, copy, or single-function edits with no active goal.

Hooks do not create the visible Codex sidebar goal; call `create_goal` when visible tracking matters.
Checkpoint promotes the next goal in state; the runtime still has to continue execution.

## Runtime Boundaries

- `.goal-matrix/project-policy.json` is the target project runtime policy source.
- `loop-governance.json` is plugin repository autonomy for this repo's own checks.
- `.goal-matrix/state.json` owns the active contract, matrix state, and Done-row retention; every state write regenerates the visible and archive Markdown projections, and `audit` checks both.
- Pushes and pull requests run the shared verifier once on Python 3.10, 3.12, and 3.14; each matrix leg must establish L3 from its current GitHub Actions context.
- Hooks guide/block; they do not run hidden work or push code.
- Codex lifecycle adapter is the only lifecycle adapter in this package.
- Codex hook enforcement covers Codex tool calls only; terminal git push requires the optional native pre-push hook.

## Publish Gate

Codex `PreToolUse` runs this gate before `git push` and configured publish commands:

```bash
python3 core/goal_guard.py publish-gate --root .
```

It fails on dirty worktrees, open active goals, missing checkpoint evidence, missing upstream, or unintegrated remote commits. Verified checkpoint commits are allowed; the gate does not impose a local commit-count limit.

## Notifications

Project setup creates optional notification settings. Use `/goal-notify status`, `/goal-notify test`, or `/goal-notify templates`. Tracked config may define popup and webhook presets, but webhook delivery requires the ignored `notifications.local.json` file or `GOAL_MATRIX_WEBHOOK_URL`.

## Package Checks

```bash
python3 scripts/validate_plugin_package.py --root .
python3 scripts/loop_verify.py
```

## Open Source

This project is open source under the [MIT License](LICENSE). You may use, modify, and distribute it within that license.

## Boundaries

UserPromptSubmit does not run `start`.

This plugin is not a background job system and not a project management platform. It only makes Codex engineering loops explicit and verifiable.
