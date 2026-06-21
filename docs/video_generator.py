#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 AI视频生成模块 - 集成豆包Seedance API"""
import requests, json, time, os
from typing import Optional, Dict, List
from datetime import datetime

API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
API_KEY = os.environ.get("DOUBAO_API_KEY", "3c15d74c-103b-44eb-8d47-b979fc7305cd")

class VideoGenerator:
    """豆包Seedance视频生成"""
    
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        self.tasks = {}
    
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
                self.tasks[task_id] = {
                    "id": task_id,
                    "status": "pending",
                    "prompt": prompt[:50],
                    "ratio": ratio,
                    "duration": duration,
                    "created_at": datetime.now().isoformat(),
                    "video_url": None,
                    "error": None
                }
                return {"success": True, "task_id": task_id, "data": r.json()}
            else:
                return {"success": False, "error": f"API Error {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def query_task(self, task_id: str) -> Dict:
        """查询任务状态并更新存储"""
        try:
            r = requests.get(
                f"{API_BASE}/contents/generations/tasks/{task_id}",
                headers=self.headers,
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                status = data.get("status", "unknown")
                
                # 更新存储的任务信息
                if task_id in self.tasks:
                    self.tasks[task_id]["status"] = status
                    self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
                    
                    # 如果任务完成，保存视频URL
                    if status == "succeeded":
                        content = data.get("content", {})
                        video_url = content.get("video_url") if content else None
                        if video_url:
                            self.tasks[task_id]["video_url"] = video_url
                            self.tasks[task_id]["duration"] = data.get("duration", self.tasks[task_id].get("duration"))
                            self.tasks[task_id]["resolution"] = data.get("resolution", "720p")
                    
                    elif status == "failed":
                        self.tasks[task_id]["error"] = data.get("error", "Unknown error")
                
                return {"success": True, "data": data}
            return {"success": False, "error": f"Query Error {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务列表"""
        return list(self.tasks.values())
    
    def get_task_detail(self, task_id: str) -> Optional[Dict]:
        """获取单个任务详情"""
        return self.tasks.get(task_id)
    
    def generate_prompt(self, keyword: str, product_type: str = "产品词") -> str:
        """根据关键词自动生成视频prompt"""
        prompts = {
            "产品词": f"第一视角展示{keyword}的施工过程，从材料搅拌到地面铺设、打磨抛光，呈现专业施工团队操作。背景音轻快，字幕突出永颐金磨石品牌。",
            "场景词": f"{keyword}实景展示，从全景到细节特写，展示地面光泽度、无缝效果和整体美感。适合商业空间宣传风格。",
            "工艺词": f"{keyword}工艺流程特写，聚焦工具操作细节和材料质感变化，体现专业技术和品质把控。",
            "品牌词": f"品牌宣传视频：{keyword}。展示品牌形象、企业文化、经典案例，搭配庄重大气的背景音乐。",
            "痛点词": f"解决方案展示：针对{keyword}问题，展示永颐金磨石如何通过专业技术解决。前后对比效果。",
            "竞品词": f"产品对比展示：{keyword}与传统方案对比，突出永颐金磨石在品质、服务、性价比方面的优势。",
        }
        # 匹配最接近的分类
        for key in prompts:
            if key[0] == product_type[0]:
                return prompts[key]
        return f"产品宣传视频：{keyword}。展示产品特点、应用场景和品牌价值。"
