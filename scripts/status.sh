#!/bin/bash
# 永颐无机磨石 · 快速状态检查
# 用法: bash scripts/status.sh

echo "╔══════════════════════════════════════╗"
echo "║  永颐无机磨石 · 施工管理平台         ║"
echo "║  v4.4.1 · $(date '+%Y-%m-%d %H:%M')      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 服务状态
echo "📊 服务状态:"
systemctl is-active yongyi-terrazzo >/dev/null 2>&1 && echo "  ✅ Web服务  运行中 (端口5000)" || echo "  ❌ Web服务  未运行"
systemctl is-active nginx >/dev/null 2>&1 && echo "  ✅ Nginx    运行中 (443/80)" || echo "  ❌ Nginx    未运行"
echo ""

# 健康检查
echo "🔍 健康检查:"
HEALTH=$(curl -s --connect-timeout 5 http://localhost:5000/api/health 2>/dev/null)
if echo "$HEALTH" | python3 -c "import sys,json;d=json.load(sys.stdin);sys.exit(0 if d.get('status')=='ok' else 1)" 2>/dev/null; then
    VERSION=$(echo "$HEALTH" | python3 -c "import sys,json;print(json.load(sys.stdin)['version'])")
    ENDPOINTS=$(echo "$HEALTH" | python3 -c "import sys,json;print(json.load(sys.stdin)['endpoints'])")
    echo "  ✅ 应用健康  版本${VERSION} · ${ENDPOINTS}端点"
else
    echo "  ❌ 应用异常"
fi
echo ""

# 备份
echo "💾 备份状态:"
BACKUP_COUNT=$(ls /root/yongyi-terrazzo/data/backups/*.db 2>/dev/null | wc -l)
echo "  📁 ${BACKUP_COUNT}个备份文件"
ls -lt /root/yongyi-terrazzo/data/backups/*.db 2>/dev/null | head -1 | awk '{print "  🕐 最新: " $6, $7, $8}'
echo ""

# 内容排期
echo "📅 内容排期:"
PLAN_FILE=$(ls -t /root/yongyi-terrazzo/docs/content/week-*.md 2>/dev/null | head -1)
if [ -n "$PLAN_FILE" ]; then
    SCRIPTS=$(grep -c "### " "$PLAN_FILE" 2>/dev/null)
    DAYS=$(grep -c "^## " "$PLAN_FILE" 2>/dev/null)
    echo "  📝 ${SCRIPTS}条脚本 · ${DAYS}天排期"
else
    echo "  ⚪ 暂无排期"
fi
echo ""

# 测试
echo "🧪 最近测试:"
cd /root/yongyi-terrazzo 2>/dev/null && python3 -m pytest tests/ -q 2>&1 | tail -1
echo ""

# SEO
echo "🌐 公网页面:"
for p in "" "/public" "/faq" "/cases" "/construction-process" "/knowledge-base" "/guide-budget" "/guide-compare" "/guide-maintenance"; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://ai.jinmojianshe.com/platform${p}" 2>/dev/null)
    [ "$CODE" = "200" ] && echo "  ✅ /platform${p}" || echo "  ⚠️ /platform${p} (${CODE})"
done
echo ""

echo "╔══════════════════════════════════════╗"
echo "║  管理面板: https://ai.jinmojianshe.com/platform/admin ║"
echo "╚══════════════════════════════════════╝"
