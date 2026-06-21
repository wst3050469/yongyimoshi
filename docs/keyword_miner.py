#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 AI Agent关键词挖掘引擎 v5.6.1
基于 DeepSeek AI Agent 多轮深度挖掘：语义扩展 + 长尾词 + 问答 + 竞品"""
import random, json, os, re, time
from datetime import datetime
from typing import List, Dict, Optional, Set

# 复用 AIClient（同目录 marketing_system.py 中）
try:
    from docs.marketing_system import ai_client
except ImportError:
    from marketing_system import ai_client

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MINED_FILE = os.path.join(DATA_DIR, "mined_keywords.json")
POOL_FILE = os.path.join(DATA_DIR, "kw_pool.json")


class KeywordMiner:
    """AI驱动多平台关键词挖掘"""

    PLATFORMS = {
        "douyin": "抖音",
        "xhs": "小红书",
        "baidu": "百度",
        "weibo": "微博",
        "zhihu": "知乎",
    }

    def __init__(self):
        self.mined = []
        self._load()

    def _ensure_dir(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def _load(self):
        try:
            if os.path.exists(MINED_FILE):
                with open(MINED_FILE, 'r', encoding='utf-8') as f:
                    self.mined = json.load(f)
        except:
            self.mined = []

    def _save(self):
        try:
            self._ensure_dir()
            with open(MINED_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.mined, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[KeywordMiner] Save error: {e}")

    # ===== AI 挖掘 =====

    def _try_ai(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        if ai_client.is_available():
            return ai_client.chat([{"role": "user", "content": prompt}], max_tokens)
        return None

    def mine_from_platform(self, platform: str = "douyin", count: int = 10) -> List[Dict]:
        """AI挖掘指定平台的热门关键词（带行业偏好）"""
        platform_cn = self.PLATFORMS.get(platform, platform)
        prompt = f"""你是{platform_cn}平台的地坪/装修行业数据分析师。请挖掘当前{platform_cn}上与「磨石地坪」「金磨石」「无机磨石」相关的热门搜索关键词。

要求：
1. 输出{count}个关键词，按热度从高到低排列
2. 每个关键词附带：关键词本身、所属分类（产品词/场景词/痛点词/工艺词/品牌词）、预估热度（高/中/低）、搜索意图（了解/对比/购买）
3. 考虑用户搜索习惯，包括长尾词和口语化表达
4. 输出JSON数组格式：[
  {{"word":"关键词","category":"分类","heat":"热度","intent":"意图"}},
  ...
]
只输出JSON数组，不要其他文字。"""

        ai_result = self._try_ai(prompt, 600)
        if ai_result:
            try:
                # 尝试解析AI返回的JSON
                json_str = ai_result.strip()
                if "```" in json_str:
                    json_str = json_str.split("```")[1]
                    if json_str.startswith("json"):
                        json_str = json_str[4:]
                result = json.loads(json_str)
                if isinstance(result, list):
                    return result
            except:
                pass

        # Mock 回退 - 按平台输出行业相关热门词
        mock_pools = {
            "douyin": [
                {"word": "无机磨石多少钱一平方", "category": "产品词", "heat": "高", "intent": "对比"},
                {"word": "磨石地面施工全过程", "category": "工艺词", "heat": "高", "intent": "了解"},
                {"word": "金磨石和瓷砖哪个好", "category": "竞品词", "heat": "中", "intent": "对比"},
                {"word": "地下室地面开裂怎么办", "category": "痛点词", "heat": "高", "intent": "购买"},
                {"word": "医院地面用什么材料", "category": "场景词", "heat": "中", "intent": "了解"},
                {"word": "磨石地坪翻新技巧", "category": "工艺词", "heat": "中", "intent": "了解"},
                {"word": "2025最火的地面材料", "category": "产品词", "heat": "高", "intent": "了解"},
                {"word": "环氧磨石施工队推荐", "category": "产品词", "heat": "中", "intent": "购买"},
                {"word": "水磨石地面优缺点", "category": "产品词", "heat": "高", "intent": "对比"},
                {"word": "车间地面不耐磨怎么办", "category": "痛点词", "heat": "中", "intent": "购买"},
            ],
            "xhs": [
                {"word": "磨石地面装修效果图", "category": "产品词", "heat": "高", "intent": "了解"},
                {"word": "金磨石装修日记", "category": "产品词", "heat": "高", "intent": "了解"},
                {"word": "装修地面材料怎么选", "category": "痛点词", "heat": "高", "intent": "对比"},
                {"word": "无缝地面太高级了", "category": "产品词", "heat": "中", "intent": "了解"},
                {"word": "地下室防潮地面方案", "category": "场景词", "heat": "中", "intent": "对比"},
                {"word": "工业风地面装修", "category": "场景词", "heat": "中", "intent": "了解"},
                {"word": "装修避坑地面篇", "category": "痛点词", "heat": "高", "intent": "了解"},
                {"word": "奶茶店地面用什么好", "category": "场景词", "heat": "中", "intent": "对比"},
                {"word": "老房翻新地面改造", "category": "工艺词", "heat": "高", "intent": "购买"},
                {"word": "最耐用的地面材料排名", "category": "产品词", "heat": "中", "intent": "对比"},
            ],
            "baidu": [
                {"word": "无机磨石厂家排名", "category": "竞品词", "heat": "高", "intent": "对比"},
                {"word": "金磨石施工工艺流程", "category": "工艺词", "heat": "高", "intent": "了解"},
                {"word": "磨石地面价格多少钱一平", "category": "产品词", "heat": "高", "intent": "对比"},
                {"word": "环氧磨石和无机磨石区别", "category": "产品词", "heat": "高", "intent": "对比"},
                {"word": "地坪漆和磨石哪个好", "category": "竞品词", "heat": "中", "intent": "对比"},
                {"word": "磨石地坪国家标准", "category": "工艺词", "heat": "中", "intent": "了解"},
                {"word": "永颐金磨石怎么样", "category": "品牌词", "heat": "中", "intent": "了解"},
                {"word": "磨石地面使用寿命多久", "category": "产品词", "heat": "中", "intent": "了解"},
                {"word": "展厅地面装修方案", "category": "场景词", "heat": "低", "intent": "了解"},
                {"word": "地面起灰处理办法", "category": "痛点词", "heat": "中", "intent": "购买"},
            ],
        }

        pool = mock_pools.get(platform, mock_pools["douyin"])
        result = random.sample(pool, min(count, len(pool)))
        for item in result:
            item["platform"] = platform
            item["mined_at"] = datetime.now().isoformat()
        return result

    def get_trending(self, platforms: List[str] = None, limit: int = 20) -> List[Dict]:
        """获取综合热门关键词（多平台汇总去重）"""
        if platforms is None:
            platforms = ["douyin", "xhs", "baidu"]

        all_kws = []
        for p in platforms:
            kws = self.mine_from_platform(p, 8)
            for kw in kws:
                kw["mined_at"] = datetime.now().isoformat()
            all_kws.extend(kws)

        # 去重 + 按热度排序
        seen = set()
        unique = []
        for kw in all_kws:
            if kw["word"] not in seen:
                seen.add(kw["word"])
                unique.append(kw)

        heat_order = {"高": 3, "中": 2, "低": 1}
        unique.sort(key=lambda x: heat_order.get(x.get("heat", "低"), 0), reverse=True)

        return unique[:limit]

    def get_mined_history(self) -> List[Dict]:
        """获取历史上的挖掘记录"""
        return list(reversed(self.mined))

    def save_mined(self, keywords: List[Dict]):
        """保存挖掘结果到历史"""
        batch = {
            "id": str(int(datetime.now().timestamp())),
            "mined_at": datetime.now().isoformat(),
            "keywords": keywords,
            "count": len(keywords)
        }
        self.mined.append(batch)
        self._save()
        return batch

    # ===== v5.6.1 AI Agent Deep Mining =====

    def _ensure_pool_dir(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def _load_pool(self) -> Dict:
        try:
            if os.path.exists(POOL_FILE):
                with open(POOL_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def _save_pool(self, pool: Dict):
        self._ensure_pool_dir()
        with open(os.path.abspath(POOL_FILE), 'w', encoding='utf-8') as f:
            json.dump(pool, f, ensure_ascii=False, indent=2)

    def get_mined_pool(self) -> List[Dict]:
        pool = self._load_pool()
        result = []
        for word, info in pool.items():
            info["word"] = word
            result.append(info)
        result.sort(key=lambda x: x.get("heat_score", 0), reverse=True)
        return result

    def _merge_into_pool(self, keywords: List[Dict], source: str = "agent") -> int:
        pool = self._load_pool()
        added = 0
        for kw in keywords:
            word = kw.get("word", "").strip()
            if not word:
                continue
            if word not in pool:
                pool[word] = {"category": kw.get("category", ""), "heat": kw.get("heat", ""),
                    "intent": kw.get("intent", ""), "platform": kw.get("platform", ""),
                    "source": source, "mined_at": datetime.now().isoformat(),
                    "heat_score": {"高": 3, "中": 2, "低": 1}.get(kw.get("heat", ""), 1)}
                added += 1
        self._save_pool(pool)
        return added

    def _agent_round(self, system_prompt: str, user_prompt: str, max_tokens: int = 800) -> Optional[List[Dict]]:
        if not ai_client.is_available():
            return None
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        ai_result = ai_client.chat(messages, max_tokens)
        if not ai_result:
            return None
        try:
            js = ai_result.strip()
            if "```" in js:
                js = js.split("```")[1]
                if js.startswith("json"):
                    js = js[4:]
            result = json.loads(js)
            if isinstance(result, list):
                # Validate all items are dicts with 'word' key
                valid = [item for item in result if isinstance(item, dict) and 'word' in item]
                if valid:
                    return valid
        except:
            pass
        return None

    # === Agent Round 1: Semantic Expansion ===

    def _agent_expand_semantic(self, seed_words: List[str], count: int = 20) -> List[Dict]:
        sys = "You are an SEO keyword research AI agent for Chinese terrazzo/flooring market. Expand seed words into synonyms, related terms, industry terminology, and social media slang. Output ONLY JSON array: [{\"word\":\"...\",\"category\":\"...\",\"heat\":\"...\",\"intent\":\"...\"}]"
        usr = f"Seeds: {', '.join(seed_words[:8])}. Generate {count} semantically expanded Chinese keywords. Categories: product/scene/pain/process/brand."
        result = self._agent_round(sys, usr, 800)
        if result:
            return result
        mock = []
        suffixes = ["价格", "施工", "厂家", "优缺点", "效果图", "多少钱", "哪家好", "工艺流程", "翻新", "报价"]
        for seed in seed_words[:5]:
            for suf in suffixes[:4]:
                mock.append({"word": f"{seed}{suf}", "category": "产品词", "heat": "中", "intent": "了解"})
        return mock[:count]

    # === Agent Round 2: Long-Tail ===

    def _agent_generate_longtail(self, seed_words: List[str], count: int = 30) -> List[Dict]:
        sys = "You are a long-tail keyword AI agent for Chinese terrazzo market. Generate scene-based, region-based, comparison, problem-solving, and purchase-intent queries. Output ONLY JSON array."
        usr = f"Seeds: {', '.join(seed_words[:6])}. Generate {count} Chinese long-tail keywords."
        result = self._agent_round(sys, usr, 1000)
        if result:
            return result
        scenes = ["医院", "学校", "商场", "车间", "车库", "展厅", "办公楼"]
        products = ["无机磨石", "环氧磨石", "金磨石"]
        needs = ["施工方案", "价格预算", "材料选择", "翻新改造"]
        mock = []
        for scene in scenes[:6]:
            for prod in products:
                mock.append({"word": f"{scene}{prod}{random.choice(needs)}", "category": "长尾词", "heat": "中", "intent": "了解"})
        return mock[:count]

    # === Agent Round 3: Questions ===

    def _agent_mine_questions(self, seed_words: List[str], count: int = 20) -> List[Dict]:
        sys = "You are a question-mining AI agent. Generate real Chinese user questions about terrazzo. Types: how-to, why, what-is, which-is-better, is-it-worth-it. Output ONLY JSON array."
        usr = f"Seeds: {', '.join(seed_words[:5])}. Generate {count} natural Chinese questions."
        result = self._agent_round(sys, usr, 800)
        if result:
            return result
        q_tmpl = ["{}怎么施工", "{}多少钱一平方", "{}和{}哪个好", "{}值得做吗", "为什么{}会开裂", "{}能用多少年"]
        mock = []
        for seed in seed_words[:5]:
            for t in q_tmpl[:3]:
                kw = t.format(seed, random.choice(seed_words[:3])) if t.count("{}") > 1 else t.format(seed)
                mock.append({"word": kw, "category": "问答词", "heat": "中", "intent": "了解"})
        return mock[:count]

    # === Agent Round 4: Competitors ===

    def _agent_mine_competitors(self, brand: str = "永颐金磨石", count: int = 15) -> List[Dict]:
        sys = "You are a competitive intelligence AI agent for Chinese terrazzo market. Mine competitor comparison keywords. Output ONLY JSON array."
        usr = f"Brand: {brand}. Mine {count} competitor-related keywords."
        result = self._agent_round(sys, usr, 600)
        if result:
            return result
        comps = ["某石地坪", "某装集团", "某材厂商", "某建材"]
        mock = []
        for c in comps:
            mock.append({"word": f"{c}磨石地坪怎么样", "category": "竞品词", "heat": "高", "intent": "对比"})
            mock.append({"word": f"{brand}和{c}对比", "category": "竞品词", "heat": "中", "intent": "对比"})
            mock.append({"word": "磨石地坪厂家排名", "category": "竞品词", "heat": "高", "intent": "对比"})
        return mock[:count]

    # === Main Agent Pipeline ===

    def deep_mine(self, seed_words: List[str] = None, platforms: List[str] = None,
                  rounds: List[str] = None) -> Dict:
        """AI Agent autonomous deep mining pipeline - semantic + longtail + questions + competitors + platforms"""
        if seed_words is None:
            seed_words = ["无机磨石", "金磨石", "环氧磨石", "磨石地坪", "水磨石"]
        if platforms is None:
            platforms = ["douyin", "xhs", "baidu"]
        if rounds is None:
            rounds = ["semantic", "longtail", "questions", "competitors"]
        start_time = datetime.now()
        all_keywords = []
        round_stats = {}
        for rn in rounds:
            rs = datetime.now()
            if rn == "semantic":
                kws = self._agent_expand_semantic(seed_words, 20)
                label = "Semantic Expansion"
            elif rn == "longtail":
                kws = self._agent_generate_longtail(seed_words, 30)
                label = "Long-tail Generation"
            elif rn == "questions":
                kws = self._agent_mine_questions(seed_words, 20)
                label = "Question Mining"
            elif rn == "competitors":
                kws = self._agent_mine_competitors()
                label = "Competitor Mining"
            else:
                kws = self.mine_from_platform(rn, 10)
                label = f"Platform: {rn}"
            for kw in kws:
                if isinstance(kw, dict):
                    kw["agent_round"] = rn
                    kw["mined_at"] = datetime.now().isoformat()
            added = self._merge_into_pool([k for k in kws if isinstance(k, dict)], source=f"agent_{rn}")
            all_keywords.extend([k for k in kws if isinstance(k, dict)])
            round_stats[rn] = {"label": label, "generated": len([k for k in kws if isinstance(k, dict)]), "added_to_pool": added,
                "time_s": round((datetime.now() - rs).total_seconds(), 1)}
        for p in platforms:
            kws = self.mine_from_platform(p, 8)
            for kw in kws:
                if isinstance(kw, dict):
                    kw["agent_round"] = f"platform_{p}"
            self._merge_into_pool([k for k in kws if isinstance(k, dict)], source=f"platform_{p}")
            all_keywords.extend([k for k in kws if isinstance(k, dict)])
            round_stats[f"platform_{p}"] = {"label": self.PLATFORMS.get(p, p),
                "generated": len(kws), "added_to_pool": 0, "time_s": 0}
        batch = self.save_mined(all_keywords)
        pool = self.get_mined_pool()
        return {"batch_id": batch["id"], "total_generated": len(all_keywords),
            "total_in_pool": len(pool), "rounds": round_stats, "sample": all_keywords[:10],
            "total_time_s": round((datetime.now() - start_time).total_seconds(), 1),
            "mined_at": start_time.isoformat()}
