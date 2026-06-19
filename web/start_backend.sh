#!/bin/bash
# 仅启动后端服务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "启动后端服务..."

# 创建 uploads 目录
mkdir -p "$PROJECT_ROOT/uploads"

cd "$SCRIPT_DIR/backend"

# 检查依赖
if ! python -c "import fastapi" 2>/dev/null; then
    echo "安装后端依赖..."
    pip install -r requirements.txt
fi

echo "后端运行在 http://localhost:8000"
python app.py

