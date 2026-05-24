#!/bin/bash
# ============================================
# 永颐无机磨石 · 施工管理平台
# 一键部署脚本 (v4.3.1)
# ============================================
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
ACTION=${1:-status}

echo "=============================="
echo " 永颐无机磨石 · 施工管理平台"
echo " 版本: v4.4.1"
echo "=============================="

case "$ACTION" in
  start)
    echo "🚀 启动服务..."
    systemctl start yongyi-terrazzo
    systemctl status yongyi-terrazzo --no-pager
    ;;
  stop)
    echo "🛑 停止服务..."
    systemctl stop yongyi-terrazzo
    echo "✅ 已停止"
    ;;
  restart)
    echo "🔄 重启服务..."
    systemctl restart yongyi-terrazzo
    systemctl status yongyi-terrazzo --no-pager
    ;;
  reload)
    echo "🔄 热重载（无中断）..."
    systemctl reload yongyi-terrazzo || kill -HUP $(cat /run/yongyi-terrazzo.pid 2>/dev/null)
    echo "✅ 已重载"
    ;;
  status)
    echo "📊 服务状态:"
    systemctl status yongyi-terrazzo --no-pager 2>/dev/null || echo "❌ 服务未安装"
    echo ""
    echo "📡 端口监听:"
    ss -tlnp | grep -E "5000|80|443" || echo "未监听"
    echo ""
    echo "🌐 公网访问测试:"
    curl -s -o /dev/null -w "   https://ai.jinmojianshe.com/platform/ → %{http_code}\n" https://ai.jinmojianshe.com/platform/ 2>/dev/null || echo "   ❌ 无法访问"
    ;;
  logs)
    echo "📋 最近50行日志:"
    tail -50 /var/log/yongyi-terrazzo/error.log
    ;;
  install)
    echo "🔧 安装系统服务..."
    cp "$APP_DIR/.env.example" "$APP_DIR/.env.production" 2>/dev/null || true
    systemctl daemon-reload
    systemctl enable yongyi-terrazzo
    systemctl start yongyi-terrazzo
    echo "✅ 安装完成！"
    ;;
  git-push)
    echo "📤 推送到 GitHub..."
    if git remote -v | grep -q origin; then
      git push origin main
      echo "✅ 推送成功！"
    else
      echo "❌ 未配置 Git 远程仓库"
      echo "   请先执行: git remote add origin <仓库地址>"
    fi
    ;;
  content-plan)
    echo "📅 生成下周内容排期..."
    python3 scripts/content_planner.py
    echo ""
    echo "💡 提示: 管理面板也可以一键生成"
    ;;
  health)
    echo "🔍 深度健康检查..."
    curl -s http://localhost:5000/api/health | python3 -m json.tool
    ;;
  check)
    bash scripts/status.sh
    ;;
  *)
    echo "用法: $0 {start|stop|restart|reload|status|logs|install|git-push}"
    echo ""
    echo "示例:"
    echo "  $0 status    # 查看服务状态"
    echo "  $0 restart   # 重启服务"
    echo "  $0 logs      # 查看错误日志"
    echo "  $0 check     # 全面状态检查"
    echo "  $0 content-plan # 生成排期"
    echo "  $0 health    # 健康检查"
    exit 1
    ;;
esac
