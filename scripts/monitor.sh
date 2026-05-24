#!/bin/bash
# 永颐无机磨石 · 施工管理平台 - 系统监控
# 每30分钟执行一次

LOG_FILE="/var/log/yongyi-terrazzo/monitor.log"
NOW=$(date '+%Y-%m-%d %H:%M:%S')

# 1. 检查服务状态
if ! systemctl is-active --quiet yongyi-terrazzo; then
    echo "[$NOW] ❌ 服务异常，正在重启..." >> "$LOG_FILE"
    systemctl restart yongyi-terrazzo
    sleep 2
    if systemctl is-active --quiet yongyi-terrazzo; then
        echo "[$NOW] ✅ 重启成功" >> "$LOG_FILE"
    else
        echo "[$NOW] ❌ 重启失败" >> "$LOG_FILE"
    fi
fi

# 2. 检查磁盘 (仅当超过80%时记录)
DISK_PCT=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_PCT" -gt 80 ]; then
    echo "[$NOW] ⚠️  磁盘使用率: ${DISK_PCT}%" >> "$LOG_FILE"
fi

# 3. 检查内存
MEM_PCT=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$MEM_PCT" -gt 90 ]; then
    echo "[$NOW] ⚠️  内存使用率: ${MEM_PCT}%" >> "$LOG_FILE"
fi

# 4. 检查数据库完整性（每天一次）
HOUR=$(date +%H)
if [ "$HOUR" = "04" ]; then
    cd /root/yongyi-terrazzo
    python3 -c "
import sys, os
os.environ['SECRET_KEY'] = 'monitor'
sys.path.insert(0, '.')
from database import check_database_integrity
result = check_database_integrity()
if result.get('ok'):
    print('[$NOW] ✅ 数据库完整性检查通过')
else:
    print('[$NOW] ❌ 数据库异常: ' + str(result))
" >> "$LOG_FILE" 2>&1
fi
