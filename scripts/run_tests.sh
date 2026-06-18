#!/usr/bin/env bash
# 运行 MVP 验收测试
# 前置: ./scripts/setup_conda.sh
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONDA_ENV="${NEWHUMAN_CONDA_ENV:-newhuman}"
MILESTONE="${1:-ALL}"
SMOKE_ONLY="${SMOKE_ONLY:-0}"
export TEST_BASE_URL="${TEST_BASE_URL:-http://127.0.0.1:8000}"

cd "$REPO_ROOT"
ARGS=(-m pytest -v --tb=short -ra)
if [[ "$SMOKE_ONLY" == "1" ]]; then
  ARGS+=(-m smoke)
elif [[ "$MILESTONE" != "ALL" ]]; then
  ARGS+=(-m "milestone_${MILESTONE,,} or smoke")
fi

conda run --no-capture-output -n "$CONDA_ENV" python "${ARGS[@]}" tests/
conda run --no-capture-output -n "$CONDA_ENV" python "$REPO_ROOT/scripts/check_milestone.py" --from-pytest
