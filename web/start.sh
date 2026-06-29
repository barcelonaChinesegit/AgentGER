#!/bin/bash
# AgentGER Web demo launcher. Starts both backend API and Vite frontend.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

PYTHON_BIN="${PYTHON_BIN:-python3}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PORT="8000"

# Default to mock so Mac local runs never try to load or download the large model.
AGENTGER_INFERENCE_MODE="${AGENTGER_INFERENCE_MODE:-mock}"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "正在停止 Web 服务..."
    if [ -n "${FRONTEND_PID:-}" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    if [ -n "${BACKEND_PID:-}" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
}
trap cleanup INT TERM EXIT

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "缺少命令: $1"
        exit 1
    fi
}

port_in_use() {
    lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

wait_for_url() {
    local url="$1"
    local name="$2"
    local i
    for i in {1..40}; do
        if curl -fsS "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 0.5
    done
    echo "$name 启动超时: $url"
    return 1
}

echo "=========================================="
echo "  AgentGER Web Demo"
echo "=========================================="
echo "项目目录: $PROJECT_ROOT"
echo "推理模式: $AGENTGER_INFERENCE_MODE"

require_command "$PYTHON_BIN"
require_command npm
require_command curl
require_command lsof

if port_in_use "$BACKEND_PORT"; then
    echo "端口 $BACKEND_PORT 已被占用，请先停止已有后端服务。"
    lsof -nP -iTCP:"$BACKEND_PORT" -sTCP:LISTEN
    exit 1
fi

if port_in_use "$FRONTEND_PORT"; then
    echo "端口 $FRONTEND_PORT 已被占用，请先停止已有前端服务。"
    lsof -nP -iTCP:"$FRONTEND_PORT" -sTCP:LISTEN
    exit 1
fi

mkdir -p "$PROJECT_ROOT/uploads"

echo ""
echo "[1/4] 检查后端依赖..."
cd "$BACKEND_DIR"
if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import fastapi
import uvicorn
import multipart
PY
then
    "$PYTHON_BIN" -m pip install -r requirements.txt
fi

echo "[2/4] 启动后端 API: http://127.0.0.1:$BACKEND_PORT"
AGENTGER_INFERENCE_MODE="$AGENTGER_INFERENCE_MODE" "$PYTHON_BIN" app.py &
BACKEND_PID=$!
wait_for_url "http://127.0.0.1:$BACKEND_PORT/api/history?limit=1&offset=0" "后端"

echo "[3/4] 检查前端依赖..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    npm install
fi

echo "[4/4] 启动前端页面: http://$FRONTEND_HOST:$FRONTEND_PORT"
npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" --strictPort &
FRONTEND_PID=$!
wait_for_url "http://$FRONTEND_HOST:$FRONTEND_PORT/" "前端"

echo ""
echo "=========================================="
echo "  服务已启动"
echo "  前端: http://$FRONTEND_HOST:$FRONTEND_PORT"
echo "  后端: http://127.0.0.1:$BACKEND_PORT"
echo "=========================================="
echo "按 Ctrl+C 停止所有服务"

wait "$BACKEND_PID" "$FRONTEND_PID"
