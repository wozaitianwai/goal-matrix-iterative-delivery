# Claude Code Adapter

Claude Code support is instruction-first in this plugin version.

## Install

```bash
python3 scripts/install_adapter.py claude-code --target /path/to/project
```

This copies `adapters/claude-code/CLAUDE.md` into the target project and initializes its `.goal-matrix` state.

Claude Code does not receive the Codex lifecycle hook from this package. It follows the copied project instructions, and projects can wire the shared guard manually if their host supports command hooks.

Use the same shared guard if the host supports command hooks:

```bash
python3 core/goal_guard.py hook SessionStart
python3 core/goal_guard.py hook UserPromptSubmit
python3 core/goal_guard.py audit < draft.md
```

Keep any future Claude Code manifest under this folder and point it at `core/goal_guard.py` instead of copying guard logic.

## Local Package Check

```bash
python3 scripts/validate_plugin_package.py --root .
python3 core/goal_guard.py doctor --root .
python3 core/goal_guard.py audit --root .
```

Required protocol invariants:

- Goal Matrix Engineering Protocol
- Initialization types
- Project policy
- Active goal contract
- Development flow
- Truth source
- Checkpoint
