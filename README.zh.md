<p align="center">
  <img src="assets/icon.png" alt="Goal Matrix Delivery icon" width="96" height="96">
</p>

# Goal Matrix Iterative Delivery

> 中文 | [English](README.md)

让 Codex 的工作保持诚实：一个 active slice，一个 truth source，一份验证证据，然后再交接。

## 安装

把 GitHub 仓库作为 Codex 插件源安装：

```bash
codex plugin marketplace add https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git --ref v0.1.14-codex.3
codex plugin add goal-matrix-iterative-delivery@goal-matrix-github
```

默认使用固定 release tag 安装，保证可复现；移动开发分支只用于未发布变更测试。

然后在 Codex Desktop 里 trust hooks，并重启一次。

## 初始化项目

创建项目本地状态：

```bash
python3 scripts/install_adapter.py codex --target /path/to/project
```

可选安装原生 push guard：

```bash
python3 scripts/install_adapter.py codex --target /path/to/project --install-git-hook
```

初始化只写 `.goal-matrix/` 文件。使用 `--install-git-hook` 时，未托管的原生 hook 只会被保留一次到同目录的 `pre-push.goal-matrix.previous`；再次执行命令会原地刷新已托管的 stale/broken wrapper。`doctor` 会报告 `absent`、`unmanaged`、`current`、`stale` 或 `broken`，不会隐式安装 hook。

## 日常循环

```bash
python3 core/goal_guard.py start --root . <<'JSON'
{
  "userOutcome": "修复下一个有边界的目标",
  "engineeringSlice": "只修改一个可验证行为",
  "initializationType": "iteration",
  "policyImpact": "none",
  "touchedPaths": ["src/module.py"],
  "deliveryBoundary": "仅限当前行为",
  "skipped": "无关工作",
  "truthSource": "tests",
  "verification": "python3 -m unittest",
  "developmentFlow": "inspect -> failing check -> implement -> verify -> checkpoint"
}
JSON
python3 core/goal_guard.py status --root .
python3 core/goal_guard.py checkpoint --root . -- python3 scripts/loop_verify.py
```

`start` 状态不变量：

- 普通单目标输入不写入状态，必须改为提交上面的结构化 JSON contract（Plain single-goal input does not write state）。
- 完整结构化输入会原位修复不完整的 active goal，并保留原 id（Complete structured input repairs an incomplete active goal in place and preserves its id）。
- 完整的 active goal 必须先 checkpoint，后续 `start` 不会覆盖它（A complete active goal requires checkpoint and is not overwritten）。
- self-evolution 在没有 pending goal 时直接返回 complete，不合成 backlog 状态（Self-evolution with no pending goal returns complete）。

流程保持很小：

```text
初始化 -> 分类 -> 设计 -> 执行 -> 验收 -> checkpoint -> 下一轮
```

遇到 broad prompt，`start` 可以创建多个 pending child goals，但主线程仍然一次只验证、checkpoint 一个 child goal。Fast Lane 只用于没有 active goal 的拼写、文案或单函数小改。

Hooks 不会自己创建 Codex 侧边栏里的可见 goal；需要可见跟踪时显式调用 `create_goal`。

## 运行边界

- `.goal-matrix/project-policy.json` 是目标项目运行时 policy 真源。
- `loop-governance.json` 只用于插件仓库自治。
- `.goal-matrix/state.json` 是 active contract、matrix 状态和 Done 行保留数的真源；每次状态写入都会重建并审计主表与归档 Markdown 投影。
- push 和 pull request 会在 Python 3.10、3.12、3.14 上各运行一次共享 verifier；每个 matrix leg 都必须用当前 GitHub Actions 上下文建立 L3。
- hooks 只提醒/阻断，不隐藏执行、不自动推送。
- Codex lifecycle adapter 是这个包里唯一的 lifecycle adapter。

## 发布门禁

Codex `PreToolUse` 会在 `git push` 和配置过的发布命令前运行：

```bash
python3 core/goal_guard.py publish-gate --root .
```

当 worktree 未提交、active goal 仍打开、checkpoint evidence 缺失、upstream 缺失或落后，或分支相对 upstream 领先超过 1 个本地提交时会失败。先 squash 或 merge，除非用户明确要保留碎历史。

## 项目通知

初始化项目会创建可选通知设置。用 `/goal-notify status`、`/goal-notify test` 或 `/goal-notify templates` 查看。tracked 配置只能定义弹窗和 webhook 模板；webhook 发送必须由已忽略的 `notifications.local.json` 或 `GOAL_MATRIX_WEBHOOK_URL` 显式启用。

## 插件检查

```bash
python3 scripts/validate_plugin_package.py --root .
python3 scripts/loop_verify.py
```

## 开源声明

本项目按 [MIT License](LICENSE) 开源。你可以在该许可证范围内使用、修改和分发。

## 边界

UserPromptSubmit 不会运行 `start`。

这个插件不是后台任务系统，也不是项目管理平台。它只负责让 Codex 里的工程循环明确、可验证。
