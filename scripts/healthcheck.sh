#!/bin/bash
# 永颐无机磨石 · 智能健康检查
# 使用 /api/health 端点进行深度检查
# 每5分钟由 cron 执行

HEALTH_URL="http://localhost:5000/api/health"
LOG_FILE="/var/log/yongyi-terrazzo/healthcheck.log"
NOW=$(date '+%Y-%m-%d %H:%M:%S')

# 抽取健康检查
RESULT=$(curl -s --connect-timeout 10 --max-time 15 "$HEALTH_URL" 2>/dev/null)

if echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status')=='ok' and d.get('database')=='connected' else 1)" 2>/dev/null; then
    # 健康 - 无需操作
    exit 0
fi

# 异常 - 记录并重启
echo "[$NOW] ⚠️  健康检查失败，尝试重启..." >> "$LOG_FILE"
echo "[$NOW] 响应: $RESULT" >> "$LOG_FILE"

systemctl restart yongyi-terrazzo
sleep 5

# 验证重启效果
RETRY=$(curl -s --connect-timeout 10 --max-time 15 "$HEALTH_URL" 2>/dev/null)
if echo "$RETRY" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status')=='ok' else 1)" 2>/dev/null; then
    echo "[$NOW] ✅ 重启成功" >> "$LOG_FILE"
else
    echo "[$NOW] ❌ 重启失败，响应: $RETRY" >> "$LOG_FILE"
fi
