# Operations

## Uninstall

Project state is local to `.goal-matrix/`. To remove project state, delete `.goal-matrix/` after saving any evidence you still need. To remove the optional native hook, delete `.git/hooks/pre-push`. If an earlier hook was chained, restore it with:

```bash
mv .git/hooks/pre-push.goal-matrix.previous .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

For a global Codex skill sync, remove the copied skill folders from `$CODEX_HOME/skills/goal-matrix-iterative-delivery` and `$CODEX_HOME/skills/loop-verifier`. Plugin marketplace/cache removal depends on the Codex install path; run `goal_guard.py doctor --root .` first to read back the configured paths.

## Migration

Use `python3 core/goal_guard.py doctor --root .` before changing install method. It reports plugin cache state, installed skill drift, native hook state, and visible-goal limitations.

Use `python3 core/goal_guard.py doctor --root . --fix` to recreate missing `.goal-matrix` docs, policy, notification templates, and the local notification gitignore entry. It does not overwrite existing project docs and does not install native git hooks.

After migration, run:

```bash
python3 scripts/validate_plugin_package.py --root .
python3 scripts/loop_verify.py
```

## Debug

- Missing hook output: confirm `CODEX_PLUGIN_ROOT` points at this plugin and that the hook is trusted by Codex.
- Prompt noise: check `.goal-matrix/project-policy.json`; default `triggerMode` is `narrow`, while `strict` enables broad engineering prompts.
- Policy not blocking: run `goal_guard.py doctor --fix --root .`, then test `policy-gate --root . --hook` with the tool payload.
- Push blocked: run `goal_guard.py publish-gate --root .` and inspect active goal, checkpoint evidence, worktree state, upstream, and ahead/behind count.
- Webhook silent: confirm project notifications are enabled, URL is `https://`, `allowedHosts` includes the host when configured, and the endpoint returns an OK response.
