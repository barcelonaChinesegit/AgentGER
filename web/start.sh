#!/bin/bash
# 图表总结评估系统 - 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  图表总结评估系统 Web 服务"
echo "=========================================="

# 创建 uploads 目录
mkdir -p "$PROJECT_ROOT/uploads"

# 启动后端
echo ""
echo "[1/2] 启动后端服务 (端口 8000)..."
cd "$SCRIPT_DIR/backend"

# 检查依赖
if ! python -c "import fastapi" 2>/dev/null; then
    echo "安装后端依赖..."
    pip install -r requirements.txt
fi

# 后台启动后端
python app.py &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 2

# 启动前端
echo ""
echo "[2/2] 启动前端服务 (端口 3000)..."
cd "$SCRIPT_DIR/frontend"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动前端
npm run dev &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"

echo ""
echo "=========================================="
echo "  服务已启动！"
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "=========================================="
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获 SIGINT 信号
trap "echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT

# 等待
wait

