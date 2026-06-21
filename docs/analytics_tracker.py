#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 效果数据跟踪引擎 v5.6.0
支持手动/自动录入各平台发布后效果数据，生成统计分析"""
import json, os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ANALYTICS_FILE = os.path.join(DATA_DIR, "analytics_data.json")


class AnalyticsTracker:
    """效果数据记录与统计分析"""

    def __init__(self):
        self.records = []
        self._load()

    def _ensure_dir(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def _load(self):
        try:
            if os.path.exists(ANALYTICS_FILE):
                with open(ANALYTICS_FILE, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
        except:
            self.records = []

    def _save(self):
        try:
            self._ensure_dir()
            with open(ANALYTICS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[AnalyticsTracker] Save error: {e}")

    def record_metrics(self, publish_id: str, platform: str,
                       views: int = 0, likes: int = 0, comments: int = 0,
                       shares: int = 0, saves: int = 0, extra: Dict = None) -> Dict:
        """录入/更新一条效果数据"""
        now = datetime.now().isoformat()
        # 查找已有记录并更新
        for r in self.records:
            if r.get("publish_id") == publish_id:
                r.update({
                    "platform": platform,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "saves": saves,
                    "engagement": likes + comments + shares + saves,
                    "engagement_rate": round((likes + comments + shares + saves) / max(views, 1) * 100, 2),
                    "extra": extra or {},
                    "updated_at": now,
                })
                self._save()
                return r

        # 新记录
        record = {
            "publish_id": publish_id,
            "platform": platform,
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
            "engagement": likes + comments + shares + saves,
            "engagement_rate": round((likes + comments + shares + saves) / max(views, 1) * 100, 2),
            "extra": extra or {},
            "created_at": now,
            "updated_at": now,
        }
        self.records.append(record)
        self._save()
        return record

    def get_content_performance(self, publish_id: str) -> Optional[Dict]:
        """获取单条内容效果数据"""
        for r in self.records:
            if r.get("publish_id") == publish_id:
                return r
        return None

    def get_all_records(self, platform: str = "", days: int = 30) -> List[Dict]:
        """获取效果数据列表"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        result = []
        for r in reversed(self.records):
            created = r.get("created_at", "")
            if created and created < cutoff:
                continue
            if platform and r.get("platform") != platform:
                continue
            result.append(r)
        return result

    def get_platform_stats(self, platform: str = "") -> Dict:
        """按平台统计"""
        records = self.records
        if platform:
            records = [r for r in records if r.get("platform") == platform]

        if not records:
            return {"platform": platform or "全部", "count": 0}

        total_views = sum(r.get("views", 0) for r in records)
        total_engagement = sum(r.get("engagement", 0) for r in records)
        return {
            "platform": platform or "全部",
            "count": len(records),
            "total_views": total_views,
            "total_likes": sum(r.get("likes", 0) for r in records),
            "total_comments": sum(r.get("comments", 0) for r in records),
            "total_shares": sum(r.get("shares", 0) for r in records),
            "total_saves": sum(r.get("saves", 0) for r in records),
            "total_engagement": total_engagement,
            "avg_views": round(total_views / len(records), 0),
            "avg_engagement_rate": round(
                sum(r.get("engagement_rate", 0) for r in records) / len(records), 2
            ),
        }

    def get_dashboard(self) -> Dict:
        """综合效果数据看板"""
        all_stats = self.get_platform_stats()
        # 各平台统计
        platforms = {}
        all_platforms = set(r.get("platform", "未知") for r in self.records)
        for p in all_platforms:
            platforms[p] = self.get_platform_stats(p)

        # Top 内容
        top_by_views = sorted(self.records, key=lambda x: x.get("views", 0), reverse=True)[:5]
        top_by_engagement = sorted(self.records, key=lambda x: x.get("engagement", 0), reverse=True)[:5]

        # 近7天趋势（简化）
        trend = []
        for i in range(6, -1, -1):
            day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_records = [r for r in self.records if r.get("created_at", "").startswith(day)]
            trend.append({
                "date": day,
                "views": sum(r.get("views", 0) for r in day_records),
                "engagement": sum(r.get("engagement", 0) for r in day_records),
                "count": len(day_records),
            })

        return {
            "overview": all_stats,
            "by_platform": platforms,
            "top_by_views": top_by_views,
            "top_by_engagement": top_by_engagement,
            "trend_7d": trend,
            "generated_at": datetime.now().isoformat(),
        }
