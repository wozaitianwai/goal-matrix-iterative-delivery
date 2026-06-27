# Codex Adapter

Codex is the only lifecycle adapter wired in this package.

## Install From GitHub

```bash
codex plugin marketplace add https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git --ref main
codex plugin add goal-matrix-iterative-delivery@goal-matrix-github
```

Trust the plugin hooks in Codex Desktop, then restart Codex once.

## Initialize One Project

```bash
python3 scripts/install_adapter.py codex --target /path/to/project
```

Project initialization writes `.goal-matrix/` state only. It does not edit Codex config.

## Files

- Root plugin manifest: plugin metadata and hook path.
- `adapters/codex/hooks/codex-lifecycle-hooks.json`: lifecycle hook wiring.
- `adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md`: skill entry point.
- `core/goal_guard.py`: shared guard, publish gate, and text audit executable.

The adapter stays thin. Workflow rules belong in `core/protocol.md`; Codex files only package those rules for Codex.

Lifecycle hooks inject context and can block unsafe publish actions. A visible Codex goal still requires the agent to call `create_goal`.

## Local Package Check

```bash
python3 scripts/validate_plugin_package.py --root .
python3 core/goal_guard.py doctor --root .
python3 core/goal_guard.py audit --root .
```
