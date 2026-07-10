# Changelog

## v0.1.12-codex.1 - 2026-07-10

- Harden hook execution and notification egress, fail closed on invalid policy, and keep structured JSON goal state authoritative over bounded Markdown projections.
- Require trusted current-head GitHub Actions context for L3, run the shared verifier across Python 3.10/3.12/3.14, and preserve verified checkpoint history through guarded feature-branch publication.
- Split policy, publish, projection, state, audit, gate, native-hook, and verification domains out of `goal_guard.py`, and make the marketplace the sole global install path.
- Publish the completed remediation under plugin version `0.1.12+codex.20260710112811` and pin Codex marketplace installation to `v0.1.12-codex.1`.

## v0.1.11-codex.2 - 2026-07-10

- Reissue `v0.1.11` after making the direct GitHub Actions Python test runner hermetic: fixtures clear inherited `GITHUB_*` variables and inject only the CI context they intend to test.
- Keep `v0.1.11-codex.1` immutable as the failed-CI tag; publish the corrected plugin under version `0.1.11+codex.20260710005948`.
- Pin Codex plugin marketplace install instructions to `v0.1.11-codex.2`.

## v0.1.11-codex.1 - 2026-07-10

- Publish the governance remediation: JSON-owned goal state and generated Markdown projection, current-head L3 CI enforcement, actor-scoped complete-range governance, and package runtime-closure validation under plugin version `0.1.11+codex.20260710005049`.
- Add fail-closed explicit governance ranges, checkpoint verification writeback, and hermetic verifier tests so release evidence cannot be bypassed by stale metadata or runner environment leakage.
- Pin Codex plugin marketplace install instructions to `v0.1.11-codex.1`.

## v0.1.10-codex.1 - 2026-07-09

- Publish committed `Goal-Matrix-Approval:` trailer support so remote CI can verify governance-approved release commits without embedding local approval env in the workflow, under plugin version `0.1.10+codex.20260709231027`.
- Supersede `v0.1.9-codex.1`, whose remote CI run started before complete governance approval evidence was available to the runner.
- Pin Codex plugin marketplace install instructions to `v0.1.10-codex.1`.

## v0.1.9-codex.1 - 2026-07-09

- Publish the archive trust-boundary docs, L3 remote-evidence freshness boundary, native pre-push enforcement boundary, and sensitive runtime path governance guardrails under plugin version `0.1.9+codex.20260709230213`.
- Pin Codex plugin marketplace install instructions to `v0.1.9-codex.1`.

## v0.1.8-codex.2 - 2026-07-09

- Reissue v0.1.8 with CI-stable friction-budget tests for fresh GitHub runner checkouts under plugin version `0.1.8+codex.20260709213513`.
- Pin Codex plugin marketplace install instructions to `v0.1.8-codex.2`.

## v0.1.8-codex.1 - 2026-07-09

- Publish the first `goal_guard.py` verification subdomain split, CI matrix/lint/PR gate hardening, and compound active verification evidence fix under plugin version `0.1.8+codex.20260709212827`.
- Pin Codex plugin marketplace install instructions to `v0.1.8-codex.1`.

## v0.1.7-codex.1 - 2026-07-09

- Publish the matrix/archive drift guardrails and next-action continuation command path under plugin version `0.1.7+codex.20260709210243`.
- Pin Codex plugin marketplace install instructions to `v0.1.7-codex.1`.

## v0.1.6-codex.1 - 2026-07-03

- Publish the matrix-first-response contract fix under plugin version `0.1.6+codex.20260703200323`.
- Pin Codex plugin marketplace install instructions to `v0.1.6-codex.1`.

## v0.1.5-codex.1 - 2026-07-02

- Publish the promote-handoff fixes under plugin version `0.1.5+codex.20260702102020`.
- Pin Codex plugin marketplace install instructions to `v0.1.5-codex.1`.

## v0.1.4-codex.1 - 2026-07-01

- Publish the loop self-evolution guardrails under plugin version `0.1.4+codex.20260701105857`.
- Pin Codex plugin marketplace install instructions to `v0.1.4-codex.1`.

## 0.1.3+codex.20260630011248 - 2026-06-30

- Bump the plugin/package version after slimming the public README pair, Codex skill prompt, and loop state docs.
- Keep install docs pinned to the latest released tag `v0.1.2-codex.1`; this entry records the pushed package version, not a new release tag.

## v0.1.2-codex.1 - 2026-06-29

- Publish the static-review guardrail fixes under plugin version `0.1.2+codex.20260629215745`.
- Pin Codex plugin marketplace install instructions to `v0.1.2-codex.1`.
- Local tag readback: `v0.1.2-codex.1` resolves to commit `7507b330e36fe9e2ebc2dcfa60121fb5fb470651`.

## v0.1.1-codex.1 - 2026-06-29

- Pin Codex plugin marketplace install instructions to `v0.1.1-codex.1` instead of a moving branch.
- Document the release checklist needed before publishing an install ref.
- Local tag readback: `v0.1.1-codex.1` resolves to commit `21498b349b29dcbc4bff726d9d4a393758afe201`.

### Release checklist

- Create the Git tag `v0.1.1-codex.1` from the verified, squashed release commit.
- Include validation output and package checksum notes in the GitHub release notes.
- Verify the Codex plugin marketplace install command uses `--ref v0.1.1-codex.1`.
- Reinstall from that tag, trust hooks, restart Codex, and run package validation before announcing the release.
