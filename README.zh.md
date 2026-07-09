<p align="center">
  <img src="assets/icon.png" alt="Goal Matrix Delivery icon" width="96" height="96">
</p>

# Goal Matrix Iterative Delivery

> 中文 | [English](README.md)

让 Codex 的工作保持诚实：一个 active slice，一个 truth source，一份验证证据，然后再交接。

## 安装

把 GitHub 仓库作为 Codex 插件源安装：

```bash
codex plugin marketplace add https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git --ref v0.1.8-codex.2
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

初始化只写 `.goal-matrix/` 文件。若已有原生 hook，安装器会保留到 `.git/hooks/pre-push.goal-matrix.previous`。

## 日常循环

```bash
printf '修复下一个有边界的目标' | python3 core/goal_guard.py start --root .
python3 core/goal_guard.py status --root .
python3 core/goal_guard.py checkpoint --root . -- python3 scripts/loop_verify.py
```

流程保持很小：

```text
初始化 -> 分类 -> 设计 -> 执行 -> 验收 -> checkpoint -> 下一轮
```

遇到 broad prompt，`start` 可以创建多个 pending child goals，但主线程仍然一次只验证、checkpoint 一个 child goal。Fast Lane 只用于没有 active goal 的拼写、文案或单函数小改。

Hooks 不会自己创建 Codex 侧边栏里的可见 goal；需要可见跟踪时显式调用 `create_goal`。

## 运行边界

- `.goal-matrix/project-policy.json` 是目标项目运行时 policy 真源。
- `loop-governance.json` 只用于插件仓库自治。
- `.goal-matrix/state.json` 是机器状态；Markdown goal 文件是人读视图。
- hooks 只提醒/阻断，不隐藏执行、不自动推送。
- Codex lifecycle adapter 是这个包里唯一的 lifecycle adapter。

## 发布门禁

Codex `PreToolUse` 会在 `git push` 和配置过的发布命令前运行：

```bash
python3 core/goal_guard.py publish-gate --root .
```

当 worktree 未提交、active goal 仍打开、checkpoint evidence 缺失、upstream 缺失或落后，或分支相对 upstream 领先超过 1 个本地提交时会失败。先 squash 或 merge，除非用户明确要保留碎历史。

## 项目通知

初始化项目会创建可选通知设置。用 `/goal-notify status`、`/goal-notify test` 或 `/goal-notify templates` 查看；webhook secret 放本地文件或 `GOAL_MATRIX_WEBHOOK_URL`。

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
