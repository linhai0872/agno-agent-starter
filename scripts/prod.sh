#!/bin/bash
#
# 生产模式启动脚本
#
# 特性：
# - 多 Worker（根据 CPU 核心数或 WORKERS 环境变量）
# - 无热重载
# - WARNING 日志级别
# - 调试模式禁用
#
# 使用方法:
#   ./scripts/prod.sh
#
# 环境变量:
#   WORKERS - Worker 数量（默认 4）
#   API_PORT - API 端口（默认 7777）
#   API_HOST - API 主机（默认 0.0.0.0）

set -e

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo "Please create .env from .env.example and configure API keys"
    exit 1
fi

# 检查必需的环境变量
source .env 2>/dev/null || true

if [ -z "$OPENROUTER_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    echo "Warning: No API key configured"
    echo "Please set at least one of: OPENROUTER_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY"
fi

if [ -z "$DATABASE_URL" ]; then
    echo "Warning: DATABASE_URL not set, using default"
fi

# 生产模式环境变量
export DEBUG_MODE=false
export WORKERS=${WORKERS:-4}
export LOG_LEVEL=WARNING

echo "Starting Agno Agent Service in PRODUCTION mode..."
echo "- Hot reload: disabled"
echo "- Workers: $WORKERS"
echo "- Debug mode: false"
echo ""

# 启动服务
python -m app.main


