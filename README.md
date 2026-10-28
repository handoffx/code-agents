# code-agents

把 code agent 使用方法论落成可实践的 Claude Code 插件。本仓库是一个插件 marketplace（`.claude-plugin/marketplace.json`），插件放在 `plugins/` 下。方法论本身的讨论记录在 Obsidian 的 `code-agents/` 目录（从"方法论总览"开始读）。

## task-contract

把多步骤开发任务按"先定决策、再拆解、小步验收、可核对证据"的流程交给 agent：分级 → 探索 → 决策清单 → 拆解（首尾整体验收）→ 小步执行 → 完成报告。L2 及以上的任务用任务文件保存决策、已排除的方案和进度，丢掉会话或上下文被压缩后都能接着做；多个任务可以在不同的 worktree 里并存。

| 组件 | 作用 |
|---|---|
| `task-contract:start` | 自动触发：做新功能、重构、迁移、多文件修复等多步骤开发任务时加载 |
| `task-contract:resume` | 列出本仓库所有 worktree 里的未完成任务供选择，从任务文件接着做 |
| `agent-tasks` | 插件自带命令：`new` 新建任务文件，`list [--all]` 列出任务 |
| SessionStart hook | 会话开始、恢复、`/clear`、上下文压缩后，有未完成任务时提示 Claude |

任务文件在每个 worktree 根目录的 `.agent-tasks/` 下。目录里有一个只写了 `*` 的 `.gitignore`，所以不会被提交，也不用改项目自己的 `.gitignore`。同一个 worktree 同一时间只建议有一个任务在改代码，要并行就用 `claude --worktree <名字>` 另开 worktree。

## 安装

从 GitHub 安装：

```bash
claude plugin marketplace add handoffx/code-agents
claude plugin install task-contract@code-agents
```

从 GitHub 安装的插件会复制到插件缓存里，仓库有更新后运行 `claude plugin marketplace update code-agents` 获取新版本。

开发时克隆仓库，从本地路径安装：

```bash
git clone https://github.com/handoffx/code-agents.git
claude plugin marketplace add ./code-agents
claude plugin install task-contract@code-agents
```

从本地路径添加的 marketplace 直接读取仓库里的文件，修改插件后在会话里运行 `/reload-plugins` 或开新会话即可生效。

## 开发

```bash
claude plugin validate .                         # 校验 marketplace
claude plugin validate ./plugins/task-contract   # 校验插件
```

## 许可证

[MIT](LICENSE) © 2026 chaojun.xiao
