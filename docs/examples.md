# Workflow Examples

## Bugfix

User outcome: fix one observed failure without widening scope.

Truth source: failing test, reproduction command, log line, API response, or browser state that shows the bug.

Verification: the same failing check passes after the fix, then `goal_guard.py checkpoint --root . -- <check>`.

## Legacy Refactor

User outcome: improve one legacy area while preserving behavior.

Truth source: current behavior inventory, existing tests, command output, or captured fixture before edits.

Verification: before/after behavior matches for the protected surface, and the refactor-specific test passes.

## New Feature

User outcome: ship the smallest usable feature slice.

Truth source: spec acceptance criteria plus the concrete code path, API response, UI state, or CLI output that proves the feature exists.

Verification: focused feature test or manual truth-source readback, followed by checkpoint evidence.

## Read-Only Review

User outcome: produce findings without modifying files.

Truth source: repository files, docs, tests, logs, CI output, or requested external evidence.

Verification: no worktree changes, cited file/line evidence, and explicit residual risk. Do not run write commands.
