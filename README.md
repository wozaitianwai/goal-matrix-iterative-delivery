# Goal Matrix Iterative Delivery

> 中文 | [English](README.en.md)

![Goal Matrix Delivery icon](assets/icon.png)

**Goal Matrix Iterative Delivery** 是一个面向 Codex 和常见 agent 工具的工程工作流插件。它把宽泛需求拆成可执行的目标矩阵，每次只推进一个 active goal，并要求用真实证据完成验证和交接。

## 安装

### 项目安装

把规则安装到某一个项目，适合 Cursor、Claude Code 或通用 agent 项目：

```bash
python3 scripts/install_adapter.py cursor --target /path/to/project
python3 scripts/install_adapter.py claude-code --target /path/to/project
python3 scripts/install_adapter.py generic --target /path/to/project
```

这些命令会写入对应工具的项目规则，并初始化目标项目的 goal matrix。

### 全局 Codex

把 Codex skill 同步到当前用户的 Codex 环境：

```bash
python3 scripts/install_adapter.py codex --scope global
```

这个命令只同步 skill 文件，不会静默修改 Codex 配置或 marketplace。

### 验证插件包

```bash
python3 scripts/validate_plugin_package.py --root .
```

### 一键工程检查

```bash
python3 scripts/loop_verify.py
```

## 工作方式

```text
初始化项目 -> 分类工作 -> 设计目标 -> 通过设计门 -> 执行切片 -> 通过验收门 -> checkpoint -> 下一轮
```

核心原则：

- 一个回合只执行一个 active goal。
- 每个 goal 都要说明交付边界、跳过内容、真源和验证方式。
- 先复用已有代码和宿主能力，再考虑新增机制。
- hook 只做提醒和约束，不隐藏执行、不自动推送。

## Codex 可见 Goal

生命周期 hook 只会给模型注入目标矩阵上下文；它不会自己创建 Codex 侧边栏里的可见 goal。需要可见 goal 时，Codex agent 必须显式调用 `create_goal`。

## 工具适配边界

| 工具 | 安装方式 | 运行边界 |
| --- | --- | --- |
| Codex | 全局 Codex 安装命令 | skill 和生命周期 hook 会注入上下文；可见 goal 仍需 agent 调用 `create_goal` |
| Cursor | 项目安装命令 | 项目规则生效；没有 Codex runtime hook |
| Claude Code | 项目安装命令 | 项目指令生效；没有 Codex runtime hook |
| Generic | 项目安装命令 | 通用规则文件生效；没有 Codex runtime hook |

## 初始化类型

| 类型 | 何时使用 |
| --- | --- |
| `new-project` | 从零启动项目或功能 |
| `iteration` | 在已有项目上继续迭代 |
| `bugfix` | 修复失败、报错或异常行为 |
| `legacy-baseline` | 接手不清楚的遗留项目 |

## 边界

这个插件不是后台任务系统，也不是项目管理平台。它只做一件事：让工程循环显性化，并要求每个小目标有证据、有边界、有下一轮。
