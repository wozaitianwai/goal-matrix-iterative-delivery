# Governance Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the three P1 and three P2 governance findings with one verified checkpoint per bounded child goal.

**Architecture:** Keep the Python standard-library runtime. Make JSON-to-Markdown flow one-way, make CI requirements explicit inputs, and strengthen existing validators instead of introducing new services or frameworks.

**Tech Stack:** Python 3.10+, stdlib, pytest, Git, GitHub Actions YAML, Markdown/JSON.

## Global Constraints

- No new dependency, service, database, queue, or plugin layer.
- One active child goal at a time; each task uses RED -> GREEN -> verifier -> checkpoint commit.
- `.goal-matrix/state.json` is authoritative; projections never overwrite it during normal operation.
- Local checks never self-assert remote CI success.
- Release, push, tag, and marketplace refresh are outside this plan.

---

### Task 1: JSON SSOT Projection

**Files:**
- Modify: `core/goal_guard.py`
- Test: `tests/test_goal_guard.py`

**Interfaces:**
- Consumes: existing `read_goal_matrix`, `write_state_json`, `render_goal_matrix`, checkpoint flow.
- Produces: state-first goal mutation and a visible projection rendered from state rows.

- [ ] Add `test_state_json_remains_authoritative_across_checkpoint` and `test_audit_rejects_missing_pending_projection_row`.
- [ ] Run `python3 -m pytest tests/test_goal_guard.py -k 'state_json_remains_authoritative or missing_pending_projection' -q`; expect failures showing Markdown wins or a missing row is ignored.
- [ ] Remove normal Markdown-to-state merging, update start/checkpoint to pass explicit goal data, and render visible rows from state.
- [ ] Re-run the focused tests, then `python3 scripts/loop_verify.py`; expect success.
- [ ] Checkpoint G156 and commit `Fix JSON goal state authority`.

### Task 2: Runtime Path Policy

**Files:**
- Modify: `core/goal_guard.py`
- Modify: `docs/threat-model.md`
- Test: `tests/test_goal_guard.py`

**Interfaces:**
- Consumes: `normalize_policy_path`, payload command collection, `policy_path_matches`.
- Produces: preserved dotfiles and literal command-token path candidates.

- [ ] Add focused tests for relative `.env`, `./.env`, and `sed -i ... .env` hook payloads.
- [ ] Run `python3 -m pytest tests/test_goal_guard.py -k 'policy_gate_dotfile or policy_gate_shell_literal_path' -q`; expect current bypasses to fail assertions.
- [ ] Replace broad `lstrip` with exact prefix removal and check literal shell tokens against configured policy patterns.
- [ ] Document dynamic expansion as outside static enforcement; run focused tests and full verifier.
- [ ] Checkpoint G157 and commit `Harden runtime path policy matching`.

### Task 3: Enforced L3 Remote Evidence

**Files:**
- Modify: `scripts/loop_audit.py`
- Modify: `scripts/loop_verify.py`
- Modify: `.github/workflows/loop-audit.yml`
- Modify: `LOOP.md`
- Test: `tests/test_goal_guard.py`

**Interfaces:**
- Produces: `--require-level`, current GitHub Actions context signal, CI invocation requiring L3.

- [ ] Add tests proving stale local evidence is rejected when L3 is required and matching GitHub Actions context satisfies current remote activity.
- [ ] Run focused tests and observe RED.
- [ ] Add required-level CLI flow, validate runner SHA against Git HEAD, and invoke CI with `--require-level L3`.
- [ ] Run focused tests and local verifier; simulate trusted CI context for the L3-required check.
- [ ] Checkpoint G158 and commit `Enforce L3 evidence in remote CI`.

### Task 4: Trusted Governance Range

**Files:**
- Modify: `scripts/check_governance.py`
- Modify: `loop-governance.json`
- Modify: `.github/workflows/loop-audit.yml`
- Modify: `docs/threat-model.md`
- Test: `tests/test_goal_guard.py`

**Interfaces:**
- Produces: explicit base/head comparison and actor-scoped committed attestation.

- [ ] Add tests for an untrusted actor trailer, a configured GitHub actor trailer, and a sensitive file changed before the final commit in an explicit range.
- [ ] Run focused tests and observe RED.
- [ ] Add `--base/--head`, use the complete diff range, and require `GITHUB_ACTIONS=true` plus configured actor for committed attestation.
- [ ] Pass event SHAs from workflow; run focused tests and governance check with explicit user approval env locally.
- [ ] Checkpoint G159 and commit `Scope governance approval and CI ranges`.

### Task 5: Package Runtime Closure

**Files:**
- Modify: `scripts/validate_plugin_package.py`
- Test: `tests/test_goal_guard.py`

**Interfaces:**
- Produces: complete required-runtime asset list.

- [ ] Add a copied-package test that removes `core/goal_guard.py`, `core/goal_verification.py`, and one template in turn and expects validation failure.
- [ ] Run `python3 -m pytest tests/test_goal_guard.py -k package_validator_requires_runtime_closure -q`; observe RED.
- [ ] Add the directly executed/imported scripts and templates to package requirements.
- [ ] Run focused tests, package validator, and full verifier.
- [ ] Checkpoint G160 and commit `Validate complete plugin runtime package`.

### Task 6: Human State Boundary

**Files:**
- Modify: `scripts/loop_audit.py`
- Modify: `STATE.md`
- Modify: `LOOP.md`
- Test: `tests/test_goal_guard.py`

**Interfaces:**
- Produces: a stale goal-status claim signal and human-only state wording.

- [ ] Add a fixture where `STATE.md` says `G121 ... in progress` and assert audit blocks it.
- [ ] Run `python3 -m pytest tests/test_goal_guard.py -k state_goal_claim -q`; observe RED.
- [ ] Reject active/pending/in-progress goal claims in `STATE.md`, remove the stale claim, and point machine status to `.goal-matrix/state.json`.
- [ ] Run focused tests and full verifier.
- [ ] Checkpoint G161 and commit `Keep human state free of machine goal status`.

### Task 7: Final Independent Acceptance

**Files:**
- Inspect: all task diffs and `.goal-matrix` evidence.

- [ ] Run `python3 scripts/loop_verify.py` and `GOAL_MATRIX_APPROVED=1 python3 scripts/check_governance.py --root .`.
- [ ] Run `python3 core/goal_guard.py audit --root .`, `status`, and `doctor`.
- [ ] Apply the packaged loop-verifier contract to the complete diff; reject if any finding lacks fresh evidence.
- [ ] Confirm G155-G161 are Done, no pending goal remains, and report that release/push was intentionally skipped.
