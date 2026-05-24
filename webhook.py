"""
永颐无机磨石 - Webhook 通知模块
支持企业微信机器人 & 钉钉机器人
"""

import json
import logging
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ============================================================
# 企业微信机器人 Webhook
# ============================================================
def send_wechat_webhook(webhook_url: str, title: str, message: str = "") -> bool:
    """
    发送消息到企业微信机器人
    
    Args:
        webhook_url: 企业微信机器人 webhook URL
        title: 消息标题
        message: 消息内容（支持Markdown）
    
    Returns:
        bool: 是否发送成功
    """
    if not webhook_url or not webhook_url.startswith("https://qyapi.weixin.qq.com"):
        return False

    # 构建 Markdown 消息
    content = f"## {title}\\n"
    if message:
        # 企业微信markdown支持: 换行用\\n，加粗用** **
        content += message.replace("\\n", "\\n").replace("\\n\\n", "\\n\\n")
    
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
    
    return _post_webhook(webhook_url, payload)


# ============================================================
# 钉钉机器人 Webhook
# ============================================================
def send_dingtalk_webhook(webhook_url: str, title: str, message: str = "") -> bool:
    """
    发送消息到钉钉机器人
    
    Args:
        webhook_url: 钉钉机器人 webhook URL
        title: 消息标题
        message: 消息内容（支持Markdown）
    
    Returns:
        bool: 是否发送成功
    """
    if not webhook_url or not webhook_url.startswith("https://oapi.dingtalk.com"):
        return False

    content = f"## {title}\\n\\n"
    if message:
        content += message
    
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title[:20],
            "text": content
        }
    }
    
    return _post_webhook(webhook_url, payload)


# ============================================================
# 通用 Webhook 发送
# ============================================================
def _post_webhook(url: str, payload: dict) -> bool:
    """发送 HTTP POST 请求到 webhook"""
    try:
        data = json.dumps(payload).encode('utf-8')
        req = Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Yongyi-Terrazzo/4.3.3'
            },
            method='POST'
        )
        resp = urlopen(req, timeout=10)
        result = json.loads(resp.read().decode('utf-8'))
        
        # 企业微信返回: {"errcode":0,"errmsg":"ok"}
        # 钉钉返回: {"errcode":0,"errmsg":"ok"}
        if result.get('errcode') == 0:
            logger.info(f"Webhook 发送成功: {url[:40]}...")
            return True
        else:
            logger.warning(f"Webhook 返回错误: {result}")
            return False
            
    except URLError as e:
        logger.error(f"Webhook 网络错误: {e}")
        return False
    except Exception as e:
        logger.error(f"Webhook 发送异常: {e}")
        return False


def send_notification(title: str, message: str = "", 
                      notif_type: str = "general",
                      project_name: str = "") -> dict:
    """
    发送通知到所有已配置的 webhook 渠道
    
    自动从 config 读取 webhook 配置，同时推送到企业微信和钉钉
    
    Returns:
        dict: {"wechat": bool, "dingtalk": bool}
    """
    from config import get_config
    
    result = {"wechat": False, "dingtalk": False}
    
    # 格式化消息
    if project_name:
        full_message = f"📌 **项目**: {project_name}\\n\\n{message}"
    else:
        full_message = message
    
    # 添加通知类型标签
    type_tags = {
        "curing_reminder": "🧊",
        "quality_test": "🧪",
        "safety": "⚠️",
        "daily_log": "📝",
        "phase_update": "🔄",
        "inventory": "📦",
        "manual": "📢",
        "general": "📋",
    }
    tag = type_tags.get(notif_type, "📋")
    full_title = f"{tag} {title}"
    
    # 推送企业微信
    wechat_url = get_config("webhook", "wechat_url")
    if wechat_url:
        result["wechat"] = send_wechat_webhook(wechat_url, full_title, full_message)
    
    # 推送钉钉
    dingtalk_url = get_config("webhook", "dingtalk_url")
    if dingtalk_url:
        result["dingtalk"] = send_dingtalk_webhook(dingtalk_url, full_title, full_message)
    
    return result


# ============================================================
# 通知模板
# ============================================================
def format_phase_update(project_name: str, phase_name: str, 
                        new_status: str, old_status: str = "") -> tuple:
    """格式化工序更新通知"""
    status_map = {
        "not_started": "⭕ 未开始",
        "in_progress": "🔵 进行中",
        "completed": "✅ 已完成"
    }
    status_text = status_map.get(new_status, new_status)
    
    title = f"工序状态更新: {phase_name}"
    message = (
        f"**项目**: {project_name}\\n"
        f"**工序**: {phase_name}\\n"
        f"**新状态**: {status_text}\\n"
    )
    if old_status:
        old_text = status_map.get(old_status, old_status)
        message += f"**旧状态**: {old_text}\\n"
    
    return title, message


def format_daily_log(project_name: str, content: str, author: str) -> tuple:
    """格式化施工日志通知"""
    title = f"新增施工日志"
    message = (
        f"**项目**: {project_name}\\n"
        f"**提交人**: {author}\\n"
        f"**内容**: {content[:200]}\\n"
    )
    return title, message


def format_safety_issue(project_name: str, issue: str, level: str) -> tuple:
    """格式化安全问题通知"""
    level_tag = {"low": "🟢", "medium": "🟡", "high": "🔴"}
    tag = level_tag.get(level, "🟡")
    title = f"{tag} 安全问题: {issue[:30]}"
    message = (
        f"**项目**: {project_name}\\n"
        f"**问题**: {issue}\\n"
        f"**严重程度**: {level}\\n"
    )
    return title, message


def format_quality_test(project_name: str, test_name: str, 
                        result: str, passed: bool) -> tuple:
    """格式化质量检测通知"""
    status = "✅ 通过" if passed else "❌ 未通过"
    title = f"质量检测: {test_name}"
    message = (
        f"**项目**: {project_name}\\n"
        f"**检测项目**: {test_name}\\n"
        f"**结果**: {status}\\n"
        f"**详情**: {result}\\n"
    )
    return title, message
