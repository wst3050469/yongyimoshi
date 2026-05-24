"""
永颐无机磨石 - 系统配置模块
管理应用设置、系统参数和运行时配置
"""

import json
import os
from typing import Any, Dict, Optional
from datetime import datetime

CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'data')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'system_config.json')

# 默认配置
DEFAULT_CONFIG = {
    "system": {
        "name": "永颐无机磨石 · 施工管理平台",
        "version": "4.5.0",
        "company": "浙江永颐装饰工程有限公司",
        "maintainer": "",
        "language": "zh-CN",
    },
    "project": {
        "default_base_thickness": 50,
        "default_surface_thickness": 15,
        "max_projects": 100,
    },
    "display": {
        "theme": "light",
        "items_per_page": 20,
        "chart_style": "bar",
    },
    "notifications": {
        "enable_reminders": True,
        "curing_reminder_days": [7, 3, 1],
        "test_reminder_days": [28, 14, 7],
    },
    "backup": {
        "auto_backup": True,
        "backup_interval_days": 7,
        "max_backups": 10,
    },
    "webhook": {
        "wechat_url": "",
        "dingtalk_url": "",
        "enabled": True,
        "notify_on": ["phase_update", "safety", "quality_test", "daily_log", "curing_reminder"],
    },
    "seo": {
        "baidu_tongji_id": "",
        "baidu_push_token": "Wv8PCYReXqOVNXYg",
        "baidu_verify": "codeva-lVx2jy1w82",
        "bing_verify": "",
        "company_telephone": "13357048951",
        "company_email": "info@jinmojianshe.com",
        "company_address": "浙江省杭州市",
        "company_area_served": "全国",
        "company_founding_date": "2018",
    },
}


def _ensure_config_dir():
    """确保配置目录存在"""
    os.makedirs(CONFIG_DIR, exist_ok=True)


def load_config() -> Dict:
    """加载系统配置（JSON文件 + 环境变量覆盖）"""
    _ensure_config_dir()
    config = DEFAULT_CONFIG.copy()
    
    # 从JSON文件加载
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                for section, values in user_config.items():
                    if section in config and isinstance(config[section], dict):
                        config[section].update(values)
                    else:
                        config[section] = values
        except (json.JSONDecodeError, IOError):
            pass
    
    # 环境变量覆盖（用于 Docker 部署）
    env_overrides = {
        ("webhook", "wechat_url"): "WECHAT_WEBHOOK_URL",
        ("webhook", "dingtalk_url"): "DINGTALK_WEBHOOK_URL",
        ("seo", "baidu_tongji_id"): "BAIDU_TONGJI_ID",
        ("seo", "baidu_push_token"): "BAIDU_PUSH_TOKEN",
    }
    for (section, key), env_name in env_overrides.items():
        env_value = os.environ.get(env_name)
        if env_value:
            if section not in config:
                config[section] = {}
            config[section][key] = env_value
    
    return config


def save_config(config: Dict) -> bool:
    """保存系统配置"""
    _ensure_config_dir()
    try:
        # 保留默认配置中所有section
        merged = DEFAULT_CONFIG.copy()
        for section, values in config.items():
            if section in merged and isinstance(merged[section], dict):
                merged[section].update(values)
            else:
                merged[section] = values
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


def get_config(section: str = "", key: str = "") -> Any:
    """获取配置项"""
    config = load_config()
    if section:
        if key:
            return config.get(section, {}).get(key, None)
        return config.get(section, {})
    return config


def update_config(section: str, updates: Dict) -> bool:
    """更新配置项"""
    config = load_config()
    if section not in config:
        config[section] = {}
    config[section].update(updates)
    return save_config(config)


# ============================================================
# 系统运行状态
# ============================================================

def get_system_status() -> Dict:
    """获取系统运行状态"""
    import time
    from database import get_db_stats, check_database_integrity, get_database_stats_detailed

    db_stats = get_db_stats()
    db_detail = get_database_stats_detailed()
    integrity = check_database_integrity()

    # 系统启动时间 (如果存在pid文件)
    pid_file = os.path.join(os.path.dirname(__file__), '.app.pid')
    uptime = "未知"
    if os.path.exists(pid_file):
        try:
            mtime = os.path.getmtime(pid_file)
            uptime_seconds = time.time() - mtime
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            uptime = f"{days}天{hours}小时"
        except:
            pass

    config = load_config()

    return {
        "version": config["system"]["version"],
        "uptime": uptime,
        "db_size_mb": db_stats.get("db_size_mb", 0),
        "db_tables": {k: v for k, v in db_stats.items() if k != "db_size_bytes" and k != "db_size_mb"},
        "total_records": sum(v for k, v in db_stats.items() 
                           if k in ["projects","daily_logs","quality_tests",
                                   "checklist_state","material_records","photos"]),
        "config_sections": list(config.keys()),
        "integrity": integrity.get("status", "unknown"),
        "db_tables_count": db_detail.get("table_count", 0),
        "db_indexes_count": db_detail.get("index_count", 0),
    }


def cleanup_old_data(days: int = 90) -> Dict:
    """
    清理旧数据

    参数:
        days: 保留天数，超过此天数的日志将被删除

    返回:
        清理统计
     """
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()

    stats = {}
    # 清理施工日志
    cursor.execute("""
        DELETE FROM daily_logs 
        WHERE log_date < date('now', '-' || ? || ' days')
    """, (days,))
    stats["deleted_logs"] = cursor.rowcount

    # 清理旧照片记录（保留文件）
    cursor.execute("""
        DELETE FROM photos 
        WHERE created_at < datetime('now', '-' || ? || ' days')
    """, (days,))
    stats["deleted_photos"] = cursor.rowcount

    # VACUUM
    cursor.execute("VACUUM")

    conn.commit()
    conn.close()
    return stats
