# Changelog

## v0.1.1-codex.1 - 2026-06-29

- Pin Codex plugin marketplace install instructions to `v0.1.1-codex.1` instead of a moving branch.
- Document the release checklist needed before publishing an install ref.

### Release checklist

- Create the Git tag `v0.1.1-codex.1` from the verified, squashed release commit.
- Include validation output and package checksum notes in the GitHub release notes.
- Verify the Codex plugin marketplace install command uses `--ref v0.1.1-codex.1`.
- Reinstall from that tag, trust hooks, restart Codex, and run package validation before announcing the release.
