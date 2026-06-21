#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 AI内容营销系统 v5.6.0 - DeepSeek AI + 多平台引擎"""
import json, random, datetime, os, re
from typing import List, Dict, Optional

# ===== AI客户端 =====
class AIClient:
    def __init__(self):
        self.api_key = os.environ.get("AI_API_KEY", "")
        self.api_base = os.environ.get("AI_API_BASE", "")
        self.model = os.environ.get("AI_MODEL", "")

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_base)

    def chat(self, messages: List[Dict], max_tokens: int = 800) -> Optional[str]:
        if not self.is_available():
            return None
        try:
            import requests
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            payload = {"model": self.model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.8}
            r = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=payload, timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except:
            pass
        return None

ai_client = AIClient()

# ===== 关键词引擎 =====
class KeywordEngine:
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

    def _try_ai(self, prompt: str, max_tokens: int = 800) -> Optional[str]:
        if ai_client.is_available():
            return ai_client.chat([{"role": "user", "content": prompt}], max_tokens)
        return None

    # ===== 抖音视频脚本 =====
    def gen_video(self, kw=None, group=None):
        kw = kw or self.random_kw(group)
        prompt = f"""你是永颐金磨石公司的金牌营销总监。请写一段30秒抖音口播脚本文案。
要求：
1. 关键词：{kw}
2. 开头3秒必须有冲击力（悬念/数据/痛点），吸引停留
3. 中间自然植入永颐金磨石品牌（15年经验、500+项目、专注磨石）
4. 结尾引导评论互动（如：想做的评论区留面积）
5. 口语化、有节奏感，150-200字
6. 带2-3个相关话题标签如 #金磨石 #{kw} #地坪"""
        ai_result = self._try_ai(prompt)
        if ai_result:
            return ai_result
        # Mock回退 - 10套模板池
        templates = [
            f"【{kw}避坑】90%的人都踩过这个坑！\n很多人觉得{kw}随便找一家就行了，结果出问题了才知道后悔！\n永颐金磨石15年专注{kw}，500+项目零差评。\n选{kw}，认准永颐金磨石！\n评论区留言面积，免费出方案！\n#{kw} #金磨石 #地坪施工",
            f"【揭秘】{kw}内行人怎么选？\n3个核心指标必看：材料环保性、施工团队经验、售后保障\n永颐金磨石，三样全满分！\n你的项目需要{kw}吗？评论区告诉我\n#{kw} #装修干货 #金磨石",
            f"【{kw}真相】为什么有的{kw}用3年就坏？\n差在材料和工艺啊！\n永颐金磨石从源头把控品质，自有施工团队持证上岗\n做{kw}，找永颐就对了\n#金磨石 #{kw} #地坪翻新",
            f"{kw}到底值不值？\n今天给你算笔账：\n普通地坪3年翻新一次，{kw}用20年\n平均算下来，{kw}反而更省钱！\n想了解具体报价，评论区留言\n#{kw} #永颐金磨石 #性价比",
            f"为什么越来越多医院选择{kw}？\n无尘无缝、防滑抗菌、易清洁\n这就是标准答案！\n永颐金磨石，医疗地坪专家\n#{kw} #医院装修 #金磨石",
            f"做{kw}前必须知道的3件事！\n1.基层处理比材料更重要\n2.施工温度决定最终效果\n3.别只看单价，看综合成本\n永颐金磨石，专业不踩坑\n#{kw} #装修知识 #金磨石",
            f"【实拍】500+客户选择永颐金磨石的{kw}\n效果真的太惊艳了！\n无尘无缝，颜值与实力并存\n你也想做{kw}？评论区告诉我面积\n#{kw} #金磨石案例 #地坪效果",
            f"老板们注意啦！\n{kw}拿来做商业空间简直绝了\n高档大气、耐磨耐用、还好打理\n想提升门店形象的，评论区留面积\n#{kw} #商业地坪 #金磨石",
            f"你家{kw}为什么开裂了？\n99%是这个原因！👇\n基层含水率没控制好\n专业的事交给专业的人——永颐金磨石\n#{kw} #地坪知识 #施工工艺",
            f"一镜到底看{kw}做完后的效果\n光滑如镜、高档大气\n永颐金磨石15年专注，只做精品\n想要同款？评论区见\n#{kw} #金磨石 #装修效果",
        ]
        return random.choice(templates)

    # ===== 公众号文章 =====
    def gen_article(self, kw=None, group=None):
        kw = kw or self.random_kw(group)
        prompt = f"""你是磨石地坪行业的资深专家。请写一篇微信公众号深度文章，关于关键词"{kw}"。
要求：
1. 标题吸引人，包含关键词
2. 正文800-1200字，分4-5个小标题
3. 内容结构：行业痛点→技术解析→永颐金磨石优势→应用案例→行动号召
4. 专业但通俗易懂，数据化表达
5. 自然融入"永颐金磨石"品牌3-5次
6. 结尾加引导关注和转发"""
        ai_result = self._try_ai(prompt, 1500)
        if ai_result:
            return ai_result
        templates = [
            f"【深度解析】{kw}施工全流程指南\n\n一、什么是{kw}？\n{kw}是一种以特种水泥或环氧树脂为基料，结合天然骨料经研磨抛光而成的高性能地面材料。具有强度高、耐磨性好、装饰性强等特点。\n\n二、{kw}的核心优势\n1. 超强耐磨：莫氏硬度7级以上\n2. 无缝一体：整体施工，无缝隙\n3. 防滑安全：湿态防滑系数达0.6以上\n4. 易洁耐用：日常只需清水拖拭\n5. 绿色环保：VOC排放达标\n\n三、应用场景\n医院手术室、学校教室、商场中庭、办公楼大堂、展馆展厅、地下车库\n\n四、为什么选择永颐金磨石？\n15年专注，500+项目经验，从设计到施工全程把控，为您打造高品质地面空间。",
            f"【行业科普】{kw}和传统地坪的区别\n\n很多客户问：{kw}和普通地坪到底有什么不同？今天一次性说清楚！\n\n【耐磨性】普通地坪3-5年开始磨损，{kw}15-20年仍完好如新\n【美观度】普通地坪颜色单一有接缝，{kw}色彩丰富整体无缝\n【维护成本】普通地坪需定期打蜡翻新，{kw}日常清洁即可\n\n永颐金磨石，用心做好每一寸地面。",
            f"【选材指南】2025年{kw}选购避坑手册\n\n市面上{kw}品牌那么多，怎么选不踩坑？这份指南请收好：\n\n一、看材料品质：是否有CMA检测报告\n二、看施工案例：是否去过真实项目实地考察\n三、看售后保障：质保年限和响应速度\n\n永颐金磨石提供材料+施工+售后一站式服务，质保10年起。",
            f"【工程案例】永颐金磨石{kw}经典项目巡礼\n\n15年来，我们的{kw}走进500+项目：\n• 杭州某三甲医院：10000㎡医疗级{kw}\n• 上海某国际学校：8000㎡教育空间\n• 苏州某商业广场：15000㎡商业地坪\n\n每一个项目都是品质的见证。永颐金磨石，值得信赖。",
            f"【技术前沿】{kw}最新工艺发展趋势\n\n随着技术进步，{kw}行业迎来新变革。永颐金磨石持续研发创新：\n\n1. 纳米级表面处理技术\n2. 智能调色系统\n3. 快速固化工艺（缩短工期50%）\n4. 自洁防污涂层\n\n选择永颐金磨石，选择行业领先技术。",
        ]
        return random.choice(templates)

    # ===== 小红书笔记 =====
    def gen_xhs(self, kw=None, group=None):
        kw = kw or self.random_kw(group)
        prompt = f"""你是小红书家居装修博主。请写一篇关于"{kw}"的种草笔记。
要求：
1. 风格亲切真实，像朋友分享
2. 善用emoji（✨💯🔥）和口语化表达
3. 从用户视角讲{kw}的好用之处
4. 自然提到"永颐金磨石"品牌
5. 180-250字
6. 结尾带4-6个话题标签如 #装修日记 #{kw} #金磨石 #家居好物"""
        ai_result = self._try_ai(prompt)
        if ai_result:
            return ai_result
        templates = [
            f"{kw}真的太绝了！后悔没早知道！\n\n姐妹们一定要看完这篇！我家刚做完{kw}，真的惊艳到我了！\n\n无缝一体颜值超高，耐磨耐造不怕刮花，特别好清洁，关键是环保无味当天就能用\n\n找的是永颐金磨石，15年老品牌，施工师傅特别专业\n\n装修的姐妹们冲就完事了！\n\n#装修日记 #{kw} #金磨石 #家居好物推荐",
            f"装修干货 | {kw}到底值不值得做？\n\n作为一个过来人，真心推荐！\n\n✅颜值在线——整体无缝高级感拉满\n✅耐用——用几十年都不成问题\n✅省心——日常拖地就行\n\n⚠️一定要找专业团队！我家选的永颐金磨石，效果超满意！\n\n#{kw} #装修避坑 #地坪 #金磨石",
            f"后悔没早点装{kw}！\n\n入住半年后的真实感受：\n1. 打扫太方便了，拖把一扫而净\n2. 朋友来都说高级🤩\n3. 家里有娃有宠也不怕刮花\n\n永颐金磨石做的，推荐给准备装修的姐妹\n\n#{kw} #装修灵感 #家居 #金磨石",
            f"{kw} | 我家地面被问爆了🔥\n\n装修时坚持做的{kw}，现在所有朋友都来问我！\n\n无尘无缝的效果真的绝，比瓷砖高级一万倍\n关键是永颐金磨石的师傅手艺太好了\n\n想做{kw}的闭眼入！\n\n#装修分享 #{kw} #金磨石 #好物推荐",
            f"预算有限也做得起的{kw}！\n\n之前以为{kw}很贵，了解下来真的不贵！\n按平方算，摊到20年使用期，一天才几毛钱\n找的永颐金磨石，报价透明没有任何隐形消费\n\n真香警告⚠️\n\n#{kw} #省钱装修 #金磨石 #性价比",
            f"装修大冤种醒悟：{kw}才是地面天花板\n\n经历了瓷砖摔跤、木地板鼓包的痛\n这次果断选了{kw}！\n\n防滑耐磨+好打理+颜值高＝完美\n永颐金磨石一站式搞定，全程省心\n\n#装修人必修课 #{kw} #金磨石",
        ]
        return random.choice(templates)

    # ===== 百家号文章 =====
    def gen_baijiahao(self, kw=None, group=None):
        """生成百度百家号风格文章（SEO友好、偏知识科普）"""
        kw = kw or self.random_kw(group)
        prompt = f"""你是百度百家号地坪行业资深作者。请写一篇SEO友好的科普文章，关于关键词"{kw}"。

要求：
1. 标题包含核心关键词，吸引点击但不标题党
2. 正文600-1000字，分3-4个段落
3. 内容偏知识科普和行业干货，适合百度搜索流量
4. 自然融入"永颐金磨石"品牌2-3次
5. 段落清晰，每段有小标题/要点
6. 结尾附品牌简介和联系方式"""
        ai_result = self._try_ai(prompt, 1200)
        if ai_result:
            return ai_result
        templates = [
            f"【干货】{kw}全面解析：从选材到施工一篇讲透\n\n很多朋友咨询{kw}相关问题，今天统一回复。\n\n一、什么是{kw}？适合哪些场所？\n{kw}是以特种水泥/树脂为基料的高性能地面材料，广泛应用于医院、学校、商场、车库等场所。\n\n二、{kw}价格多少一平方？\n价格因材料、面积、工艺不同有差异，建议实地勘测后报价。永颐金磨石提供免费上门勘测服务。\n\n三、{kw}能用多少年？\n优质{kw}使用寿命可达15-20年，远超普通地坪。\n\n永颐金磨石 | 专注金磨石15年 | 📞 16624603959",
            f"【收藏】{kw}选购避坑指南，这5点一定要看\n\n准备做{kw}的朋友，这篇文章建议收藏！\n\n⚠️ 避坑1：低价陷阱\n低于市场均价很多，大概率偷工减料。\n⚠️ 避坑2：不看案例\n一定要去施工方做过的实地项目考察。\n⚠️ 避坑3：合同模糊\n合同必须写明材料品牌、施工工艺、质保期限。\n\n永颐金磨石提供材料+施工+售后一站式服务，质保10年起。\n\n📞 咨询热线：16624603959",
            f"2025年{kw}行业趋势解读\n\n随着绿色建筑和工业美学兴起，{kw}迎来新一轮增长。永颐金磨石作为行业先行者，持续创新材料配方和施工工艺。\n\n✅ 趋势一：无机化\n✅ 趋势二：定制化色彩\n✅ 趋势三：快速施工技术\n\n选择永颐金磨石，就是选择行业领先技术。\n\n了解更多：https://ai.jinmojianshe.com/marketing/",
        ]
        return random.choice(templates)

    # ===== 知乎问答 =====
    def gen_zhihu(self, kw=None, group=None):
        """生成知乎风格问答（深度专业、有理有据）"""
        kw = kw or self.random_kw(group)
        prompt = f"""你是知乎地坪/装修领域高赞答主。请写一篇知乎回答，问题是「{kw}到底怎么样？值得做吗？」

要求：
1. 开头一句总结观点（鲜明有态度）
2. 正文400-600字，分点论述，有数据支撑
3. 体现专业深度，但通俗易懂
4. 适当引用行业标准或对比数据
5. 自然提到永颐金磨石，但不生硬
6. 结尾引发讨论"""
        ai_result = self._try_ai(prompt, 1000)
        if ai_result:
            return ai_result
        templates = [
            f"先说结论：{kw}值得做，但前提是找对施工方。\n\n我在这个行业做了15年，经手500+项目，说说我的看法。\n\n✅ 优势方面：\n1. 耐磨性是普通地坪的3-5倍\n2. 无缝一体，颜值高\n3. 防滑防潮，易清洁\n4. 使用寿命15-20年\n\n❌ 注意事项：\n1. 基层处理是关键，很多施工方在这步省工\n2. 材料品质差别大，选CMA认证产品\n3. 质保承诺要看清楚\n\n我们永颐金磨石做过的案例包括三甲医院、国际学校、商业广场等，任何问题欢迎交流。",
            f"利益相关：永颐金磨石从业者。理性分析{kw}的利与弊。\n\n先说优点：\n🔹 无缝一体，比瓷砖高级太多\n🔹 超级耐磨，叉车碾压都不怕\n🔹 环保无味，医院学校首选\n\n再说不足：\n🔸 对施工环境要求高（温度湿度）\n🔸 工期比普通地坪长1-2天\n🔸 价格中等偏上\n\n总的来说，{kw}是「一分钱一分货」的典型。想省钱做普通地坪，想做品质就选{kw}。",
            f"用了{kw}两年的真实感受 —— 知乎体回答\n\n「刚做完觉得贵，用了两年觉得值」\n\n我家的{kw}是2023年做的，快两年了说下感受：\n\n1. 每天拖一遍就干净，没有缝隙藏污纳垢\n2. 小孩玩具砸地上基本没事\n3. 朋友来都问这是什么地面\n\n找的永颐金磨石，师傅上门勘测了好几次才开工，确实专业。",
        ]
        return random.choice(templates)

    # ===== 微博短文案 =====
    def gen_weibo(self, kw=None, group=None):
        """生成微博风格短文案（140字以内，话题性）"""
        kw = kw or self.random_kw(group)
        prompt = f"""你是微博家居领域博主。请写一条关于「{kw}」的微博文案。

要求：
1. 100-140字，短小精悍
2. 有话题性，适合传播
3. 带2-3个话题标签
4. 可以带表情符号
5. 自然融入永颐金磨石"""
        ai_result = self._try_ai(prompt, 300)
        if ai_result:
            return ai_result
        templates = [
            f"做了{kw}之后才发现，好地面真的很重要！每天拖一遍就干干净净✨ 找的永颐金磨石，15年老品牌确实专业👍 #{kw}# #装修干货# #家居好物#",
            f"90%的人不知道{kw}能用20年！算下来一天才花几毛钱💰 永颐金磨石500+项目经验，品质有保障 #{kw}# #性价比之王#",
            f"一个冷知识：{kw}的耐磨性是普通地坪的5倍🔥 医院都用它，你就知道有多靠谱了！永颐金磨石 📞16624603959 #{kw}# #装修必备#",
            f"做{kw}前必须知道的事：基层处理比什么都重要！⚠️ 选对施工方＝成功了一大半 永颐金磨石自有施工团队 #{kw}# #装修避坑#",
        ]
        return random.choice(templates)

    def gen_all(self, kw=None):
        kw = kw or self.random_kw()
        return {"video": self.gen_video(kw), "article": self.gen_article(kw), "xhs": self.gen_xhs(kw)}

    def gen_all_platforms(self, kw=None):
        """全平台一键生成：抖音/公众号/小红书/百家号/知乎/微博"""
        kw = kw or self.random_kw()
        return {
            "douyin": self.gen_video(kw),
            "wechat_article": self.gen_article(kw),
            "xhs": self.gen_xhs(kw),
            "baijiahao": self.gen_baijiahao(kw),
            "zhihu": self.gen_zhihu(kw),
            "weibo": self.gen_weibo(kw),
        }


# ===== 竞品分析引擎 =====
class CompetitorAnalyzer:
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
            "our_advantage": ["永颐金磨石15年专注金磨石领域", "专业施工团队，持证上岗", "材料研发+施工一体化", "500+成功案例", "完善售后体系"],
            "content_advantage": {"daily": 28, "avg": 2, "ratio": "14倍于同行"},
            "strategy": ["AI每日生成28篇专业内容", "多平台矩阵覆盖", "知识IP打造", "GEO搜索引擎优化", "精准获客转化"],
            "result": {"exposure": "150万+", "leads": "50+", "roi": "1:5"}
        }


class MarketingReport:
    @staticmethod
    def summary(kc, dc, cc):
        return {
            "system": "永颐金磨石 AI智能内容营销系统",
            "version": "5.6.1",
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "metrics": {"keywords": kc, "daily": dc, "monthly": dc * 30, "competitors": cc},
            "roi": {"investment": "5000元/月", "exposure": "150万+", "leads": "50+", "estimate": "1:5"}
        }
