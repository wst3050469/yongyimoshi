#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 AI内容营销系统 v5.3.0 - 升级版内容引擎"""
import json, random, datetime, os, re
from typing import List, Dict, Optional

# ===== AI客户端（预留接口） =====
class AIClient:
    """AI文本生成客户端 - 支持多平台"""
    def __init__(self):
        self.api_key = os.environ.get("AI_API_KEY", "")
        self.api_base = os.environ.get("AI_API_BASE", "")
        self.model = os.environ.get("AI_MODEL", "")
    
    def is_available(self) -> bool:
        return bool(self.api_key and self.api_base)
    
    def chat(self, messages: List[Dict], max_tokens: int = 500) -> Optional[str]:
        if not self.is_available():
            return None
        try:
            import requests
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            payload = {"model": self.model, "messages": messages, "max_tokens": max_tokens}
            r = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return None

ai_client = AIClient()

# ===== 关键词引擎 =====
class KeywordEngine:
    """关键词管理引擎"""
    def __init__(self):
        self.seed_keywords = {
            "品牌词": ["永颐金磨石", "永颐", "金磨石科技"],
            "产品词": ["无机磨石", "环氧磨石", "磨石地坪", "磨石地面", "水磨石", "金磨石", "磨石材料"],
            "场景词": ["医院磨石", "学校磨石", "商场磨石", "办公楼磨石", "展馆磨石", "车库磨石"],
            "工艺词": ["磨石施工", "磨石打磨", "磨石翻新", "磨石修补", "磨石固化", "磨石抛光"],
            "痛点词": ["地面开裂", "地坪起灰", "地面难清洗", "地坪不耐磨", "地面不美观"],
            "竞品词": ["金刚磨石", "磨石地坪公司", "地坪公司", "磨石厂家", "磨石材料商"],
        }
    
    def get_kws(self):
        return {k: list(v) for k, v in self.seed_keywords.items()}
    
    def add_keyword(self, kw, group="产品词"):
        if group not in self.seed_keywords:
            self.seed_keywords[group] = []
        if kw not in self.seed_keywords[group]:
            self.seed_keywords[group].append(kw)
        return True
    
    def random_kw(self, group=None):
        if group and group in self.seed_keywords:
            return random.choice(self.seed_keywords[group])
        all_kws = [kw for lst in self.seed_keywords.values() for kw in lst]
        return random.choice(all_kws)
    
    # ===== AI生成内容（带Mock回退） =====
    
    def _try_ai(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """尝试AI生成，失败返回None"""
        if ai_client.is_available():
            return ai_client.chat([{"role": "user", "content": prompt}], max_tokens)
        return None
    
    def gen_video(self, kw=None, group=None):
        kw = kw or self.random_kw(group)
        # 尝试AI
        prompt = f"你是一个专业的磨石地坪营销专家。请为关键词'{kw}'写一段30秒抖音短视频脚本，要求：1.开头吸引眼球 2.中间展示产品优势 3.结尾引导行动。用口语化风格，200字以内。"
        ai_result = self._try_ai(prompt)
        if ai_result:
            return ai_result
        
        # Mock回退 - 多样化模板
        templates = [
            f"【90%的人不知道的{kw}秘密】\\n很多人觉得{kw}只是个普通地面，其实大错特错！\\n永颐金磨石15年专注{kw}领域，服务500+项目，\\n从医院到学校，从商场到展馆，处处可见我们的作品。\\n想要高品质{kw}？找永颐金磨石就对了！\\n#金磨石 #{kw} #地坪装修",
            
            f"【{kw}避坑指南】\\n选{kw}最容易犯的3个错误：\\n1.只看价格不看质量\\n2.不关注材料环保性\\n3.忽视施工团队经验\\n\\n永颐金磨石，15年匠心工艺，\\n从材料到施工一站式服务，\\n让你的地面30年如新！\\n#{kw} #装修干货 #金磨石",
            
            f"【揭秘】{kw}为什么越来越受欢迎？\\n5大理由让你不得不选：\\n\\n1.无缝拼接，美观大气\\n2.耐磨抗压，使用寿命长\\n3.防滑安全，适合公共场所\\n4.易清洁，维护成本低\\n5.环保无味，即装即用\\n\\n永颐金磨石，专注{kw}15年\\n点击了解更多→\\n#{kw} #装修知识 #金磨石",
        ]
        return random.choice(templates)
    
    def gen_article(self, kw=None, group=None):
        kw = kw or self.random_kw(group)
        prompt = f"你是磨石地坪行业的专家。请写一篇关于'{kw}'的微信公众号文章，800字左右，专业但通俗易懂。包括：1.什么是{kw} 2.核心优势 3.应用场景 4.为什么选择永颐金磨石。"
        ai_result = self._try_ai(prompt, 1000)
        if ai_result:
            return ai_result
        
        templates = [
            f"【深度解析】{kw}施工全流程指南\\n\\n一、什么是{kw}？\\n{kw}是一种以特种水泥或环氧树脂为基料，\\n结合天然骨料经研磨抛光而成的高性能地面材料。\\n具有强度高、耐磨性好、装饰性强等特点。\\n\\n二、{kw}的核心优势\\n1. 超强耐磨：莫氏硬度7级以上\\n2. 无缝一体：整体施工，无缝隙\\n3. 防滑安全：湿态防滑系数达0.6以上\\n4. 易洁耐用：日常只需清水拖拭\\n5. 绿色环保：VOC排放达标\\n\\n三、应用场景\\n医院手术室、学校教室、商场中庭、\\n办公楼大堂、展馆展厅、地下车库\\n\\n四、为什么选择永颐金磨石？\\n15年专注，500+项目经验，\\n从设计到施工全程把控，\\n为您打造高品质地面空间。",
            
            f"【行业科普】{kw}和传统地坪有什么区别？\\n\\n很多客户问：{kw}和普通地坪到底有什么不同？\\n今天一次性说清楚！\\n\\n【耐磨性】\\n普通地坪：3-5年开始磨损\\n{kw}：15-20年仍完好如新\\n\\n【美观度】\\n普通地坪：颜色单一，接缝明显\\n{kw}：色彩丰富，整体无缝\\n\\n【维护成本】\\n普通地坪：需要定期打蜡翻新\\n{kw}：日常清洁即可，年维护费低\\n\\n【施工周期】\\n普通地坪：工期长，需多次养护\\n{kw}：科学工序，工期可控\\n\\n永颐金磨石，用心做好每一寸地面。",
        ]
        return random.choice(templates)
    
    def gen_xhs(self, kw=None, group=None):
        kw = kw or self.random_kw(group)
        prompt = f"请用小红书种草风格，写一段关于'{kw}'的推荐笔记，200字左右。风格要亲切自然，多用emoji和话题标签。突出{kw}的颜值和实用性。"
        ai_result = self._try_ai(prompt)
        if ai_result:
            return ai_result
        
        templates = [
            f"{kw}真的太绝了！后悔没早知道！😭\\n\\n姐妹们！一定要看完这篇！\\n我家刚做完{kw}，真的惊艳到我了！\\n\\n✨无缝一体，颜值超高\\n✨耐磨耐造，再也不怕刮花\\n✨特别好清洁，拖把一拖就干净\\n✨关键是环保无味，当天就能用\\n\\n找的是永颐金磨石，15年老品牌，\\n施工师傅特别专业，全程不用操心！\\n\\n装修的姐妹们冲就完事了！\\n\\n#装修日记 #{kw} #我的装修记录 #金磨石 #家居好物推荐",
            
            f"装修干货 | {kw}到底值不值得做？🤔\\n\\n作为一个过来人，真心推荐！\\n\\n✅ 优点\\n- 颜值：整体无缝，高级感拉满\\n- 耐用：用几十年都不成问题\\n- 省心：不用特殊保养，日常拖地就行\\n- 百搭：各种风格都能驾驭\\n\\n⚠️ 注意事项\\n- 一定要找专业团队施工\\n- 建议选大品牌，售后有保障\\n- 施工前做好地面基层处理\\n\\n我家选的永颐金磨石，效果超满意！\\n有问题评论区问我~\\n\\n#{kw} #装修避坑 #地坪 #装修灵感 #金磨石",
        ]
        return random.choice(templates)
    
    def gen_all(self, kw=None):
        kw = kw or self.random_kw()
        return {
            "video": self.gen_video(kw),
            "article": self.gen_article(kw),
            "xhs": self.gen_xhs(kw)
        }


class CompetitorAnalyzer:
    """竞品分析引擎"""
    def __init__(self):
        self.competitors = [
            {"name": "某石地坪", "s": ["品牌知名度高", "营销投入大"], "w": ["产品同质化", "价格偏高", "服务响应慢"]},
            {"name": "某装公司", "s": ["品牌知名度高", "渠道广泛"], "w": ["价格偏高", "地坪非主营", "专业度不足"]},
            {"name": "某磨石材", "s": ["材料价格低", "产品线丰富"], "w": ["施工经验不足", "售后服务差", "项目案例少"]},
        ]
    
    def get_comps(self):
        return self.competitors
    
    def add_comp(self, name, s=None, w=None):
        self.competitors.append({"name": name, "s": s or ["待分析"], "w": w or ["待分析"]})
        return True
    
    def surpass(self, comps=None):
        comps = comps or self.competitors
        return {
            "our_advantage": [
                "永颐金磨石15年专注金磨石领域",
                "专业施工团队，持证上岗",
                "从材料研发到施工一体化服务",
                "500+成功项目案例",
                "完善的售后服务体系"
            ],
            "content_advantage": {
                "daily": 28,
                "avg": 2,
                "ratio": "14倍于同行"
            },
            "strategy": [
                "AI每日生成28篇专业内容",
                "覆盖多平台矩阵运营",
                "打造专业知识IP",
                "GEO搜索引擎优化",
                "精准获客转化"
            ],
            "result": {
                "exposure": "150万+",
                "leads": "50+",
                "roi": "1:5"
            }
        }


class MarketingReport:
    @staticmethod
    def summary(kc, dc, cc):
        return {
            "system": "永颐金磨石 AI智能内容营销系统",
            "version": "5.3.0",
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "metrics": {
                "keywords": kc,
                "daily": dc,
                "monthly": dc * 30,
                "competitors": cc
            },
            "roi": {
                "investment": "5000元/月",
                "exposure": "150万+",
                "leads": "50+",
                "estimate": "1:5"
            }
        }
