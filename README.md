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
codex plugin marketplace add https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git --ref v0.1.1-codex.1
codex plugin add goal-matrix-iterative-delivery@goal-matrix-github
```

Use a tagged release for reproducible installs. The moving development branch is only for unreleased testing.

Then trust the plugin hooks in Codex Desktop and restart Codex once so the lifecycle hooks load.

## Initialize A Project

Create goal-matrix state for one project:

```bash
python3 scripts/install_adapter.py codex --target /path/to/project
```

This writes only `.goal-matrix/` files in the target project. It does not edit Codex config.

To also enforce publish policy for shell or manual pushes, install the native git hook:

```bash
python3 scripts/install_adapter.py codex --target /path/to/project --install-git-hook
```

## Daily Loop

```bash
printf 'fix the next bounded goal' | python3 core/goal_guard.py start --root .
python3 core/goal_guard.py status --root .
python3 core/goal_guard.py checkpoint --root . -- python3 scripts/loop_verify.py
```

`scripts/loop_audit.py --json` reports `runLogNeedsSummary` when `loop-run-log.md` grows past 500 lines; run a summary/pruning child goal before continuing long-loop work.

`.goal-matrix/project-policy.json` is the target project runtime policy source for path, command, and publish-action gates. `loop-governance.json` is only the plugin repository autonomy policy used by this repo's own CI/static governance checks. `STATE.md` is human-readable only; it must not repeat approval envs, protected paths, or publish patterns. Audit reports `stateGovernanceDuplication` when human state copies machine-owned policy values.

Fast Lane is available when there is no active goal and the request is a trivial typo, copy, or single-function edit. It keeps policy/publish gates and focused verification, but skips goal-matrix checkpointing. Protected paths, publish actions, unclear scope, or multi-file behavior changes use the normal loop.

The loop is deliberately small:

```text
initialize -> classify -> design -> execute -> review -> checkpoint -> next loop
```

## Project Notifications

Project initialization also creates optional notification settings. Enable them in the project state, then use the Codex popup command:

```bash
/goal-notify status
/goal-notify test
/goal-notify templates
```

The command is loaded from the packaged `pi.extensions` entry and uses Codex `ctx.ui.notify`; it is not a hook log or chat-message notification.

Webhook presets are included for generic, Slack, Discord, Feishu, DingTalk, and WeChat Work payload shapes. Enable webhook delivery in the project config and put real webhook secrets in the local notification file or `GOAL_MATRIX_WEBHOOK_URL`; the local file is added to `.gitignore`.

## What The Hooks Enforce

- State the boundary, skipped scope, truth source, and verification before editing.
- Execute one active goal per loop.
- Prefer existing project code and host behavior before adding machinery.
- Block unsafe publish actions; hooks guide the agent, but they do not run hidden work or push code.

## Publish Gate

The Codex `PreToolUse` hook runs this gate before `git push` and commands matching `publishActionPatterns` such as `npm publish`, `twine upload`, and `gh release`:

```bash
python3 core/goal_guard.py publish-gate --root .
```

It fails when the worktree is dirty, an active goal is still open, checkpoint evidence is missing, upstream is missing or behind, or the branch has more than one local commit ahead of upstream. Squash or merge first, or set `GOAL_MATRIX_ALLOW_FRAGMENTED_PUSH=1` only when the user explicitly wants to preserve fragmented local commits.

The optional native `pre-push` hook runs the same gate, so direct shell pushes use the same policy. If a hook already exists, it is chained from `.git/hooks/pre-push.goal-matrix.previous`; restore it by moving that file back to `.git/hooks/pre-push`.

## Package Checks

```bash
python3 scripts/validate_plugin_package.py --root .
python3 scripts/loop_verify.py
```

## Open Source

This project is open source under the [MIT License](LICENSE). You may use, modify, and distribute it within that license.

## Boundaries

Lifecycle hooks inject context into the model. They do not create the visible Codex sidebar goal by themselves. When a visible goal is needed, the agent must explicitly call `create_goal`.

Codex is the only lifecycle adapter in this package. Add another adapter only when this repo contains real hook wiring for that host.

This plugin is not a background job system and not a project management platform. It makes engineering loops explicit and verifiable inside Codex.
