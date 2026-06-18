#!/usr/bin/env bash
# 初始化 workspace/default 模板
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec powershell -NoProfile -File "$REPO_ROOT/scripts/setup_workspace.ps1" 2>/dev/null || {
  WS="$REPO_ROOT/workspace/default"
  mkdir -p "$WS/memory" "$WS/skills/kb-qa"
  [[ -f "$WS/SOUL.md" ]] || cat > "$WS/SOUL.md" <<'EOF'
# SOUL — Agent 人格

你是 NewHuman 个人 AI 助手。回复简洁、准确，优先使用工具获取事实。
EOF
  echo "[workspace] ready: $WS"
}
