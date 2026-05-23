#!/bin/bash
# ============================================
# 永颐无机磨石 · 施工管理平台
# 一键部署脚本 (支持Docker和直接运行)
# ============================================
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=${1:-5000}
MODE=${2:-auto}

echo "=============================="
echo " 永颐无机磨石 · 施工管理平台"
echo " 版本: v3.7.0"
echo "=============================="

# 检测Docker
if [ "$MODE" = "docker" ] || ([ "$MODE" = "auto" ] && command -v docker &>/dev/null); then
    echo "🐳 使用 Docker 部署..."
    cd "$APP_DIR"
    docker compose up -d --build
    echo "✅ Docker 部署完成!"
    echo "   地址: http://localhost:$PORT"
    exit 0
fi

# 直接运行模式
echo "🔍 检查环境..."

# Python检查
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then echo "❌ 需要 Python 3.10+"; exit 1; fi

# 依赖检查
if ! $PYTHON -c "import flask" 2>/dev/null; then
    echo "📦 安装依赖..."
    pip3 install flask gunicorn -q
fi

# 端口检查
if lsof -ti:$PORT &>/dev/null 2>&1; then
    echo "⚠️  端口 $PORT 已被占用，正在释放..."
    fuser -k $PORT/tcp 2>/dev/null || true
    sleep 1
fi

# 初始化目录
mkdir -p "${APP_DIR}/data/photos" "${APP_DIR}/data/backups" "${APP_DIR}/logs"

# 数据库优化
echo "🗄️  优化数据库..."
$PYTHON -c "
from database import optimize_database, init_db
init_db()
result = optimize_database()
print(f'   索引已优化: {result[\"indexes_created\"]}个')
"

# 启动
echo "🚀 启动服务 (端口: $PORT)..."
cd "$APP_DIR"
gunicorn -w 2 \
    -b 0.0.0.0:$PORT \
    --daemon \
    --pid "${APP_DIR}/.app.pid" \
    --error-logfile "${APP_DIR}/logs/error.log" \
    --access-logfile "${APP_DIR}/logs/access.log" \
    --timeout 60 \
    app:app

sleep 2

if lsof -ti:$PORT &>/dev/null 2>&1; then
    echo "✅ 服务启动成功！"
    echo "   地址: http://localhost:$PORT"
    echo "   API文档: http://localhost:$PORT/api/docs-page"
    echo "   PID: $(cat ${APP_DIR}/.app.pid 2>/dev/null || lsof -ti:$PORT)"
else
    echo "❌ 启动失败，请查看日志: ${APP_DIR}/logs/error.log"
    exit 1
fi

echo ""
echo "📋 功能面板:"
echo "   📐 材料计算  📦 采购清单  📅 进度计划"
echo "   ✅ 检查清单  📝 施工日志  📸 照片墙"
echo "   📦 库存管理  📊 进度看板  📋 技术参数"
echo ""
echo "🛑 停止: kill \$(cat ${APP_DIR}/.app.pid)"
