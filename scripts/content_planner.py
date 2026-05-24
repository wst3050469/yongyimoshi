"""
永颐无机磨石 · 抖音内容排期生成器
基于网站内容资产自动生成4号矩阵的周内容计划

用法:
  python3 scripts/content_planner.py         # 生成本周排期
  python3 scripts/content_planner.py --push   # 生成+推送到企业微信
  python3 scripts/content_planner.py --week 2 # 指定下周
"""

import sys
import json
import os
from datetime import datetime, timedelta

# ============================================================
# 内容资产库（从网站现有页面提取）
# ============================================================

FAQS = [
    ("无机磨石和环氧磨石哪个好？", "环保/防火/耐磨/价格四维对比，帮你选"),
    ("无机磨石多少钱一平？", "120-280元/㎡三档价位详解"),
    ("无机磨石能用多少年？", "规范施工20年+，每3-5年密封固化"),
    ("旧地面可以直接做无机磨石吗？", "需凿除旧面层+修补裂缝+重新找平"),
    ("无机磨石施工要多久？", "标准工期22天，9道工序详解"),
    ("无机磨石会开裂吗？", "规范施工不会开裂，关键在于基层处理"),
    ("无机磨石可以做彩色吗？", "无机颜料调色，纯色/水磨石/艺术拼花都可以"),
    ("无机磨石和瓷砖怎么选？", "磨石无缝整体，瓷砖施工快，看场景选"),
]

CASES = [
    ("五星酒店大堂磨石·5000㎡环氧磨石艺术拼花", "酒店"),
    ("三甲医院无机磨石·12000㎡门诊+住院部", "医院"),
    ("大型会展中心·25000㎡大面无缝施工", "会展"),
    ("商业综合体·8000㎡环氧磨石色彩分区", "商业"),
    ("大学图书馆·6000㎡浅色无机磨石", "教育"),
    ("总部办公楼·4000㎡企业VI色设计", "办公"),
]

PROCESS_STEPS = [
    ("基层处理·3天", "清理修补找平，强度C25以上"),
    ("抗裂砂浆·5天", "30-50mm厚，6m分隔缝"),
    ("基层养护·7天", "保湿养护，每天洒水2-3次"),
    ("界面处理·1天", "涂刷界面剂增强粘结"),
    ("面层浇筑·3天", "15mm厚无机磨石，刮尺找平"),
    ("面层养护·7天", "保湿养护，避免重压"),
    ("打磨抛光·2天", "粗磨50目→中磨200目→精磨800目"),
    ("密封固化·1天", "提高硬度/耐磨/防污"),
]

KNOWLEDGE = [
    ("抗压强度≥60MPa意味着什么？", "耐磨/承重/耐用全面解析"),
    ("无机磨石的环保标准", "零VOC/A级防火/无甲醛"),
    ("密封固化剂的作用原理", "渗透反应生成致密结构"),
    ("光泽度70GU和85GU的区别", "不同场景对亮度的要求"),
]

TOOL_FEATURES = [
    ("工序看板·可视化", "9道工序状态一目了然"),
    ("材料自动计算", "输入面积自动算用量"),
    ("质量检测追踪", "检测记录+自动提醒"),
    ("环境监测", "温湿度/含水率趋势图"),
]

# 账号配置
ACCOUNTS = [
    {"id": "A", "name": "行业专家", "emoji": "🔴", "style": "行业洞察", "color": "蓝底"},
    {"id": "B", "name": "工地实拍", "emoji": "🟡", "style": "实拍展示", "color": "工地背景"},
    {"id": "C", "name": "知识科普", "emoji": "🟢", "style": "选材对比", "color": "白底"},
    {"id": "D", "name": "工具种草", "emoji": "🔵", "style": "平台演示", "color": "灰底"},
]

DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
HASHTAGS = "#无机磨石 #金磨石 #地坪施工"


def generate_weekly_plan(week_offset=0):
    """生成一周排期"""
    today = datetime.now()
    # 找到本周一
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    
    plan = []
    
    # 每天4个账号各1条
    for day_idx, day_name in enumerate(DAYS):
        date = monday + timedelta(days=day_idx)
        date_str = date.strftime("%m/%d")
        
        day_plan = {"date": f"{day_name} {date_str}", "accounts": []}
        
        for acc in ACCOUNTS:
            # 根据账号类型从不同素材库取内容
            if acc["id"] == "A":  # 专家 - 行业洞察
                idx = (day_idx * 2) % len(KNOWLEDGE)
                topic, sub = KNOWLEDGE[idx]
                hook = f"干了{15+day_idx}年磨石，说句大实话"
                body = f"{topic}：{sub}"
                cta = "你觉得呢？评论区说说"
                
            elif acc["id"] == "B":  # 工地 - 实拍展示
                if day_idx % 2 == 0:
                    idx = (day_idx // 2) % len(PROCESS_STEPS)
                    topic, sub = PROCESS_STEPS[idx]
                    hook = f"磨石施工第{idx+1}步，很多人都做错了"
                else:
                    idx = (day_idx // 2) % len(CASES)
                    topic, sub = CASES[idx]
                    hook = f"看看我们刚做完的项目"
                body = f"{topic}：{sub}"
                cta = "想看更多案例的关注我"
                
            elif acc["id"] == "C":  # 科普 - 选材对比
                idx = day_idx % len(FAQS)
                topic, sub = FAQS[idx]
                hook = f"粉丝问得最多的一个问题"
                body = f"{topic}：{sub}"
                cta = "还有疑问的评论区留言"
                
            else:  # D - 工具演示
                idx = day_idx % len(TOOL_FEATURES)
                topic, sub = TOOL_FEATURES[idx]
                hook = f"一个功能帮你省掉一半管理时间"
                body = f"{topic}：{sub}"
                cta = "想体验的发私信'平台'"
            
            day_plan["accounts"].append({
                "account": f"{acc['emoji']} 号{acc['id']}·{acc['name']}",
                "style": acc["style"],
                "hook": hook,
                "body": body,
                "cta": cta,
                "tags": HASHTAGS,
            })
        
        plan.append(day_plan)
    
    return plan


def format_markdown(plan, week_offset=0):
    """格式化为Markdown排期"""
    lines = [f"# 📅 永颐无机磨石 · 第{datetime.now().isocalendar()[1] + week_offset}周内容排期"]
    lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    
    for day_plan in plan:
        lines.append(f"---")
        lines.append(f"## 📆 {day_plan['date']}")
        lines.append("")
        
        for acc in day_plan["accounts"]:
            lines.append(f"### {acc['account']}")
            lines.append(f"**风格**: {acc['style']}")
            lines.append("")
            lines.append(f"【钩子】{acc['hook']}")
            lines.append(f"【内容】{acc['body']}")
            lines.append(f"【引导】{acc['cta']}")
            lines.append(f"【标签】{acc['tags']}")
            lines.append("")
    
    return "\n".join(lines)


def push_to_webhook(plan_md, account_name=""):
    """把排期推送到企业微信/钉钉"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        os.environ['SECRET_KEY'] = 'content-planner'
        from webhook import send_notification
        
        # 截取前500字（避免消息太长）
        preview = plan_md[:800] + "\n\n... 完整排期见 docs/content/"
        
        result = send_notification(
            title=f"📅 本周抖音内容排期已生成",
            message=preview,
            notif_type="daily_log",
            project_name=account_name
        )
        return result
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    week_offset = 0
    do_push = False
    
    for arg in sys.argv[1:]:
        if arg == "--push":
            do_push = True
        elif arg.startswith("--week"):
            week_offset = int(arg.split("=")[-1]) if "=" in arg else 1
    
    plan = generate_weekly_plan(week_offset)
    md = format_markdown(plan, week_offset)
    
    # 输出到文件
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "content")
    os.makedirs(output_dir, exist_ok=True)
    
    week_num = datetime.now().isocalendar()[1] + week_offset
    output_file = os.path.join(output_dir, f"week-{week_num}-plan.md")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md)
    
    print(f"✅ 第{week_num}周排期已生成 → docs/content/week-{week_num}-plan.md")
    print(f"📊 共 {len(plan)} 天 × 4 账号 = {len(plan)*4} 条脚本")
    
    if do_push:
        result = push_to_webhook(md)
        print(f"📨 Webhook推送结果: {result}")
