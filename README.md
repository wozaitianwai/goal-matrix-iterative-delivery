<p align="center">
  <img src="assets/icon.png" alt="Goal Matrix Delivery icon" width="96" height="96">
</p>

# Goal Matrix Iterative Delivery

> English | [中文](README.zh.md)

Keep Codex work honest: one goal matrix, one active slice, one proof before handoff.

Use it when a request is too broad for a single edit and you need the agent to keep scope, evidence, and restart state visible.

## Why Use It

| Problem | Guardrail |
| --- | --- |
| Work expands while nobody notices | One active goal at a time |
| "Done" is claimed from vibes | Completion needs a truth source |
| Restarts lose context | Project-local `.goal-matrix/` state |
| Push history gets noisy | Publish gate requires a clean branch |

## Install

Install the GitHub repository as a Codex plugin source:

```bash
codex plugin marketplace add https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git --ref main
codex plugin add goal-matrix-iterative-delivery@goal-matrix-github
```

Then trust the plugin hooks in Codex Desktop and restart Codex once so the lifecycle hooks load.

## Initialize A Project

Create goal-matrix state for one project:

```bash
python3 scripts/install_adapter.py codex --target /path/to/project
```

This writes only `.goal-matrix/` files in the target project. It does not edit Codex config.

## Daily Loop

```bash
printf 'fix the next bounded goal' | python3 core/goal_guard.py start --root .
python3 core/goal_guard.py status --root .
python3 core/goal_guard.py checkpoint --root . -- python3 scripts/loop_verify.py
```

The loop is deliberately small:

```text
initialize -> classify -> design -> execute -> review -> checkpoint -> next loop
```

## What The Hooks Enforce

- State the boundary, skipped scope, truth source, and verification before editing.
- Execute one active goal per loop.
- Prefer existing project code and host behavior before adding machinery.
- Block unsafe publish actions; hooks guide the agent, but they do not run hidden work or push code.

## Publish Gate

The Codex `PreToolUse` hook runs this gate before `git push`:

```bash
python3 core/goal_guard.py publish-gate --root .
```

It fails when the branch has more than one local commit ahead of its upstream. Squash or merge first, or set `GOAL_MATRIX_ALLOW_FRAGMENTED_PUSH=1` when the user explicitly wants to preserve the history.

## Package Checks

```bash
python3 scripts/validate_plugin_package.py --root .
python3 scripts/loop_verify.py
```

## Boundaries

Lifecycle hooks inject context into the model. They do not create the visible Codex sidebar goal by themselves. When a visible goal is needed, the agent must explicitly call `create_goal`.

Codex is the only lifecycle adapter in this package. Add another adapter only when this repo contains real hook wiring for that host.

This plugin is not a background job system and not a project management platform. It makes engineering loops explicit and verifiable inside Codex.
