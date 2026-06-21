#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 真实发布通道 v5.6.2
对接微信公众号草稿箱 + 多平台格式化导出"""
import json, os, time, requests
from datetime import datetime
from typing import List, Dict, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PUBLISHED_FILE = os.path.join(DATA_DIR, "published_content.json")

# 微信公众号配置
APP_ID = os.environ.get("WECHAT_APP_ID", "wxe6d7e3ee6c4eb2d6")
APP_SECRET = os.environ.get("WECHAT_APP_SECRET", "")

# 各平台发布规格
PLATFORM_SPECS = {
    "douyin": {
        "name": "抖音", "max_chars": 500, "hashtag_style": "#话题#",
        "export_hint": "打开抖音APP → 发布 → 粘贴文案 + 上传视频/图片"
    },
    "xhs": {
        "name": "小红书", "max_chars": 1000, "hashtag_style": "#话题",
        "export_hint": "打开小红书APP → ＋ → 粘贴笔记 + 添加图片"
    },
    "wechat_article": {
        "name": "公众号", "max_chars": 20000, "hashtag_style": "#话题#",
        "export_hint": "微信公众号后台 → 新建图文 → 粘贴内容"
    },
    "baijiahao": {
        "name": "百家号", "max_chars": 20000, "hashtag_style": "#话题#",
        "export_hint": "百家号后台 → 发布 → 粘贴文章"
    },
    "zhihu": {
        "name": "知乎", "max_chars": 10000, "hashtag_style": "#话题#",
        "export_hint": "知乎 → 写回答/文章 → 粘贴内容"
    },
    "weibo": {
        "name": "微博", "max_chars": 140, "hashtag_style": "#话题#",
        "export_hint": "微博APP → 发微博 → 粘贴文案"
    },
}


class WeChatPublisher:
    """微信公众号发布通道：access_token管理 + 草稿箱 + 群发"""

    def __init__(self):
        self._access_token = None
        self._token_expires = 0

    @property
    def is_configured(self) -> bool:
        return bool(APP_SECRET)

    def _get_access_token(self) -> Optional[str]:
        """获取/刷新微信公众号 access_token"""
        if not APP_SECRET:
            return None
        now = time.time()
        if self._access_token and now < self._token_expires - 300:
            return self._access_token
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
            r = requests.get(url, timeout=10)
            data = r.json()
            if "access_token" in data:
                self._access_token = data["access_token"]
                self._token_expires = now + data.get("expires_in", 7200)
                return self._access_token
            print(f"[WeChatPublisher] Token error: {data}")
        except Exception as e:
            print(f"[WeChatPublisher] Token exception: {e}")
        return None

    def create_draft(self, title: str, content: str, thumb_media_id: str = "") -> Dict:
        """创建微信公众号草稿（图文消息）
        
        Args:
            title: 文章标题 (必填)
            content: 正文HTML内容
            thumb_media_id: 封面缩略图media_id
        
        Returns:
            {"success": bool, "media_id": str, "error": str}
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "微信公众号APP_SECRET未配置，请在.env中添加WECHAT_APP_SECRET",
                "hint": "获取方式: 微信公众号后台 → 开发 → 基本配置 → AppSecret",
                "ready_to_paste": True,
                "paste_instruction": "请手动粘贴到微信公众号后台 → 新建图文"
            }

        token = self._get_access_token()
        if not token:
            return {"success": False, "error": "无法获取access_token，请检查APP_SECRET是否正确"}

        # 构建图文消息草稿
        articles = [{
            "title": title,
            "content": content,
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]
        if thumb_media_id:
            articles[0]["thumb_media_id"] = thumb_media_id

        try:
            url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
            payload = {"articles": articles}
            r = requests.post(url, json=payload, timeout=15)
            data = r.json()
            if "media_id" in data:
                return {
                    "success": True,
                    "media_id": data["media_id"],
                    "platform": "wechat_article",
                    "published_at": datetime.now().isoformat()
                }
            return {"success": False, "error": json.dumps(data, ensure_ascii=False)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_draft_list(self) -> Dict:
        """获取草稿列表"""
        if not self.is_configured:
            return {"success": False, "error": "微信未配置"}
        token = self._get_access_token()
        if not token:
            return {"success": False, "error": "token获取失败"}
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token={token}"
            r = requests.post(url, json={"offset": 0, "count": 20, "no_content": 1}, timeout=10)
            return r.json()
        except Exception as e:
            return {"success": False, "error": str(e)}


class PublishExporter:
    """多平台内容格式化导出器"""

    @staticmethod
    def export_for_platform(content: str, platform: str, title: str = "", keyword: str = "") -> Dict:
        """为指定平台生成即用发布包"""
        spec = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["wechat_article"])
        formatted = content
        
        # 截断超长内容
        if len(content) > spec["max_chars"]:
            formatted = content[:spec["max_chars"] - 3] + "..."

        export_package = {
            "platform": platform,
            "platform_name": spec["name"],
            "title": title,
            "content": formatted,
            "content_length": len(formatted),
            "export_hint": spec["export_hint"],
            "copy_ready": True,
            "exported_at": datetime.now().isoformat()
        }
        return export_package

    @staticmethod
    def export_all_platforms(contents: Dict[str, str], keyword: str = "") -> List[Dict]:
        """批量生成所有平台的发布包"""
        packages = []
        for platform, content in contents.items():
            if content:
                pkg = PublishExporter.export_for_platform(content, platform, keyword, keyword)
                packages.append(pkg)
        return packages

    @staticmethod
    def export_html_article(title: str, content: str, author: str = "永颐金磨石") -> str:
        """将纯文本内容转换为微信公众号兼容的HTML格式"""
        paragraphs = content.split("\n")
        html_parts = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if p.startswith("【") or p.startswith("##"):
                html_parts.append(f'<h2 style="color:#1a1a2e;">{p.strip("【】##")}</h2>')
            elif p.startswith("#"):
                html_parts.append(f'<h3>{p.strip("#")}</h3>')
            else:
                html_parts.append(f'<p style="line-height:2;margin-bottom:12px;color:#333;">{p}</p>')
        
        html = f'''<section style="padding:10px;">
{"".join(html_parts)}
<p style="text-align:center;color:#8898aa;font-size:13px;margin-top:24px;">
永颐金磨石 | 专注金磨石15年 | 500+项目经验<br/>
📞 16624603959 | 🌐 ai.jinmojianshe.com
</p>
</section>'''
        return html


# 持久化已发布记录
class PublishedStore:
    def __init__(self):
        self.records = []
        self._load()

    def _ensure_dir(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def _load(self):
        try:
            if os.path.exists(PUBLISHED_FILE):
                with open(PUBLISHED_FILE, 'r', encoding='utf-8') as f:
                    self.records = json.load(f)
        except:
            self.records = []

    def _save(self):
        try:
            self._ensure_dir()
            with open(PUBLISHED_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except:
            pass

    def add(self, publish_id: str, platform: str, result: Dict) -> Dict:
        record = {
            "publish_id": publish_id,
            "platform": platform,
            "result": result,
            "published_at": datetime.now().isoformat()
        }
        self.records.append(record)
        self._save()
        return record

    def get_all(self) -> List[Dict]:
        return list(reversed(self.records))

    def get_stats(self) -> Dict:
        platforms = {}
        for r in self.records:
            p = r.get("platform", "未知")
            platforms[p] = platforms.get(p, 0) + 1
        return {"total": len(self.records), "by_platform": platforms}
