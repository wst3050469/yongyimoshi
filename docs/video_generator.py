#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 AI视频生成模块 - 集成豆包Seedance API v2"""
import requests, json, time, os, threading
from typing import Optional, Dict, List
from datetime import datetime

API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
API_KEY = os.environ.get("DOUBAO_API_KEY", "3c15d74c-103b-44eb-8d47-b979fc7305cd")
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "video_tasks.json")

class VideoGenerator:
    """豆包Seedance视频生成（带持久化存储）"""
    
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        self.tasks = {}
        self._load_tasks()
        self._start_bg_poller()
    
    # ========== 持久化 ==========
    
    def _data_path(self):
        return os.path.abspath(DATA_FILE)
    
    def _ensure_data_dir(self):
        d = os.path.dirname(self._data_path())
        os.makedirs(d, exist_ok=True)
    
    def _save_tasks(self):
        try:
            self._ensure_data_dir()
            with open(self._data_path(), 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[VideoGenerator] Save error: {e}")
    
    def _load_tasks(self):
        try:
            if os.path.exists(self._data_path()):
                with open(self._data_path(), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = data
                print(f"[VideoGenerator] Loaded {len(self.tasks)} tasks from {self._data_path()}")
        except Exception as e:
            print(f"[VideoGenerator] Load error: {e}")
    
    # ========== 后台轮询 ==========
    
    def _start_bg_poller(self):
        """启动后台线程，自动轮询运行中的任务"""
        def poll_loop():
            while True:
                try:
                    for tid, task in list(self.tasks.items()):
                        if task.get("status") in ("running", "pending"):
                            self.query_task(tid, save=False)
                    self._save_tasks()
                except Exception as e:
                    print(f"[VideoGenerator] Poll error: {e}")
                time.sleep(15)  # 每15秒轮询一次
        t = threading.Thread(target=poll_loop, daemon=True)
        t.start()
    
    # ========== API调用 ==========
    
    def create_task(self, prompt: str,
                    ref_images: Optional[List[str]] = None,
                    ref_video: Optional[str] = None,
                    ref_audio: Optional[str] = None,
                    ratio: str = "16:9",
                    duration: int = 11,
                    generate_audio: bool = True) -> Dict:
        """创建视频生成任务"""
        content = [{"type": "text", "text": prompt}]
        
        if ref_images:
            for img_url in ref_images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img_url},
                    "role": "reference_image"
                })
        if ref_video:
            content.append({
                "type": "video_url",
                "video_url": {"url": ref_video},
                "role": "reference_video"
            })
        if ref_audio:
            content.append({
                "type": "audio_url",
                "audio_url": {"url": ref_audio},
                "role": "reference_audio"
            })
        
        payload = {
            "model": "doubao-seedance-2-0-260128",
            "content": content,
            "generate_audio": generate_audio,
            "ratio": ratio,
            "duration": duration,
            "watermark": False
        }
        
        try:
            r = requests.post(
                f"{API_BASE}/contents/generations/tasks",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if r.status_code == 200:
                task_id = r.json().get("id")
                now = datetime.now().isoformat()
                self.tasks[task_id] = {
                    "id": task_id,
                    "status": "pending",
                    "prompt": prompt[:50],
                    "ratio": ratio,
                    "duration": duration,
                    "created_at": now,
                    "updated_at": now,
                    "video_url": None,
                    "error": None,
                    "resolution": None,
                    "seed": None
                }
                self._save_tasks()
                return {"success": True, "task_id": task_id, "data": r.json()}
            else:
                return {"success": False, "error": f"API Error {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def query_task(self, task_id: str, save: bool = True) -> Dict:
        """查询任务状态"""
        try:
            r = requests.get(
                f"{API_BASE}/contents/generations/tasks/{task_id}",
                headers=self.headers,
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                status = data.get("status", "unknown")
                
                if task_id in self.tasks:
                    self.tasks[task_id]["status"] = status
                    self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
                    
                    if status == "succeeded":
                        c = data.get("content", {}) or {}
                        vu = c.get("video_url")
                        if vu:
                            self.tasks[task_id]["video_url"] = vu
                            self.tasks[task_id]["resolution"] = data.get("resolution", "720p")
                            self.tasks[task_id]["seed"] = data.get("seed")
                    elif status == "failed":
                        self.tasks[task_id]["error"] = data.get("error", "Unknown error")
                    
                    if save:
                        self._save_tasks()
                
                return {"success": True, "data": data}
            return {"success": False, "error": f"Query Error {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_all_tasks(self) -> List[Dict]:
        return list(self.tasks.values())
    
    def get_task_detail(self, task_id: str) -> Optional[Dict]:
        return self.tasks.get(task_id)
    
    def generate_prompt(self, keyword: str, product_type: str = "产品词") -> str:
        prompts = {
            "品": f"第一视角展示{keyword}的施工过程，从材料搅拌到地面铺设、打磨抛光，呈现专业施工团队操作。背景音轻快，字幕突出永颐金磨石品牌。",
            "产": f"{keyword}实景展示，从全景到细节特写，展示地面光泽度、无缝效果和整体美感。适合商业空间宣传风格。",
            "场": f"{keyword}实景展示，从全景到细节特写，展示地面光泽度、无缝效果和整体美感。",
            "工": f"{keyword}工艺流程特写，聚焦工具操作细节和材料质感变化，体现专业技术和品质把控。",
            "痛": f"解决方案展示：针对{keyword}问题，展示永颐金磨石如何通过专业技术解决。前后对比效果。",
            "竞": f"产品对比展示：{keyword}与传统方案对比，突出永颐金磨石在品质、服务、性价比方面的优势。",
        }
        return prompts.get(product_type[0], f"产品宣传视频：{keyword}。展示产品特点和应用场景。")
