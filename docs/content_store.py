#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内容持久化存储模块 - v5.2.0"""
import json, os, uuid
from datetime import datetime
from typing import List, Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONTENT_FILE = os.path.join(DATA_DIR, "content_history.json")

class ContentStore:
    """保存和管理AI生成的营销内容"""
    
    def __init__(self):
        self._contents = []
        self._load()
    
    def _ensure_dir(self):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def _load(self):
        try:
            if os.path.exists(CONTENT_FILE):
                with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
                    self._contents = json.load(f)
        except Exception as e:
            print(f"[ContentStore] Load error: {e}")
            self._contents = []
    
    def _save(self):
        try:
            self._ensure_dir()
            with open(CONTENT_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._contents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ContentStore] Save error: {e}")
    
    def save(self, content_type: str, keyword: str, group: str, content: str) -> Dict:
        """保存一条生成的内容"""
        record = {
            "id": str(uuid.uuid4())[:8],
            "type": content_type,
            "keyword": keyword,
            "group": group,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        self._contents.append(record)
        self._save()
        return record
    
    def get_all(self) -> List[Dict]:
        """获取所有内容历史"""
        return list(reversed(self._contents))  # 最新在前
    
    def get_by_type(self, content_type: str) -> List[Dict]:
        """按类型筛选"""
        return [c for c in reversed(self._contents) if c.get("type") == content_type]
    
    def delete(self, content_id: str) -> bool:
        """删除指定ID的内容"""
        before = len(self._contents)
        self._contents = [c for c in self._contents if c.get("id") != content_id]
        if len(self._contents) < before:
            self._save()
            return True
        return False
    
    def get_stats(self) -> Dict:
        """获取内容统计"""
        counts = {"video_script": 0, "article": 0, "xhs_note": 0}
        for c in self._contents:
            t = c.get("type", "")
            if t in counts:
                counts[t] += 1
        return {
            "total": len(self._contents),
            "counts": counts,
            "daily": sum(1 for c in self._contents 
                        if c.get("created_at", "").startswith(datetime.now().strftime("%Y-%m-%d")))
        }
