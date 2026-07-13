# Codex Adapter

Codex is the only lifecycle adapter wired in this package.

## Install From GitHub

```bash
codex plugin marketplace add https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git --ref v0.1.14-codex.2
codex plugin add goal-matrix-iterative-delivery@goal-matrix-github
```

Use the pinned release tag for reproducible installs. Use the moving development branch only when testing unreleased changes.
The marketplace commands above are the only supported global install path. `install_adapter.py` is project-only and never writes `$CODEX_HOME/skills`.

Trust the plugin hooks in Codex Desktop, then restart Codex once.

## Initialize One Project

```bash
python3 scripts/install_adapter.py codex --target /path/to/project
```

Project initialization writes `.goal-matrix/` state only. It does not edit Codex config.

To also enforce publish policy for shell or manual pushes:

```bash
python3 scripts/install_adapter.py codex --target /path/to/project --install-git-hook
```

If an unmanaged `pre-push` already exists, the installer chains it once from the sibling `pre-push.goal-matrix.previous`. A managed stale/broken wrapper is refreshed in place when the command is rerun. Use `goal_guard.py doctor --root .` to read `prePushHookState` and the effective path, including custom `core.hooksPath` repositories.

## Files

- Root plugin manifest: plugin metadata and hook path.
- `adapters/codex/hooks/codex-lifecycle-hooks.json`: lifecycle hook wiring.
- `adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md`: skill entry point.
- `core/goal_guard.py`: shared guard, publish gate, and text audit executable.

The adapter stays thin. Workflow rules belong in `core/protocol.md`; Codex files only package those rules for Codex.

Lifecycle hooks inject context and can block unsafe publish actions. A visible Codex goal still requires the agent to call `create_goal`.
Checkpoint promotes the next goal in state; the runtime still has to continue execution.

## Project Notifications

The packaged `pi.extensions` entry loads `pi-extension/index.js`, which registers `/goal-notify`. It uses `ctx.ui.notify` for Codex popup notifications; it does not send chat messages for notification status.

Project initialization creates notification settings and gitignores the local secret override file. Tracked config may define common webhook payload presets, but it cannot enable delivery or select the URL source. Opt in through `notifications.local.json` or `GOAL_MATRIX_WEBHOOK_URL`.

## Local Package Check

```bash
python3 scripts/validate_plugin_package.py --root .
python3 core/goal_guard.py doctor --root .
python3 core/goal_guard.py audit --root .
```

Internal docs:

- Operations, migration, uninstall, and debug: `docs/operations.md`.
- Workflow examples: `docs/examples.md`.
- Threat model and enforcement boundaries: `docs/threat-model.md`.
