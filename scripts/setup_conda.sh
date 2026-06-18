#!/usr/bin/env bash
# 创建或更新 NewHuman conda 环境
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_NAME="${NEWHUMAN_CONDA_ENV:-newhuman}"

if ! command -v conda >/dev/null 2>&1; then
  echo "未找到 conda，请先安装 Miniconda / Anaconda / Miniforge" >&2
  exit 1
fi

cd "$REPO_ROOT"
if conda env list | grep -qE "^${ENV_NAME}[[:space:]]"; then
  echo "[conda] 更新环境: $ENV_NAME"
  conda env update -f environment.yml --prune -y
else
  echo "[conda] 创建环境: $ENV_NAME"
  conda env create -f environment.yml -y
fi

echo ""
echo "激活: conda activate $ENV_NAME"
