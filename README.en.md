# Goal Matrix Iterative Delivery

> English | [中文](README.md)

![Goal Matrix Delivery icon](assets/icon.png)

**Goal Matrix Iterative Delivery** is an engineering workflow plugin for Codex and common agent tools. It turns broad requests into an executable goal matrix, advances one active goal at a time, and requires real evidence before completion.

## Install

### Project Install

Install rules into one project for Cursor, Claude Code, or a generic agent host:

```bash
python3 scripts/install_adapter.py cursor --target /path/to/project
python3 scripts/install_adapter.py claude-code --target /path/to/project
python3 scripts/install_adapter.py generic --target /path/to/project
```

These commands install the matching project rule and initialize the target project's goal matrix.

### Global Codex

Sync the Codex skill into the current user's Codex environment:

```bash
python3 scripts/install_adapter.py codex --scope global
```

This command syncs skill files only. It does not silently edit Codex config or marketplace files.

### Validate Package

```bash
python3 scripts/validate_plugin_package.py --root .
```

### One-command Engineering Check

```bash
python3 scripts/loop_verify.py
```

## Loop Model

```text
initialize project -> classify work -> design goals -> pass design gate -> execute slice -> pass review gate -> checkpoint -> next loop
```

The rules are intentionally small:

- Execute one active goal per loop.
- Every goal names its boundary, skipped scope, truth source, and verification.
- Reuse existing code and host capabilities before adding machinery.
- Hooks guide and constrain; they do not execute hidden work or push automatically.

## Visible Codex Goal

Lifecycle hooks inject goal-matrix context into the model; they do not create the visible Codex sidebar goal by themselves. When a visible goal is needed, the Codex agent must explicitly call `create_goal`.

## Tool Adapter Boundaries

| Tool | Install path | Runtime boundary |
| --- | --- | --- |
| Codex | Global Codex command | Skill and lifecycle hooks inject context; visible goals still require the agent to call `create_goal` |
| Cursor | Project Install command | Project rules apply; no Codex runtime hook |
| Claude Code | Project Install command | Project instructions apply; no Codex runtime hook |
| Generic | Project Install command | Generic rules apply; no Codex runtime hook |

## Initialization Types

| Type | Use when |
| --- | --- |
| `new-project` | Starting a project or feature from scratch |
| `iteration` | Iterating on an existing project |
| `bugfix` | Fixing a failure, error, or unexpected behavior |
| `legacy-baseline` | Taking over an unclear legacy project |

## Boundary

This plugin is not a background runner or a project management system. It does one thing: make engineering loops explicit, with evidence, scope, and a next step for each small goal.
