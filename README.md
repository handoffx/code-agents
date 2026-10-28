# code-agents

把 code agent 使用方法论落成可实践的 Claude Code 插件。本仓库是一个插件 marketplace（`.claude-plugin/marketplace.json`），插件放在 `plugins/` 下。

## 方法论

这套方法与具体工具和项目无关，插件只是它在 Claude Code 上的一种落地。五条核心命题：

1. **任务粒度由你的验证能力决定，而不是模型能力。** 验证能力包括三部分：发现错误、回退改动、证明正确。你验证不了的步骤，就不该一次交出去
2. **拆解的单位是决策，不是代码行数。** 你在意、但还没定的决策，在执行前就要摆出来让你定；执行中冒出新的决策，agent 要停下来问，不能自己做掉
3. **执行上下文和验收节点分开。** 给 agent 完整的目标和背景，同时让它小步交付、每步给出能核对的证据：贴出实际运行的命令和输出，只说"测试已通过"不算证据
4. **成本和不确定性成正比。** 按"有没有未定的决策"分级，简单任务直接做，复杂任务才走决策清单和完整拆解；数据迁移、改接口、鉴权、依赖升级这类改动出了错发现慢、回退难，至少走决策清单
5. **审查的是契约，不是 diff。** 机器负责证明，agent 的报告只当索引，人只判断契约层面的变化：新接口、新抽象、新依赖、模块边界。审查深度与发现和回退能力成反比

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
