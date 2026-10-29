# code-agents

把 code agent 使用方法论落成可实践的 Claude Code 插件。本仓库是一个插件 marketplace（`.claude-plugin/marketplace.json`），插件放在 `plugins/` 下。

## 方法论

这套方法与具体工具和项目无关，插件只是它在 Claude Code 上的一种落地。五条核心命题：

1. **任务粒度由你的验证能力决定，而不是模型能力。** 验证能力包括三部分：发现错误、回退改动、证明正确。你验证不了的步骤，就不该一次交出去
2. **拆解的单位是决策，不是代码行数。** 你在意、但还没定的决策，在执行前就要摆出来让你定；执行中冒出新的决策，agent 要停下来问，不能自己做掉
3. **执行上下文和验收节点分开。** 给 agent 完整的目标和背景，同时让它小步交付、每步给出能核对的证据：贴出实际运行的命令和输出，只说"测试已通过"不算证据
4. **成本和不确定性成正比。** 按"有没有未定的决策"分级，简单任务直接做，复杂任务才走决策清单和完整拆解；数据迁移、改接口、鉴权、依赖升级这类改动出了错发现慢、回退难，至少走决策清单
5. **审查的是契约，不是 diff。** 机器负责证明，agent 的报告只当索引，人只判断契约层面的变化：新接口、新抽象、新依赖、模块边界。审查深度与发现和回退能力成反比

完整的方法论笔记见 [docs/](docs/README.md)，由作者的 Obsidian 笔记单向导出，建议从"方法论总览"读起。

## task-contract

把多步骤开发任务按"先定决策、再拆解、小步验收、可核对证据"的流程交给 agent：分级 → 探索 → 决策清单 → 拆解（首尾整体验收）→ 小步执行 → 完成报告。L2 及以上的任务用任务文件保存决策、已排除的方案和进度，丢掉会话或上下文被压缩后都能接着做；多个任务可以在不同的 worktree 里并存。

| 组件 | 作用 |
|---|---|
| `task-contract:start` | 自动触发：做新功能、重构、迁移、多文件修复等多步骤开发任务时加载 |
| `task-contract:resume` | 列出本仓库所有 worktree 里的未完成任务供选择，从任务文件接着做 |
| `agent-tasks` | 插件自带命令：`new` 新建任务文件，`list [--all]` 列出任务 |
| SessionStart hook | 会话开始、恢复、`/clear`、上下文压缩后，有未完成任务时提示 Claude |

执行阶段有两种方式：**逐步**（默认，每完成一步停下来交证据）和**一口气**（决策和拆解定下来后一直做完，证据写进任务文件，只在冒出新决策、卡住、做到一大半补不完时停）。后台会话（`claude --bg`）里检测到 `CLAUDE_JOB_DIR` 时默认一口气；前台确认拆解时可以选。两种方式都要先写整体验收检查，最后给出固定 6 段标题的完成报告。

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

### Eval

`plugins/task-contract/evals/` 下有 7 个用例，检查插件的关键行为：多步骤任务触发 `start`、问答不触发、决策清单先写进任务文件并标"待表态"、表态之前不改 `.py` 文件、看起来很小的数据迁移也按 L2 处理、没有选择框时退回文字清单、用户事先授权时一口气做完并给出 6 段完成报告。判分只用确定性的 grader（正则、工具调用、文件是否存在），不调用评审模型。

```bash
scripts/eval.sh smoke   # 冒烟档：每个用例 1 次、不跑无插件对照组，约 7 次 agent 运行
scripts/eval.sh full    # 全套：每个用例 3 次 + 无插件对照组，约 42 次 agent 运行
scripts/eval.sh smoke --case 'no-*'   # 其余参数原样传给 claude plugin eval
```

- **什么时候跑**：改完插件跑冒烟档；发布新版本前跑全套
- **费用**：eval 用你自己的 Claude Code 凭据调用模型，计入你的用量。冒烟档约 $1.9（2026-10-29 实测，7 个用例），全套约 $8.8；加 `-j 4` 并行时全套约 7 分钟
- **环境**：用例要真实建出任务文件，脚本授权了限定范围的 Bash（`agent-tasks`、`git`、`python3`）和 Write、Edit，并把仓库里的 `plugins/task-contract/bin` 放在 PATH 最前面（否则 eval 会继承当前会话 PATH 里已安装版本的 `agent-tasks`）。Bash 在沙箱里运行，Linux 上需要 `bubblewrap` 和 `socat`
- **测不到的**：eval 是非交互会话，没有 AskUserQuestion，所以"用选择框逐项提问"这条要在发布前人工检查；eval 只放行 `EVAL_*` 环境变量，后台会话的 `CLAUDE_JOB_DIR` 自动检测也测不到，要用 `claude --bg` 实际跑一次
- 每次运行的报告写在 `plugins/task-contract/evals/results/`，不提交
- 实践中暴露的问题修好后，补一个对应的用例

### 方法论文档

`docs/` 由 `scripts/export-docs.py` 从 Obsidian 笔记单向导出，不要直接修改：只导出状态为"共识"的方法论笔记（路线图除外），笔记之间的双链转成相对链接，指向未公开笔记的双链只保留文字。

```bash
export OBSIDIAN_VAULT=<Obsidian vault 路径>   # 也可以每次用 --vault 指定
scripts/export-docs.py            # 改完笔记后重新导出，再提交 docs/
scripts/export-docs.py --check    # 只比较不写入；docs/ 与笔记不一致时退出码为 1
python3 scripts/test_export_docs.py   # 导出脚本的测试；设了 OBSIDIAN_VAULT 时还会检查真实笔记
```

提交前跑一次 `--check`：它能发现"改了笔记忘了导出"和"有人直接改了 docs/"两种情况。

## 发布新版本

从 GitHub 安装的用户只有在插件的 `version` 变化时才会拿到新版本。改了插件却不改版本号，推送上去用户也收不到。

1. 修改插件
2. 改 `plugins/task-contract/.claude-plugin/plugin.json` 里的 `version`：修正问题改第三位（`0.1.0` → `0.1.1`），新增或改变行为改第二位（`0.1.1` → `0.2.0`）
3. 校验：`claude plugin validate .`
4. 跑全套 eval：`scripts/eval.sh full`，退出码为 0
5. 人工检查选择框：在交互会话里用 `/task-contract:start` 开一个 L2 任务，确认决策是用选择框一项一项问的
6. 提交并推送到 `main`

用户端获取新版本，任选一种：

- 会话里运行 `/plugin marketplace update code-agents`
- shell 里运行 `claude plugin update task-contract@code-agents`
- 在 `/plugin` 的 Marketplaces 里选中 `code-agents`，打开 Enable auto-update（默认关闭），之后会在后台自动更新

更新后开新会话或运行 `/reload-plugins` 生效。

注意：

- 版本号只写在 `plugin.json` 里，不要在 `marketplace.json` 的条目里再写一份。两处都写时以 `plugin.json` 为准，`claude plugin validate` 会报不一致
- 从本地路径安装的插件不受版本号控制，每次会话启动都直接读仓库里的文件

## 许可证

[MIT](LICENSE) © 2026 chaojun.xiao
