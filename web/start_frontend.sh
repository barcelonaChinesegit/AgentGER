#!/bin/bash
# 仅启动前端服务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "启动前端服务..."

cd "$SCRIPT_DIR/frontend"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "前端运行在 http://localhost:3000"
npm run dev

