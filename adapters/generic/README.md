# Generic Adapter

Generic instruction hosts can use `adapters/generic/AGENTS.md` as a copyable rule file.

## Install

```bash
python3 scripts/install_adapter.py generic --target /path/to/project
```

This copies `adapters/generic/AGENTS.md` into the target project and initializes its `.goal-matrix` state.

This adapter has no runtime hook. The host should read the rule file before implementation and use `core/goal_guard.py audit` as an optional manual check.

## Local Package Check

```bash
python3 scripts/validate_plugin_package.py --root .
python3 core/goal_guard.py doctor --root .
python3 core/goal_guard.py audit --root .
```
