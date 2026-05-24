#!/bin/bash
# 永颐无机磨石 · 快速生成抖音脚本模板
# 用法: bash scripts/quick_script.sh <主题>

echo "======================================"
echo " 永颐无机磨石 · 抖音脚本生成器"
echo "======================================"
echo ""

cat << 'TEMPLATE'
【标题】: ${1:-请输入主题}
【时长】: 30秒
【类型】: □ 知识科普 □ 实拍展示 □ 案例分享 □ 工具演示

【视频结构】

前3秒（钩子）:
""

中间（核心内容）:
""

最后5秒（引导）:
""

【画面描述】:
1. 
2. 
3. 

【字幕重点】:
• 
• 
• 

【话题标签】:
#无机磨石 #金磨石 #地坪施工 

【BGM建议】:
□ 轻快 □ 正式 □ 舒缓 □ 科技感
TEMPLATE

echo "======================================"
echo "提示: 从网站页面提取素材:"
echo "  FAQ → faq.html"
echo "  工艺 → construction_process.html"
echo "  案例 → cases.html"
echo "  知识 → knowledge-base.html"
echo "  对比 → guide-compare.html"
echo "  价格 → guide-budget.html"
echo "======================================"
