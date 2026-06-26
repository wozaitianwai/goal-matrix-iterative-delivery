# Codex Adapter

Codex is the first fully wired host adapter.

## Install

```bash
python3 scripts/install_adapter.py codex --scope global
```

This syncs the Codex skill into `CODEX_HOME` and does not edit Codex config or marketplace files.

## Files

- `.codex-plugin/plugin.json`: Codex plugin manifest at the repository root.
- `adapters/codex/hooks/claude-codex-hooks.json`: lifecycle hook wiring.
- `adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md`: skill entry point.
- `core/goal_guard.py`: shared guard and text audit executable.

The adapter must stay thin. Workflow rules belong in `core/protocol.md`; Codex files only package those rules for Codex.

Codex is the only adapter in this package with lifecycle hook wiring. The lifecycle hook injects context only. A visible Codex goal still requires the agent to call `create_goal`.

## Local Package Check

```bash
python3 scripts/validate_plugin_package.py --root .
python3 core/goal_guard.py doctor --root .
python3 core/goal_guard.py audit --root .
```
