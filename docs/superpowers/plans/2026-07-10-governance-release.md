# Governance Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish `v0.1.11-codex.1` with plugin version `0.1.11+codex.20260710005049`, then refresh the local Codex installation from that tag.

**Architecture:** Keep the existing tagged-Git-marketplace release model. Version manifests, pinned install documentation, changelog, and the release-tag regression constant move together; the release is a verified commit, annotated tag, GitHub Release, and marketplace reinstall.

**Tech Stack:** Git, GitHub CLI, Codex CLI, Python/Node project verifier.

## Global Constraints

- Preserve the existing `v<semver>-codex.1` tag convention.
- Do not change plugin behavior or marketplace files by hand.
- Push only after the full verifier and publish gate pass.

---

### Task 1: Prepare Release Metadata

**Files:**
- Modify: `package.json`
- Modify: `.codex-plugin/plugin.json`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `README.zh.md`
- Modify: `adapters/codex/README.md`
- Modify: `tests/test_goal_guard.py`

- [ ] Set both manifest versions to `0.1.11+codex.20260710005049`.
- [ ] Pin all installation docs and `RELEASE_INSTALL_TAG` to `v0.1.11-codex.1`.
- [ ] Add changelog notes for JSON SSOT, CI L3 enforcement, governance range/actor hardening, package closure, and state-boundary fixes.
- [ ] Run `python3 -m pytest tests/test_goal_guard.py -k release_install_docs -q`.

### Task 2: Verify And Commit Release Candidate

**Files:**
- Modify: files from Task 1 plus this plan

- [ ] Run `GOAL_MATRIX_APPROVED=1 python3 scripts/loop_verify.py`.
- [ ] Run `GOAL_MATRIX_APPROVED=1 python3 core/goal_guard.py publish-gate --root .` after readable release history is prepared.
- [ ] Checkpoint G165 with the full verifier and commit the release metadata with a `Goal-Matrix-Approval:` trailer.

### Task 3: Publish And Refresh Local Plugin

**Files:**
- No repository file changes

- [ ] Push `main`, create and push annotated tag `v0.1.11-codex.1`, then create the matching GitHub Release.
- [ ] Reconfigure `goal-matrix-github` to `--ref v0.1.11-codex.1`, refresh its snapshot, and reinstall `goal-matrix-iterative-delivery@goal-matrix-github`.
- [ ] Read back remote tag/release and `codex plugin list`; run `python3 core/goal_guard.py doctor --root .`.
