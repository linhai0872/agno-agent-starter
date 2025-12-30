#!/bin/bash
#
# 开发模式启动脚本
#
# 特性：
# - 热重载（代码变更自动重启）
# - 单 Worker
# - DEBUG 日志级别
# - 调试模式启用
#
# 使用方法:
#   ./scripts/dev.sh
#
# 环境要求:
# - Python 3.10+
# - .env 文件配置好
# - PostgreSQL 运行中

set -e

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查虚拟环境
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Virtual environment not activated"
    echo "Consider running: source venv/bin/activate"
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found"
    echo "Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Please edit .env and configure your API keys"
    fi
fi

# 开发模式环境变量
export DEBUG_MODE=true
export WORKERS=1
export LOG_LEVEL=DEBUG

echo "Starting Agno Agent Service in DEVELOPMENT mode..."
echo "- Hot reload: enabled"
echo "- Workers: 1"
echo "- Debug mode: true"
echo ""

# 启动服务
python -m app.main


