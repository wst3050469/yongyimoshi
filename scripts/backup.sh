#!/bin/bash
# ============================================
# 永颐无机磨石 · 施工管理平台
# 自动备份脚本 (v4.3.2)
# 由 cron 每天凌晨 3:00 执行
# ============================================

APP_DIR="/root/yongyi-terrazzo"
BACKUP_DIR="${APP_DIR}/data/backups"
LOG_FILE="/var/log/yongyi-terrazzo/backup.log"
MAX_BACKUPS=30
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 开始备份..." >> "$LOG_FILE"

# 执行备份
cd "$APP_DIR"
BACKUP_PATH=$(python3 -c "
import sys
sys.path.insert(0, '.')
import os
os.environ['SECRET_KEY'] = 'backup-script-key'
from database import backup_database
result = backup_database()
print(result)
" 2>&1)

if echo "$BACKUP_PATH" | grep -q "backups/"; then
    FILENAME=$(basename "$BACKUP_PATH")
    FILESIZE=$(stat -c%s "$BACKUP_PATH" 2>/dev/null || stat -f%z "$BACKUP_PATH" 2>/dev/null || echo "0")
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 备份成功: $FILENAME ($((FILESIZE/1024))KB)" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 备份失败: $BACKUP_PATH" >> "$LOG_FILE"
    exit 1
fi

# 清理超30天的旧备份
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🧹 清理 ${RETENTION_DAYS}天前的备份..." >> "$LOG_FILE"
find "$BACKUP_DIR" -name "yongyi_backup_*.db" -mtime +${RETENTION_DAYS} -delete 2>/dev/null
BACKUP_COUNT=$(ls "${BACKUP_DIR}"/*.db 2>/dev/null | wc -l)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 当前备份数: ${BACKUP_COUNT}" >> "$LOG_FILE"

# 磁盘空间检查
DISK_USAGE=$(df -h "${APP_DIR}/data" 2>/dev/null | tail -1 | awk '{print $5}')
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 💾 磁盘使用率: ${DISK_USAGE:-unknown}" >> "$LOG_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 备份流程完成" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
