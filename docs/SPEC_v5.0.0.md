# AI智能内容营销系统 v5.0.0 - 技术规格

## 概述
永颐金磨石AI智能内容营销系统，提供关键词管理、AI内容生成、竞品分析、综合报告功能。

## 架构
- 后端: Flask (Python3)
- 前端: HTML + JavaScript (原生)
- 部署: systemd + Nginx反向代理
- 服务器: 47.110.126.148:5050
- 访问: https://ai.jinmojianshe.com/marketing/

## 核心模块

### 1. KeywordEngine (关键词引擎)
- 6大分类: 品牌词/产品词/场景词/工艺词/痛点词/竞品词
- 每类5+种子关键词
- 方法: get_kws(), add_keyword(), random_kw(), gen_video(), gen_article(), gen_xhs()

### 2. CompetitorAnalyzer (竞品分析)
- 默认3个竞品
- 方法: get_comps(), add_comp(), surpass()
- 输出: 优势分析/内容策略/ROI评估

### 3. MarketingReport (综合报告)
- 方法: summary(kc, dc, cc)
- 输出: 系统状态/流量指标/ROI分析

## API接口

| 端点 | 方法 | 参数 | 说明 |
|------|------|------|------|
| /api/keywords | GET | - | 获取关键词列表 |
| /api/keywords | POST | {"action":"add","keyword":"xxx"} | 添加关键词 |
| /api/generate | POST | {"keyword":"xxx","group":"xxx"} | 生成内容 |
| /api/competitors | GET | - | 获取竞品列表 |
| /api/competitors | POST | {"url":"xxx"} | 添加竞品 |
| /api/analysis | GET | - | 竞品分析 |
| /api/report | POST | {"type":"monthly"} | 生成报告 |

## 部署配置
- Systemd服务: yongyi-marketing.service
- 自动重启: enabled
- 日志: journalctl -u yongyi-marketing.service
