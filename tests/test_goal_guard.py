import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "core" / "goal_guard.py"
PACKAGE_VALIDATOR = ROOT / "scripts" / "validate_plugin_package.py"
LOOP_AUDIT = ROOT / "scripts" / "loop_audit.py"
GOVERNANCE_CHECK = ROOT / "scripts" / "check_governance.py"
CODEX_HOOK_FIXTURES = ROOT / "tests" / "fixtures" / "codex-hooks"
RELEASE_INSTALL_TAG = "v0.1.1-codex.1"

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
        "budget, blocker, or no pending goal",
        "checkpoint commit",
        "design_gate",
        "review_gate",
        "Next loop",
    ):
        assert phrase in text


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
            "budget, blocker, or no pending goal",
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


def test_install_adapter_global_codex_syncs_installed_skill():
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
        installed = Path(tmp) / "skills" / "goal-matrix-iterative-delivery" / "SKILL.md"
        verifier = Path(tmp) / "skills" / "loop-verifier" / "SKILL.md"
        installed_text = installed.read_text(encoding="utf-8") if installed.is_file() else ""
        verifier_text = verifier.read_text(encoding="utf-8") if verifier.is_file() else ""

    assert result.returncode == 0, result.stderr
    assert installed_text == read_text("adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md")
    assert verifier_text == read_text("adapters/codex/skills/loop-verifier/SKILL.md")


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
        hook_result = subprocess.run([str(hook)], cwd=target, text=True, capture_output=True)

    assert result.returncode == 0, result.stderr
    assert hook_exists
    assert hook_is_executable
    assert "goal_guard.py\" publish-gate --root \"$repo_root\"" in hook_text
    assert hook_result.returncode == 1
    assert "fragmented history" in hook_result.stderr


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
    assert "pre-push.goal-matrix.previous" in hook_text
    assert hook_result.returncode == 0, hook_result.stderr
    assert chained_text == "chained"


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
    for path in ("README.md", "README.zh.md", "adapters/codex/README.md"):
        text = read_text(path)
        assert f"--ref {RELEASE_INSTALL_TAG}" in text, path
        assert "--ref main" not in text, path

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
    assert audit["level"] == ("L3" if audit["signals"]["remoteRunEvidence"] else "L2")
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
    if audit["signals"]["remoteRunEvidence"]:
        assert audit["blocked"] == []
    elif audit["signals"]["githubRemote"]:
        assert any("Remote workflow run evidence" in item for item in audit["blocked"])
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
    assert audit["level"] == ("L3" if audit["signals"]["remoteRunEvidence"] else "L2")


def test_loop_engineering_gap_register_tracks_unfinished_work():
    loop = read_text("LOOP.md")
    state = read_text("STATE.md")

    for phrase in (
        "Engineering Gap Register",
        "Resolved: keep run URL/status",
        "maker-checker",
        "run-evidence",
        "Resolved: keep clone/install/doctor evidence",
        "connectors",
        "governance",
        "Resolved: keep policy, tests, and verifier output together",
    ):
        assert phrase in loop
    assert "G28 gap register" in state


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
    assert audit["level"] == ("L3" if audit["signals"]["remoteRunEvidence"] else "L2")


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
    assert audit["nextAction"] == "No unresolved loop-engineering gaps."


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
                "approvalRequiredPaths": ["package.json"],
                "blockedPaths": [".goal-matrix/**"],
                "publishActionPatterns": ["npm publish"],
            }
        ),
    )


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


def test_loop_verify_keeps_approval_env_out_of_non_governance_checks():
    code = (
        "import json, scripts.loop_verify as loop_verify; "
        "print(json.dumps({"
        "'tests': loop_verify.command_env('tests').get('GOAL_MATRIX_APPROVED'), "
        "'governance': loop_verify.command_env('governance').get('GOAL_MATRIX_APPROVED')"
        "}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        cwd=ROOT,
        env={**os.environ, "GOAL_MATRIX_APPROVED": "1"},
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {"tests": None, "governance": "1"}


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
    assert audit["level"] == ("L3" if audit["signals"]["remoteRunEvidence"] else "L2")


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

        missing = subprocess.run(
            [sys.executable, str(LOOP_AUDIT), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )
        write_file(
            root / "loop-run-log.md",
            "# Runs\n\n## Recent Runs\nremote-ci-readback github-check-run\n",
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
                '"run_url":"https://example.invalid/run","head_sha":"abc123"}\n'
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
    assert present_audit["level"] == "L3"


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
    assert "GOAL_MATRIX_APPROVED: \"1\"" in workflow_text
    assert "python3 scripts/loop_verify.py" in workflow_text


def test_ci_workflow_lists_native_test_surfaces_explicitly():
    text = (ROOT / ".github" / "workflows" / "loop-audit.yml").read_text(encoding="utf-8")
    for phrase in (
        "python3 tests/test_goal_guard.py",
        "python3 scripts/validate_plugin_package.py --root .",
        "node --test pi-extension/test/extension.test.js",
        "python3 scripts/install_adapter.py codex --target",
        "hook UserPromptSubmit",
        "hook PreToolUse",
        "hook Stop",
        "python3 scripts/loop_verify.py",
    ):
        assert phrase in text


def test_ci_workflow_has_loop_cadence_trigger():
    text = (ROOT / ".github" / "workflows" / "loop-audit.yml").read_text(encoding="utf-8")
    assert "schedule:" in text
    assert "cron:" in text


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
    assert "squash or merge" in context
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
    assert "fragmented history" in publish.stderr


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


def test_user_prompt_submit_triggers_for_self_evolution_runs():
    prompt = json.dumps({"prompt": "开始自我进化，连续迭代到预算、阻塞或没有 pending goal"})
    result = run_guard(["hook", "UserPromptSubmit"], prompt)

    assert result.returncode == 0, result.stderr
    context = hook_context(json.loads(result.stdout))
    assert "self-evolution run" in context
    assert "budget, blocker, or no pending goal" in context


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
    assert " checkpoint --if-active --root . --" not in stop_command
    assert " gate --phase review_gate --root . --verify" in stop_command
    assert " active-verify --root ." in stop_command
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


def test_stop_hook_preserves_review_gate_failure():
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
            "if 'gate' in sys.argv:\n"
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


def test_audit_rejects_push_claim_without_history_consolidation():
    draft = VALID_INITIALIZED_GOAL + "\nPushed branch to origin.\n"
    result = run_guard(["audit"], draft)

    assert result.returncode == 1
    assert "history consolidation" in result.stderr


def test_audit_accepts_push_claim_with_history_consolidation():
    draft = (
        VALID_INITIALIZED_GOAL
        + "\nHistory consolidated: squash or merge before push.\n"
        + "Pushed branch to origin after final verification.\n"
    )
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


def test_policy_gate_accepts_payload_approval_token():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_policy_project(root, approvalRequiredPaths=["package.json"])
        payload = json.dumps({"approvalToken": "approved", "tool_input": {"file": "package.json"}})
        result = run_guard(["policy-gate", "--root", str(root), "--hook"], payload)

    assert result.returncode == 0, result.stderr


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


def test_publish_gate_rejects_fragmented_history_before_push():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        git_commit(repo, "one.txt", "one\n", "one")
        git_commit(repo, "two.txt", "two\n", "two")

        result = run_guard(["publish-gate", "--root", str(repo)])

    assert result.returncode == 1
    assert "fragmented history" in result.stderr


def test_publish_gate_allow_fragmented_push_only_skips_fragmented_history():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        git_commit(repo, "one.txt", "one\n", "one")
        git_commit(repo, "two.txt", "two\n", "two")

        result = run_guard(
            ["publish-gate", "--root", str(repo)],
            env={**os.environ, "GOAL_MATRIX_ALLOW_FRAGMENTED_PUSH": "1"},
        )

    assert result.returncode == 0, result.stderr


def test_publish_gate_allow_fragmented_push_still_rejects_dirty_worktree():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        git_commit(repo, "one.txt", "one\n", "one")
        write_file(repo / "dirty.txt", "dirty\n")

        result = run_guard(
            ["publish-gate", "--root", str(repo)],
            env={**os.environ, "GOAL_MATRIX_ALLOW_FRAGMENTED_PUSH": "1"},
        )

    assert result.returncode == 1
    assert "uncommitted changes" in result.stderr


def test_publish_gate_allow_fragmented_push_still_rejects_active_goal():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        commit_goal_matrix(repo, active_goal="G2 - Still running")

        result = run_guard(
            ["publish-gate", "--root", str(repo)],
            env={**os.environ, "GOAL_MATRIX_ALLOW_FRAGMENTED_PUSH": "1"},
        )

    assert result.returncode == 1
    assert "active goal" in result.stderr


def test_publish_gate_allow_fragmented_push_still_rejects_missing_checkpoint_evidence():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        commit_goal_matrix(repo, evidence=False)

        result = run_guard(
            ["publish-gate", "--root", str(repo)],
            env={**os.environ, "GOAL_MATRIX_ALLOW_FRAGMENTED_PUSH": "1"},
        )

    assert result.returncode == 1
    assert "missing checkpoint evidence" in result.stderr


def test_publish_gate_allow_fragmented_push_still_rejects_missing_upstream():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True)
        git_commit(repo, "README.md", "base\n", "base")

        result = run_guard(
            ["publish-gate", "--root", str(repo)],
            env={**os.environ, "GOAL_MATRIX_ALLOW_FRAGMENTED_PUSH": "1"},
        )

    assert result.returncode == 1
    assert "missing upstream" in result.stderr


def test_publish_gate_allow_fragmented_push_still_rejects_behind_upstream():
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

        result = run_guard(
            ["publish-gate", "--root", str(repo)],
            env={**os.environ, "GOAL_MATRIX_ALLOW_FRAGMENTED_PUSH": "1"},
        )

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


def test_publish_gate_hook_rejects_push_with_fragmented_history():
    with tempfile.TemporaryDirectory() as tmp:
        repo = make_publish_repo(Path(tmp))
        git_commit(repo, "one.txt", "one\n", "one")
        git_commit(repo, "two.txt", "two\n", "two")
        payload = json.dumps({"tool_input": {"cmd": "git push origin HEAD"}})

        result = run_guard(["publish-gate", "--root", str(repo), "--hook"], payload)

    assert result.returncode == 1
    assert "fragmented history" in result.stderr


def test_publish_gate_hook_rejects_publish_action_patterns():
    for command in ("npm publish", "gh release create v1.2.3"):
        with tempfile.TemporaryDirectory() as tmp:
            repo = make_publish_repo(Path(tmp))
            write_file(
                repo / ".goal-matrix" / "project-policy.json",
                json.dumps({"publishActionPatterns": ["npm publish", "gh release"]}, indent=2) + "\n",
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
            payload = json.dumps({"tool_input": {"cmd": command}})

            result = run_guard(["publish-gate", "--root", str(repo), "--hook"], payload)

        assert result.returncode == 1, command
        assert "fragmented history" in result.stderr


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
    assert status["goalMatrix"]["childGoals"][1]["dependencies"] == "G1"
    assert status["goalMatrix"]["childGoals"][1]["risk"] == "P1"
    assert status["goalMatrix"]["childGoals"][1]["parallelSafety"] == "independent if touched paths do not overlap"
    assert "| Dependencies | Risk | Parallel safety | Status |" in matrix_text
    assert "scheduler/acceptance active goal" in active_text
    assert "verify each child goal before checkpoint" in active_text


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


def test_checkpoint_command_requires_passing_verification_before_advancing_goal():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        assert run_guard(["start", "--root", tmp], "ship real loop step").returncode == 0

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
        assert run_guard(["start", "--root", tmp], "ship real loop step").returncode == 0

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
        assert run_guard(["start", "--root", tmp], "ship real loop step").returncode == 0

        verified = run_guard(
            [
                "checkpoint",
                "--root",
                tmp,
                "--",
                sys.executable,
                "-c",
                "print('verified proof')",
            ]
        )
        status_result = run_guard(["status", "--root", tmp])
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
    assert status["goalMatrix"]["childGoals"][0]["status"] == "Done"


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
    assert "--install-git-hook" in payload["nativeHooks"]["installCommand"]


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


def test_review_gate_allows_fast_lane_when_no_active_goal():
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
