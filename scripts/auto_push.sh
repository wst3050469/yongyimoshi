#!/bin/bash
# ============================================
# 永颐无机磨石 · 百度站长自动推送
# 从config.py读取Token（不再硬编码）
# 由cron每天8:00执行
# ============================================

SITE="https://ai.jinmojianshe.com"
LOG_FILE="/var/log/yongyi-terrazzo/push.log"
APP_DIR="/root/yongyi-terrazzo"

echo "[$(date)] 🔄 开始推送..." >> "$LOG_FILE"

# 从config获取Token（使用Python读取）
TOKEN=$(cd "$APP_DIR" && python3 -c "
import sys, os
os.environ['SECRET_KEY'] = 'push-script'
sys.path.insert(0, '.')
from config import get_config
token = get_config('seo', 'baidu_push_token') or ''
print(token)
" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "[$(date)] ❌ 未配置百度推送Token（config.py seo.baidu_push_token）" >> "$LOG_FILE"
    exit 1
fi

BAIDU_API="http://data.zz.baidu.com/urls?site=${SITE}&token=${TOKEN}"

# 获取sitemap
echo "[$(date)] 📡 获取Sitemap..." >> "$LOG_FILE"
SITEMAP_CONTENT=$(curl -s -k "${SITE}/platform/sitemap.xml" 2>/dev/null)

if [ -z "$SITEMAP_CONTENT" ]; then
    echo "[$(date)] ❌ 无法获取Sitemap" >> "$LOG_FILE"
    exit 1
fi

# 提取URL
URLS=$(echo "$SITEMAP_CONTENT" | grep -oP '(?<=<loc>).*?(?=</loc>)')
COUNT=$(echo "$URLS" | grep -c . 2>/dev/null || echo "0")
echo "[$(date)] 📊 发现 $COUNT 个URL" >> "$LOG_FILE"

if [ "$COUNT" -eq 0 ]; then
    echo "[$(date)] ⚠️ 没有URL需要推送" >> "$LOG_FILE"
    exit 0
fi

# 推送到百度
echo "[$(date)] 📤 推送中..." >> "$LOG_FILE"
PUSH_RESULT=$(echo "$URLS" | curl -s -H 'Content-Type:text/plain' --data-binary @- "$BAIDU_API" 2>/dev/null)
echo "[$(date)] ✅ 推送完成: $PUSH_RESULT" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
