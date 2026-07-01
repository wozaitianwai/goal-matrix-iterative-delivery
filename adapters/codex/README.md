# Codex Adapter

Codex is the only lifecycle adapter wired in this package.

## Install From GitHub

```bash
codex plugin marketplace add https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git --ref v0.1.4-codex.1
codex plugin add goal-matrix-iterative-delivery@goal-matrix-github
```

Use the pinned release tag for reproducible installs. Use the moving development branch only when testing unreleased changes.

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

If `.git/hooks/pre-push` already exists, the installer chains it from `.git/hooks/pre-push.goal-matrix.previous`. To restore the original hook, move that file back to `.git/hooks/pre-push`.

## Files

- Root plugin manifest: plugin metadata and hook path.
- `adapters/codex/hooks/codex-lifecycle-hooks.json`: lifecycle hook wiring.
- `adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md`: skill entry point.
- `core/goal_guard.py`: shared guard, publish gate, and text audit executable.

The adapter stays thin. Workflow rules belong in `core/protocol.md`; Codex files only package those rules for Codex.

Lifecycle hooks inject context and can block unsafe publish actions. A visible Codex goal still requires the agent to call `create_goal`.

## Project Notifications

The packaged `pi.extensions` entry loads `pi-extension/index.js`, which registers `/goal-notify`. It uses `ctx.ui.notify` for Codex popup notifications; it does not send chat messages for notification status.

Project initialization creates notification settings and gitignores the local secret override file. Common webhook payload presets are available through `/goal-notify templates`; enable webhook delivery in project config and keep real URLs in the local override file or `GOAL_MATRIX_WEBHOOK_URL`.

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
