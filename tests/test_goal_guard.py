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
    assert "immutablePaths" in policy
    assert "approvalRequiredPaths" in policy
    assert "truthSources" in policy
    assert "verification" in policy["completionRequires"]
    assert "truthSource" in policy["completionRequires"]
    assert "checkpoint" in policy["completionRequires"]


def test_goal_matrix_initialization_is_project_local():
    with tempfile.TemporaryDirectory() as tmp:
        init = run_guard(["init", "--root", tmp, "--type", "iteration"])
        audit = run_guard(["audit", "--root", tmp])

    assert init.returncode == 0, init.stderr
    assert audit.returncode == 0, audit.stderr


def test_manifest_wires_skill_and_hooks():
    manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())

    assert manifest["name"] == "goal-matrix-iterative-delivery"
    assert manifest["skills"] == "./adapters/codex/skills/"
    assert manifest["hooks"] == "./adapters/codex/hooks/claude-codex-hooks.json"
    assert (ROOT / manifest["hooks"]).is_file()
    assert (ROOT / manifest["skills"]).is_dir()


def test_git_tracked_files_exclude_local_state_and_overlay_dirs():
    result = subprocess.run(
        ["git", "ls-files"],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    tracked = result.stdout.splitlines()
    for prefix in (".agents/", ".codex/", ".goal-matrix/", "plugins/"):
        assert not any(path.startswith(prefix) for path in tracked), prefix


def test_public_readmes_are_bilingual_and_hide_development_process_paths():
    chinese = read_text("README.md")
    english = read_text("README.en.md")

    assert "中文 | [English]" in chinese
    assert "English | [中文]" in english
    assert "Goal Matrix Iterative Delivery" in chinese
    assert "Goal Matrix Iterative Delivery" in english
    assert "create_goal" in chinese
    assert "create_goal" in english
    assert "validate_plugin_package.py" in chinese
    assert "validate_plugin_package.py" in english
    assert "项目安装" in chinese
    assert "全局 Codex" in chinese
    assert "Project Install" in english
    assert "Global Codex" in english
    assert "python3 scripts/install_adapter.py cursor --target /path/to/project" in chinese
    assert "python3 scripts/install_adapter.py codex --scope global" in english
    assert "python3 scripts/loop_verify.py" in chinese
    assert "python3 scripts/loop_verify.py" in english
    for phrase in ("Cursor", "Claude Code", "Generic"):
        assert phrase in chinese
        assert phrase in english
    for text in (chinese, english):
        assert "tests/" not in text
        assert "docs/" not in text
        assert ".codex-plugin" not in text
        assert "core/" not in text


def test_adapter_directories_exist():
    for path in (
        "adapters/codex/hooks/claude-codex-hooks.json",
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
        "adapters/cursor/goal-matrix-iterative-delivery.mdc",
        "adapters/claude-code/CLAUDE.md",
        "adapters/claude-code/README.md",
        "adapters/generic/AGENTS.md",
        "assets/icon.png",
        "scripts/install_adapter.py",
        "scripts/validate_plugin_package.py",
    ):
        assert (ROOT / path).is_file(), path


def test_instruction_adapters_include_core_invariants():
    for path in (
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
        "adapters/cursor/goal-matrix-iterative-delivery.mdc",
        "adapters/generic/AGENTS.md",
    ):
        text = read_text(path)
        for phrase in PROTOCOL_INVARIANTS:
            assert phrase in text, f"{path} missing {phrase}"


def test_instruction_adapters_include_skill_plugin_routing():
    for path in (
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
        "adapters/cursor/goal-matrix-iterative-delivery.mdc",
        "adapters/claude-code/CLAUDE.md",
        "adapters/generic/AGENTS.md",
    ):
        text = read_text(path)
        assert "Skill and plugin routing" in text, path
        assert "verification-before-completion" in text, path


def test_instruction_adapters_include_full_loop_boundaries():
    for path in (
        "adapters/codex/skills/goal-matrix-iterative-delivery/SKILL.md",
        "adapters/cursor/goal-matrix-iterative-delivery.mdc",
        "adapters/claude-code/CLAUDE.md",
        "adapters/generic/AGENTS.md",
    ):
        text = read_text(path)
        for phrase in (
            "project_initialization",
            "design_gate",
            "review_gate",
            "Next loop",
            "visible Codex goal",
        ):
            assert phrase in text, f"{path} missing {phrase}"


def test_adapter_readmes_include_install_and_validation_commands():
    for path in (
        "adapters/codex/README.md",
        "adapters/cursor/README.md",
        "adapters/claude-code/README.md",
        "adapters/generic/README.md",
    ):
        text = read_text(path)
        assert "install_adapter.py" in text, path
        assert "validate_plugin_package.py" in text, path
        assert "goal_guard.py doctor" in text, path
        assert "goal_guard.py audit" in text, path


def test_install_adapter_project_cursor_copies_rule_and_initializes_goal_matrix():
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
        target = Path(tmp)

        assert result.returncode == 0, result.stderr
        assert (target / ".cursor" / "rules" / "goal-matrix-iterative-delivery.mdc").is_file()
        assert (target / ".goal-matrix" / "project-policy.json").is_file()


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
    assert package["adapters"] == ["codex", "cursor", "claude-code", "generic"]
    assert package["manifest"]["name"] == "goal-matrix-iterative-delivery"


def test_l1_loop_ready_spine_files_are_committable():
    for path in ("LOOP.md", "STATE.md", "loop-budget.md", "loop-run-log.md", "scripts/loop_audit.py"):
        assert (ROOT / path).is_file(), path

    tracked = subprocess.run(["git", "ls-files"], text=True, capture_output=True, cwd=ROOT)

    assert tracked.returncode == 0, tracked.stderr
    for path in ("LOOP.md", "STATE.md", "loop-budget.md", "loop-run-log.md", "scripts/loop_audit.py"):
        assert path in tracked.stdout.splitlines(), path


def test_loop_audit_scores_current_repo_l2_assisted_with_verifier():
    result = subprocess.run(
        [sys.executable, str(LOOP_AUDIT), "--root", str(ROOT), "--json"],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["level"] == "L2"
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
    if audit["signals"]["githubRemote"]:
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
    assert audit["level"] == "L2"


def test_loop_engineering_gap_register_tracks_unfinished_work():
    loop = read_text("LOOP.md")
    state = read_text("STATE.md")

    for phrase in (
        "Engineering Gap Register",
        "remote-ci",
        "maker-checker",
        "run-evidence",
        "distribution",
        "connectors",
        "governance",
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
    assert audit["level"] == "L2"


def test_loop_audit_reports_unresolved_gap_register_items():
    result = subprocess.run(
        [sys.executable, str(LOOP_AUDIT), "--root", str(ROOT), "--json"],
        text=True,
        capture_output=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr
    audit = json.loads(result.stdout)
    assert audit["signals"]["gapRegister"] is True
    assert "remote-ci" in audit["unresolvedGaps"]
    assert "distribution" in audit["unresolvedGaps"]
    if audit["signals"]["githubRemote"]:
        assert audit["nextAction"] == "Append remote-ci-readback evidence after the workflow passes."
    else:
        assert audit["nextAction"] == "Add GitHub remote, push, and read back the workflow result."


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
    assert audit["signals"]["remoteRunEvidence"] is False
    assert audit["level"] == "L2"


def test_loop_verify_script_and_ci_share_one_gate():
    script = ROOT / "scripts" / "loop_verify.py"
    workflow = ROOT / ".github" / "workflows" / "loop-audit.yml"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    for phrase in (
        "scripts/loop_audit.py",
        "scripts/validate_plugin_package.py",
        "tests/test_goal_guard.py",
        "py_compile",
        "git diff --check",
    ):
        assert phrase in text
    assert "python3 scripts/loop_verify.py" in workflow.read_text(encoding="utf-8")


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


def test_session_start_injects_fused_rules():
    result = run_guard(["hook", "SessionStart"], "{}")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["systemMessage"] == "GOAL-MATRIX:ACTIVE"
    assert "Superpowers discipline" in hook_context(payload)
    assert "Ponytail scope" in hook_context(payload)


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
        "goal_guard.py status",
        "goal_guard.py gate",
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


def test_user_prompt_submit_triggers_for_engineering_habit_work():
    prompt = json.dumps({"prompt": "优化这个 plugin，按我的高频使用习惯和开发流程融合"})
    result = run_guard(["hook", "UserPromptSubmit"], prompt)

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
    result = run_guard(["hook", "UserPromptSubmit"], prompt)

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


def test_codex_hook_config_wires_loop_events():
    hooks = json.loads(read_text("adapters/codex/hooks/claude-codex-hooks.json"))["hooks"]
    for event in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"):
        assert event in hooks


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
[plugins."goal-matrix-iterative-delivery@goal-matrix-local"]
enabled = true
""",
        )
        (codex_home / "plugins" / "cache" / "goal-matrix-local" / "goal-matrix-iterative-delivery" / version).mkdir(
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
    assert source["codexMarketplaceConfigured"] is False
    assert source["codexPluginEnabled"] is True
    assert source["codexCacheHasManifest"] is False
    assert source["codexHookTrusted"] is False


def test_gate_command_returns_design_for_missing_design_evidence():
    result = run_guard(["gate", "--phase", "design_gate"], "No gate evidence yet.")

    assert result.returncode == 1
    decision = json.loads(result.stdout)
    assert decision["next"] == "design"
    assert "clarity decision" in decision["reason"]


def test_gate_command_returns_execute_for_failed_review():
    result = run_guard(["gate", "--phase", "review_gate"], "Verified with tests. Reviewer: changes requested")

    assert result.returncode == 1
    decision = json.loads(result.stdout)
    assert decision["next"] == "execute"
    assert "review requested changes" in decision["reason"]


def test_gate_command_returns_checkpoint_after_verified_review():
    text = "Clarity decision: proceed. Verified with tests. Reviewer: approved"
    result = run_guard(["gate", "--phase", "review_gate"], text)

    assert result.returncode == 0, result.stderr
    decision = json.loads(result.stdout)
    assert decision["next"] == "checkpoint"


def test_gate_command_reads_loop_note_from_root_when_stdin_is_empty():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert run_guard(["init", "--root", tmp, "--type", "iteration"]).returncode == 0
        write_file(
            root / ".goal-matrix" / "loop-note.md",
            "Clarity decision: proceed\nVerified with tests\nReviewer: approved\n",
        )

        result = run_guard(["gate", "--phase", "review_gate", "--root", tmp])

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
