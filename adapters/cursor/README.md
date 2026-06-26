# Cursor Adapter

Cursor support is instruction-only in this plugin version.

## Install

```bash
python3 scripts/install_adapter.py cursor --target /path/to/project
```

This copies `adapters/cursor/goal-matrix-iterative-delivery.mdc` into the target project's `.cursor/rules/` directory and initializes its `.goal-matrix` state.

Cursor cannot run this plugin's hook gate directly, so enforcement is advisory unless the project adds its own command or pre-commit checks.

## Local Package Check

```bash
python3 scripts/validate_plugin_package.py --root .
python3 core/goal_guard.py doctor --root .
python3 core/goal_guard.py audit --root .
```
