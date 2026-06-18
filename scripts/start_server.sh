#!/usr/bin/env bash
# NewHuman MVP - 启动 FastAPI 服务
# 用法: ./scripts/start_server.sh [port]
# 前置: ./scripts/setup_conda.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$REPO_ROOT/code/app"
ENV_FILE="$APP_DIR/.env"
ENV_DEMO="$APP_DIR/.env.demo"
CONDA_ENV="${NEWHUMAN_CONDA_ENV:-newhuman}"

if ! command -v conda >/dev/null 2>&1; then
  echo "未找到 conda，请运行 scripts/setup_conda.sh" >&2
  exit 1
fi

if [[ ! -d "$APP_DIR" ]]; then
  echo "应用目录不存在: $APP_DIR" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$ENV_DEMO" ]]; then
    cp "$ENV_DEMO" "$ENV_FILE"
    echo "[setup] 已从 .env.demo 复制 .env"
  else
    echo "缺少 .env 与 .env.demo" >&2
    exit 1
  fi
fi

bash "$REPO_ROOT/scripts/setup_workspace.sh"

cd "$APP_DIR"
export PYTHONPATH="$APP_DIR"

PORT="${1:-${SERVICE_PORT:-8000}}"
export SERVICE_PORT="$PORT"

echo "========================================"
echo " NewHuman API (conda: $CONDA_ENV)"
echo " http://127.0.0.1:$PORT"
echo "========================================"

exec conda run --no-capture-output -n "$CONDA_ENV" python -m uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload
