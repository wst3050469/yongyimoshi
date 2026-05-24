#!/bin/bash
# 永颐无机磨石 · 施工管理平台 - 健康检查脚本
# 由 cron 每5分钟执行一次

HEALTH_URL="https://ai.jinmojianshe.com/platform/"
LOG_FILE="/var/log/yongyi-terrazzo/healthcheck.log"

# 检查服务是否响应
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 15 "$HEALTH_URL" 2>/dev/null)

if [ "$HTTP_CODE" != "200" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  服务异常 (HTTP $HTTP_CODE)，尝试重启..." >> "$LOG_FILE"
    systemctl restart yongyi-terrazzo
    sleep 3
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 15 "$HEALTH_URL" 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 重启成功" >> "$LOG_FILE"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 重启失败，HTTP=$HTTP_CODE" >> "$LOG_FILE"
    fi
fi
