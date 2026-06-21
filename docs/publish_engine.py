#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 发布管理引擎 v5.6.0
支持提交审核 → 人工审批 → 标记发布 完整工作流"""
import json, os, uuid
from datetime import datetime
from typing import List, Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PUBLISH_FILE = os.path.join(DATA_DIR, "publish_queue.json")

# 状态流转: pending → approved/rejected → published
VALID_STATUSES = ["pending", "approved", "rejected", "published"]

PLATFORM_LABELS = {
    "douyin": "抖音",
    "xhs": "小红书",
    "wechat_article": "公众号",
    "baijiahao": "百家号",
    "zhihu": "知乎",
    "weibo": "微博",
}


class PublishEngine:
    """发布管理 + 审核工作流"""

    def __init__(self):
        self.queue = []
        self._load()

    def _ensure_dir(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def _load(self):
        try:
            if os.path.exists(PUBLISH_FILE):
                with open(PUBLISH_FILE, 'r', encoding='utf-8') as f:
                    self.queue = json.load(f)
        except:
            self.queue = []

    def _save(self):
        try:
            self._ensure_dir()
            with open(PUBLISH_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.queue, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[PublishEngine] Save error: {e}")

    def submit_for_review(self, content: str, platform: str, keyword: str = "",
                          title: str = "", note: str = "") -> Dict:
        """提交内容到审核队列"""
        pid = str(uuid.uuid4())[:8]
        record = {
            "id": pid,
            "platform": platform,
            "platform_label": PLATFORM_LABELS.get(platform, platform),
            "title": title or keyword or f"{platform}内容",
            "keyword": keyword,
            "content": content,
            "note": note,
            "status": "pending",
            "submitted_at": datetime.now().isoformat(),
            "reviewed_at": None,
            "published_at": None,
            "review_comment": None,
            "publish_url": None,
        }
        self.queue.append(record)
        self._save()
        return record

    def approve(self, publish_id: str, comment: str = "") -> Dict:
        """审核通过"""
        for item in self.queue:
            if item["id"] == publish_id:
                if item["status"] != "pending":
                    return {"success": False, "error": f"当前状态为{item['status']}，无法审核"}
                item["status"] = "approved"
                item["reviewed_at"] = datetime.now().isoformat()
                item["review_comment"] = comment or "审核通过"
                self._save()
                return {"success": True, "data": item}
        return {"success": False, "error": "未找到该发布记录"}

    def reject(self, publish_id: str, reason: str = "") -> Dict:
        """驳回（带原因）"""
        for item in self.queue:
            if item["id"] == publish_id:
                if item["status"] != "pending":
                    return {"success": False, "error": f"当前状态为{item['status']}，无法驳回"}
                item["status"] = "rejected"
                item["reviewed_at"] = datetime.now().isoformat()
                item["review_comment"] = reason or "已驳回"
                self._save()
                return {"success": True, "data": item}
        return {"success": False, "error": "未找到该发布记录"}

    def publish(self, publish_id: str, url: str = "") -> Dict:
        """标记已发布（审核通过后执行）"""
        for item in self.queue:
            if item["id"] == publish_id:
                if item["status"] != "approved":
                    return {"success": False, "error": "只有已通过的内容才能发布"}
                item["status"] = "published"
                item["published_at"] = datetime.now().isoformat()
                item["publish_url"] = url or f"https://ai.jinmojianshe.com/marketing/published/{publish_id}"
                self._save()
                return {"success": True, "data": item}
        return {"success": False, "error": "未找到该发布记录"}

    def get_queue(self, status: str = "") -> List[Dict]:
        """获取审核队列
        status: 空=全部, pending/approved/rejected/published"""
        if status and status in VALID_STATUSES:
            return [item for item in reversed(self.queue) if item["status"] == status]
        return list(reversed(self.queue))

    def get_stats(self) -> Dict:
        """发布统计"""
        counts = {s: 0 for s in VALID_STATUSES}
        for item in self.queue:
            if item["status"] in counts:
                counts[item["status"]] += 1

        platform_counts = {}
        for item in self.queue:
            p = item.get("platform_label", item["platform"])
            platform_counts[p] = platform_counts.get(p, 0) + 1

        return {
            "total": len(self.queue),
            "by_status": counts,
            "by_platform": platform_counts,
        }

    def get_item(self, publish_id: str) -> Optional[Dict]:
        """获取单条发布记录"""
        for item in self.queue:
            if item["id"] == publish_id:
                return item
        return None

    def batch_submit(self, contents: List[Dict]) -> List[Dict]:
        """批量提交审核"""
        results = []
        for c in contents:
            result = self.submit_for_review(
                content=c.get("content", ""),
                platform=c.get("platform", "wechat_article"),
                keyword=c.get("keyword", ""),
                title=c.get("title", ""),
                note=c.get("note", "")
            )
            results.append(result)
        return results
