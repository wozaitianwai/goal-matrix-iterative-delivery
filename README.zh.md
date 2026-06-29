<p align="center">
  <img src="assets/icon.png" alt="Goal Matrix Delivery icon" width="96" height="96">
</p>

# Goal Matrix Iterative Delivery

> 中文 | [English](README.md)

让 Codex 的工作保持诚实：一个目标矩阵，一个 active slice，一份验证证据，然后再交接。

当需求大到不是一次简单编辑就能完成时，用它约束 agent：先定边界、真源和验证，再开始动手。

## 为什么用它

| 问题 | 护栏 |
| --- | --- |
| 工作范围悄悄膨胀 | 一个回合只保留一个 active goal |
| 完成声明只靠感觉 | 必须有 truth source 才能交付 |
| 重启后上下文丢失 | 项目内 `.goal-matrix/` 状态可读回 |
| 推送历史变得很乱 | 发布门禁要求分支历史干净 |

## 安装

把 GitHub 仓库作为 Codex 插件源安装：

```bash
codex plugin marketplace add https://github.com/wozaitianwai/goal-matrix-iterative-delivery.git --ref v0.1.1-codex.1
codex plugin add goal-matrix-iterative-delivery@goal-matrix-github
```

默认使用固定 release tag 安装，保证可复现；移动开发分支只用于未发布变更测试。

然后在 Codex Desktop 里 trust 这个插件的 hooks，并重启一次 Codex 让 lifecycle hooks 生效。

## 初始化项目

给某个项目创建 goal-matrix 状态：

```bash
python3 scripts/install_adapter.py codex --target /path/to/project
```

这个命令只会在目标项目写入 `.goal-matrix/` 文件，不会修改 Codex 配置。

如果还要约束 shell 或人工手动 push，可以安装原生 git hook：

```bash
python3 scripts/install_adapter.py codex --target /path/to/project --install-git-hook
```

## 日常循环

```bash
printf '修复下一个有边界的目标' | python3 core/goal_guard.py start --root .
python3 core/goal_guard.py status --root .
python3 core/goal_guard.py checkpoint --root . -- python3 scripts/loop_verify.py
```

`scripts/loop_audit.py --json` 会在 `loop-run-log.md` 超过 500 行时报告 `runLogNeedsSummary`；继续长期循环前先执行 summary/pruning 子目标。

`.goal-matrix/project-policy.json` 是目标项目运行时 policy 真源，负责 path、command 和 publish-action gate。`loop-governance.json` 只用于插件仓库自治，也就是本仓库自己的 CI/static governance 检查。`STATE.md` 只做人读视图，不重复 approval env、受保护路径或 publish pattern。人读状态复制机器 policy 值时，audit 会报告 `stateGovernanceDuplication`。

Fast Lane 只在没有 active goal，且请求只是拼写、文案或单函数小改时可用。它保留 policy/publish gate 和 focused verification，但跳过 goal-matrix checkpoint。命中受保护路径、发布动作、范围不清晰或多文件行为变更时回到正常 loop。

流程故意保持很小：

```text
初始化 -> 分类 -> 设计 -> 执行 -> 验收 -> checkpoint -> 下一轮
```

## 项目通知

初始化项目时也会创建可选的通知设置。启用项目状态里的通知后，用 Codex 弹窗命令查看：

```bash
/goal-notify status
/goal-notify test
/goal-notify templates
```

这个命令由打包后的 `pi.extensions` 入口加载，并使用 Codex 的 `ctx.ui.notify`；不是 hook 日志或聊天消息通知。

内置 generic、Slack、Discord、飞书、钉钉、企业微信的 webhook payload 模板。需要 webhook 投递时在项目配置里启用，真实 webhook secret 放在本地通知文件或 `GOAL_MATRIX_WEBHOOK_URL`；本地通知文件会写入 `.gitignore`。

## Hooks 会约束什么

- 动手前写清楚交付边界、跳过内容、真源和验证方式。
- 一个回合只执行一个 active goal。
- 先复用项目已有代码和宿主能力，再考虑新增机制。
- 阻断不安全的发布动作；hooks 只负责提醒和约束，不隐藏执行、不自动推送。

## 发布门禁

Codex `PreToolUse` hook 会在 `git push` 以及命中 `publishActionPatterns` 的命令前运行，例如 `npm publish`、`twine upload`、`gh release`：

```bash
python3 core/goal_guard.py publish-gate --root .
```

当 worktree 未提交、active goal 仍打开、checkpoint evidence 缺失、upstream 缺失或落后，或分支相对 upstream 领先超过 1 个本地提交时会失败。先 squash 或 merge；只有用户明确要求保留碎历史时，才设置 `GOAL_MATRIX_ALLOW_FRAGMENTED_PUSH=1` 放行。

可选的原生 `pre-push` hook 运行同一个 gate，直接 shell push 也会走同一套策略。如果已有 hook，安装器会把它链到 `.git/hooks/pre-push.goal-matrix.previous`；恢复时把该文件移回 `.git/hooks/pre-push`。

## 插件检查

```bash
python3 scripts/validate_plugin_package.py --root .
python3 scripts/loop_verify.py
```

## 开源声明

本项目按 [MIT License](LICENSE) 开源。你可以在该许可证范围内使用、修改和分发。

## 边界

lifecycle hooks 只会给模型注入上下文，不会自己创建 Codex 侧边栏里的可见 goal。需要可见 goal 时，agent 必须显式调用 `create_goal`。

这个包里只有 Codex lifecycle adapter。只有当仓库包含某个宿主的真实 hook wiring 时，才新增对应 adapter。

这个插件不是后台任务系统，也不是项目管理平台。它只负责在 Codex 里把工程循环变得明确、可验证。
