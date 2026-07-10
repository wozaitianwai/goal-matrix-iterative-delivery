#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


ADAPTERS = {
    "codex": (
        "adapters/codex/README.md",
        "adapters/codex/hooks/codex-lifecycle-hooks.json",
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
        "adapters/codex/skills/loop-verifier/SKILL.md",
    ),
}

ASSETS = (
    "package.json",
    "assets/icon.png",
    "core/goal_guard.py",
    "core/goal_native_hook.py",
    "core/goal_policy.py",
    "core/goal_publish.py",
    "core/goal_verification.py",
    "core/protocol.md",
    "core/templates/active-goal.md",
    "core/templates/checks.md",
    "core/templates/decisions.md",
    "core/templates/goal-matrix.md",
    "core/templates/loop-note.md",
    "core/templates/notifications.json",
    "core/templates/project-context.md",
    "core/templates/project-policy.json",
    "pi-extension/index.js",
    "pi-extension/package.json",
    "loop-governance.json",
    "scripts/check_governance.py",
    "scripts/install_adapter.py",
    "scripts/lint_python.py",
    "scripts/validate_plugin_package.py",
    "scripts/loop_audit.py",
    "scripts/loop_verify.py",
    "LOOP.md",
    "STATE.md",
    "loop-budget.md",
    "loop-run-log.md",
)

INSTRUCTION_FILES = (
    "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
)

INSTRUCTION_PHRASES = (
    "Goal Matrix Engineering Protocol",
    "Initialization types",
    "Project policy",
    "Active goal",
    "Development flow",
    "Truth source",
    "Checkpoint",
    "project_initialization",
    "design_gate",
    "review_gate",
    "Next loop",
    "visible Codex goal",
)


def read_json(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path}: {exc}")
        return {}


def require_file(root, rel, errors):
    path = root / rel
    if not path.is_file():
        errors.append(f"missing file: {rel}")
    return path


def require_phrase(root, rel, phrase, errors):
    path = require_file(root, rel, errors)
    if path.is_file() and phrase not in path.read_text(encoding="utf-8"):
        errors.append(f"{rel}: missing {phrase}")


def validate(root):
    errors = []
    manifest = read_json(require_file(root, ".codex-plugin/plugin.json", errors), errors)
    package = read_json(require_file(root, "package.json", errors), errors)
    hooks = manifest.get("hooks", "")
    skills = manifest.get("skills", "")
    if manifest.get("name") != "goal-matrix-iterative-delivery":
        errors.append("manifest name mismatch")
    if package.get("name") != manifest.get("name"):
        errors.append("package name must match manifest name")
    if package.get("version") != manifest.get("version"):
        errors.append("package version must match manifest version")
    if package.get("type") != "module":
        errors.append("package type must be module for pi-extension ESM loading")
    if package.get("pi", {}).get("extensions") != ["./pi-extension/index.js"]:
        errors.append("package pi.extensions must expose ./pi-extension/index.js")
    if not (root / "pi-extension" / "index.js").is_file():
        errors.append("package pi extension path missing: ./pi-extension/index.js")
    interface = manifest.get("interface", {})
    if interface.get("logo") != "./assets/icon.png":
        errors.append("manifest interface.logo mismatch")
    if interface.get("composerIcon") != "./assets/icon.png":
        errors.append("manifest interface.composerIcon mismatch")
    if hooks and not (root / hooks).is_file():
        errors.append(f"manifest hooks path missing: {hooks}")
    if skills and not (root / skills).is_dir():
        errors.append(f"manifest skills path missing: {skills}")
    for rel in ASSETS:
        require_file(root, rel, errors)
    icon = root / "assets/icon.png"
    if icon.is_file() and icon.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        errors.append("assets/icon.png is not a PNG")
    for rel, phrase in (
        ("LOOP.md", "Active Loops"),
        ("STATE.md", "Last run:"),
        ("loop-budget.md", "Kill Switch"),
        ("loop-run-log.md", "Recent Runs"),
    ):
        require_phrase(root, rel, phrase, errors)

    for files in ADAPTERS.values():
        for rel in files:
            require_file(root, rel, errors)

    for rel in INSTRUCTION_FILES:
        for phrase in INSTRUCTION_PHRASES:
            require_phrase(root, rel, phrase, errors)

    for rel in ("adapters/codex/README.md",):
        for phrase in ("install_adapter.py", "validate_plugin_package.py", "goal_guard.py doctor", "goal_guard.py audit"):
            require_phrase(root, rel, phrase, errors)

    for phrase in ("independent verifier", "truth source", "reject completion"):
        require_phrase(root, "adapters/codex/skills/loop-verifier/SKILL.md", phrase, errors)

    return {
        "ok": not errors,
        "adapters": list(ADAPTERS),
        "manifest": {"name": manifest.get("name"), "version": manifest.get("version")},
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    result = validate(Path(args.root).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
