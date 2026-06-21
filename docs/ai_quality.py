#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 AI质量引擎 v5.6.2
AI深度参与：内容评分 → 优化建议 → 效果洞察 → 策略推荐"""
import json, os, random
from datetime import datetime
from typing import List, Dict, Optional

try:
    from docs.marketing_system import ai_client
except ImportError:
    from marketing_system import ai_client


class AIQualityEngine:
    """AI内容质量评估与优化引擎"""

    def _try_ai(self, system_prompt: str, user_prompt: str, max_tokens: int = 600) -> Optional[str]:
        if ai_client.is_available():
            return ai_client.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], max_tokens)
        return None

    # ===== 1. AI 内容评分 =====

    def score_content(self, content: str, platform: str, keyword: str = "") -> Dict:
        """AI 对内容进行多维度评分 (0-100)"""
        sys = f"""你是{platform}平台的内容质量审核专家。请对以下营销内容进行5维度评分。
每个维度0-100分，给出总分和一句话评价。
只输出JSON: {{"total":85,"readability":90,"seo":80,"engagement":75,"brand_fit":95,"comment":"评价"}}"""
        
        usr = f"关键词:{keyword}\n平台:{platform}\n内容:\n{content[:1500]}"
        result = self._try_ai(sys, usr, 400)
        if result:
            try:
                js = result.strip()
                if "```" in js:
                    js = js.split("```")[1].replace("json", "", 1)
                return json.loads(js)
            except:
                pass
        # Mock fallback
        scores = {
            "total": random.randint(65, 92),
            "readability": random.randint(60, 95),
            "seo": random.randint(55, 90),
            "engagement": random.randint(50, 88),
            "brand_fit": random.randint(70, 98),
            "comment": "AI评分Mock模式 - 内容整体可用，建议优化开头吸引力"
        }
        return scores

    # ===== 2. AI 优化建议 =====

    def suggest_improvements(self, content: str, platform: str, scores: Dict = None) -> Dict:
        """AI 给出具体优化建议"""
        sys = f"""你是{platform}平台的内容优化专家。分析内容弱点，给出3-5条具体可执行的优化建议。
每条建议格式: {{"issue":"问题","suggestion":"建议","priority":"高/中/低"}}
只输出JSON数组: [{{"issue":"...","suggestion":"...","priority":"..."}}]"""
        
        score_info = f"当前评分: {json.dumps(scores, ensure_ascii=False)}" if scores else ""
        usr = f"{score_info}\n内容:\n{content[:1200]}"
        result = self._try_ai(sys, usr, 600)
        if result:
            try:
                js = result.strip()
                if "```" in js:
                    js = js.split("```")[1].replace("json", "", 1)
                suggestions = json.loads(js)
                if isinstance(suggestions, list):
                    return {"suggestions": suggestions, "ai_generated": True}
            except:
                pass
        # Mock fallback
        return {
            "suggestions": [
                {"issue": "开头吸引力不足", "suggestion": "前3秒加入数据或悬念钩子", "priority": "高"},
                {"issue": "品牌露出不够自然", "suggestion": "在案例描述中自然嵌入品牌名", "priority": "中"},
                {"issue": "缺少行动号召", "suggestion": "结尾添加明确的CTA引导评论/留资", "priority": "高"},
                {"issue": "关键词密度偏低", "suggestion": f"核心关键词出现至少3次", "priority": "中"},
            ],
            "ai_generated": False
        }

    def optimize_content(self, content: str, platform: str, keyword: str = "") -> Dict:
        """AI 直接输出优化后的版本"""
        sys = f"""你是{platform}平台的顶级内容创作者。请优化以下内容，保持原意但提升质量：
1. 开头更吸引人
2. 中间更流畅自然
3. 结尾引导互动
4. 保持品牌调性(永颐金磨石,15年专注,500+项目)
输出格式:
原始内容
---
优化后内容"""
        
        usr = f"关键词:{keyword}\n内容:\n{content[:1500]}"
        result = self._try_ai(sys, usr, 1000)
        if result:
            parts = result.split("---", 1)
            optimized = parts[1].strip() if len(parts) > 1 else result
            return {"original": content, "optimized": optimized, "ai_generated": True}
        return {"original": content, "optimized": content, "ai_generated": False}

    # ===== 3. AI 效果洞察 =====

    def analyze_performance(self, analytics_data: Dict) -> Dict:
        """AI 分析效果数据，给出洞察结论"""
        sys = """你是营销数据分析师。根据内容效果数据，分析:
1. 为什么表现好/差
2. 观众画像推断
3. 下一步优化方向
只输出JSON: {"insight":"核心洞察","strengths":["优势1","优势2"],"weaknesses":["弱点"],"next_actions":["建议"]}"""
        
        usr = f"效果数据:\n{json.dumps(analytics_data, ensure_ascii=False, indent=2)[:1500]}"
        result = self._try_ai(sys, usr, 500)
        if result:
            try:
                js = result.strip()
                if "```" in js:
                    js = js.split("```")[1].replace("json", "", 1)
                return json.loads(js)
            except:
                pass
        views = analytics_data.get("views", 0)
        engagement = analytics_data.get("engagement", 0)
        rate = analytics_data.get("engagement_rate", 0)
        
        if rate > 5:
            insight = f"互动率{rate}%表现优秀，内容引发了用户共鸣。继续保持这种风格。"
        elif rate > 2:
            insight = f"互动率{rate}%中等偏上，可以尝试在开头加入更强的钩子提升互动。"
        else:
            insight = f"互动率{rate}%偏低，建议优化开头吸引力和结尾CTA。"
        
        return {
            "insight": insight,
            "strengths": ["内容结构清晰"] if views > 500 else [],
            "weaknesses": ["开头吸引力可提升"] if rate < 5 else [],
            "next_actions": [
                "优化标题和开头钩子" if rate < 5 else "复制成功模式到其他平台",
                "增加互动引导话术",
                "尝试不同发布时间"
            ]
        }

    # ===== 4. AI 策略推荐 =====

    def recommend_strategy(self, history_stats: Dict) -> Dict:
        """AI 根据历史数据推荐内容策略"""
        sys = """你是内容营销策略师。根据账号数据，推荐最佳内容策略。
只输出JSON: {"best_platform":"平台","best_content_type":"类型","best_publish_time":"时间","topic_suggestions":["话题1","话题2"],"overall_strategy":"策略总结"}"""
        
        usr = f"历史数据:\n{json.dumps(history_stats, ensure_ascii=False, indent=2)[:1200]}"
        result = self._try_ai(sys, usr, 500)
        if result:
            try:
                js = result.strip()
                if "```" in js:
                    js = js.split("```")[1].replace("json", "", 1)
                return json.loads(js)
            except:
                pass
        return {
            "best_platform": "公众号",
            "best_content_type": "深度科普文章",
            "best_publish_time": "周二/周四 上午10:00",
            "topic_suggestions": [
                "无机磨石vs环氧磨石怎么选",
                "医院地坪翻新避坑指南",
                "2025地面材料趋势解读"
            ],
            "overall_strategy": "以公众号深度文章为内容基石，拆解为短视频和小红书笔记做全平台分发。重点打'医疗地坪专家'心智。"
        }

    # ===== 综合评估包 =====

    def full_review(self, content: str, platform: str, keyword: str = "") -> Dict:
        """一键全评估：评分 + 建议 + 优化版"""
        scores = self.score_content(content, platform, keyword)
        suggestions = self.suggest_improvements(content, platform, scores)
        optimized = self.optimize_content(content, platform, keyword)
        return {
            "scores": scores,
            "suggestions": suggestions.get("suggestions", []),
            "optimized": optimized.get("optimized", content),
            "ai_powered": ai_client.is_available(),
            "reviewed_at": datetime.now().isoformat()
        }
