#!/bin/bash
# 运行 task-contract 插件的 eval。
#   scripts/eval.sh smoke   每个用例跑 1 次、不跑无插件对照组，改完插件后快速检查
#   scripts/eval.sh full    每个用例默认 3 次 + 无插件对照组，发布新版本前跑
# 其余参数原样传给 claude plugin eval，例如 --case 'decision-*'
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:-smoke}"; shift || true
case "$mode" in
  smoke) tier=(--runs 1 --ablation none) ;;
  full)  tier=() ;;
  *) echo "用法：$0 smoke|full [claude plugin eval 的其他参数]" >&2; exit 64 ;;
esac
# 用例要真实建出任务文件，所以授权限定范围的 Bash 和文件写入；Bash 在沙箱里运行
exec claude plugin eval ./plugins/task-contract \
  "${tier[@]}" \
  --scaffold \
  --trust-plugin \
  --no-publish \
  --allow-tools "Bash(agent-tasks *)" "Bash(git *)" Write Edit \
  "$@"
