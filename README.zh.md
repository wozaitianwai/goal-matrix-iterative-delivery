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

把当前 checkout 作为本地 Codex 插件源安装：

```bash
codex plugin marketplace add .
codex plugin add goal-matrix-iterative-delivery@goal-matrix-local
```

然后在 Codex Desktop 里 trust 这个插件的 hooks，并重启一次 Codex 让 lifecycle hooks 生效。

## 初始化项目

给某个项目创建 goal-matrix 状态：

```bash
python3 scripts/install_adapter.py codex --target /path/to/project
```

这个命令只会在目标项目写入 `.goal-matrix/` 文件，不会修改 Codex 配置。

## 日常循环

```bash
printf '修复下一个有边界的目标' | python3 core/goal_guard.py start --root .
python3 core/goal_guard.py status --root .
python3 core/goal_guard.py checkpoint --root . -- python3 scripts/loop_verify.py
```

流程故意保持很小：

```text
初始化 -> 分类 -> 设计 -> 执行 -> 验收 -> checkpoint -> 下一轮
```

## Hooks 会约束什么

- 动手前写清楚交付边界、跳过内容、真源和验证方式。
- 一个回合只执行一个 active goal。
- 先复用项目已有代码和宿主能力，再考虑新增机制。
- 阻断不安全的发布动作；hooks 只负责提醒和约束，不隐藏执行、不自动推送。

## 发布门禁

Codex `PreToolUse` hook 会在 `git push` 前运行：

```bash
python3 core/goal_guard.py publish-gate --root .
```

当分支相对 upstream 领先超过 1 个本地提交时会失败。先 squash 或 merge；只有用户明确要求保留碎历史时，才设置 `GOAL_MATRIX_ALLOW_FRAGMENTED_PUSH=1` 放行。

## 插件检查

```bash
python3 scripts/validate_plugin_package.py --root .
python3 scripts/loop_verify.py
```

## 边界

lifecycle hooks 只会给模型注入上下文，不会自己创建 Codex 侧边栏里的可见 goal。需要可见 goal 时，agent 必须显式调用 `create_goal`。

这个包里只有 Codex lifecycle adapter。只有当仓库包含某个宿主的真实 hook wiring 时，才新增对应 adapter。

这个插件不是后台任务系统，也不是项目管理平台。它只负责在 Codex 里把工程循环变得明确、可验证。
