# Threat Model

Goal Matrix Iterative Delivery is a Codex lifecycle adapter and workflow guardrail. It is not a security sandbox, an authorization system, or a background project-management service.

## What It Enforces

- `PreToolUse` runs `policy-gate` before normal tool execution. It can block tool payloads that target `.goal-matrix/project-policy.json` `immutablePaths`, require `GOAL_MATRIX_APPROVED` or a scoped payload approval for `approvalRequiredPaths`, and block configured `protectedCommands`.
- `policy-gate --debug` prints the paths and commands recognized from a hook payload so fixture updates can be checked against the real parser surface.
- `PreToolUse` runs `publish-gate` before `git push` and before commands matching `.goal-matrix/project-policy.json` `publishActionPatterns`. It checks upstream state, local ahead/behind count, clean worktree state, open active goal state, and current checkpoint evidence.
- `Stop` preserves the review gate exit code. A failed review gate blocks the lifecycle hook instead of being swallowed by `exit 0`.
- `checkpoint` rejects metadata-only proof such as `goal_guard.py status` and records verification output under `.goal-matrix/evidence/`.
- The optional native `pre-push` hook runs the same `publish-gate` for shell pushes and chains an existing hook from `.git/hooks/pre-push.goal-matrix.previous`.

## What It Does Not Enforce

- It does not prevent a user or process from disabling hooks, editing files outside Codex, changing git history, or bypassing the optional native hook.
- It does not create the visible Codex sidebar goal by itself; the agent still has to call `create_goal`.
- It does not sandbox shell commands, filesystem writes, network access, secrets, package scripts, or third-party tools.
- It does not prove product correctness. Verification commands must still be chosen to test the actual code, docs, API, database, log, browser, or release behavior.
- It does not replace repository permissions, branch protection, CI protection, secret scanning, code review, or deployment approval.

## Fail-Open Boundaries

- Hooks fail open when `CODEX_PLUGIN_ROOT` is missing or does not point at this plugin. This avoids blocking unrelated projects from a stale or foreign cwd.
- `policy-gate` fails open when `.goal-matrix/project-policy.json` is missing, invalid, or not initialized. Run `goal_guard.py doctor --fix --root .` or `goal_guard.py init --root .` before relying on project policy.
- `publish-gate --hook` ignores payloads that are neither `git push` nor configured `publishActionPatterns`. It is a publish guard, not a general command firewall.
- Native `pre-push` protection is optional and only applies after `scripts/install_adapter.py codex --target <repo> --install-git-hook`.

## Webhook Egress

- Webhook notifications are disabled by default.
- Webhook URLs must use `https://`; non-HTTPS URLs are rejected before `fetch`.
- Projects can set `allowedHosts` to restrict outbound webhook hosts.
- Webhook delivery uses an `AbortController` timeout and treats non-2xx/failed responses as failed sends.
- Payload templates should use minimal event fields. Put real webhook URLs in `GOAL_MATRIX_WEBHOOK_URL` or ignored local notification config, not in tracked files.

## Operator Controls

- Keep `.goal-matrix/project-policy.json` explicit and reviewed when enabling path or command policy.
- Treat `GOAL_MATRIX_APPROVED=1` as a short-lived local emergency override, not a persistent shell default. Payload approvals should bind the active goal, path, future expiry, and reason.
- Keep CI and branch protection authoritative for team workflows. This plugin provides local and lifecycle guardrails; it is not the final trust boundary.
