import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# Keep fixtures deterministic; GitHub scenarios below inject their own context.
for _key in tuple(os.environ):
    if _key.startswith("GITHUB_"):
        os.environ.pop(_key)


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "core" / "goal_guard.py"
PACKAGE_VALIDATOR = ROOT / "scripts" / "validate_plugin_package.py"
LOOP_AUDIT = ROOT / "scripts" / "loop_audit.py"
GOVERNANCE_CHECK = ROOT / "scripts" / "check_governance.py"
CODEX_HOOK_FIXTURES = ROOT / "tests" / "fixtures" / "codex-hooks"
RELEASE_INSTALL_TAG = "v0.1.13-codex.1"

PROTOCOL_INVARIANTS = (
    "Goal Matrix Engineering Protocol",
    "Initialization types",
    "Project policy",
    "Active goal contract",
    "Development flow",
    "Truth source",
    "Checkpoint",
)


def read_text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def run_guard(args, text="", cwd=ROOT, env=None):
    return subprocess.run(
        [sys.executable, str(GUARD), *args],
        input=text,
        text=True,
        capture_output=True,
        cwd=cwd,
        env=env,
    )


def run_structured_start(root, title, verification="python3 --version"):
    contract = {
        "userOutcome": title,
        "engineeringSlice": f"Implement {title}",
        "initializationType": "iteration",
        "policyImpact": "none",
        "touchedPaths": ["tests/test_goal_guard.py"],
        "deliveryBoundary": f"{title} only",
        "skipped": "unrelated work",
        "truthSource": "test readback",
        "verification": verification,
        "developmentFlow": "inspect -> failing check -> implement -> verify -> checkpoint",
    }
    return run_guard(["start", "--root", str(root)], json.dumps(contract))


def hook_context(payload):
    return payload["hookSpecificOutput"]["additionalContext"]


def read_hook_fixture(name):
    return (CODEX_HOOK_FIXTURES / name).read_text(encoding="utf-8")


def test_core_protocol_exists_with_required_sections():
    text = read_text("core/protocol.md")
    for phrase in (
        "Goal Matrix Engineering Protocol",
        "Initialization types",
        "Project policy",
        "Active goal contract",
        "Development flow",
        "Truth source",
        "Checkpoint",
    ):
        assert phrase in text


def test_core_protocol_defines_skill_plugin_routing_contract():
    text = read_text("core/protocol.md")
    for phrase in (
        "Skill and plugin routing",
        "brainstorming",
        "writing-plans",
        "test-driven-development",
        "systematic-debugging",
        "verification-before-completion",
        "finishing-a-development-branch",
    ):
        assert phrase in text


def test_core_protocol_defines_loop_stage_chain():
    text = read_text("core/protocol.md")
    for phrase in (
        "project_initialization",
        "work_classification",
        "design_gate",
        "review_gate",
        "design_iteration",
    ):
        assert phrase in text


def test_core_protocol_defines_loop_engineering_contract():
    text = read_text("core/protocol.md")
    for phrase in (
        "Loop engineering",
        "project initialization status -> active goal -> failing check",
        "self-evolution run",
        "pending goals already recorded",
        "report complete instead of synthesizing a backlog",
        "checkpoint commit",
        "design_gate",
        "review_gate",
        "Next loop",
    ):
        assert phrase in text


def test_start_docs_require_structured_contract_and_mark_plain_text_as_draft():
    protocol = read_text("core/protocol.md")
    skill = read_text("adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md")
    english = read_text("README.md")
    chinese = read_text("README.zh.md")

    for field in (
        "userOutcome",
        "engineeringSlice",
        "initializationType",
        "policyImpact",
        "touchedPaths",
        "deliveryBoundary",
        "skipped",
        "truthSource",
        "verification",
        "developmentFlow",
    ):
        assert f'"{field}"' in protocol
    assert "structured JSON" in skill
    assert "plain text" in skill.lower() and "draft" in skill.lower()
    assert '"userOutcome"' in english
    assert '"userOutcome"' in chinese


def test_core_templates_exist():
    for path in (
        "core/templates/project-policy.json",
        "core/templates/project-context.md",
        "core/templates/checks.md",
        "core/templates/decisions.md",
        "core/templates/goal-matrix.md",
        "core/templates/active-goal.md",
        "core/templates/loop-note.md",
        "core/templates/notifications.json",
    ):
        assert (ROOT / path).is_file(), path


def test_loop_note_template_has_gate_evidence_fields():
    text = read_text("core/templates/loop-note.md")
    for phrase in (
        "Phase:",
        "Clarity decision:",
        "Policy impact:",
        "Truth source:",
        "Verification:",
        "Reviewer:",
        "Gate return:",
    ):
        assert phrase in text


def test_project_context_template_has_lifecycle_classification_fields():
    text = read_text("core/templates/project-context.md")
    for phrase in (
        "Project charter",
        "Work classification",
        "Lifecycle support cycle",
        "Idea source:",
        "User/operator:",
        "Success criteria:",
        "Support horizon:",
        "Retirement trigger:",
    ):
        assert phrase in text


def test_project_policy_template_is_valid_json():
    policy = json.loads(read_text("core/templates/project-policy.json"))
    assert policy["version"] == 1
    assert policy["initializationType"] == "new-project"
    assert policy["triggerMode"] == "narrow"
    assert "immutablePaths" in policy
    assert "approvalRequiredPaths" in policy
    assert "publishActionPatterns" in policy
    assert "truthSources" in policy
    assert "verification" in policy["completionRequires"]
    assert "truthSource" in policy["completionRequires"]
    assert "checkpoint" in policy["completionRequires"]


def test_notification_template_uses_codex_popup_and_common_webhook_presets():
    notifications = json.loads(read_text("core/templates/notifications.json"))

    assert notifications["enabled"] is False
    assert notifications["codexPopup"]["enabled"] is True
    assert notifications["webhook"]["enabled"] is False
    assert "session_start" in notifications["webhook"]["events"]
    assert notifications["webhook"]["urlEnv"] == "GOAL_MATRIX_WEBHOOK_URL"
    assert notifications["webhook"]["eventFields"] == ["event", "message", "provider"]
    assert set(notifications["webhook"]["presets"]) >= {
        "generic",
        "slack",
        "discord",
        "feishu",
        "dingtalk",
        "wechat_work",
    }
    assert "https://" not in json.dumps(notifications)


def test_goal_matrix_initialization_is_project_local():
    with tempfile.TemporaryDirectory() as tmp:
        init = run_guard(["init", "--root", tmp, "--type", "iteration"])
        audit = run_guard(["audit", "--root", tmp])

    assert init.returncode == 0, init.stderr
    assert audit.returncode == 0, audit.stderr


def test_goal_matrix_initialization_adds_notifications_and_gitignore():
    with tempfile.TemporaryDirectory() as tmp:
        init = run_guard(["init", "--root", tmp, "--type", "iteration"])
        notification_path = Path(tmp) / ".goal-matrix" / "notifications.json"
        gitignore = (Path(tmp) / ".gitignore").read_text(encoding="utf-8")
        notification_text = notification_path.read_text(encoding="utf-8") if notification_path.is_file() else ""
        notification_exists = notification_path.is_file()

    assert init.returncode == 0, init.stderr
    assert notification_exists
    assert ".goal-matrix/notifications.local.json" in gitignore
    assert "GOAL_MATRIX_WEBHOOK_URL" in notification_text


def test_manifest_wires_skill_and_hooks():
    manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())

    assert manifest["name"] == "goal-matrix-iterative-delivery"
    assert manifest["skills"] == "./adapters/codex/skills/"
    assert manifest["hooks"] == "./adapters/codex/hooks/codex-lifecycle-hooks.json"
    assert "hook-backed" in manifest["description"]
    assert "truth-source verification" in manifest["interface"]["longDescription"]
    assert manifest["author"]["url"] == "https://github.com/wozaitianwai"
    assert manifest["homepage"] == "https://github.com/wozaitianwai/goal-matrix-iterative-delivery"
    assert manifest["repository"] == "https://github.com/wozaitianwai/goal-matrix-iterative-delivery"
    assert manifest["interface"]["websiteURL"] == "https://github.com/wozaitianwai/goal-matrix-iterative-delivery"
    assert (ROOT / manifest["hooks"]).is_file()
    assert (ROOT / manifest["skills"]).is_dir()


def test_root_package_exposes_pi_extension_for_tool_native_popups():
    package = json.loads(read_text("package.json"))

    assert package["name"] == "goal-matrix-iterative-delivery"
    assert package["private"] is True
    assert package["type"] == "module"
    assert package["pi"]["extensions"] == ["./pi-extension/index.js"]
    assert (ROOT / "pi-extension" / "index.js").is_file()


def test_git_tracked_files_exclude_local_state_and_overlay_dirs():
    result = subprocess.run(
        ["git", "ls-files"],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    tracked = result.stdout.splitlines()
    allowed_agents_files = {".agents/plugins/marketplace.json"}
    assert not any(path.startswith(".agents/") and path not in allowed_agents_files for path in tracked)
    for prefix in (".codex/", ".goal-matrix/", "plugins/"):
        assert not any(path.startswith(prefix) for path in tracked), prefix


def test_public_readmes_are_bilingual_and_hide_development_process_paths():
    english = read_text("README.md")
    chinese = read_text("README.zh.md")

    assert "中文 | [English](README.md)" in chinese
    assert "English | [中文](README.zh.md)" in english
    assert "Goal Matrix Iterative Delivery" in chinese
    assert "Goal Matrix Iterative Delivery" in english
    assert "create_goal" in chinese
    assert "create_goal" in english
    assert "validate_plugin_package.py" in chinese
    assert "validate_plugin_package.py" in english
    assert "初始化项目" in chinese
    assert "Initialize A Project" in english
    assert f"codex plugin marketplace add https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git --ref {RELEASE_INSTALL_TAG}" in chinese
    assert f"codex plugin marketplace add https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git --ref {RELEASE_INSTALL_TAG}" in english
    assert "--ref main" not in chinese
    assert "--ref main" not in english
    assert "codex plugin add goal-matrix-iterative-delivery@goal-matrix-github" in chinese
    assert "codex plugin add goal-matrix-iterative-delivery@goal-matrix-github" in english
    assert "python3 scripts/install_adapter.py codex --target /path/to/project" in chinese
    assert "python3 scripts/loop_verify.py" in chinese
    assert "python3 scripts/loop_verify.py" in english
    assert "goal_guard.py start --root ." in chinese
    assert "goal_guard.py start --root ." in english
    assert "goal_guard.py checkpoint --root ." in chinese
    assert "goal_guard.py checkpoint --root ." in english
    assert "Codex lifecycle adapter" in chinese
    assert "lifecycle adapter" in english
    assert "不是后台任务系统" in chinese
    assert "not a background job system" in english
    for phrase in ("cursor --target", "instruction-host --target", "generic --target"):
        assert phrase not in chinese
        assert phrase not in english
    for text in (chinese, english):
        assert "tests/" not in text
        assert "docs/" not in text
        assert ".codex-plugin" not in text


def test_adapter_directories_exist():
    for path in (
        "CHANGELOG.md",
        "adapters/codex/hooks/codex-lifecycle-hooks.json",
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
        "docs/examples.md",
        "docs/operations.md",
        "docs/threat-model.md",
        "assets/icon.png",
        "pi-extension/index.js",
        "pi-extension/package.json",
        "scripts/install_adapter.py",
        "scripts/validate_plugin_package.py",
    ):
        assert (ROOT / path).is_file(), path

    for path in ("adapters/cursor", "adapters/instruction-host", "adapters/generic"):
        assert not (ROOT / path).exists(), path


def test_instruction_adapters_include_core_invariants():
    for path in (
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
    ):
        text = read_text(path)
        for phrase in PROTOCOL_INVARIANTS:
            assert phrase in text, f"{path} missing {phrase}"


def test_instruction_adapters_include_skill_plugin_routing():
    for path in (
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
    ):
        text = read_text(path)
        assert "Skill and plugin routing" in text, path
        assert "verification-before-completion" in text, path


def test_instruction_adapters_include_full_loop_boundaries():
    for path in (
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
    ):
        text = read_text(path)
        for phrase in (
            "project_initialization",
            "design_gate",
            "review_gate",
            "Next loop",
            "self-evolution run",
            "pending goals already recorded",
            "report complete instead of synthesizing a backlog",
            "visible Codex goal",
        ):
            assert phrase in text, f"{path} missing {phrase}"


def test_adapter_readmes_include_install_and_validation_commands():
    for path in ("adapters/codex/README.md",):
        text = read_text(path)
        assert "install_adapter.py" in text, path
        assert "validate_plugin_package.py" in text, path
        assert "goal_guard.py doctor" in text, path
        assert "goal_guard.py audit" in text, path
        assert "docs/operations.md" in text, path
        assert "docs/examples.md" in text, path
        assert "docs/threat-model.md" in text, path


def test_operations_docs_cover_uninstall_migration_debug_and_examples():
    operations = read_text("docs/operations.md")
    examples = read_text("docs/examples.md")
    for phrase in (
        "Uninstall",
        "Migration",
        "Debug",
        "doctor --fix",
        "pre-push.goal-matrix.previous",
    ):
        assert phrase in operations
    for phrase in (
        "Bugfix",
        "Legacy Refactor",
        "New Feature",
        "Read-Only Review",
        "Truth source",
        "Verification",
    ):
        assert phrase in examples


def test_native_pre_push_boundary_is_documented():
    readme = read_text("README.md")
    adapter = read_text("adapters/codex/README.md")
    operations = read_text("docs/operations.md")

    for phrase in (
        "Codex hook enforcement covers Codex tool calls only",
        "terminal git push requires the optional native pre-push hook",
    ):
        assert phrase in readme
    assert "shell or manual pushes" in adapter
    assert "prePushHookInstalled" in operations
    assert "prePushHookState" in operations
    for state in ("absent", "unmanaged", "current", "stale", "broken"):
        assert state in operations
    assert "python3 scripts/install_adapter.py codex --target . --install-git-hook" in operations


def test_threat_model_documents_enforcement_and_boundaries():
    text = read_text("docs/threat-model.md")
    for phrase in (
        "What It Enforces",
        "What It Does Not Enforce",
        "Fail-Open Boundaries",
        "Webhook Egress",
        "PreToolUse",
        "Stop",
        "policy-gate",
        "publish-gate",
        "not a security sandbox",
        "CODEX_PLUGIN_ROOT",
        "https://",
        "allowedHosts",
    ):
        assert phrase in text


def test_install_adapter_rejects_non_hook_instruction_adapters():
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install_adapter.py"),
                "cursor",
                "--target",
                tmp,
            ],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_install_adapter_rejects_legacy_global_scope_without_writing_skills():
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "CODEX_HOME": tmp}
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install_adapter.py"),
                "codex",
                "--scope",
                "global",
            ],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env=env,
        )
        skills = Path(tmp) / "skills"

    assert result.returncode != 0
    assert "--scope" in result.stderr
    assert not skills.exists()
    adapter_readme = read_text("adapters/codex/README.md")
    assert "project-only" in adapter_readme
    assert "only supported global install path" in adapter_readme


def test_install_adapter_can_install_native_pre_push_hook():
    with tempfile.TemporaryDirectory() as tmp:
        target = make_publish_repo(Path(tmp))
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install_adapter.py"),
                "codex",
                "--target",
                str(target),
                "--install-git-hook",
            ],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        hook = target / ".git" / "hooks" / "pre-push"
        hook_text = hook.read_text(encoding="utf-8") if hook.is_file() else ""
        hook_exists = hook.is_file()
        hook_is_executable = os.access(hook, os.X_OK)
        git_commit(target, "one.txt", "one\n", "one")
        git_commit(target, "two.txt", "two\n", "two")
        write_file(target / "dirty.txt", "dirty\n")
        hook_result = subprocess.run([str(hook)], cwd=target, text=True, capture_output=True)

    assert result.returncode == 0, result.stderr
    assert hook_exists
    assert hook_is_executable
    assert "goal-matrix-managed-pre-push:v1" in hook_text
    assert 'python3 "$goal_guard" publish-gate --root "$repo_root"' in hook_text
    assert hook_result.returncode == 1
    assert "uncommitted changes" in hook_result.stderr


def test_install_adapter_chains_existing_native_pre_push_hook():
    with tempfile.TemporaryDirectory() as tmp:
        target = make_publish_repo(Path(tmp))
        hook = target / ".git" / "hooks" / "pre-push"
        previous = target / ".git" / "hooks" / "pre-push.goal-matrix.previous"
        write_file(hook, "#!/bin/sh\nprintf chained > chained-hook.txt\n")
        hook.chmod(0o755)

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install_adapter.py"),
                "codex",
                "--target",
                str(target),
                "--install-git-hook",
            ],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        hook_text = hook.read_text(encoding="utf-8") if hook.is_file() else ""
        previous_exists = previous.is_file()
        previous_text = previous.read_text(encoding="utf-8") if previous.is_file() else ""
        commit_goal_matrix(target)
        hook_result = subprocess.run(
            [str(hook)],
            cwd=target,
            text=True,
            capture_output=True,
        )
        chained_text = (target / "chained-hook.txt").read_text(encoding="utf-8") if (target / "chained-hook.txt").is_file() else ""

    assert result.returncode == 0, result.stderr
    assert previous_exists
    assert previous_text == "#!/bin/sh\nprintf chained > chained-hook.txt\n"
    assert '${0}.goal-matrix.previous' in hook_text
    assert hook_result.returncode == 0, hook_result.stderr
    assert chained_text == "chained"


def test_install_adapter_refreshes_legacy_stale_hook_without_rechaining():
    with tempfile.TemporaryDirectory() as tmp:
        target = make_publish_repo(Path(tmp))
        hook = target / ".git" / "hooks" / "pre-push"
        previous = target / ".git" / "hooks" / "pre-push.goal-matrix.previous"
        stale_guard = Path(tmp) / "old-plugin" / "core" / "goal_guard.py"
        write_file(
            hook,
            f'''#!/bin/sh
set -eu
repo_root=$(git rev-parse --show-toplevel)
python3 "{stale_guard}" publish-gate --root "$repo_root"
previous_hook="$repo_root/.git/hooks/pre-push.goal-matrix.previous"
''',
        )
        hook.chmod(0o755)

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install_adapter.py"),
                "codex",
                "--target",
                str(target),
                "--install-git-hook",
            ],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        refreshed = hook.read_text(encoding="utf-8")
        previous_exists = previous.exists()

    assert result.returncode == 0, result.stderr
    assert "goal-matrix-managed-pre-push:v1" in refreshed
    assert str(ROOT / "core" / "goal_guard.py") in refreshed
    assert str(stale_guard) not in refreshed
    assert previous_exists is False


def test_install_adapter_and_doctor_respect_custom_hooks_path():
    with tempfile.TemporaryDirectory() as tmp:
        target = make_publish_repo(Path(tmp))
        subprocess.run(
            ["git", "config", "core.hooksPath", ".githooks"],
            cwd=target,
            check=True,
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install_adapter.py"),
                "codex",
                "--target",
                str(target),
                "--install-git-hook",
            ],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        doctor = run_guard(["doctor", "--root", str(target)])
        hook = target / ".githooks" / "pre-push"
        hook_exists = hook.is_file()
        hook_path = str(hook.resolve())

    assert result.returncode == 0, result.stderr
    assert hook_exists
    native_hooks = json.loads(doctor.stdout)["nativeHooks"]
    assert native_hooks["prePushHookPath"] == hook_path
    assert native_hooks["prePushHookState"] == "current"


def test_readmes_document_native_pre_push_hook_restore_path():
    for path in ("README.md", "README.zh.md", "adapters/codex/README.md"):
        text = read_text(path)
        assert "pre-push.goal-matrix.previous" in text


def test_runtime_policy_source_docs_are_consistent():
    english = read_text("README.md")
    chinese = read_text("README.zh.md")
    protocol = read_text("core/protocol.md")
    threat_model = read_text("docs/threat-model.md")

    assert ".goal-matrix/project-policy.json" in english
    assert "target project runtime policy source" in english
    assert "plugin repository autonomy" in english
    assert "目标项目运行时 policy 真源" in chinese
    assert "插件仓库自治" in chinese
    assert "target project runtime policy source" in protocol
    assert "plugin repository autonomy" in protocol
    assert "publishActionPatterns" in threat_model


def test_release_install_docs_are_reproducible_and_changelog_backed():
    changelog = read_text("CHANGELOG.md")
    tag_commit = subprocess.run(
        ["git", "rev-parse", RELEASE_INSTALL_TAG],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    for path in ("README.md", "README.zh.md", "adapters/codex/README.md"):
        text = read_text(path)
        assert f"--ref {RELEASE_INSTALL_TAG}" in text, path
        assert "--ref main" not in text, path

    assert tag_commit.returncode == 0, tag_commit.stderr
    assert RELEASE_INSTALL_TAG in changelog
    assert "Release checklist" in changelog
    assert "Codex plugin marketplace" in changelog


def test_package_validator_checks_current_repo():
    result = subprocess.run(
        [sys.executable, str(PACKAGE_VALIDATOR), "--root", str(ROOT)],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    package = json.loads(result.stdout)
    assert package["ok"] is True
    assert package["adapters"] == ["codex"]
    assert package["manifest"]["name"] == "goal-matrix-iterative-delivery"


def test_package_validator_requires_runtime_closure():
    required_runtime = (
        "core/goal_guard.py",
        "core/goal_gate.py",
        "core/goal_native_hook.py",
        "core/goal_policy.py",
        "core/goal_projection.py",
        "core/goal_publish.py",
        "core/goal_state.py",
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
        "scripts/check_governance.py",
        "scripts/lint_python.py",
        "loop-governance.json",
    )
    with tempfile.TemporaryDirectory() as tmp:
        package_root = Path(tmp) / "package"
        shutil.copytree(
            ROOT,
            package_root,
            ignore=shutil.ignore_patterns(".git", ".goal-matrix", "__pycache__", ".pytest_cache"),
        )

        for rel in required_runtime:
            path = package_root / rel
            content = path.read_bytes()
            path.unlink()
            result = subprocess.run(
                [sys.executable, str(PACKAGE_VALIDATOR), "--root", str(package_root)],
                text=True,
                capture_output=True,
                cwd=ROOT,
            )
            path.write_bytes(content)

            assert result.returncode == 1, rel
            assert f"missing file: {rel}" in json.loads(result.stdout)["errors"], rel


def test_l1_loop_ready_spine_files_are_committable():
    for path in ("LOOP.md", "STATE.md", "loop-budget.md", "loop-run-log.md", "scripts/loop_audit.py"):
        assert (ROOT / path).is_file(), path

    tracked = subprocess.run(["git", "ls-files"], text=True, capture_output=True, cwd=ROOT)

    assert tracked.returncode == 0, tracked.stderr
    for path in ("LOOP.md", "STATE.md", "loop-budget.md", "loop-run-log.md", "scripts/loop_audit.py"):
        assert path in tracked.stdout.splitlines(), path


def test_patterns_registry_lists_machine_readable_local_loop_pattern():
    registry = ROOT / "patterns" / "registry.yaml"
    assert registry.is_file(), "patterns/registry.yaml"
    text = registry.read_text(encoding="utf-8")

    for phrase in (
        "patterns:",
        "id: package-triage",
        "name:",
        "goal:",
        "cadence:",
        "risk:",
        "tools:",
        "skills:",
        "state:",
        "phases:",
        "human_gates:",
        "week_one_mode:",
        "token_cost:",
    ):
        assert phrase in text


def test_loop_audit_scores_current_repo_l2_assisted_with_verifier():
    result = subprocess.run(
        [sys.executable, str(LOOP_AUDIT), "--root", str(ROOT), "--json"],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["level"] == ("L3" if audit["signals"]["remoteRunEvidenceCurrentHead"] else "L2")
    assert audit["score"] >= 58
    assert audit["signals"]["stateFile"] is True
    assert audit["signals"]["loopConfig"] is True
    assert audit["signals"]["budgetDoc"] is True
    assert audit["signals"]["runLog"] is True
    assert audit["signals"]["completionMatrix"] is True
    assert audit["signals"]["verifier"] is True
    assert isinstance(audit["signals"]["githubRemote"], bool)


def test_loop_engineering_completion_matrix_is_audited():
    result = subprocess.run(
        [sys.executable, str(LOOP_AUDIT), "--root", str(ROOT), "--json"],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["signals"]["completionMatrix"] is True
    assert audit["levels"]["L1"] == "report-only"
    assert audit["levels"]["L2"] == "assisted-with-verifier"
    assert audit["levels"]["L3"] == "remote-ci-activity"
    if audit["signals"]["remoteCiContextCurrentHead"]:
        assert audit["blocked"] == []
    elif audit["signals"]["remoteCiContext"]:
        assert any("current HEAD" in item for item in audit["blocked"])
    elif audit["signals"]["githubRemote"] and audit["signals"]["githubWorkflows"]:
        assert any("informational only" in item for item in audit["blocked"])
    else:
        assert any("GitHub remote" in item for item in audit["blocked"])


def test_loop_verifier_skill_is_packaged_and_audited():
    verifier = ROOT / "adapters" / "codex" / "skills" / "loop-verifier" / "SKILL.md"
    assert verifier.is_file()
    text = verifier.read_text(encoding="utf-8")
    for phrase in ("truth source", "independent verifier", "reject completion"):
        assert phrase in text

    result = subprocess.run(
        [sys.executable, str(LOOP_AUDIT), "--root", str(ROOT), "--json"],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["signals"]["verifier"] is True
    assert audit["level"] == ("L3" if audit["signals"]["remoteRunEvidenceCurrentHead"] else "L2")


def test_loop_docs_describe_current_operational_boundaries():
    loop = read_text("LOOP.md")
    state = read_text("STATE.md")

    for phrase in (
        "run-log readback is informational only",
        "trusted GitHub Actions context matching the checked-out HEAD",
        "pull request and required-check ruleset",
        "machine goal status is read from `.goal-matrix/state.json`",
    ):
        assert phrase in loop
    assert "G23-G36" not in loop
    assert "Engineering Gap Register" not in loop
    assert "Resolved:" not in loop
    assert "marketplace is the only global plugin installation path" in state
    assert "current-head PR and CI evidence" in state
    assert "machine goal status stays in `.goal-matrix/state.json`" in state
    assert "Hook/runtime simplification remains outside" not in state


def test_ci_workflow_runs_loop_engineering_gates():
    workflow = ROOT / ".github" / "workflows" / "loop-audit.yml"
    script = ROOT / "scripts" / "loop_verify.py"
    assert workflow.is_file()
    assert script.is_file()
    text = workflow.read_text(encoding="utf-8") + script.read_text(encoding="utf-8")
    for phrase in (
        "scripts/loop_audit.py",
        "scripts/validate_plugin_package.py",
        "scripts/check_governance.py",
        "tests/test_goal_guard.py",
    ):
        assert phrase in text

    result = subprocess.run(
        [sys.executable, str(LOOP_AUDIT), "--root", str(ROOT), "--json"],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["signals"]["githubWorkflows"] is True
    assert isinstance(audit["signals"]["githubRemote"], bool)
    assert audit["level"] == ("L3" if audit["signals"]["remoteRunEvidenceCurrentHead"] else "L2")


def test_loop_audit_reports_unresolved_gap_register_items():
    result = subprocess.run(
        [sys.executable, str(LOOP_AUDIT), "--root", str(ROOT), "--json"],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["signals"]["gapRegister"] is False
    assert audit["signals"]["repeatedRunEvidence"] is True
    assert "remote-ci" not in audit["unresolvedGaps"]
    assert "distribution" not in audit["unresolvedGaps"]
    assert "maker-checker" not in audit["unresolvedGaps"]
    assert "governance" not in audit["unresolvedGaps"]
    assert "run-evidence" not in audit["unresolvedGaps"]
    assert "connectors" not in audit["unresolvedGaps"]
    assert audit["unresolvedGaps"] == []
    if audit["signals"]["remoteRunEvidenceCurrentHead"]:
        assert audit["nextAction"] == "No unresolved loop-engineering gaps."
    else:
        assert audit["nextAction"] == "Run the current HEAD verifier in GitHub Actions."


def test_loop_audit_flags_oversized_run_log_for_summary_goal():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_file(root / "STATE.md", "Last run: now\n\n## High Priority\n\n## Watch List\n")
        write_file(root / "loop-budget.md", "Max tokens: 100\nKill Switch: stop\n")
        write_file(
            root / "LOOP.md",
            "# Loop\n\n## Active Loops\npackage-triage\n\n## Human Gates\n## Budget\n",
        )
        records = [
            json.dumps({"run_id": f"r{i}", "outcome": "local"}, separators=(",", ":"))
            for i in range(501)
        ]
        write_file(root / "loop-run-log.md", "# Runs\n\n## Recent Runs\n" + "\n".join(records) + "\n")

        result = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["signals"]["runLogNeedsSummary"] is True
    assert audit["runLogLineCount"] > audit["runLogLineLimit"]
    assert any("summary/pruning goal" in item for item in audit["blocked"])


def test_loop_audit_reports_current_friction_budget():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "core").mkdir()
        write_file(root / "core" / "goal_guard.py", GUARD.read_text(encoding="utf-8"))
        write_file(
            root / "core" / "goal_gate.py",
            (ROOT / "core" / "goal_gate.py").read_text(encoding="utf-8"),
        )
        write_file(
            root / "core" / "goal_verification.py",
            (ROOT / "core" / "goal_verification.py").read_text(encoding="utf-8"),
        )
        write_file(
            root / "core" / "goal_native_hook.py",
            (ROOT / "core" / "goal_native_hook.py").read_text(encoding="utf-8"),
        )
        write_file(
            root / "core" / "goal_policy.py",
            (ROOT / "core" / "goal_policy.py").read_text(encoding="utf-8"),
        )
        write_file(
            root / "core" / "goal_projection.py",
            (ROOT / "core" / "goal_projection.py").read_text(encoding="utf-8"),
        )
        write_file(
            root / "core" / "goal_publish.py",
            (ROOT / "core" / "goal_publish.py").read_text(encoding="utf-8"),
        )
        write_file(
            root / "core" / "goal_state.py",
            (ROOT / "core" / "goal_state.py").read_text(encoding="utf-8"),
        )
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        result = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", tmp, "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert result.returncode in {0, 2}, result.stderr
    audit = json.loads(result.stdout)
    budget = audit["frictionBudget"]
    assert budget["statusOutputChars"] > 0
    assert budget["hookOutputChars"] > 0
    assert budget["hookOutputCharLimit"] == 6000
    assert budget["statusOutputChars"] <= budget["statusOutputCharLimit"]
    assert budget["hookOutputChars"] <= budget["hookOutputCharLimit"]
    assert audit["signals"]["frictionBudgetExceeded"] is False


def test_loop_audit_flags_oversized_loop_friction():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_file(root / "STATE.md", "Last run: now\n\n## High Priority\n\n## Watch List\n")
        write_file(root / "loop-budget.md", "Max tokens: 100\nKill Switch: stop\n")
        write_file(root / "LOOP.md", "# Loop\n\n## Active Loops\npackage-triage\n\n## Human Gates\n## Budget\n")
        write_file(root / "loop-run-log.md", "# Runs\n\n## Recent Runs\n{\"outcome\":\"local\"}\n")
        write_file(
            root / "core" / "goal_guard.py",
            (
                "import sys\n"
                "if 'status' in sys.argv:\n"
                "    print('s' * 40001)\n"
                "elif 'hook' in sys.argv:\n"
                "    print('h' * 12001)\n"
            ),
        )

        result = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["signals"]["frictionBudgetExceeded"] is True
    assert audit["frictionBudget"]["statusOutputChars"] > audit["frictionBudget"]["statusOutputCharLimit"]
    assert audit["frictionBudget"]["hookOutputChars"] > audit["frictionBudget"]["hookOutputCharLimit"]
    assert any("friction budget" in item for item in audit["blocked"])


def test_loop_audit_flags_state_governance_policy_duplication():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_file(
            root / "STATE.md",
            (
                "Last run: now\n\n## High Priority\n\n"
                "- Keep governance gate active.\n\n"
                "## Watch List\n\n"
                "- G43 governance gate blocks package.json unless GOAL_MATRIX_APPROVED is set.\n"
            ),
        )
        write_file(root / "loop-budget.md", "Max tokens: 100\nKill Switch: stop\n")
        write_file(
            root / "LOOP.md",
            "# Loop\n\n## Active Loops\npackage-triage\n\n## Human Gates\n## Budget\n",
        )
        write_file(root / "loop-run-log.md", "# Runs\n\n## Recent Runs\n{\"outcome\":\"local\"}\n")
        write_file(
            root / "loop-governance.json",
            json.dumps(
                {"approvalEnv": "GOAL_MATRIX_APPROVED", "approvalRequiredPaths": ["package.json"]},
                indent=2,
            ),
        )

        result = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["signals"]["stateGovernanceDuplication"] is True
    assert audit["signals"]["stateGovernanceDrift"] is True
    assert "GOAL_MATRIX_APPROVED" in audit["stateGovernanceMachineValues"]
    assert "package.json" in audit["stateGovernanceMachineValues"]
    assert any("STATE.md repeats machine governance values" in item for item in audit["blocked"])


def test_loop_audit_flags_state_md_version_drift():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_file(
            root / "STATE.md",
            (
                "Last run: now\n\n## High Priority\n\n"
                "- Keep plugin cache current.\n\n"
                "## Watch List\n\n"
                "- Codex plugin cache refreshed to `0.1.0+codex.old`.\n"
            ),
        )
        write_file(root / "package.json", json.dumps({"version": "0.1.1+codex.current"}) + "\n")
        write_file(root / ".codex-plugin" / "plugin.json", json.dumps({"version": "0.1.1+codex.current"}) + "\n")
        write_file(root / "loop-budget.md", "Max tokens: 100\nKill Switch: stop\n")
        write_file(
            root / "LOOP.md",
            "# Loop\n\n## Active Loops\npackage-triage\n\n## Human Gates\n## Budget\n",
        )
        write_file(root / "loop-run-log.md", "# Runs\n\n## Recent Runs\n{\"outcome\":\"local\"}\n")

        result = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["signals"]["stateVersionDrift"] is True
    assert "0.1.0+codex.old" in audit["stateVersionMentions"]
    assert any("STATE.md mentions stale plugin version" in item for item in audit["blocked"])


def test_loop_audit_current_state_md_version_matches_manifest():
    result = subprocess.run(
        [sys.executable, str(LOOP_AUDIT), "--root", str(ROOT), "--json"],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["repoVersions"]["package"] == audit["repoVersions"]["plugin"]
    assert audit["signals"]["stateVersionDrift"] is False


def make_governance_repo(root):
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "base"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    write_file(
        root / "loop-governance.json",
        json.dumps(
            {
                "approvalEnv": "GOAL_MATRIX_APPROVED",
                "approvalActors": ["trusted-owner"],
                "approvalRequiredPaths": ["package.json"],
                "blockedPaths": [".goal-matrix/**"],
                "publishActionPatterns": ["npm publish"],
            }
        ),
    )


def make_governance_merge_repo(root, approval_trailer):
    make_governance_repo(root)
    subprocess.run(["git", "add", "loop-governance.json"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "policy"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    subprocess.run(["git", "switch", "-c", "feature"], cwd=root, check=True, capture_output=True, text=True)
    write_file(root / "package.json", '{"sensitive": true}\n')
    subprocess.run(["git", "add", "package.json"], cwd=root, check=True, capture_output=True, text=True)
    commit = [
        "git",
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-m",
        "sensitive",
    ]
    if approval_trailer:
        commit.extend(["-m", approval_trailer])
    subprocess.run(commit, cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "switch", branch], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "merge",
            "--no-ff",
            "feature",
            "-m",
            "Merge pull request",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    return base, head


def test_governance_sensitive_runtime_paths_require_approval():
    policy = json.loads(read_text("loop-governance.json"))
    assert policy["approvalActors"] == ["wozaitianwai"]
    required = [
        ".codex-plugin/plugin.json",
        ".github/workflows/**",
        "adapters/codex/hooks/**",
        "adapters/codex/skills/**",
        "core/goal_guard.py",
        "scripts/check_governance.py",
        "scripts/loop_audit.py",
    ]
    for path in required:
        assert path in policy["approvalRequiredPaths"]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
        write_file(root / "loop-governance.json", json.dumps(policy) + "\n")
        write_file(root / ".codex-plugin" / "plugin.json", "{}\n")
        write_file(root / ".github" / "workflows" / "loop-audit.yml", "name: ci\n")
        write_file(root / "adapters" / "codex" / "hooks" / "codex-lifecycle-hooks.json", "{}\n")
        write_file(root / "adapters" / "codex" / "skills" / "goal-matrix-iterative-delivery" / "SKILL.md", "---\n")
        write_file(root / "core" / "goal_guard.py", "print('guard')\n")
        write_file(root / "scripts" / "check_governance.py", "print('governance')\n")
        write_file(root / "scripts" / "loop_audit.py", "print('audit')\n")

        denied = subprocess.run(
            [sys.executable, str(GOVERNANCE_CHECK), "--root", str(root)],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert denied.returncode == 1
    for path in (
        ".codex-plugin/plugin.json",
        ".github/workflows/loop-audit.yml",
        "adapters/codex/hooks/codex-lifecycle-hooks.json",
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
        "core/goal_guard.py",
        "scripts/check_governance.py",
        "scripts/loop_audit.py",
    ):
        assert f"{path} requires approval" in denied.stderr


def test_governance_blocks_approval_required_paths_without_approval():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_governance_repo(root)
        write_file(root / "package.json", "{}\n")

        denied = subprocess.run(
            [sys.executable, str(GOVERNANCE_CHECK), "--root", str(root)],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        approved = subprocess.run(
            [sys.executable, str(GOVERNANCE_CHECK), "--root", str(root)],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env={**os.environ, "GOAL_MATRIX_APPROVED": "1"},
        )

    assert denied.returncode == 1
    assert "package.json requires approval" in denied.stderr
    assert approved.returncode == 0, approved.stderr


def test_governance_local_approval_trailer_does_not_approve_clean_commit():
    env_without_approval = {
        key: value
        for key, value in os.environ.items()
        if key != "GOAL_MATRIX_APPROVED" and not key.startswith("GITHUB_")
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_governance_repo(root)
        write_file(root / "package.json", "{}\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "approved package change",
                "-m",
                "Goal-Matrix-Approval: G154 user-approved release governance evidence",
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            [sys.executable, str(GOVERNANCE_CHECK), "--root", str(root)],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env=env_without_approval,
        )

    assert result.returncode == 1
    assert "package.json requires approval" in result.stderr


def test_governance_approval_trailer_rejects_untrusted_ci_actor():
    env_without_approval = {
        key: value
        for key, value in os.environ.items()
        if key != "GOAL_MATRIX_APPROVED" and not key.startswith("GITHUB_")
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_governance_repo(root)
        write_file(root / "package.json", "{}\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "untrusted attestation",
                "-m",
                "Goal-Matrix-Approval: G159 governance evidence",
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            [sys.executable, str(GOVERNANCE_CHECK), "--root", str(root)],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env={**env_without_approval, "GITHUB_ACTIONS": "true", "GITHUB_ACTOR": "contributor"},
        )

    assert result.returncode == 1
    assert "package.json requires approval" in result.stderr


def test_governance_approval_trailer_allows_configured_ci_actor():
    env_without_approval = {
        key: value
        for key, value in os.environ.items()
        if key != "GOAL_MATRIX_APPROVED" and not key.startswith("GITHUB_")
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_governance_repo(root)
        write_file(root / "package.json", "{}\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "trusted attestation",
                "-m",
                "Goal-Matrix-Approval: G159 governance evidence",
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            [sys.executable, str(GOVERNANCE_CHECK), "--root", str(root)],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env={**env_without_approval, "GITHUB_ACTIONS": "true", "GITHUB_ACTOR": "trusted-owner"},
        )

    assert result.returncode == 0, result.stderr


def test_governance_accepts_approved_tip_behind_standard_merge_commit():
    env_without_approval = {
        key: value
        for key, value in os.environ.items()
        if key != "GOAL_MATRIX_APPROVED" and not key.startswith("GITHUB_")
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base, head = make_governance_merge_repo(
            root,
            "Goal-Matrix-Approval: G188 trusted merge evidence",
        )

        result = subprocess.run(
            [
                sys.executable,
                str(GOVERNANCE_CHECK),
                "--root",
                str(root),
                "--base",
                base,
                "--head",
                head,
            ],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env={**env_without_approval, "GITHUB_ACTIONS": "true", "GITHUB_ACTOR": "trusted-owner"},
        )

    assert result.returncode == 0, result.stderr


def test_governance_rejects_unapproved_tip_behind_standard_merge_commit():
    env_without_approval = {
        key: value
        for key, value in os.environ.items()
        if key != "GOAL_MATRIX_APPROVED" and not key.startswith("GITHUB_")
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base, head = make_governance_merge_repo(root, "")

        result = subprocess.run(
            [
                sys.executable,
                str(GOVERNANCE_CHECK),
                "--root",
                str(root),
                "--base",
                base,
                "--head",
                head,
            ],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env={**env_without_approval, "GITHUB_ACTIONS": "true", "GITHUB_ACTOR": "trusted-owner"},
        )

    assert result.returncode == 1
    assert "package.json requires approval" in result.stderr


def test_governance_explicit_range_catches_sensitive_earlier_commit():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_governance_repo(root)
        write_file(root / "package.json", "{}\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "baseline"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        write_file(root / "package.json", '{"sensitive": true}\n')
        subprocess.run(["git", "add", "package.json"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "sensitive"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        write_file(root / "README.md", "ordinary final commit\n")
        subprocess.run(["git", "add", "README.md"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "ordinary"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()

        result = subprocess.run(
            [
                sys.executable,
                str(GOVERNANCE_CHECK),
                "--root",
                str(root),
                "--base",
                base,
                "--head",
                head,
            ],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert result.returncode == 1
    assert "package.json requires approval" in result.stderr


def test_governance_invalid_explicit_range_fails_closed():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_governance_repo(root)

        result = subprocess.run(
            [
                sys.executable,
                str(GOVERNANCE_CHECK),
                "--root",
                str(root),
                "--base",
                "missing-base",
                "--head",
                "HEAD",
            ],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert result.returncode == 2
    assert "invalid governance diff range" in result.stderr


def test_governance_committed_approval_trailer_does_not_approve_worktree_changes():
    env_without_approval = {
        key: value
        for key, value in os.environ.items()
        if key != "GOAL_MATRIX_APPROVED" and not key.startswith("GITHUB_")
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_governance_repo(root)
        write_file(root / "package.json", "{}\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "approved package change",
                "-m",
                "Goal-Matrix-Approval: G154 user-approved release governance evidence",
            ],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        write_file(root / "package.json", "{\"dirty\": true}\n")

        denied = subprocess.run(
            [sys.executable, str(GOVERNANCE_CHECK), "--root", str(root)],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env=env_without_approval,
        )

    assert denied.returncode == 1
    assert "package.json requires approval" in denied.stderr


def test_governance_allows_package_version_only_bump_without_approval():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_governance_repo(root)
        write_file(root / "package.json", json.dumps({"name": "demo", "version": "0.1.0"}) + "\n")
        write_file(root / ".codex-plugin" / "plugin.json", json.dumps({"version": "0.1.0"}) + "\n")
        write_file(root / "CHANGELOG.md", "# Changelog\n\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "baseline"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )

        write_file(root / "package.json", json.dumps({"name": "demo", "version": "0.1.1"}) + "\n")
        write_file(root / ".codex-plugin" / "plugin.json", json.dumps({"version": "0.1.1"}) + "\n")
        write_file(root / "CHANGELOG.md", "# Changelog\n\n## 0.1.1\n\n- Version bump.\n")
        result = subprocess.run(
            [sys.executable, str(GOVERNANCE_CHECK), "--root", str(root)],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert result.returncode == 0, result.stderr


def test_loop_verify_keeps_approval_env_out_of_non_governance_checks():
    code = (
        "import json, scripts.loop_verify as loop_verify; "
        "print(json.dumps({"
        "'tests': loop_verify.command_env('tests').get('GOAL_MATRIX_APPROVED'), "
        "'governance': loop_verify.command_env('governance').get('GOAL_MATRIX_APPROVED'), "
        "'tests_base': loop_verify.command_env('tests').get('GOAL_MATRIX_BASE_SHA'), "
        "'governance_base': loop_verify.command_env('governance').get('GOAL_MATRIX_BASE_SHA'), "
        "'tests_github': loop_verify.command_env('tests').get('GITHUB_ACTIONS'), "
        "'audit_github': loop_verify.command_env('loop audit').get('GITHUB_ACTIONS'), "
        "'governance_github': loop_verify.command_env('governance').get('GITHUB_ACTIONS')"
        "}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        cwd=ROOT,
        env={
            **os.environ,
            "GOAL_MATRIX_APPROVED": "1",
            "GOAL_MATRIX_BASE_SHA": "base",
            "GITHUB_ACTIONS": "true",
        },
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "tests": None,
        "governance": "1",
        "tests_base": None,
        "governance_base": "base",
        "tests_github": None,
        "audit_github": "true",
        "governance_github": "true",
    }


def test_governance_blocks_publish_actions_without_approval():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_governance_repo(root)
        write_file(root / ".github" / "workflows" / "release.yml", "steps:\n  - run: echo ok\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "workflow"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        write_file(root / ".github" / "workflows" / "release.yml", "steps:\n  - run: npm publish\n")

        denied = subprocess.run(
            [sys.executable, str(GOVERNANCE_CHECK), "--root", str(root)],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert denied.returncode == 1
    assert "publish action requires approval" in denied.stderr


def test_distribution_readback_is_recorded_from_remote_source():
    log = read_text("loop-run-log.md")
    for phrase in (
        "distribution-readback",
        "remote-source-install-verified",
        "package_validation_ok",
        "doctor_installed_skill_matches_adapter",
        "doctor_installed_verifier_skill_matches_adapter",
        "b94dcc92102a23d27afb2b0d9a2bb48e56e8d388",
    ):
        assert phrase in log


def test_maker_checker_worktree_evidence_is_recorded():
    log = read_text("loop-run-log.md")
    for phrase in (
        '"pattern":"maker-checker"',
        '"branch":"codex/g42-maker-checker"',
        '"maker_commit":"51134ff"',
        '"checker_command":"python3 scripts/loop_verify.py"',
        '"checker_result":"pass"',
    ):
        assert phrase in log


def test_loop_audit_does_not_report_l3_without_remote_run_evidence():
    result = subprocess.run(
        [sys.executable, str(LOOP_AUDIT), "--root", str(ROOT), "--json"],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    simulated_score = audit["score"] + 6
    assert simulated_score >= 78
    assert audit["signals"]["githubWorkflows"] is True
    assert audit["level"] == ("L3" if audit["signals"]["remoteRunEvidenceCurrentHead"] else "L2")


def test_loop_audit_l3_requires_remote_run_evidence():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://example.invalid/repo.git"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        write_file(root / "STATE.md", "Last run: now\n\n## High Priority\n\n## Watch List\n")
        write_file(root / "loop-budget.md", "Max tokens: 100\nKill Switch: stop\n")
        write_file(root / "loop-run-log.md", "# Runs\n\n## Recent Runs\n{\"outcome\":\"local\"}\n")
        write_file(
            root / "LOOP.md",
            """# Loop

## Active Loops
package-triage

## Loop Engineering Completion Matrix
Readiness Levels
remote-ci-activity

## Engineering Gap Register
| Gap | Current state | Missing for loop-engineering parity | Next action |
| --- | --- | --- | --- |
| remote-ci | remote exists | Actions evidence | Add remote, push, read check result |

## Human Gates
## Budget
""",
        )
        write_file(
            root / "adapters" / "codex" / "skills" / "loop-verifier" / "SKILL.md",
            "independent verifier\ntruth source\nreject completion\n",
        )
        (root / ".github" / "workflows").mkdir(parents=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "base"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        missing = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        write_file(
            root / "loop-run-log.md",
            "# Runs\n\n## Recent Runs\noutcome remote-ci-readback github-check-run\n",
        )
        prose = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        write_file(
            root / "loop-run-log.md",
            '# Runs\n\n## Recent Runs\n{"outcome":"remote-ci-readback","run_url":"https://example.invalid/run"}\n',
        )
        incomplete = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        write_file(
            root / "loop-run-log.md",
            (
                '# Runs\n\n## Recent Runs\n'
                '{"pattern":"github-check-run","outcome":"remote-ci-readback",'
                '"run_status":"completed","run_conclusion":"success",'
                f'"run_url":"https://example.invalid/run","head_sha":"{head}"}}\n'
            ),
        )
        present = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert missing.returncode == 0, missing.stderr
    missing_audit = json.loads(missing.stdout)
    assert missing_audit["signals"]["githubRemote"] is True
    assert missing_audit["signals"]["githubWorkflows"] is True
    assert missing_audit["signals"]["remoteRunEvidence"] is False
    assert missing_audit["level"] == "L2"

    assert prose.returncode == 0, prose.stderr
    prose_audit = json.loads(prose.stdout)
    assert prose_audit["signals"]["remoteRunEvidence"] is False
    assert prose_audit["level"] == "L2"

    assert incomplete.returncode == 0, incomplete.stderr
    incomplete_audit = json.loads(incomplete.stdout)
    assert incomplete_audit["signals"]["remoteRunEvidence"] is False
    assert incomplete_audit["level"] == "L2"

    assert present.returncode == 0, present.stderr
    present_audit = json.loads(present.stdout)
    assert present_audit["signals"]["remoteRunEvidence"] is True
    assert present_audit["signals"]["recordedRemoteReadbackCurrentHead"] is True
    assert present_audit["signals"]["remoteRunEvidenceCurrentHead"] is False
    assert present_audit["level"] == "L2"


def test_loop_audit_recorded_readback_never_promotes_l3():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://example.invalid/repo.git"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        write_file(root / "STATE.md", "Last run: now\n\n## High Priority\n\n## Watch List\n")
        write_file(root / "loop-budget.md", "Max tokens: 100\nKill Switch: stop\n")
        write_file(
            root / "LOOP.md",
            """# Loop

## Active Loops
package-triage

## Loop Engineering Completion Matrix
Readiness Levels
remote-ci-activity

## Human Gates
## Budget
""",
        )
        write_file(
            root / "adapters" / "codex" / "skills" / "loop-verifier" / "SKILL.md",
            "independent verifier\ntruth source\nreject completion\n",
        )
        (root / ".github" / "workflows").mkdir(parents=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "base"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        write_file(
            root / "loop-run-log.md",
            (
                '# Runs\n\n## Recent Runs\n'
                '{"pattern":"github-check-run","outcome":"remote-ci-readback",'
                '"run_status":"completed","run_conclusion":"success",'
                '"run_url":"https://example.invalid/run","head_sha":"stale"}\n'
            ),
        )
        stale = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        write_file(
            root / "loop-run-log.md",
            (
                '# Runs\n\n## Recent Runs\n'
                '{"pattern":"github-check-run","outcome":"remote-ci-readback",'
                '"run_status":"completed","run_conclusion":"success",'
                f'"run_url":"https://example.invalid/run","head_sha":"{head}"}}\n'
            ),
        )
        fresh = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert stale.returncode == 0, stale.stderr
    stale_audit = json.loads(stale.stdout)
    assert stale_audit["signals"]["remoteRunEvidence"] is True
    assert stale_audit["signals"]["remoteRunEvidenceCurrentHead"] is False
    assert stale_audit["level"] == "L2"
    assert any("informational only" in item for item in stale_audit["blocked"])
    assert stale_audit["nextAction"] == "Run the current HEAD verifier in GitHub Actions."

    assert fresh.returncode == 0, fresh.stderr
    fresh_audit = json.loads(fresh.stdout)
    assert fresh_audit["signals"]["remoteRunEvidence"] is True
    assert fresh_audit["signals"]["recordedRemoteReadbackCurrentHead"] is True
    assert fresh_audit["signals"]["remoteRunEvidenceCurrentHead"] is False
    assert fresh_audit["level"] == "L2"
    assert fresh_audit["nextAction"] == "Run the current HEAD verifier in GitHub Actions."


def make_l3_context_repo(root):
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://example.invalid/repo.git"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    write_file(root / "STATE.md", "Last run: now\n\n## High Priority\n\n## Watch List\n")
    write_file(root / "loop-budget.md", "Max tokens: 100\nKill Switch: stop\n")
    write_file(
        root / "LOOP.md",
        """# Loop

## Active Loops
package-triage

## Loop Engineering Completion Matrix
## Readiness Levels
remote-ci-activity

## Human Gates
## Budget
""",
    )
    write_file(
        root / "loop-run-log.md",
        (
            '# Runs\n\n## Recent Runs\n'
            '{"pattern":"github-check-run","outcome":"remote-ci-readback",'
            '"run_status":"completed","run_conclusion":"success",'
            '"run_url":"https://example.invalid/run","head_sha":"stale"}\n'
        ),
    )
    write_file(
        root / "adapters" / "codex" / "skills" / "loop-verifier" / "SKILL.md",
        "independent verifier\ntruth source\nreject completion\n",
    )
    write_file(root / ".github" / "workflows" / "audit.yml", "name: audit\n")
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "base"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_loop_audit_levels_require_documented_signals_not_score():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_l3_context_repo(root)
        env = {key: value for key, value in os.environ.items() if not key.startswith("GITHUB_")}
        loop_path = root / "LOOP.md"
        complete_loop = loop_path.read_text(encoding="utf-8")

        loop_path.write_text(
            complete_loop.replace("## Loop Engineering Completion Matrix\n", ""),
            encoding="utf-8",
        )
        without_matrix = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env=env,
        )

        loop_path.write_text(
            complete_loop.replace("package-triage", "manual-review"),
            encoding="utf-8",
        )
        without_triage = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env=env,
        )

    matrix_audit = json.loads(without_matrix.stdout)
    assert matrix_audit["score"] >= 58
    assert matrix_audit["signals"]["completionMatrix"] is False
    assert matrix_audit["level"] == "L1"

    triage_audit = json.loads(without_triage.stdout)
    assert triage_audit["score"] >= 58
    assert triage_audit["signals"]["triage"] is False
    assert triage_audit["level"] == "L0"


def test_loop_audit_l3_required_rejects_stale_evidence():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_l3_context_repo(root)
        env = {key: value for key, value in os.environ.items() if not key.startswith("GITHUB_")}

        result = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json", "--require-level", "L3"],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env=env,
        )

    assert result.returncode == 3
    assert json.loads(result.stdout)["level"] == "L2"
    assert "required readiness L3, got L2" in result.stderr


def test_loop_audit_github_actions_current_head_satisfies_l3():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        head = make_l3_context_repo(root)
        env = {
            **{key: value for key, value in os.environ.items() if not key.startswith("GITHUB_")},
            "GITHUB_ACTIONS": "true",
            "GITHUB_SHA": head,
            "GITHUB_RUN_ID": "12345",
            "GITHUB_REPOSITORY": "example/repo",
            "GITHUB_WORKFLOW": "Loop Readiness Audit",
        }

        result = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json", "--require-level", "L3"],
            text=True,
            capture_output=True,
            cwd=ROOT,
            env=env,
        )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["level"] == "L3"
    assert audit["signals"]["remoteCiContextCurrentHead"] is True
    assert audit["signals"]["remoteRunEvidenceCurrentHead"] is True


def test_loop_audit_rejects_state_goal_status_claim():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_l3_context_repo(root)
        write_file(
            root / "STATE.md",
            "Last run: now (G999 active)\n\n## High Priority\n\n## Watch List\n",
        )

        result = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert result.returncode == 4
    audit = json.loads(result.stdout)
    assert audit["signals"]["stateGoalStatusClaim"] is True
    assert any("STATE.md claims machine goal status" in item for item in audit["blocked"])


def test_loop_audit_detects_remote_from_linked_worktree():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        worktree = Path(tmp) / "worktree"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "https://example.invalid/repo.git"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        write_file(repo / "STATE.md", "Last run: now\n\n## High Priority\n\n## Watch List\n")
        write_file(repo / "loop-budget.md", "Max tokens: 100\nKill Switch: stop\n")
        write_file(repo / "loop-run-log.md", "# Runs\n\n## Recent Runs\n{\"outcome\":\"local\"}\n")
        write_file(
            repo / "LOOP.md",
            """# Loop

## Active Loops
package-triage

## Loop Engineering Completion Matrix
Readiness Levels
remote-ci-activity

## Engineering Gap Register
| Gap | Current state | Missing for loop-engineering parity | Next action |
| --- | --- | --- | --- |
| maker-checker | verifier exists | worktree evidence | Add when remote branch exists |

## Human Gates
## Budget
""",
        )
        write_file(
            repo / "adapters" / "codex" / "skills" / "loop-verifier" / "SKILL.md",
            "independent verifier\ntruth source\nreject completion\n",
        )
        (repo / ".github" / "workflows").mkdir(parents=True)
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "init"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "worktree", "add", str(worktree), "-b", "checker"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(worktree), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["signals"]["githubRemote"] is True


def test_loop_verify_script_and_ci_share_one_gate():
    script = ROOT / "scripts" / "loop_verify.py"
    workflow = ROOT / ".github" / "workflows" / "loop-audit.yml"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    for phrase in (
        "scripts/loop_audit.py",
        "scripts/validate_plugin_package.py",
        "scripts/check_governance.py",
        "tests/test_goal_guard.py",
        "py_compile",
        "git diff --check",
        "PYTHONPYCACHEPREFIX",
        "Path.cwd()",
    ):
        assert phrase in text
    workflow_text = workflow.read_text(encoding="utf-8")
    assert "GOAL_MATRIX_APPROVED" not in workflow_text
    assert "fetch-depth: 0" in workflow_text
    assert "fetch-tags: true" in workflow_text
    assert workflow_text.count("python3 scripts/loop_verify.py --require-level L3") == 1


def test_ci_workflow_delegates_native_surfaces_to_shared_verifier():
    workflow_text = (ROOT / ".github" / "workflows" / "loop-audit.yml").read_text(encoding="utf-8")
    verify_text = (ROOT / "scripts" / "loop_verify.py").read_text(encoding="utf-8")
    for phrase in (
        "python3 scripts/lint_python.py",
        "python3 tests/test_goal_guard.py",
        "python3 scripts/validate_plugin_package.py --root .",
        "node --test pi-extension/test/extension.test.js",
    ):
        assert phrase not in workflow_text
    for phrase in ("scripts/lint_python.py", "tests/test_goal_guard.py", "scripts/validate_plugin_package.py"):
        assert phrase in verify_text


def test_ci_workflow_uses_current_official_actions():
    workflow_text = (ROOT / ".github" / "workflows" / "loop-audit.yml").read_text(encoding="utf-8")

    assert "actions/checkout@v6" in workflow_text
    assert "actions/setup-python@v6" in workflow_text
    assert "actions/setup-node@v6" in workflow_text
    assert 'node-version: "24"' in workflow_text


def test_ci_workflow_has_pr_gate_python_matrix_and_lint():
    workflow_text = (ROOT / ".github" / "workflows" / "loop-audit.yml").read_text(
        encoding="utf-8"
    )
    verify_text = (ROOT / "scripts" / "loop_verify.py").read_text(encoding="utf-8")

    assert "pull_request:" in workflow_text
    assert "strategy:" in workflow_text
    assert "matrix:" in workflow_text
    assert 'python-version: ["3.10", "3.12", "3.14"]' in workflow_text
    assert "python-version: ${{ matrix.python-version }}" in workflow_text
    assert "scripts/lint_python.py" in verify_text


def test_ci_workflow_l3_required_gate():
    workflow_text = (ROOT / ".github" / "workflows" / "loop-audit.yml").read_text(encoding="utf-8")

    assert "python3 scripts/loop_verify.py --require-level L3" in workflow_text


def test_governance_workflow_passes_event_diff_range():
    workflow_text = (ROOT / ".github" / "workflows" / "loop-audit.yml").read_text(encoding="utf-8")

    assert "GOAL_MATRIX_BASE_SHA" in workflow_text
    assert "github.event.pull_request.base.sha || github.event.before" in workflow_text
    assert "GOAL_MATRIX_HEAD_SHA" in workflow_text
    assert "github.event.pull_request.head.sha || github.sha" in workflow_text


def test_ci_workflow_runs_on_push_and_pull_request_only():
    text = (ROOT / ".github" / "workflows" / "loop-audit.yml").read_text(encoding="utf-8")
    assert "push:" in text
    assert "pull_request:" in text
    assert "schedule:" not in text
    assert "cron:" not in text


def test_repository_content_has_no_private_project_context():
    scanned_paths = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and ".goal-matrix" not in path.parts
        and ".recode" not in path.parts
        and "__pycache__" not in path.parts
    ]
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in scanned_paths)
    private_path_patterns = (
        "/" + "Users/",
        "Pycharm" + "Projects/",
        "/" + "private/",
        "KAG" + "_PY",
        "wechat" + "-download-api",
        "agnes" + "_account",
        "Miro" + "Fish",
        "fxzy" + "_GUI",
    )
    for pattern in private_path_patterns:
        assert pattern not in text


def test_session_start_injects_execution_rules():
    result = run_guard(["hook", "SessionStart"], "{}")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["systemMessage"] == "GOAL-MATRIX:ACTIVE"
    assert "Execution discipline" in hook_context(payload)
    assert "Scope control" in hook_context(payload)


def test_session_start_injects_initialization_governance():
    result = run_guard(["hook", "SessionStart"], "{}")

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "Initialization governance" in context
    assert "new-project, iteration, bugfix, legacy-baseline" in context
    assert ".goal-matrix/project-policy.json" in context
    assert "Immutable paths are blocked" in context
    assert "Policy impact" in context


def test_session_start_injects_user_habits():
    result = run_guard(["hook", "SessionStart"], "{}")

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "User operating habits" in context
    assert "read-only request" in context
    assert "named truth source" in context
    assert "scope narrowed" in context


def test_session_start_injects_fusion_workflow_and_generic_routing():
    result = run_guard(["hook", "SessionStart"], "{}")

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "Fusion workflow" in context
    assert "Intake -> Matrix -> Active goal -> Development flow -> Execute -> Verify -> Checkpoint" in context
    assert "Work routing" in context
    assert "Product/UI" in context
    assert "Data/API" in context
    assert "Operations" in context


def test_session_start_injects_skill_plugin_routing_contract():
    result = run_guard(["hook", "SessionStart"], "{}")

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    for phrase in (
        "Skill/plugin routing",
        "brainstorming",
        "writing-plans",
        "test-driven-development",
        "systematic-debugging",
        "verification-before-completion",
        "finishing-a-development-branch",
    ):
        assert phrase in context


def test_session_start_injects_lifecycle_cli_commands():
    result = run_guard(["hook", "SessionStart"], "{}")

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    for phrase in (
        "goal_guard.py classify",
        "goal_guard.py init",
        "goal_guard.py start",
        "goal_guard.py checkpoint",
        "goal_guard.py status",
        "goal_guard.py gate",
        "goal_guard.py policy-gate",
        "goal_guard.py publish-gate",
        "goal_guard.py audit",
    ):
        assert phrase in context


def test_hook_context_explains_visible_codex_goal_boundary():
    result = run_guard(["hook", "SessionStart"], "{}")

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "create_goal" in context
    assert "visible Codex goal" in context


def test_session_start_requires_matrix_first_response_contract():
    result = run_guard(["hook", "SessionStart"], "{}")

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "First substantive response" in context
    assert "goal matrix or active-goal block" in context
    assert "freeform discussion" in context


def test_plugin_skill_and_default_prompt_require_matrix_first_response():
    skill_text = read_text("adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md")
    agent_text = read_text("adapters/codex/skills/goal-matrix-iterative-delivery/agents/openai.yaml")
    manifest = json.loads(read_text(".codex-plugin/plugin.json"))
    default_prompt = " ".join(manifest["interface"]["defaultPrompt"])

    assert "first substantive response" in skill_text.lower()
    assert "goal matrix or active-goal block" in skill_text
    assert "first substantive response" in agent_text.lower()
    assert "first substantive response" in default_prompt.lower()


def test_user_prompt_submit_injects_goal_self_correction_for_goal_work():
    prompt = json.dumps({"prompt": "形成goal 迭代矩阵，然后 迭代goal下发执行"})
    result = run_guard(["hook", "UserPromptSubmit"], prompt)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    context = hook_context(payload)
    assert "Goal self-correction" in context
    assert "Active goal" in context
    assert "Development flow" in context
    assert "truth source" in context


def test_user_prompt_submit_stays_quiet_for_broad_engineering_work_by_default():
    prompt = json.dumps({"prompt": "优化这个 plugin，按我的高频使用习惯和开发流程融合"})

    with tempfile.TemporaryDirectory() as tmp:
        init = run_guard(["init", "--root", tmp, "--type", "iteration"])
        assert init.returncode == 0, init.stderr
        result = run_guard(["hook", "UserPromptSubmit"], prompt, cwd=tmp)

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_user_prompt_submit_uses_broad_engineering_triggers_only_in_strict_mode():
    prompt = json.dumps({"prompt": "优化这个 plugin，按我的高频使用习惯和开发流程融合"})

    with tempfile.TemporaryDirectory() as tmp:
        init = run_guard(["init", "--root", tmp, "--type", "iteration"])
        assert init.returncode == 0, init.stderr
        policy_path = Path(tmp) / ".goal-matrix" / "project-policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["triggerMode"] = "strict"
        policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = run_guard(["hook", "UserPromptSubmit"], prompt, cwd=tmp)

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "Fusion workflow" in context
    assert "Work routing" in context
    assert "Goal self-correction" in context


def test_user_prompt_submit_injects_loop_engineering_commit_policy():
    prompt = json.dumps({"prompt": "loop-engineering 自动循环工程 小步提交 合并 推送"})
    result = run_guard(["hook", "UserPromptSubmit"], prompt)

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "Loop engineering" in context
    assert "checkpoint commit" in context
    assert "preserve verified checkpoint commits" in context
    assert "clean, integrated branch" in context
    assert "push" in context


def test_user_prompt_submit_classifies_chinese_test_request_as_verify_phase():
    prompt = json.dumps({"prompt": "我已重启codex，再次测试loop-engineering能力"})
    result = run_guard(["hook", "UserPromptSubmit"], prompt)

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "Loop phase: verify" in context
    assert "truth-source check" in context


def test_user_prompt_submit_classifies_unclear_draft_as_clarify_phase():
    prompt = json.dumps({"prompt": "我有一个草案，但是需求还不清晰，先讨论设计"})

    with tempfile.TemporaryDirectory() as tmp:
        init = run_guard(["init", "--root", tmp, "--type", "iteration"])
        assert init.returncode == 0, init.stderr
        policy_path = Path(tmp) / ".goal-matrix" / "project-policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["strictMode"] = True
        policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = run_guard(["hook", "UserPromptSubmit"], prompt, cwd=tmp)

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "Loop phase: clarify" in context
    assert "ask blocking questions before implementation" in context


def test_user_prompt_submit_classifies_execute_request_as_execute_phase():
    prompt = json.dumps({"prompt": "执行 goal 迭代，开始实现当前 active goal"})
    result = run_guard(["hook", "UserPromptSubmit"], prompt)

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "Loop phase: execute" in context
    assert "one active goal only" in context


def test_lifecycle_hooks_inject_single_step_boundaries():
    for event, phrase in (
        ("PreToolUse", "Before tool use"),
        ("PostToolUse", "After tool use"),
        ("Stop", "Before completion"),
    ):
        result = run_guard(["hook", event], "{}")
        assert result.returncode == 0, result.stderr
        context = hook_context(json.loads(result.stdout))
        assert phrase in context
        assert "one loop step" in context


def test_lifecycle_hooks_include_fast_lane_boundary():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(root / ".goal-matrix" / "goals" / "active-goal.md", "Active goal: none\n")
        results = [run_guard(["hook", event], "{}", cwd=tmp) for event in ("PreToolUse", "PostToolUse", "Stop")]

    for result in results:
        assert result.returncode == 0, result.stderr
        context = hook_context(json.loads(result.stdout))
        assert "Fast Lane" in context
        assert "trivial" in context
        assert "no active goal" in context


def test_lifecycle_hooks_include_resume_status_context():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        active_goal = next(
            line.split(":", 1)[1].strip()
            for line in (Path(tmp) / ".goal-matrix" / "goals" / "active-goal.md").read_text().splitlines()
            if line.startswith("Active goal:")
        )
        results = [run_guard(["hook", event], "{}", cwd=tmp) for event in ("PreToolUse", "PostToolUse", "Stop")]

    for result in results:
        assert result.returncode == 0, result.stderr
        context = hook_context(json.loads(result.stdout))
        assert "Project initialization status" in context
        assert f"Active goal: {active_goal}" in context
        assert "Next loop:" in context
        assert "Goal matrix:" in context
        assert "child goals" in context


def test_stop_hook_demands_next_loop_handoff():
    result = run_guard(["hook", "Stop"], "{}")

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "Next loop:" in context
    assert "select next pending goal" in context
    assert "continue with it before final completion" in context
    assert "mark blocked" not in context
    assert "keep the active goal open" in context


def test_codex_hook_payload_fixtures_drive_lifecycle_and_gate_paths():
    user_prompt = run_guard(["hook", "UserPromptSubmit"], read_hook_fixture("user-prompt-goal-matrix.json"))
    stop = run_guard(["hook", "Stop"], read_hook_fixture("stop-empty.json"))

    with tempfile.TemporaryDirectory() as tmp:
        policy_root = Path(tmp) / "policy"
        make_policy_project(policy_root, immutablePaths=["secrets/**"], protectedCommands=["git reset --hard"])
        immutable = run_guard(
            ["policy-gate", "--root", str(policy_root), "--hook"],
            read_hook_fixture("pre-tool-immutable-path.json"),
        )
        protected = run_guard(
            ["policy-gate", "--root", str(policy_root), "--hook"],
            read_hook_fixture("pre-tool-protected-command.json"),
        )
        edit = run_guard(
            ["policy-gate", "--root", str(policy_root), "--hook"],
            read_hook_fixture("pre-tool-edit.json"),
        )
        patch = run_guard(
            ["policy-gate", "--root", str(policy_root), "--hook"],
            read_hook_fixture("pre-tool-apply-patch.json"),
        )
        shell_args = run_guard(
            ["policy-gate", "--root", str(policy_root), "--hook"],
            read_hook_fixture("pre-tool-shell-args.json"),
        )
        unknown = run_guard(
            ["policy-gate", "--root", str(policy_root), "--hook", "--debug"],
            read_hook_fixture("pre-tool-unknown.json"),
        )

        publish_root = make_publish_repo(Path(tmp) / "publish")
        git_commit(publish_root, "one.txt", "one\n", "one")
        git_commit(publish_root, "two.txt", "two\n", "two")
        write_file(publish_root / "dirty.txt", "dirty\n")
        publish = run_guard(
            ["publish-gate", "--root", str(publish_root), "--hook"],
            read_hook_fixture("pre-tool-git-push.json"),
        )

    assert user_prompt.returncode == 0, user_prompt.stderr
    assert "Goal self-correction" in hook_context(json.loads(user_prompt.stdout))
    assert stop.returncode == 0, stop.stderr
    assert "Before completion" in hook_context(json.loads(stop.stdout))
    assert immutable.returncode == 1
    assert "immutable path" in immutable.stderr
    assert protected.returncode == 1
    assert "protected command" in protected.stderr
    assert edit.returncode == 1
    assert "immutable path" in edit.stderr
    assert patch.returncode == 1
    assert "immutable path" in patch.stderr
    assert shell_args.returncode == 1
    assert "protected command" in shell_args.stderr
    assert unknown.returncode == 0, unknown.stderr
    assert json.loads(unknown.stdout) == {"paths": [], "commands": []}
    assert publish.returncode == 1
    assert "uncommitted changes" in publish.stderr


def test_policy_gate_debug_reports_paths_and_commands():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_policy_project(root, immutablePaths=["secrets/**"], protectedCommands=["git reset --hard"])
        payload = json.dumps(
            {
                "tool_input": {
                    "patch": "*** Begin Patch\n*** Update File: secrets/token.txt\n@@\n-old\n+new\n*** End Patch\n",
                    "args": ["git", "reset", "--hard", "HEAD"],
                }
            }
        )
        result = run_guard(["policy-gate", "--root", str(root), "--hook", "--debug"], payload)

    assert result.returncode == 1
    assert json.loads(result.stdout) == {"paths": ["secrets/token.txt"], "commands": ["git reset --hard HEAD"]}
    assert "immutable path" in result.stderr
    assert "protected command" in result.stderr


def test_policy_gate_fails_closed_for_invalid_existing_policy():
    cases = (
        ("{broken", "invalid project policy JSON"),
        ("[]", "top-level value must be an object"),
        ('{"version": 2}', "expected 1"),
    )
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        policy_path = root / ".goal-matrix" / "project-policy.json"
        policy_path.parent.mkdir(parents=True)

        missing = run_guard(["policy-gate", "--root", tmp, "--hook"], "{}")
        assert missing.returncode == 0, missing.stderr

        for contents, diagnostic in cases:
            write_file(policy_path, contents)
            result = run_guard(["policy-gate", "--root", tmp, "--hook"], "{}")
            assert result.returncode == 1
            assert diagnostic in result.stderr


def test_user_prompt_submit_triggers_for_self_evolution_runs():
    prompt = json.dumps({"prompt": "开始自我进化，连续迭代到预算、阻塞或没有 pending goal"})
    result = run_guard(["hook", "UserPromptSubmit"], prompt)

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "self-evolution run" in context
    assert "pending goals already recorded" in context
    assert "never synthesize work" in context


def test_codex_hook_config_wires_loop_events():
    hooks = json.loads(read_text("adapters/codex/hooks/codex-lifecycle-hooks.json"))["hooks"]
    for event in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"):
        assert event in hooks


def test_codex_hook_config_invokes_lifecycle_commands():
    hooks = json.loads(read_text("adapters/codex/hooks/codex-lifecycle-hooks.json"))["hooks"]
    user_prompt_command = hooks["UserPromptSubmit"][0]["hooks"][0]["command"]
    user_prompt_command_windows = hooks["UserPromptSubmit"][0]["hooks"][0]["commandWindows"]
    pre_tool_command = hooks["PreToolUse"][0]["hooks"][0]["command"]
    stop_command = hooks["Stop"][0]["hooks"][0]["command"]
    stop_command_windows = hooks["Stop"][0]["hooks"][0]["commandWindows"]

    assert " hook UserPromptSubmit" in user_prompt_command
    assert " start --root ." not in user_prompt_command
    assert " start --root ." not in user_prompt_command_windows
    assert "CODEX_PLUGIN_ROOT" in user_prompt_command
    assert " policy-gate --root . --hook" in pre_tool_command
    assert " publish-gate --root . --hook" in pre_tool_command
    assert pre_tool_command.index(" policy-gate --root . --hook") < pre_tool_command.index(" publish-gate --root . --hook")
    assert " hook PreToolUse" in pre_tool_command
    assert " completion-gate --root ." in stop_command
    assert " --verify" not in stop_command
    assert " active-verify" not in stop_command
    assert "scripts/loop_verify.py" not in stop_command
    assert 'rc=$?; if [ "$rc" -ne 0 ]; then exit "$rc"; fi' in stop_command
    assert "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }" in stop_command_windows
    assert " hook Stop" in stop_command


def test_user_prompt_submit_does_not_auto_start_goal_state():
    hooks = json.loads(read_text("adapters/codex/hooks/codex-lifecycle-hooks.json"))["hooks"]
    hook = hooks["UserPromptSubmit"][0]["hooks"][0]
    docs = "\n".join(read_text(path) for path in ("README.md", "README.zh.md", "core/protocol.md"))

    assert "hook UserPromptSubmit" in hook["command"]
    assert "start --root" not in hook["command"]
    assert "start --root" not in hook["commandWindows"]
    assert "UserPromptSubmit does not run `start`" in docs
    assert "UserPromptSubmit 不会运行 `start`" in docs


def test_active_verify_runs_target_active_goal_verification_command():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            f"""# Active Goal

Active goal: G1 - Verify target
Initialization type: iteration
Policy impact: none
Touched paths: verified.txt
Delivery boundary: target verification
Skipped: none
Truth source: verified.txt
Verification: {sys.executable} -c "from pathlib import Path; Path('verified.txt').write_text('ok')"
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
        )

        result = run_guard(["active-verify", "--root", tmp])
        verified = (root / "verified.txt").read_text(encoding="utf-8") if (root / "verified.txt").is_file() else ""

    assert result.returncode == 0, result.stderr
    assert verified == "ok"


def test_active_verify_runs_compound_verification_command():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        first = f"{sys.executable} -c \"from pathlib import Path; Path('first.txt').write_text('one')\""
        second = f"{sys.executable} -c \"from pathlib import Path; Path('second.txt').write_text('two')\""
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            f"""# Active Goal

Active goal: G1 - Verify target
Initialization type: iteration
Policy impact: none
Touched paths: first.txt, second.txt
Delivery boundary: compound verification
Skipped: none
Truth source: first.txt and second.txt
Verification: {first} && {second}
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
        )

        result = run_guard(["active-verify", "--root", tmp])
        first_text = (root / "first.txt").read_text(encoding="utf-8") if (root / "first.txt").is_file() else ""
        second_text = (root / "second.txt").read_text(encoding="utf-8") if (root / "second.txt").is_file() else ""

    assert result.returncode == 0, result.stderr
    assert first_text == "one"
    assert second_text == "two"


def test_active_verify_uses_state_json_instead_of_edited_markdown():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_guard(["start", "--root", tmp], "Verify JSON contract").returncode == 0
        state_path = root / ".goal-matrix" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state_goal = state["goalMatrix"]["childGoals"][0]
        state_goal["verification"] = shlex.join(
            [sys.executable, "-c", "from pathlib import Path; Path('state-source').write_text('ok')"]
        )
        write_file(state_path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            f"""# Active Goal

Active goal: G1 - Verify JSON contract
Initialization type: iteration
Policy impact: none
Touched paths: markdown-source
Delivery boundary: edited boundary
Skipped: none
Truth source: markdown-source
Verification: {sys.executable} -c "from pathlib import Path; Path('markdown-source').write_text('wrong')"
Development flow: inspect -> verify
""",
        )

        result = run_guard(["active-verify", "--root", tmp])

        assert result.returncode == 0, result.stderr
        assert (root / "state-source").read_text(encoding="utf-8") == "ok"
        assert not (root / "markdown-source").exists()


def test_audit_rejects_active_goal_projection_drift_and_status_uses_state():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_guard(["start", "--root", tmp], "JSON boundary").returncode == 0
        state_path = root / ".goal-matrix" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state_goal = state["goalMatrix"]["childGoals"][0]
        state_goal.update(
            {
                "deliveryBoundary": "state boundary",
                "truthSource": "state truth",
                "verification": "python3 --version",
            }
        )
        write_file(state_path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        active_path = root / ".goal-matrix" / "goals" / "active-goal.md"
        write_file(active_path, active_path.read_text(encoding="utf-8").replace(
            "Delivery boundary: one bounded child goal from the current prompt",
            "Delivery boundary: edited by hand",
        ))

        audit = run_guard(["audit", "--root", tmp])
        status = run_guard(["status", "--root", tmp])

        assert audit.returncode == 1
        assert "active goal projection drift" in audit.stderr
        payload = json.loads(status.stdout)
        assert payload["nextAction"]["deliveryBoundary"] == "state boundary"
        assert payload["nextAction"]["truthSource"] == "state truth"


def test_stop_hook_preserves_completion_gate_failure():
    hooks = json.loads(read_text("adapters/codex/hooks/codex-lifecycle-hooks.json"))["hooks"]
    stop_command = hooks["Stop"][0]["hooks"][0]["command"]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plugin_root = root / "plugin"
        project_root = root / "project"
        marker = plugin_root / "stop-called"
        write_file(plugin_root / ".codex-plugin" / "plugin.json", "{}\n")
        write_file(
            plugin_root / "core" / "goal_guard.py",
            "import pathlib, sys\n"
            "if 'completion-gate' in sys.argv:\n"
            "    raise SystemExit(7)\n"
            "if sys.argv[-2:] == ['hook', 'Stop']:\n"
            f"    pathlib.Path({str(marker)!r}).write_text('called')\n",
        )
        project_root.mkdir()

        env = {**os.environ, "CODEX_PLUGIN_ROOT": str(plugin_root)}
        result = subprocess.run(
            ["/bin/sh", "-c", stop_command],
            input="{}",
            text=True,
            capture_output=True,
            cwd=project_root,
            env=env,
        )

        assert result.returncode == 7
        assert not marker.exists()


def test_stop_hook_never_executes_active_goal_verification():
    hooks = json.loads(read_text("adapters/codex/hooks/codex-lifecycle-hooks.json"))["hooks"]
    stop_command = hooks["Stop"][0]["hooks"][0]["command"]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        marker = root / "stop-side-effect"
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_guard(["start", "--root", tmp], "Unsafe verification").returncode == 0
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            f"""# Active Goal

Active goal: G1 - Unsafe verification
Initialization type: iteration
Policy impact: none
Touched paths: stop-side-effect
Delivery boundary: Stop must not execute this command
Skipped: none
Truth source: stop-side-effect
Verification: {sys.executable} -c "from pathlib import Path; Path('stop-side-effect').write_text('executed')"
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
        )
        write_file(root / ".goal-matrix" / "loop-note.md", "Reviewer: approved\n")

        result = subprocess.run(
            ["/bin/sh", "-c", stop_command],
            input="",
            text=True,
            capture_output=True,
            cwd=root,
            env={**os.environ, "CODEX_PLUGIN_ROOT": str(ROOT)},
        )

        assert not marker.exists()
        assert result.returncode != 0
        assert "checkpoint" in result.stderr.lower()


def test_stop_hook_allows_no_active_goal():
    hooks = json.loads(read_text("adapters/codex/hooks/codex-lifecycle-hooks.json"))["hooks"]
    stop_command = hooks["Stop"][0]["hooks"][0]["command"]

    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_structured_start(tmp, "Finish loop").returncode == 0
        verify = [sys.executable, "-c", "raise SystemExit(0)"]
        assert run_guard(["checkpoint", "--root", tmp, "--", *verify]).returncode == 0

        env = {**os.environ, "CODEX_PLUGIN_ROOT": str(ROOT)}
        result = subprocess.run(
            ["/bin/sh", "-c", stop_command],
            input="{}",
            text=True,
            capture_output=True,
            cwd=project_root,
            env=env,
        )

    assert result.returncode == 0, result.stderr


def test_stop_hook_rejects_dirty_no_active_goal_without_fast_lane_evidence():
    hooks = json.loads(read_text("adapters/codex/hooks/codex-lifecycle-hooks.json"))["hooks"]
    stop_command = hooks["Stop"][0]["hooks"][0]["command"]

    with tempfile.TemporaryDirectory() as tmp:
        project_root = Path(tmp)
        subprocess.run(["git", "init"], cwd=project_root, check=True, capture_output=True, text=True)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            project_root / ".goal-matrix" / "goals" / "active-goal.md",
            "Active goal: none\n",
        )
        subprocess.run(["git", "add", "."], cwd=project_root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "baseline"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
        write_file(project_root / "note.txt", "dirty\n")

        env = {**os.environ, "CODEX_PLUGIN_ROOT": str(ROOT)}
        result = subprocess.run(
            ["/bin/sh", "-c", stop_command],
            input="{}",
            text=True,
            capture_output=True,
            cwd=project_root,
            env=env,
        )

    assert result.returncode == 1
    assert "Fast Lane requires focused verification" in result.stderr


def test_codex_hook_commands_fail_open_without_plugin_root_in_foreign_cwd():
    hooks = json.loads(read_text("adapters/codex/hooks/codex-lifecycle-hooks.json"))["hooks"]
    env = {key: value for key, value in os.environ.items() if key != "CODEX_PLUGIN_ROOT"}

    def run_commands(foreign_root):
        for event in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"):
            command = hooks[event][0]["hooks"][0]["command"]
            result = subprocess.run(
                ["/bin/sh", "-c", command],
                input="{}",
                text=True,
                capture_output=True,
                cwd=foreign_root,
                env=env,
            )

            assert result.returncode == 0, f"{event}: {result.stderr}"
            assert "can't open file" not in result.stderr, f"{event}: {result.stderr}"
            assert "foreign goal guard executed" not in result.stdout + result.stderr, event

    with tempfile.TemporaryDirectory() as tmp:
        foreign_root = Path(tmp)
        assert not (foreign_root / "core" / "goal_guard.py").exists()
        run_commands(foreign_root)

        write_file(
            foreign_root / "core" / "goal_guard.py",
            "import sys\nprint('foreign goal guard executed')\nsys.exit(3)\n",
        )
        run_commands(foreign_root)


def test_public_package_copy_uses_generic_scope_language():
    banned = ("pony" + "tail", "super" + "power", "super" + "powers", "cl" + "aud")
    paths = (
        "README.md",
        "README.zh.md",
        ".codex-plugin/plugin.json",
        "adapters/codex/README.md",
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
        "adapters/codex/skills/goal-matrix-iterative-delivery/agents/openai.yaml",
        "core/goal_guard.py",
    )
    text = "\n".join(read_text(path).lower() for path in paths)
    for token in banned:
        assert token not in text


def test_user_prompt_submit_reports_missing_project_initialization():
    prompt = json.dumps({"prompt": "goal matrix 工程化"})
    with tempfile.TemporaryDirectory() as tmp:
        result = run_guard(["hook", "UserPromptSubmit"], prompt, cwd=tmp)

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "Project initialization status" in context
    assert "missing .goal-matrix/project-policy.json" in context
    assert "first loop action" in context


def test_user_prompt_submit_stays_quiet_for_unrelated_prompts():
    result = run_guard(["hook", "UserPromptSubmit"], json.dumps({"prompt": "翻译这句话"}))

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_user_prompt_submit_stays_quiet_for_ordinary_fix_prompt_by_default():
    prompt = json.dumps({"prompt": "修复登录页按钮样式，然后提交代码"})

    with tempfile.TemporaryDirectory() as tmp:
        init = run_guard(["init", "--root", tmp, "--type", "iteration"])
        assert init.returncode == 0, init.stderr
        result = run_guard(["hook", "UserPromptSubmit"], prompt, cwd=tmp)

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_agent_metadata_disables_broad_implicit_invocation_by_default():
    agent = read_text("adapters/codex/skills/goal-matrix-iterative-delivery/agents/openai.yaml")

    assert "allow_implicit_invocation: false" in agent


def test_audit_rejects_completion_without_evidence():
    draft = """
# Parser Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | User can parse files | Add parser | CLI output | Unit test | In progress |

Active goal: G1 - parser
Initialization type: bugfix
Policy impact: none
Touched paths: core/goal_guard.py
Delivery boundary: parser only
Skipped: UI
Truth source: tests
Verification: unit test
Development flow: inspect -> failing check -> implement -> verify -> checkpoint

Completed G1: parser is done.
"""
    result = run_guard(["audit"], draft)

    assert result.returncode == 1
    assert "completion evidence" in result.stderr


def test_audit_rejects_broad_active_goal_without_slice():
    draft = """
# Platform Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | Ship the whole platform | Build all backend and frontend | Tests | Full suite | Pending |

Active goal: G1 - 完整平台全部重构
Initialization type: iteration
Policy impact: none
Touched paths: app/**
Delivery boundary: everything
Skipped: nothing
Truth source: tests
Verification: full suite
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
"""
    result = run_guard(["audit"], draft)

    assert result.returncode == 1
    assert "active goal too broad" in result.stderr


def test_audit_rejects_ui_only_completion_claims():
    draft = """
# UX Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | UI is clearer | Copy update | Browser and API | Browser check | Done |

Active goal: G1 - copy update
Initialization type: iteration
Policy impact: none
Touched paths: ui/**
Delivery boundary: one view
Skipped: backend
Truth source: browser
Verification: browser check
Development flow: inspect -> failing check -> implement -> verify -> checkpoint

Completed G1: 页面看起来好了，UI refresh 正常.
"""
    result = run_guard(["audit"], draft)

    assert result.returncode == 1
    assert "UI-only evidence" in result.stderr


def test_audit_accepts_matrix_active_goal_and_verification():
    draft = """
# Parser Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | User can parse files | Add parser | CLI output | Unit test | Done |

Active goal: G1 - parser
Initialization type: bugfix
Policy impact: none
Touched paths: core/goal_guard.py
Delivery boundary: parser only
Skipped: UI
Truth source: tests
Verification: unit test
Development flow: inspect -> failing check -> implement -> verify -> checkpoint

Completed G1: parser works. Verified with `python -m pytest tests/test_parser.py`. Checkpoint updated.
Next loop: choose the next pending goal from the matrix.
"""
    result = run_guard(["audit"], draft)

    assert result.returncode == 0, result.stderr


def test_audit_rejects_completion_without_next_loop_handoff():
    draft = """
# Parser Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | User can parse files | Add parser | CLI output | Unit test | Done |

Active goal: G1 - parser
Initialization type: bugfix
Policy impact: none
Touched paths: core/goal_guard.py
Delivery boundary: parser only
Skipped: UI
Truth source: tests
Verification: python3 tests/test_goal_guard.py
Development flow: inspect -> failing check -> implement -> verify -> checkpoint

Completed G1: parser works. Verified with `python3 tests/test_goal_guard.py`. Checkpoint updated.
"""
    result = run_guard(["audit"], draft)

    assert result.returncode == 1
    assert "next loop" in result.stderr.lower()


def test_audit_rejects_active_goal_without_development_flow():
    draft = """
# Parser Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | User can parse files | Add parser | CLI output | Unit test | Pending |

Active goal: G1 - parser
Delivery boundary: parser only
Skipped: UI
Verification: unit test
"""
    result = run_guard(["audit"], draft)

    assert result.returncode == 1
    assert "Development flow" in result.stderr


def test_audit_rejects_unclear_draft_without_clarity_decision():
    draft = """
Draft requirement: 草案还不清晰，需要先讨论设计。

# Parser Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | User can parse files | Add parser | CLI output | Unit test | Pending |

Active goal: G1 - parser
Initialization type: iteration
Policy impact: none
Touched paths: core/goal_guard.py
Delivery boundary: parser only
Skipped: UI
Truth source: tests
Verification: python3 tests/test_goal_guard.py
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
"""
    result = run_guard(["audit"], draft)

    assert result.returncode == 1
    assert "clarity decision" in result.stderr.lower()


def test_audit_accepts_unclear_draft_with_clarity_decision():
    draft = """
Draft requirement: 草案还不清晰，需要先讨论设计。
Clarity decision: blocking questions resolved; proceed to one active goal.

# Parser Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | User can parse files | Add parser | CLI output | Unit test | Pending |

Active goal: G1 - parser
Initialization type: iteration
Policy impact: none
Touched paths: core/goal_guard.py
Delivery boundary: parser only
Skipped: UI
Truth source: tests
Verification: python3 tests/test_goal_guard.py
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
"""
    result = run_guard(["audit"], draft)

    assert result.returncode == 0, result.stderr


def test_audit_rejects_multiple_active_goals():
    draft = VALID_INITIALIZED_GOAL.replace(
        "Active goal: G1 - parser",
        "Active goal: G1 - parser\nActive goal: G2 - formatter",
    )
    result = run_guard(["audit"], draft)

    assert result.returncode == 1
    assert "one active goal" in result.stderr


VALID_INITIALIZED_GOAL = """
# Parser Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | User can parse files | Add parser | CLI output | Unit test | Done |

Active goal: G1 - parser
Initialization type: bugfix
Policy impact: none
Touched paths: core/goal_guard.py, tests/test_goal_guard.py
Delivery boundary: parser only
Skipped: UI
Truth source: tests
Verification: python3 tests/test_goal_guard.py
Development flow: inspect -> failing check -> implement -> verify -> checkpoint

Completed G1: parser works. Verified with `python3 tests/test_goal_guard.py`. Checkpoint updated.
Next loop: choose the next pending goal from the matrix.
"""


def test_audit_rejects_missing_initialization_type():
    draft = VALID_INITIALIZED_GOAL.replace("Initialization type: bugfix\n", "")
    result = run_guard(["audit"], draft)
    assert result.returncode == 1
    assert "Initialization type" in result.stderr


def test_audit_rejects_missing_policy_impact():
    draft = VALID_INITIALIZED_GOAL.replace("Policy impact: none\n", "")
    result = run_guard(["audit"], draft)
    assert result.returncode == 1
    assert "Policy impact" in result.stderr


def test_audit_rejects_missing_touched_paths():
    draft = VALID_INITIALIZED_GOAL.replace(
        "Touched paths: core/goal_guard.py, tests/test_goal_guard.py\n",
        "",
    )
    result = run_guard(["audit"], draft)
    assert result.returncode == 1
    assert "Touched paths" in result.stderr


def test_audit_rejects_missing_truth_source():
    draft = VALID_INITIALIZED_GOAL.replace("Truth source: tests\n", "")
    result = run_guard(["audit"], draft)
    assert result.returncode == 1
    assert "Truth source" in result.stderr


def test_audit_rejects_completion_without_checkpoint():
    draft = VALID_INITIALIZED_GOAL.replace(" Checkpoint updated.", "")
    result = run_guard(["audit"], draft)
    assert result.returncode == 1
    assert "checkpoint" in result.stderr.lower()


def test_audit_rejects_blocked_policy_impact():
    draft = VALID_INITIALIZED_GOAL.replace("Policy impact: none", "Policy impact: blocked")
    result = run_guard(["audit"], draft)
    assert result.returncode == 1
    assert "blocked" in result.stderr


def test_audit_rejects_approval_required_without_approval_note():
    draft = VALID_INITIALIZED_GOAL.replace("Policy impact: none", "Policy impact: approval-required")
    result = run_guard(["audit"], draft)
    assert result.returncode == 1
    assert "approval" in result.stderr.lower()


def test_audit_accepts_approval_required_with_approval_note():
    draft = VALID_INITIALIZED_GOAL.replace(
        "Policy impact: none",
        "Policy impact: approval-required\nApproval: approved by user",
    )
    result = run_guard(["audit"], draft)
    assert result.returncode == 0, result.stderr


def test_audit_accepts_valid_initialized_goal():
    result = run_guard(["audit"], VALID_INITIALIZED_GOAL)
    assert result.returncode == 0, result.stderr


def test_audit_rejects_push_claim_without_final_verification():
    unverified = VALID_INITIALIZED_GOAL.replace(
        "Completed G1: parser works. Verified with `python3 tests/test_goal_guard.py`. Checkpoint updated.",
        "Completed G1: parser works. Checkpoint updated.",
    )
    draft = unverified + "\nPushed branch to origin.\n"
    result = run_guard(["audit"], draft)

    assert result.returncode == 1
    assert "final verification" in result.stderr


def test_audit_accepts_push_claim_after_final_verification():
    draft = VALID_INITIALIZED_GOAL + "\nPushed branch to origin after final verification.\n"
    result = run_guard(["audit"], draft)

    assert result.returncode == 0, result.stderr


def write_file(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git_commit(root, path, text, message):
    write_file(root / path, text)
    subprocess.run(["git", "add", path], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", message],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def make_publish_repo(root):
    remote = root / "remote.git"
    repo = root / "repo"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True)
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    git_commit(repo, "README.md", "base\n", "base")
    subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "push", "-u", "origin", branch], cwd=repo, check=True, capture_output=True, text=True)
    return repo


def make_policy_project(root, **updates):
    init = run_guard(["init", "--root", str(root), "--type", "iteration"])
    assert init.returncode == 0, init.stderr
    policy_path = root / ".goal-matrix" / "project-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy.update(updates)
    policy_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_policy_gate_blocks_immutable_paths_from_tool_payload():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_policy_project(root, immutablePaths=["secrets/**"])
        payload = json.dumps({"tool_input": {"path": "secrets/token.txt"}})
        result = run_guard(["policy-gate", "--root", str(root), "--hook"], payload)

    assert result.returncode == 1
    assert "immutable path" in result.stderr
    assert "secrets/token.txt" in result.stderr


def test_policy_gate_blocks_approval_required_paths_without_approval():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_policy_project(root, approvalRequiredPaths=["package.json"])
        payload = json.dumps({"tool_input": {"file": "package.json"}})
        denied = run_guard(["policy-gate", "--root", str(root), "--hook"], payload)
        approved = run_guard(
            ["policy-gate", "--root", str(root), "--hook"],
            payload,
            env={**os.environ, "GOAL_MATRIX_APPROVED": "1"},
        )

    assert denied.returncode == 1
    assert "requires approval" in denied.stderr
    assert approved.returncode == 0, approved.stderr


def test_policy_gate_dotfile_paths_keep_leading_dot():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_policy_project(root, approvalRequiredPaths=[".env", ".env.*"])

        env_file = run_guard(
            ["policy-gate", "--root", str(root), "--hook", "--debug"],
            json.dumps({"tool_input": {"path": ".env"}}),
        )
        env_local = run_guard(
            ["policy-gate", "--root", str(root), "--hook"],
            json.dumps({"tool_input": {"path": "./.env.local"}}),
        )

    assert env_file.returncode == 1
    assert json.loads(env_file.stdout)["paths"] == [".env"]
    assert ".env requires approval" in env_file.stderr
    assert env_local.returncode == 1
    assert ".env.local requires approval" in env_local.stderr


def test_policy_gate_shell_literal_path_requires_approval_and_documents_dynamic_boundary():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_policy_project(root, approvalRequiredPaths=[".env"])
        payload = json.dumps({"tool_input": {"cmd": "sed -i s/old/new/ .env"}})

        denied = run_guard(["policy-gate", "--root", str(root), "--hook", "--debug"], payload)
        approved = run_guard(
            ["policy-gate", "--root", str(root), "--hook"],
            payload,
            env={**os.environ, "GOAL_MATRIX_APPROVED": "1"},
        )

    threat_model = read_text("docs/threat-model.md")
    assert denied.returncode == 1
    assert json.loads(denied.stdout)["paths"] == [".env"]
    assert ".env requires approval" in denied.stderr
    assert approved.returncode == 0, approved.stderr
    assert "literal shell path tokens" in threat_model
    assert "dynamic shell expansion" in threat_model


def test_policy_gate_rejects_unscoped_payload_approval():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_policy_project(root, approvalRequiredPaths=["package.json"])
        payload = json.dumps({"approvalToken": "approved", "tool_input": {"file": "package.json"}})
        result = run_guard(["policy-gate", "--root", str(root), "--hook"], payload)

    assert result.returncode == 1
    assert "requires approval" in result.stderr


def test_policy_gate_accepts_scoped_payload_approval():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_policy_project(root, approvalRequiredPaths=["package.json"])
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            """# Active Goal

Active goal: G1 - approved package change
Initialization type: iteration
Policy impact: approval-required
Touched paths: package.json
Delivery boundary: test approval
Skipped: none
Truth source: policy gate
Verification: policy gate
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
        )
        payload = json.dumps(
            {
                "approval": {
                    "goal": "G1",
                    "paths": ["package.json"],
                    "expiresAt": "2099-01-01T00:00:00Z",
                    "reason": "user approved package change",
                },
                "tool_input": {"file": "package.json"},
            }
        )
        result = run_guard(["policy-gate", "--root", str(root), "--hook"], payload)

    assert result.returncode == 0, result.stderr


def test_policy_gate_rejects_expired_or_path_mismatched_payload_approval():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_policy_project(root, approvalRequiredPaths=["package.json"])
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            """# Active Goal

Active goal: G1 - approved package change
Initialization type: iteration
Policy impact: approval-required
Touched paths: package.json
Delivery boundary: test approval
Skipped: none
Truth source: policy gate
Verification: policy gate
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
        )
        expired = json.dumps(
            {
                "approval": {
                    "goal": "G1",
                    "paths": ["package.json"],
                    "expiresAt": "2000-01-01T00:00:00Z",
                    "reason": "old approval",
                },
                "tool_input": {"file": "package.json"},
            }
        )
        wrong_path = json.dumps(
            {
                "approval": {
                    "goal": "G1",
                    "paths": ["README.md"],
                    "expiresAt": "2099-01-01T00:00:00Z",
                    "reason": "wrong file",
                },
                "tool_input": {"file": "package.json"},
            }
        )
        expired_result = run_guard(["policy-gate", "--root", str(root), "--hook"], expired)
        wrong_path_result = run_guard(["policy-gate", "--root", str(root), "--hook"], wrong_path)

    assert expired_result.returncode == 1
    assert wrong_path_result.returncode == 1


def test_policy_gate_blocks_protected_commands_from_tool_payload():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_policy_project(root, protectedCommands=["rm", "git reset --hard"])
        payload = json.dumps({"tool_input": {"cmd": "git reset --hard HEAD"}})
        result = run_guard(["policy-gate", "--root", str(root), "--hook"], payload)

    assert result.returncode == 1
    assert "protected command" in result.stderr
    assert "git reset --hard" in result.stderr


def commit_goal_matrix(repo, active_goal="none", evidence=True):
    write_file(
        repo / ".goal-matrix" / "goals" / "goal-matrix.md",
        """# Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | Publish verified work | Ship one slice | tests | focused tests | Done |
""",
    )
    write_file(
        repo / ".goal-matrix" / "goals" / "active-goal.md",
        f"""# Active Goal

Active goal: {active_goal}
Initialization type: iteration
Policy impact: none
Touched paths: none
Delivery boundary: publish gate fixture
Skipped: none
Truth source: tests
Verification: focused tests
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
    )
    if evidence:
        write_file(repo / ".goal-matrix" / "evidence" / "G1.log", "Goal: G1\nExit code: 0\n")
    subprocess.run(["git", "add", ".goal-matrix"], cwd=repo, check=True, capture_output=True, text=True)
    if (repo / ".gitignore").exists():
        subprocess.run(["git", "add", ".gitignore"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "goal state"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def test_publish_gate_accepts_multiple_checkpoint_commits():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        git_commit(repo, "one.txt", "one\n", "one")
        git_commit(repo, "two.txt", "two\n", "two")

        result = run_guard(["publish-gate", "--root", str(repo)])

    assert result.returncode == 0, result.stderr


def test_publish_gate_rejects_missing_upstream():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True)
        git_commit(repo, "README.md", "base\n", "base")

        result = run_guard(["publish-gate", "--root", str(repo)])

    assert result.returncode == 1
    assert "missing upstream" in result.stderr


def test_publish_gate_accepts_first_feature_branch_push_against_remote_default():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        subprocess.run(["git", "remote", "set-head", "origin", "--auto"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(["git", "switch", "-c", "feature"], cwd=repo, check=True, capture_output=True, text=True)
        git_commit(repo, "feature.txt", "feature\n", "feature")

        result = run_guard(["publish-gate", "--root", str(repo)])

    assert result.returncode == 0, result.stderr


def test_publish_gate_rejects_first_feature_branch_push_behind_remote_default():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = make_publish_repo(root)
        branch = subprocess.run(
            ["git", "branch", "--show-current"], cwd=repo, check=True, capture_output=True, text=True
        ).stdout.strip()
        subprocess.run(["git", "remote", "set-head", "origin", "--auto"], cwd=repo, check=True, capture_output=True, text=True)
        subprocess.run(["git", "switch", "-c", "feature"], cwd=repo, check=True, capture_output=True, text=True)
        other = root / "other"
        subprocess.run(
            ["git", "clone", "--branch", branch, str(root / "remote.git"), str(other)],
            check=True,
            capture_output=True,
            text=True,
        )
        git_commit(other, "remote.txt", "remote\n", "remote")
        subprocess.run(["git", "push", "origin", branch], cwd=other, check=True, capture_output=True, text=True)
        subprocess.run(["git", "fetch", "origin"], cwd=repo, check=True, capture_output=True, text=True)

        result = run_guard(["publish-gate", "--root", str(repo)])

    assert result.returncode == 1
    assert "remote history not integrated" in result.stderr


def test_publish_gate_rejects_behind_upstream():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = make_publish_repo(root)
        remote = root / "remote.git"
        other = root / "other"
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subprocess.run(["git", "clone", str(remote), str(other)], check=True, capture_output=True, text=True)
        git_commit(other, "remote.txt", "remote\n", "remote")
        subprocess.run(["git", "push", "origin", branch], cwd=other, check=True, capture_output=True, text=True)
        subprocess.run(["git", "fetch", "origin"], cwd=repo, check=True, capture_output=True, text=True)

        result = run_guard(["publish-gate", "--root", str(repo)])

    assert result.returncode == 1
    assert "remote history not integrated" in result.stderr


def test_publish_gate_accepts_single_commit_before_push():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        git_commit(repo, "one.txt", "one\n", "one")

        result = run_guard(["publish-gate", "--root", str(repo)])

    assert result.returncode == 0, result.stderr


def test_publish_gate_rejects_dirty_worktree_before_push():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        git_commit(repo, "one.txt", "one\n", "one")
        write_file(repo / "dirty.txt", "dirty\n")

        result = run_guard(["publish-gate", "--root", str(repo)])

    assert result.returncode == 1
    assert "uncommitted changes" in result.stderr


def test_publish_gate_rejects_active_goal_before_push():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        commit_goal_matrix(repo, active_goal="G2 - Still running")

        result = run_guard(["publish-gate", "--root", str(repo)])

    assert result.returncode == 1
    assert "active goal" in result.stderr


def test_publish_gate_rejects_missing_checkpoint_evidence_before_push():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        commit_goal_matrix(repo, evidence=False)

        result = run_guard(["publish-gate", "--root", str(repo)])

    assert result.returncode == 1
    assert "missing checkpoint evidence" in result.stderr


def test_publish_gate_accepts_single_commit_with_goal_evidence():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        commit_goal_matrix(repo)

        result = run_guard(["publish-gate", "--root", str(repo)])

    assert result.returncode == 0, result.stderr


def test_publish_gate_hook_ignores_non_push_tools():
    payload = json.dumps({"tool_input": {"cmd": "git status --short"}})
    result = run_guard(["publish-gate", "--root", str(ROOT), "--hook"], payload)

    assert result.returncode == 0, result.stderr


def test_publish_gate_hook_accepts_push_with_multiple_commits():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        git_commit(repo, "one.txt", "one\n", "one")
        git_commit(repo, "two.txt", "two\n", "two")
        payload = json.dumps({"tool_input": {"cmd": "git push origin HEAD"}})

        result = run_guard(["publish-gate", "--root", str(repo), "--hook"], payload)

    assert result.returncode == 0, result.stderr


def test_publish_gate_hook_rejects_push_with_git_global_options():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        git_commit(repo, "one.txt", "one\n", "one")
        git_commit(repo, "two.txt", "two\n", "two")
        write_file(repo / "dirty.txt", "dirty\n")
        payload = json.dumps({"tool_input": {"cmd": "git -C . push origin HEAD"}})

        result = run_guard(["publish-gate", "--root", str(repo), "--hook"], payload)

    assert result.returncode == 1
    assert "uncommitted changes" in result.stderr


def test_publish_gate_hook_rejects_publish_action_patterns():
    for command in ("npm publish", "gh release create v1.2.3"):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_publish_repo(Path(tmp))
            write_file(
                repo / ".goal-matrix" / "project-policy.json",
                json.dumps({"version": 1, "publishActionPatterns": ["npm publish", "gh release"]}, indent=2) + "\n",
            )
            subprocess.run(["git", "add", ".goal-matrix"], cwd=repo, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "policy"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
            git_commit(repo, "one.txt", "one\n", "one")
            git_commit(repo, "two.txt", "two\n", "two")
            write_file(repo / "dirty.txt", "dirty\n")
            payload = json.dumps({"tool_input": {"cmd": command}})

            result = run_guard(["publish-gate", "--root", str(repo), "--hook"], payload)

        assert result.returncode == 1, command
        assert "uncommitted changes" in result.stderr


def test_status_command_reports_active_and_next_loop():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            root / ".goal-matrix" / "goals" / "goal-matrix.md",
            """# Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G7 | Resume after restart | Add status readback | CLI output | status command | Pending |
| G8 | Publish clean history | Consolidate commits | Git log | final verification | Pending |
""",
        )
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            """# Active Goal

Active goal: G7 - status readback
Initialization type: iteration
Policy impact: none
Touched paths: core/goal_guard.py
Delivery boundary: status only
Skipped: daemon
Truth source: CLI output
Verification: status command
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
        )

        result = run_guard(["status", "--root", tmp])

    assert result.returncode == 0, result.stderr
    status = json.loads(result.stdout)
    assert status["initialized"] is True
    assert status["auditProblems"] == []
    assert status["activeGoal"] == "G7 - status readback"
    assert status["nextLoop"] == "G8 - Publish clean history"
    assert status["goalMatrix"]["total"] == 2
    assert status["goalMatrix"]["pending"] == 2
    assert status["goalMatrix"]["activeId"] == "G7"
    assert status["goalMatrix"]["childGoals"][0] == {
        "id": "G7",
        "userOutcome": "Resume after restart",
        "engineeringSlice": "Add status readback",
        "truthSource": "CLI output",
        "verification": "status command",
        "status": "Pending",
    }
    assert status["loopStages"] == [
        "project_initialization",
        "work_classification",
        "design",
        "design_gate",
        "execute",
        "review_gate",
        "checkpoint",
        "design_iteration",
    ]


def test_status_command_reports_no_next_loop_when_no_goal_is_pending():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            root / ".goal-matrix" / "goals" / "goal-matrix.md",
            """# Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | Finish runnable loop | Align skill | Doctor output | doctor command | Done |
| G2 | Publish when requested | Consolidate history | Git log | final check | Deferred |
""",
        )
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            """# Active Goal

Active goal: G1 - Finish runnable loop
Initialization type: iteration
Policy impact: none
Touched paths: core/goal_guard.py
Delivery boundary: status only
Skipped: publishing
Truth source: CLI output
Verification: status command
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
        )

        result = run_guard(["status", "--root", tmp])

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["nextLoop"] is None


def test_start_command_creates_pending_active_goal_from_prompt():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        started = run_guard(["start", "--root", tmp], "goal iteration still does not start")
        status_result = run_guard(["status", "--root", tmp])

    assert started.returncode == 0, started.stderr
    payload = json.loads(started.stdout)
    assert payload["activeGoal"] == "G1 - goal iteration still does not start"

    status = json.loads(status_result.stdout)
    assert status["activeGoal"] == "G1 - goal iteration still does not start"
    assert status["goalMatrix"]["pending"] == 1
    assert status["goalMatrix"]["childGoals"][0]["id"] == "G1"
    assert status["goalMatrix"]["childGoals"][0]["status"] == "Pending"


def test_start_command_accepts_complete_structured_contract():
    contract = {
        "userOutcome": "Structured goal",
        "engineeringSlice": "Implement one parser branch",
        "initializationType": "iteration",
        "policyImpact": "none",
        "touchedPaths": ["core/goal_guard.py", "tests/test_goal_guard.py"],
        "deliveryBoundary": "structured start only",
        "skipped": "other commands",
        "truthSource": "state and projection readback",
        "verification": "python3 --version",
        "developmentFlow": "inspect -> failing check -> implement -> verify -> checkpoint",
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        started = run_guard(["start", "--root", tmp], json.dumps(contract))
        audit = run_guard(["audit", "--root", tmp])
        state = json.loads((root / ".goal-matrix" / "state.json").read_text(encoding="utf-8"))
        active_text = (root / ".goal-matrix" / "goals" / "active-goal.md").read_text(encoding="utf-8")

    assert started.returncode == 0, started.stderr
    assert json.loads(started.stdout)["activeGoal"] == "G1 - Structured goal"
    goal = state["goalMatrix"]["childGoals"][0]
    assert goal["contractComplete"] is True
    assert goal["touchedPaths"] == "core/goal_guard.py, tests/test_goal_guard.py"
    assert "Delivery boundary: structured start only" in active_text
    assert audit.returncode == 0, audit.stderr


def test_plain_start_creates_blocked_draft_contract():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        started = run_guard(["start", "--root", tmp], "Unclear draft")
        audit = run_guard(["audit", "--root", tmp])
        checkpoint = run_guard(
            [
                "checkpoint",
                "--root",
                tmp,
                "--",
                sys.executable,
                "-c",
                "from pathlib import Path; Path('draft-ran').write_text('wrong')",
            ]
        )
        state = json.loads((root / ".goal-matrix" / "state.json").read_text(encoding="utf-8"))

        assert started.returncode == 0, started.stderr
        assert state["goalMatrix"]["childGoals"][0]["contractComplete"] is False
        assert audit.returncode == 1
        assert "active goal contract is incomplete" in audit.stderr
        assert checkpoint.returncode == 1
        assert not (root / "draft-ran").exists()


def test_structured_start_rejects_metadata_only_verification_before_state_write():
    contract = {
        "userOutcome": "Weak contract",
        "engineeringSlice": "Record status",
        "initializationType": "iteration",
        "policyImpact": "none",
        "touchedPaths": ["core/goal_guard.py"],
        "deliveryBoundary": "one parser branch",
        "skipped": "none",
        "truthSource": "status",
        "verification": "python3 core/goal_guard.py status --root .",
        "developmentFlow": "inspect -> verify -> checkpoint",
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        started = run_guard(["start", "--root", tmp], json.dumps(contract))

        assert started.returncode == 2
        assert "metadata-only" in started.stderr
        assert not (root / ".goal-matrix" / "state.json").exists()


def test_structured_start_rejects_non_string_verification_without_traceback():
    contract = {
        "userOutcome": "Invalid contract",
        "engineeringSlice": "Reject invalid input",
        "initializationType": "iteration",
        "policyImpact": "none",
        "touchedPaths": ["core/goal_guard.py"],
        "deliveryBoundary": "input validation only",
        "skipped": "none",
        "truthSource": "CLI exit code",
        "verification": ["python3", "--version"],
        "developmentFlow": "inspect -> failing check -> implement -> verify -> checkpoint",
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        started = run_guard(["start", "--root", tmp], json.dumps(contract))

        assert started.returncode == 2
        assert "missing verification" in started.stderr
        assert "Traceback" not in started.stderr
        assert not (root / ".goal-matrix" / "state.json").exists()


def test_start_command_keeps_existing_active_goal():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_guard(["start", "--root", tmp], "first goal").returncode == 0

        second = run_guard(["start", "--root", tmp], "second goal")
        status_result = run_guard(["status", "--root", tmp])

    assert second.returncode == 0, second.stderr
    assert json.loads(second.stdout)["activeGoal"] == "G1 - first goal"
    status = json.loads(status_result.stdout)
    assert status["activeGoal"] == "G1 - first goal"
    assert status["goalMatrix"]["total"] == 1
    assert status["goalMatrix"]["pending"] == 1


def test_start_command_extracts_prompt_from_hook_json():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        started = run_guard(["start", "--root", tmp], json.dumps({"prompt": "goal matrix 工程化"}))

    assert started.returncode == 0, started.stderr
    assert json.loads(started.stdout)["activeGoal"] == "G1 - goal matrix 工程化"


def test_start_broad_prompt_creates_pending_matrix_before_dispatch():
    prompt = """全部完成:
P1 UserPromptSubmit auto-start writes state too eagerly
P1 policy gate payload parsing heuristic
P2 Markdown canonical state
"""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        started = run_guard(["start", "--root", tmp], prompt)
        status_result = run_guard(["status", "--root", tmp])
        matrix_text = (root / ".goal-matrix" / "goals" / "goal-matrix.md").read_text(encoding="utf-8")
        active_text = (root / ".goal-matrix" / "goals" / "active-goal.md").read_text(encoding="utf-8")

    assert started.returncode == 0, started.stderr
    payload = json.loads(started.stdout)
    assert payload["activeGoal"] == "G1 - Schedule broad prompt delivery"
    assert payload["plannedChildGoals"] == ["G2", "G3", "G4"]

    status = json.loads(status_result.stdout)
    assert status["activeGoal"] == "G1 - Schedule broad prompt delivery"
    assert status["nextLoop"] == "G2 - UserPromptSubmit auto-start writes state too eagerly"
    assert status["goalMatrix"]["total"] == 4
    assert status["goalMatrix"]["pending"] == 4
    assert status["goalMatrix"]["childGoals"][1]["engineeringSlice"].startswith("Subagent candidate:")
    assert status["goalMatrix"]["childGoals"][1]["dependencies"] == "G1"
    assert status["goalMatrix"]["childGoals"][1]["risk"] == "P1"
    assert status["goalMatrix"]["childGoals"][1]["parallelSafety"] == "independent if touched paths do not overlap"
    assert "| Dependencies | Risk | Parallel safety | Status |" in matrix_text
    assert "scheduler/acceptance active goal" in active_text
    assert "verify each child goal before checkpoint" in active_text


def test_start_self_evolution_prompt_does_not_invent_backlog():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        started = run_guard(["start", "--root", tmp], "开始进化")
        active_verify_result = run_guard(["active-verify", "--root", tmp])
        status_result = run_guard(["status", "--root", tmp])

    assert started.returncode == 0, started.stderr
    assert active_verify_result.returncode == 1
    assert "metadata-only" in active_verify_result.stderr
    payload = json.loads(started.stdout)
    assert payload["activeGoal"] == "G1 - 开始进化"
    assert "plannedChildGoals" not in payload

    status = json.loads(status_result.stdout)
    assert status["activeGoal"] == "G1 - 开始进化"
    assert status["nextLoop"] is None
    assert status["goalMatrix"]["total"] == 1
    assert status["goalMatrix"]["pending"] == 1
    assert status["goalMatrix"]["childGoals"][0]["contractComplete"] is False


def test_start_command_escapes_pipe_in_prompt_title():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        started = run_guard(["start", "--root", tmp], "fix parser | keep table safe")
        status_result = run_guard(["status", "--root", tmp])
        matrix_text = (root / ".goal-matrix" / "goals" / "goal-matrix.md").read_text(encoding="utf-8")

    assert started.returncode == 0, started.stderr
    status = json.loads(status_result.stdout)
    assert status["activeGoal"] == "G1 - fix parser | keep table safe"
    assert status["goalMatrix"]["childGoals"][0]["userOutcome"] == "fix parser | keep table safe"
    assert "fix parser \\| keep table safe" in matrix_text


def test_state_json_is_canonical_after_start():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        started = run_guard(["start", "--root", tmp], "canonical machine state")
        state_path = root / ".goal-matrix" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        write_file(root / ".goal-matrix" / "goals" / "active-goal.md", "Active goal: corrupted\n")
        write_file(
            root / ".goal-matrix" / "goals" / "goal-matrix.md",
            "# Goal Matrix\n\n| broken |\n| --- |\n| bad |\n",
        )
        status_result = run_guard(["status", "--root", tmp])

    assert started.returncode == 0, started.stderr
    assert state["schemaVersion"] == 1
    assert state["activeGoal"] == "G1 - canonical machine state"
    assert state["goalMatrix"]["childGoals"][0]["id"] == "G1"
    status = json.loads(status_result.stdout)
    assert status["activeGoal"] == "G1 - canonical machine state"
    assert status["goalMatrix"]["pending"] == 1
    assert status["goalMatrix"]["childGoals"][0]["userOutcome"] == "canonical machine state"


def test_prune_archive_keeps_json_state_and_visible_recent_done():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        goals = [
            {
                "id": f"G{index}",
                "userOutcome": f"Done {index}",
                "engineeringSlice": "slice",
                "truthSource": "tests",
                "verification": f"pytest test_{index}",
                "status": "Done",
            }
            for index in range(1, 5)
        ]
        goals.append(
            {
                "id": "G5",
                "userOutcome": "Active slice",
                "engineeringSlice": "slice",
                "truthSource": "tests",
                "verification": "pytest active",
                "status": "Pending",
            }
        )
        write_file(
            root / ".goal-matrix" / "state.json",
            json.dumps(
                {
                    "schemaVersion": 1,
                    "activeGoal": "G5 - Active slice",
                    "nextLoop": None,
                    "nextAction": {},
                    "subagentCandidates": [],
                    "goalMatrix": {
                        "total": len(goals),
                        "done": 4,
                        "pending": 1,
                        "activeId": "G5",
                        "childGoals": goals,
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )

        result = run_guard(["prune", "--root", tmp, "--keep-done", "1"])
        status_result = run_guard(["status", "--root", tmp])
        matrix_text = (root / ".goal-matrix" / "goals" / "goal-matrix.md").read_text(encoding="utf-8")
        archive_text = (root / ".goal-matrix" / "goals" / "archive.md").read_text(encoding="utf-8")
        state_after_prune = json.loads((root / ".goal-matrix" / "state.json").read_text(encoding="utf-8"))

        checkpoint = run_guard(
            ["checkpoint", "--root", tmp, "--", sys.executable, "-c", "print('verified')"]
        )
        final_state = json.loads((root / ".goal-matrix" / "state.json").read_text(encoding="utf-8"))
        final_matrix = (root / ".goal-matrix" / "goals" / "goal-matrix.md").read_text(encoding="utf-8")
        final_archive = (root / ".goal-matrix" / "goals" / "archive.md").read_text(encoding="utf-8")

    assert result.returncode == 0, result.stderr
    assert "| G4 | Done 4 |" in matrix_text
    assert "| G5 | Active slice |" in matrix_text
    assert "| G3 | Done 3 |" not in matrix_text
    assert "| G3 | Done 3 |" in archive_text
    status = json.loads(status_result.stdout)
    assert status["goalMatrix"]["total"] == 5
    assert status["goalMatrix"]["pending"] == 1
    assert state_after_prune["projection"]["keepDone"] == 1
    assert checkpoint.returncode == 0, checkpoint.stderr
    assert final_state["projection"]["keepDone"] == 1
    assert "| G5 | Active slice |" in final_matrix
    assert "| G4 | Done 4 |" not in final_matrix
    assert "| G4 | Done 4 |" in final_archive


def test_audit_rejects_archive_projection_drift():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_structured_start(tmp, "Archive truth").returncode == 0
        assert run_guard(["prune", "--root", tmp, "--keep-done", "0"]).returncode == 0
        archive_path = root / ".goal-matrix" / "goals" / "archive.md"
        archive_path.write_text(archive_path.read_text(encoding="utf-8") + "manual edit\n", encoding="utf-8")

        result = run_guard(["audit", "--root", tmp])

    assert result.returncode == 1
    assert "archive projection drift" in result.stderr


def test_audit_rejects_invalid_projection_retention():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_structured_start(tmp, "Projection config").returncode == 0
        state_path = root / ".goal-matrix" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["projection"]["keepDone"] = -1
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = run_guard(["audit", "--root", tmp])

    assert result.returncode == 1
    assert "projection.keepDone must be a non-negative integer" in result.stderr


def test_archive_projection_trust_boundary_is_documented():
    protocol = read_text("core/protocol.md")

    assert ".goal-matrix/goals/archive.md" in protocol
    assert "generated projection" in protocol
    assert "drift detection" in protocol
    assert "state.json" in protocol


def test_audit_rejects_visible_done_goal_with_status_only_verification():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            root / ".goal-matrix" / "goals" / "goal-matrix.md",
            """# Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | Weak proof | Record metadata | `.goal-matrix` status | `python3 core/goal_guard.py status --root .` | Done |
""",
        )

        result = run_guard(["audit", "--root", tmp])

    assert result.returncode == 1
    assert "Done goal G1 verification cannot be metadata-only status" in result.stderr


def test_audit_allows_compound_done_verification_with_status_and_real_check():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            root / ".goal-matrix" / "goals" / "goal-matrix.md",
            """# Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | Strong proof | Verify after metadata readback | tests | `python3 core/goal_guard.py status --root . && python3 tests/test_goal_guard.py` | Done |
""",
        )

        result = run_guard(["audit", "--root", tmp])

    assert result.returncode == 0, result.stderr


def test_verification_helpers_are_in_subdomain_module():
    spec = importlib.util.spec_from_file_location("goal_verification", ROOT / "core" / "goal_verification.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.normalized_verification("`python3 --version`") == "python3 --version"
    assert module.verification_is_metadata_status("python3 core/goal_guard.py status --root .")
    assert not module.verification_is_metadata_status(
        "python3 core/goal_guard.py status --root . && python3 tests/test_goal_guard.py"
    )
    assert module.active_goal_iteration_commands(".") == {
        "verify": "python3 core/goal_guard.py active-verify --root .",
        "checkpoint": "python3 core/goal_guard.py checkpoint --root . -- python3 core/goal_guard.py active-verify --root .",
    }


def test_policy_helpers_are_in_subdomain_module():
    policy_path = ROOT / "core" / "goal_policy.py"
    spec = importlib.util.spec_from_file_location("goal_policy", policy_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert callable(module.policy_gate)
    guard = read_text("core/goal_guard.py")
    for signature in ("def collect_payload_paths(", "def policy_gate_problems(", "def policy_gate("):
        assert signature not in guard
    for path in ("scripts/validate_plugin_package.py", "scripts/loop_verify.py"):
        assert "core/goal_policy.py" in read_text(path)


def test_publish_helpers_are_in_subdomain_module():
    publish_path = ROOT / "core" / "goal_publish.py"
    spec = importlib.util.spec_from_file_location("goal_publish", publish_path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(publish_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)

    assert callable(module.publish_gate)
    assert module.command_is_git_push("git -C . push origin main")
    assert not module.command_is_git_push("git status")
    guard = read_text("core/goal_guard.py")
    for signature in ("def command_is_git_push(", "def publish_state_problems(", "def publish_gate("):
        assert signature not in guard
    for path in ("scripts/validate_plugin_package.py", "scripts/loop_verify.py"):
        assert "core/goal_publish.py" in read_text(path)


def test_projection_helpers_are_in_subdomain_module():
    projection_path = ROOT / "core" / "goal_projection.py"
    spec = importlib.util.spec_from_file_location("goal_projection", projection_path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(projection_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)

    row = module.markdown_table_row(["G1", "Keep | escaped"])
    assert module.split_markdown_table_row(row) == ["G1", "Keep | escaped"]
    goals = [
        {"id": "G1", "status": "Done"},
        {"id": "G2", "status": "Done"},
        {"id": "G3", "status": "Pending"},
    ]
    visible, archived = module.split_goal_projections(goals, "G3 - Pending", 1)
    assert [goal["id"] for goal in visible] == ["G2", "G3"]
    assert [goal["id"] for goal in archived] == ["G1"]

    guard = read_text("core/goal_guard.py")
    for signature in ("def split_markdown_table_row(", "def render_goal_matrix(", "def write_goal_projections("):
        assert signature not in guard
    for path in ("scripts/validate_plugin_package.py", "scripts/loop_verify.py"):
        assert "core/goal_projection.py" in read_text(path)


def test_state_helpers_are_in_subdomain_module():
    state_path = ROOT / "core" / "goal_state.py"
    spec = importlib.util.spec_from_file_location("goal_state", state_path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(state_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)

    goals = [
        {"id": "G1", "userOutcome": "Done", "status": "Done"},
        {"id": "G2", "userOutcome": "Next", "status": "Pending"},
    ]
    assert callable(module.write_state_json)
    assert module.next_goal_id(goals) == "G3"
    assert module.pending_goal_after_active(goals, "G1 - Done")["id"] == "G2"

    guard = read_text("core/goal_guard.py")
    for signature in ("def load_state_json(", "def next_action_payload(", "def write_state_json("):
        assert signature not in guard
    for path in ("scripts/validate_plugin_package.py", "scripts/loop_verify.py"):
        assert "core/goal_state.py" in read_text(path)


def test_gate_helpers_are_in_subdomain_module():
    gate_path = ROOT / "core" / "goal_gate.py"
    spec = importlib.util.spec_from_file_location("goal_gate", gate_path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(gate_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)

    assert callable(module.audit_project)
    assert callable(module.completion_gate)
    assert any("missing completion evidence" in problem for problem in module.audit("Done"))

    guard = read_text("core/goal_guard.py")
    for signature in ("def audit_project(", "def completion_gate(", "def gate_decision("):
        assert signature not in guard
    for path in ("scripts/validate_plugin_package.py", "scripts/loop_verify.py"):
        assert "core/goal_gate.py" in read_text(path)


def test_audit_rejects_visible_goal_matrix_drift_from_state_json():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        goal = {
            "id": "G1",
            "userOutcome": "JSON truth",
            "engineeringSlice": "slice",
            "truthSource": "tests",
            "verification": "python3 tests/test_goal_guard.py",
            "status": "Pending",
        }
        write_file(
            root / ".goal-matrix" / "state.json",
            json.dumps(
                {
                    "schemaVersion": 1,
                    "activeGoal": "G1 - JSON truth",
                    "nextLoop": None,
                    "nextAction": {},
                    "subagentCandidates": [],
                    "goalMatrix": {
                        "total": 1,
                        "done": 0,
                        "pending": 1,
                        "activeId": "G1",
                        "childGoals": [goal],
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )
        write_file(
            root / ".goal-matrix" / "goals" / "goal-matrix.md",
            """# Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | Edited by hand | slice | tests | python3 tests/test_goal_guard.py | Pending |
""",
        )

        result = run_guard(["audit", "--root", tmp])

    assert result.returncode == 1
    assert "goal matrix projection drift: goal-matrix.md differs from state.json" in result.stderr


def test_state_json_remains_authoritative_across_checkpoint():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_structured_start(tmp, "JSON truth").returncode == 0
        matrix_path = root / ".goal-matrix" / "goals" / "goal-matrix.md"
        matrix_path.write_text(
            matrix_path.read_text(encoding="utf-8").replace("JSON truth", "Edited by hand"),
            encoding="utf-8",
        )

        checkpoint = run_guard(["checkpoint", "--root", tmp, "--", sys.executable, "-c", "print('ok')"])
        state = json.loads((root / ".goal-matrix" / "state.json").read_text(encoding="utf-8"))
        matrix_text = matrix_path.read_text(encoding="utf-8")

    assert checkpoint.returncode == 0, checkpoint.stderr
    assert state["goalMatrix"]["childGoals"][0]["userOutcome"] == "JSON truth"
    assert state["goalMatrix"]["childGoals"][0]["status"] == "Done"
    assert "| G1 | JSON truth |" in matrix_text
    assert "Edited by hand" not in matrix_text


def test_audit_rejects_missing_pending_projection_row():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_guard(["start", "--root", tmp], "Required pending row").returncode == 0
        write_file(
            root / ".goal-matrix" / "goals" / "goal-matrix.md",
            """# Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
""",
        )

        result = run_guard(["audit", "--root", tmp])

    assert result.returncode == 1
    assert "goal matrix projection drift: goal-matrix.md differs from state.json" in result.stderr


def test_checkpoint_preserves_extended_matrix_fields():
    prompt = "剩余 backlog:\nP1 first item\nP2 second item\n"
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_guard(["start", "--root", tmp], prompt).returncode == 0

        checkpoint = run_guard(["checkpoint", "--root", tmp, "--", sys.executable, "-c", "print('ok')"])
        status_result = run_guard(["status", "--root", tmp])

    assert checkpoint.returncode == 0, checkpoint.stderr
    status = json.loads(status_result.stdout)
    scheduler = status["goalMatrix"]["childGoals"][0]
    assert scheduler["id"] == "G1"
    assert scheduler["status"] == "Done"
    assert scheduler["dependencies"] == "none"
    assert scheduler["risk"] == "medium"
    assert scheduler["parallelSafety"] == "main thread only"


def test_checkpoint_command_requires_passing_verification_before_advancing_goal():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_structured_start(tmp, "ship real loop step").returncode == 0

        failed = run_guard(["checkpoint", "--root", tmp, "--", sys.executable, "-c", "raise SystemExit(7)"])
        status_result = run_guard(["status", "--root", tmp])

    assert failed.returncode == 7
    status = json.loads(status_result.stdout)
    assert status["activeGoal"] == "G1 - ship real loop step"
    assert status["goalMatrix"]["pending"] == 1
    assert status["goalMatrix"]["childGoals"][0]["status"] == "Pending"


def test_checkpoint_command_rejects_metadata_only_status_verification():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_structured_start(tmp, "ship real loop step").returncode == 0

        rejected = run_guard(
            [
                "checkpoint",
                "--root",
                tmp,
                "--",
                sys.executable,
                str(GUARD),
                "status",
                "--root",
                tmp,
            ]
        )
        status_result = run_guard(["status", "--root", tmp])

    assert rejected.returncode == 2
    assert "metadata-only verification" in rejected.stderr
    status = json.loads(status_result.stdout)
    assert status["activeGoal"] == "G1 - ship real loop step"
    assert status["goalMatrix"]["pending"] == 1
    assert status["goalMatrix"]["childGoals"][0]["status"] == "Pending"


def test_checkpoint_command_marks_active_goal_done_after_machine_verification():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_structured_start(tmp, "ship real loop step").returncode == 0
        verify_command = [sys.executable, "-c", "print('verified proof')"]

        verified = run_guard(
            [
                "checkpoint",
                "--root",
                tmp,
                "--",
                *verify_command,
            ]
        )
        status_result = run_guard(["status", "--root", tmp])
        audit_result = run_guard(["audit", "--root", tmp])
        evidence_path = Path(tmp) / ".goal-matrix" / "evidence" / "G1.log"
        evidence_exists = evidence_path.is_file()
        evidence = evidence_path.read_text(encoding="utf-8") if evidence_exists else ""

    assert verified.returncode == 0, verified.stderr
    payload = json.loads(verified.stdout)
    assert payload["completedGoal"] == "G1 - ship real loop step"
    assert payload["evidence"] == ".goal-matrix/evidence/G1.log"
    assert evidence_exists
    assert "Command:" in evidence
    assert "verified proof" in evidence
    status = json.loads(status_result.stdout)
    assert status["activeGoal"] is None
    assert status["goalMatrix"]["pending"] == 0
    completed = status["goalMatrix"]["childGoals"][0]
    assert completed["status"] == "Done"
    assert completed["verification"] == f"`{shlex.join(verify_command)}`"
    assert audit_result.returncode == 0, audit_result.stderr


def test_checkpoint_command_promotes_next_pending_goal_for_self_evolution_run():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            root / ".goal-matrix" / "goals" / "goal-matrix.md",
            """# Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Status |
| --- | --- | --- | --- | --- | --- |
| G1 | First slice | Implement first slice | Tests | unit test | Pending |
| G2 | Second slice | Implement second slice | Logs | log readback | Pending |
""",
        )
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            """# Active Goal

Active goal: G1 - First slice
Initialization type: iteration
Policy impact: none
Touched paths: tests/test_goal_guard.py
Delivery boundary: first slice only
Skipped: second slice
Truth source: Tests
Verification: unit test
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
        )

        verified = run_guard(
            [
                "checkpoint",
                "--root",
                tmp,
                "--",
                sys.executable,
                "-c",
                "print('first slice verified')",
            ]
        )
        status_result = run_guard(["status", "--root", tmp])

    assert verified.returncode == 0, verified.stderr
    payload = json.loads(verified.stdout)
    assert payload["completedGoal"] == "G1 - First slice"
    assert payload["nextActiveGoal"] == "G2 - Second slice"
    status = json.loads(status_result.stdout)
    assert status["activeGoal"] == "G2 - Second slice"
    assert status["nextLoop"] is None
    assert status["goalMatrix"]["pending"] == 1
    assert status["goalMatrix"]["childGoals"][0]["status"] == "Done"
    assert status["goalMatrix"]["childGoals"][1]["status"] == "Pending"


def test_checkpoint_if_active_ignores_missing_active_goal():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0

        result = run_guard(["checkpoint", "--if-active", "--root", tmp, "--", sys.executable, "-c", "raise SystemExit(9)"])

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""


def test_doctor_command_reports_resume_and_plugin_source():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        active_goal = next(
            line.split(":", 1)[1].strip()
            for line in (Path(tmp) / ".goal-matrix" / "goals" / "active-goal.md").read_text().splitlines()
            if line.startswith("Active goal:")
        )
        result = run_guard(["doctor", "--root", tmp])

    assert result.returncode == 0, result.stderr
    doctor = json.loads(result.stdout)
    assert doctor["resume"]["activeGoal"] == active_goal
    assert "nextLoop" in doctor["resume"]
    assert doctor["source"]["pluginRoot"] == str(ROOT)
    assert doctor["source"]["manifestPath"].endswith(".codex-plugin/plugin.json")
    assert doctor["source"]["adapterSkillPath"].endswith(
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md"
    )


def test_status_or_doctor_surfaces_next_action():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            root / ".goal-matrix" / "goals" / "goal-matrix.md",
            """# Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Dependencies | Risk | Parallel safety | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | First slice | Implement first slice | Tests | unit test | none | P1 | main thread only | Pending |
| G2 | Independent investigation | Investigate second slice | Logs | log readback | none | P2 | independent if touched paths do not overlap | Pending |
""",
        )
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            """# Active Goal

Active goal: G1 - First slice
Initialization type: iteration
Policy impact: none
Touched paths: tests/test_goal_guard.py
Delivery boundary: first slice only
Skipped: second slice
Truth source: Tests
Verification: unit test
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
        )
        run_guard(["status", "--root", tmp])
        status_result = run_guard(["status", "--root", tmp])
        doctor_result = run_guard(["doctor", "--root", tmp])

    assert status_result.returncode == 0, status_result.stderr
    status = json.loads(status_result.stdout)
    assert status["nextAction"]["type"] == "continue_active_goal"
    assert status["nextAction"]["goal"] == "G1 - First slice"
    assert status["nextAction"]["verification"] == "unit test"
    assert status["nextAction"]["deliveryBoundary"] == "first slice only"
    assert status["subagentCandidates"] == [
        {
            "goal": "G2 - Independent investigation",
            "dependencies": "none",
            "risk": "P2",
            "parallelSafety": "independent if touched paths do not overlap",
        }
    ]
    assert "Continue active goal G1 - First slice." in status["nextAction"]["continuePrompt"]

    assert doctor_result.returncode == 0, doctor_result.stderr
    doctor = json.loads(doctor_result.stdout)
    assert doctor["resume"]["nextAction"] == status["nextAction"]
    assert doctor["resume"]["subagentCandidates"] == status["subagentCandidates"]


def test_promote_handoff_excludes_promoted_goal_and_normalizes_verification():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            root / ".goal-matrix" / "goals" / "goal-matrix.md",
            """# Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Dependencies | Risk | Parallel safety | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | Next slice | Start next slice | Status JSON | `python3 -m pytest tests/test_goal_guard.py -q` | none | P1 | independent if touched paths do not overlap | Pending |
| G2 | Parallel slice | Work another slice | Doctor JSON | log readback | none | P2 | independent if touched paths do not overlap | Pending |
""",
        )
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            """# Active Goal

Active goal: none
Initialization type: iteration
Policy impact: none
Touched paths: none
Delivery boundary: none
Skipped: none
Truth source: none
Verification: none
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
        )
        status_result = run_guard(["status", "--root", tmp])
        doctor_result = run_guard(["doctor", "--root", tmp])

    assert status_result.returncode == 0, status_result.stderr
    status = json.loads(status_result.stdout)
    assert status["nextAction"] == {
        "type": "promote_pending_goal",
        "goal": "G1 - Next slice",
        "verification": "python3 -m pytest tests/test_goal_guard.py -q",
        "truthSource": "Status JSON",
        "continuePrompt": "Start next pending goal G1 - Next slice. Verification: python3 -m pytest tests/test_goal_guard.py -q.",
    }
    assert status["subagentCandidates"] == [
        {
            "goal": "G2 - Parallel slice",
            "dependencies": "none",
            "risk": "P2",
            "parallelSafety": "independent if touched paths do not overlap",
        }
    ]

    assert doctor_result.returncode == 0, doctor_result.stderr
    doctor = json.loads(doctor_result.stdout)
    assert doctor["resume"]["nextAction"] == status["nextAction"]
    assert doctor["resume"]["subagentCandidates"] == status["subagentCandidates"]


def test_continue_next_action_exposes_iteration_commands():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            root / ".goal-matrix" / "goals" / "goal-matrix.md",
            """# Goal Matrix

| Goal | User outcome | Engineering slice | Truth source | Verification | Dependencies | Risk | Parallel safety | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | First slice | Build first slice | Status JSON | `python3 --version` | none | P1 | sequential | Pending |
| G2 | Next slice | Build next slice | Status JSON | `python3 --version` | G1 | P1 | sequential | Pending |
""",
        )
        write_file(
            root / ".goal-matrix" / "goals" / "active-goal.md",
            """# Active Goal

Active goal: G1 - First slice
Initialization type: iteration
Policy impact: none
Touched paths: tests/test_goal_guard.py
Delivery boundary: first slice only
Skipped: second slice
Truth source: Status JSON
Verification: python3 --version
Development flow: inspect -> failing check -> implement -> verify -> checkpoint
""",
        )
        status_result = run_guard(["status", "--root", tmp])
        doctor_result = run_guard(["doctor", "--root", tmp])

    assert status_result.returncode == 0, status_result.stderr
    status = json.loads(status_result.stdout)
    assert status["nextAction"]["type"] == "continue_active_goal"
    assert status["nextAction"]["commands"] == {
        "verify": shlex.join(["python3", "core/goal_guard.py", "active-verify", "--root", tmp]),
        "checkpoint": shlex.join(
            [
                "python3",
                "core/goal_guard.py",
                "checkpoint",
                "--root",
                tmp,
                "--",
                "python3",
                "core/goal_guard.py",
                "active-verify",
                "--root",
                tmp,
            ]
        ),
    }

    assert doctor_result.returncode == 0, doctor_result.stderr
    doctor = json.loads(doctor_result.stdout)
    assert doctor["resume"]["nextAction"]["commands"] == status["nextAction"]["commands"]


def test_doctor_runtime_contract_is_explicit():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        result = run_guard(["doctor", "--root", tmp])

    assert result.returncode == 0, result.stderr
    doctor = json.loads(result.stdout)
    runtime = doctor["runtime"]
    assert runtime["visibleGoalRequiresCreateGoal"] is True
    assert runtime["hookCanCreateCodexGoal"] is False
    assert runtime["checkpointPromotesNextGoal"] is True
    assert runtime["runtimeContinuesWhilePendingGoalsExist"] is True
    assert runtime["completionWhenNoPendingGoal"] is True
    assert runtime["continuationMode"] == "checkpoint_promotes_existing_pending_goal"
    assert "create_goal" in runtime["minimalFixPath"]

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    adapter_readme = (ROOT / "adapters" / "codex" / "README.md").read_text(encoding="utf-8")
    assert "Checkpoint promotes the next goal in state; the runtime still has to continue execution." in readme
    assert "Checkpoint promotes the next goal in state; the runtime still has to continue execution." in adapter_readme


def test_doctor_command_reports_installed_skill_drift():
    with tempfile.TemporaryDirectory() as tmp:
        codex_home = Path(tmp)
        installed = codex_home / "skills" / "goal-matrix-iterative-delivery" / "SKILL.md"
        write_file(installed, "old installed skill\n")
        env = {**os.environ, "CODEX_HOME": str(codex_home)}

        result = run_guard(["doctor", "--root", str(ROOT)], env=env)

    assert result.returncode == 0, result.stderr
    doctor = json.loads(result.stdout)
    assert doctor["source"]["installedSkillPath"] == str(installed)
    assert doctor["source"]["installedSkillExists"] is True
    assert doctor["source"]["installedSkillMatchesAdapter"] is False


def test_doctor_command_reports_installed_verifier_skill_drift():
    with tempfile.TemporaryDirectory() as tmp:
        codex_home = Path(tmp)
        installed = codex_home / "skills" / "loop-verifier" / "SKILL.md"
        write_file(installed, "old verifier skill\n")
        env = {**os.environ, "CODEX_HOME": str(codex_home)}

        result = run_guard(["doctor", "--root", str(ROOT)], env=env)

    assert result.returncode == 0, result.stderr
    doctor = json.loads(result.stdout)
    assert doctor["source"]["installedVerifierSkillPath"] == str(installed)
    assert doctor["source"]["installedVerifierSkillExists"] is True
    assert doctor["source"]["installedVerifierSkillMatchesAdapter"] is False


def test_doctor_command_reports_codex_runtime_boundaries():
    with tempfile.TemporaryDirectory() as tmp:
        codex_home = Path(tmp)
        version = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())["version"]
        write_file(
            codex_home / "config.toml",
            """
[marketplaces.goal-matrix-github]
source_type = "git"
source = "https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git"
ref = "main"

[plugins."goal-matrix-iterative-delivery@goal-matrix-github"]
enabled = true
""",
        )
        (codex_home / "plugins" / "cache" / "goal-matrix-github" / "goal-matrix-iterative-delivery" / version).mkdir(
            parents=True
        )
        env = {**os.environ, "CODEX_HOME": str(codex_home)}

        result = run_guard(["doctor", "--root", str(ROOT)], env=env)

    assert result.returncode == 0, result.stderr
    doctor = json.loads(result.stdout)
    runtime = doctor["runtime"]
    source = doctor["source"]
    assert runtime["visibleGoalRequiresCreateGoal"] is True
    assert runtime["hookCanCreateCodexGoal"] is False
    assert source["codexMarketplaceConfigured"] is True
    assert source["codexPluginEnabled"] is True
    assert source["codexCacheHasManifest"] is False
    assert source["codexHookTrusted"] is False


def test_doctor_fix_creates_missing_project_docs_and_gitignore():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = run_guard(["doctor", "--root", tmp, "--fix"])
        audit = run_guard(["audit", "--root", tmp])
        gitignore = (root / ".gitignore").read_text(encoding="utf-8") if (root / ".gitignore").is_file() else ""

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["fix"]["applied"] is True
    assert ".goal-matrix/project-policy.json" in payload["fix"]["created"]
    assert audit.returncode == 0, audit.stderr
    assert ".goal-matrix/notifications.local.json" in gitignore


def test_doctor_reports_native_pre_push_hook_install_hint():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        result = run_guard(["doctor", "--root", str(repo)])

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["nativeHooks"]["prePushHookInstalled"] is False
    assert payload["nativeHooks"]["prePushHookExists"] is False
    assert payload["nativeHooks"]["prePushHookState"] == "absent"
    assert "--install-git-hook" in payload["nativeHooks"]["installCommand"]


def test_doctor_reports_current_stale_and_broken_managed_pre_push_hooks():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        install = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "install_adapter.py"),
                "codex",
                "--target",
                str(repo),
                "--install-git-hook",
            ],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        hook = repo / ".git" / "hooks" / "pre-push"
        current = run_guard(["doctor", "--root", str(repo)])

        expected_guard = ROOT / "core" / "goal_guard.py"
        stale_guard = Path(tmp) / "old-plugin" / "core" / "goal_guard.py"
        hook.write_text(
            hook.read_text(encoding="utf-8").replace(str(expected_guard), str(stale_guard)),
            encoding="utf-8",
        )
        stale = run_guard(["doctor", "--root", str(repo)])

        hook.write_text(
            hook.read_text(encoding="utf-8").replace(str(stale_guard), str(expected_guard)),
            encoding="utf-8",
        )
        hook.chmod(0o644)
        broken = run_guard(["doctor", "--root", str(repo)])

    assert install.returncode == 0, install.stderr
    current_hooks = json.loads(current.stdout)["nativeHooks"]
    assert current_hooks["prePushHookState"] == "current"
    assert current_hooks["prePushHookInstalled"] is True
    assert current_hooks["prePushHookManaged"] is True
    assert current_hooks["prePushHookGuardPath"] == str(expected_guard)

    stale_hooks = json.loads(stale.stdout)["nativeHooks"]
    assert stale_hooks["prePushHookState"] == "stale"
    assert stale_hooks["prePushHookInstalled"] is False
    assert stale_hooks["refreshRequired"] is True

    broken_hooks = json.loads(broken.stdout)["nativeHooks"]
    assert broken_hooks["prePushHookState"] == "broken"
    assert broken_hooks["prePushHookInstalled"] is False
    assert broken_hooks["prePushHookExecutable"] is False


def test_gate_command_returns_design_for_missing_design_evidence():
    result = run_guard(["gate", "--phase", "design_gate"], "No gate evidence yet.")

    assert result.returncode == 1
    decision = json.loads(result.stdout)
    assert decision["next"] == "design"
    assert "clarity decision" in decision["reason"]


def test_gate_command_returns_execute_for_failed_review():
    result = run_guard(["gate", "--phase", "review_gate"], "Verified with tests\nReviewer: changes requested\n")

    assert result.returncode == 1
    decision = json.loads(result.stdout)
    assert decision["next"] == "execute"
    assert "review requested changes" in decision["reason"]


def test_gate_command_keeps_goal_open_when_reviewer_decision_is_missing():
    text = "Verified with tests. External prerequisite missing: refresh qwen token/cookies."
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        result = run_guard(["gate", "--phase", "review_gate", "--root", tmp], text)

    assert result.returncode == 1
    decision = json.loads(result.stdout)
    assert decision["next"] == "execute"
    assert "missing reviewer decision" in decision["reason"]


def test_gate_command_rejects_review_incantation_without_machine_verification():
    text = "Clarity decision: proceed\nVerified with tests\nReviewer: approved\n"
    result = run_guard(["gate", "--phase", "review_gate"], text)

    assert result.returncode == 1
    decision = json.loads(result.stdout)
    assert decision["next"] == "execute"
    assert "machine verification" in decision["reason"]


def test_gate_command_returns_checkpoint_after_machine_verified_review():
    text = "Clarity decision: proceed\nReviewer: approved\n"
    result = run_guard(
        ["gate", "--phase", "review_gate", "--verify", sys.executable, "-c", "raise SystemExit(0)"],
        text,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["next"] == "checkpoint"


def test_review_gate_blocks_fast_lane_when_machine_verification_fails():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(root / ".goal-matrix" / "goals" / "active-goal.md", "Active goal: none\n")

        result = run_guard(
            [
                "gate",
                "--phase",
                "review_gate",
                "--root",
                tmp,
                "--verify",
                sys.executable,
                "-c",
                "raise SystemExit(9)",
            ],
            "",
        )

    assert result.returncode == 1
    decision = json.loads(result.stdout)
    assert decision["next"] == "execute"
    assert "Fast Lane" in decision["reason"]


def test_review_gate_allows_fast_lane_after_machine_verification_passes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(root / ".goal-matrix" / "goals" / "active-goal.md", "Active goal: none\n")

        result = run_guard(
            [
                "gate",
                "--phase",
                "review_gate",
                "--root",
                tmp,
                "--verify",
                sys.executable,
                "-c",
                "raise SystemExit(0)",
            ],
            "",
        )

    assert result.returncode == 0, result.stderr
    decision = json.loads(result.stdout)
    assert decision["next"] == "checkpoint"
    assert "Fast Lane" in decision["reason"]


def test_gate_command_reads_loop_note_from_root_when_stdin_is_empty():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            root / ".goal-matrix" / "loop-note.md",
            "Clarity decision: proceed\nVerified with tests\nReviewer: approved\n",
        )

        result = run_guard(
            ["gate", "--phase", "review_gate", "--root", tmp, "--verify", sys.executable, "-c", "raise SystemExit(0)"]
        )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["next"] == "checkpoint"


def test_classify_command_detects_new_project():
    result = run_guard(["classify"], "新项目立项，做一个从零开始的工具")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["initializationType"] == "new-project"
    assert payload["firstStage"] == "project_initialization"


def test_classify_command_detects_bugfix():
    result = run_guard(["classify"], "线上失败，需要修复这个 bug")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["initializationType"] == "bugfix"
    assert payload["firstGate"] == "review_gate"


def test_classify_command_defaults_to_iteration():
    result = run_guard(["classify"], "继续完善现有插件的生命周期")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["initializationType"] == "iteration"


def test_audit_root_rejects_missing_project_policy():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_guard(["audit", "--root", tmp])

    assert result.returncode == 1
    assert ".goal-matrix/project-policy.json" in result.stderr


def test_audit_root_rejects_missing_required_docs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_file(root / ".goal-matrix" / "project-policy.json", read_text("core/templates/project-policy.json"))
        result = run_guard(["audit", "--root", tmp])

    assert result.returncode == 1
    assert "missing required doc" in result.stderr


def test_audit_root_accepts_initialized_project_docs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_file(root / ".goal-matrix" / "project-policy.json", read_text("core/templates/project-policy.json"))
        for doc in (
            "project-context.md",
            "checks.md",
            "goals/goal-matrix.md",
            "goals/active-goal.md",
        ):
            write_file(root / ".goal-matrix" / doc, "# test\n")
        result = run_guard(["audit", "--root", tmp])

    assert result.returncode == 0, result.stderr


def test_init_command_creates_goal_matrix_baseline():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_guard(["init", "--root", tmp, "--type", "iteration"])
        root = Path(tmp)

        assert result.returncode == 0, result.stderr
        assert (root / ".goal-matrix" / "project-policy.json").is_file()
        assert (root / ".goal-matrix" / "project-context.md").is_file()
        assert (root / ".goal-matrix" / "checks.md").is_file()
        assert (root / ".goal-matrix" / "decisions.md").is_file()
        assert (root / ".goal-matrix" / "loop-note.md").is_file()
        assert (root / ".goal-matrix" / "specs").is_dir()
        assert (root / ".goal-matrix" / "goals" / "goal-matrix.md").is_file()
        assert (root / ".goal-matrix" / "goals" / "active-goal.md").is_file()
        policy = json.loads((root / ".goal-matrix" / "project-policy.json").read_text())
        assert policy["initializationType"] == "iteration"
        assert run_guard(["audit", "--root", tmp]).returncode == 0


def test_init_command_does_not_overwrite_existing_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        existing = root / ".goal-matrix" / "checks.md"
        write_file(existing, "# Checks\n\ncustom project check\n")

        result = run_guard(["init", "--root", tmp, "--type", "bugfix"])

        assert result.returncode == 0, result.stderr
        assert existing.read_text(encoding="utf-8") == "# Checks\n\ncustom project check\n"
        policy = json.loads((root / ".goal-matrix" / "project-policy.json").read_text())
        assert policy["initializationType"] == "bugfix"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("goal guard tests passed")
