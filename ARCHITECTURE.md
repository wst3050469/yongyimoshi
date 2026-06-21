# 永颐金磨石 AI智能内容营销系统 — 架构与技术方案

## 一、系统概述

为永颐金磨石打造的「挖掘→生成→审核→发布→跟踪」全链路AI营销平台。
部署于阿里云 ECS (47.110.126.148)，Flask + DeepSeek AI + 豆包Seedance 视频生成。

## 二、系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx (HTTPS)                        │
│          ai.jinmojianshe.com/marketing/ → :5050         │
├─────────────────────────────────────────────────────────┤
│                   app.py (Flask路由层)                   │
│  认证(before_request) │ 34个API端点 │ CORS │ 错误处理    │
├──────────┬──────────┬──────────┬──────────┬────────────┤
│ keyword  │marketing │ publish  │analytics │  video_gen │
│ _miner   │_system   │_engine   │_tracker  │  +wechat   │
├──────────┴──────────┴──────────┴──────────┴────────────┤
│                  AIClient (DeepSeek)                    │
├─────────────────────────────────────────────────────────┤
│              data/*.json (持久化存储)                    │
└─────────────────────────────────────────────────────────┘
```

### 模块职责

| 模块 | 文件 | 行数 | 核心职责 |
|------|------|------|---------|
| 路由控制 | `app.py` | 453行 | Flask路由、Session认证、CORS |
| AI客户端 | `marketing_system.py` | 280行 | DeepSeek API封装 + 6平台内容生成 |
| 关键词引擎 | `keyword_miner.py` | 366行 | AI Agent 4轮深度挖掘 + 持久化词池 |
| 发布引擎 | `publish_engine.py` | 158行 | 审核工作流(待审→通过/驳回→已发布) |
| 效果跟踪 | `analytics_tracker.py` | 160行 | 浏览量/互动率/7天趋势/Top排行 |
| 内容存储 | `content_store.py` | 85行 | JSON持久化，支持7种内容类型 |
| 视频生成 | `video_generator.py` | 189行 | 豆包Seedance API + 后台轮询 |
| 微信处理 | `wechat_handler.py` | 154行 | 公众号消息签名验证+关键词回复 |

## 三、核心技术方案

### 3.1 AI Agent关键词挖掘

**问题**：如何自动挖尽所有相关关键词和长尾词？

**方案**：AI Agent 多轮管线式挖掘
```
种子词 → [语义扩展] → [长尾词生成] → [问答挖掘] → [竞品分析] → [平台热词] → 去重词池
```

每轮使用独立的 System Prompt 引导 DeepSeek 扮演不同角色：
- R1 语义扩展：SEO分析师视角，扩展同义词、关联术语
- R2 长尾词：用户搜索行为视角，场景/地域/对比/购买意图组合
- R3 问答挖掘：知乎/百度知道视角，怎么/为什么/哪个好
- R4 竞品挖掘：竞争情报视角，品牌对比/排名/口碑

**容错**：每轮AI失败时自动回退预置Mock词库(50+词)，确保零中断。

**持久化**：所有挖掘结果存入 `data/kw_pool.json`，自动去重，热度评分排序，跨会话累积。

### 3.2 多平台内容生成

**问题**：不同平台调性差异大，如何自动适配？

**方案**：每个平台独立 Prompt 模板 + 角色化 AI 设定

| 平台 | AI角色 | 字数 | 特征 |
|------|--------|------|------|
| 抖音 | 金牌营销总监 | 150-200字 | 3秒冲击力开头、引导评论互动、话题标签 |
| 公众号 | 行业资深专家 | 800-1200字 | 4-5小标题、痛点→技术→优势→案例 |
| 小红书 | 家居装修博主 | 180-250字 | emoji、口语化、种草分享、4-6标签 |
| 百家号 | SEO科普作者 | 600-1000字 | 知识干货、搜索友好、品牌植入 |
| 知乎 | 高赞答主 | 400-600字 | 观点鲜明、数据支撑、引发讨论 |
| 微博 | 家居博主 | 100-140字 | 短小精悍、话题传播、表情符号 |

**技术实现**：
- `gen_video(kw)` / `gen_article(kw)` / `gen_xhs(kw)` — 单平台生成
- `gen_all_platforms(kw)` — 全平台一键生成
- AI模式(Mock回退)双轨制，确保AI不可用时服务不中断

### 3.3 发布审核工作流

**问题**：AI生成内容质量不可控，需要人工把关。

**方案**：状态机驱动的审核工作流
```
   ┌──────────────────────────────────┐
   │          submit_for_review()     │
   │               ↓                  │
   │  ┌──────────────────────┐       │
   │  │      pending          │       │
   │  │      (待审核)          │       │
   │  └──────┬───────────────┘       │
   │         │                       │
   │    ┌────▼────┐    ┌────────┐    │
   │    │ approve │    │ reject │    │
   │    │ (通过)  │    │ (驳回) │    │
   │    └────┬────┘    └────────┘    │
   │         │                       │
   │    ┌────▼────┐                  │
   │    │ publish │                  │
   │    │ (发布)  │                  │
   │    └─────────┘                  │
   └──────────────────────────────────┘
```

**数据模型**：
```json
{
  "id": "uuid8",
  "platform": "douyin",
  "title": "...",
  "content": "...",
  "status": "pending|approved|rejected|published",
  "submitted_at": "ISO8601",
  "reviewed_at": "ISO8601",
  "published_at": "ISO8601",
  "review_comment": "...",
  "publish_url": "..."
}
```

**API设计**：
- `POST /api/publish/submit` — 提交审核
- `POST /api/publish/batch-submit` — 批量提交
- `GET /api/publish/queue?status=pending` — 查看队列
- `POST /api/publish/approve` — 审核通过
- `POST /api/publish/reject` — 驳回
- `POST /api/publish/publish` — 标记发布

### 3.4 效果数据跟踪

**问题**：发布后如何衡量内容效果？

**方案**：手动录入 + 自动计算 + 多维度统计

**数据模型**：
```json
{
  "publish_id": "关联发布记录",
  "platform": "平台",
  "views": 1500, "likes": 120, "comments": 15,
  "shares": 30, "saves": 45,
  "engagement": 210,
  "engagement_rate": 14.0
}
```

**统计维度**：
- 综合看板：总浏览量、总互动、内容数、平均互动率
- 各平台统计：分平台汇总对比
- 7天趋势：按日统计浏览和互动变化
- Top排行：浏览量Top5、互动量Top5
- 单条详情：指定内容的效果数据

## 四、数据存储方案

采用 JSON 文件持久化（轻量级，无需数据库）：

| 文件 | 内容 | 容量 |
|------|------|------|
| `content_history.json` | 所有生成内容 | ~870KB / 360条 |
| `publish_queue.json` | 发布审核队列 | ~2KB |
| `analytics_data.json` | 效果数据 | ~1KB |
| `video_tasks.json` | 视频生成任务 | ~4KB |
| `mined_keywords.json` | 挖掘历史批次 | ~33KB |
| `kw_pool.json` | 去重关键词池 | ~5KB / 76词 |

## 五、部署架构

```
用户 → Nginx(HTTPS) → Flask(:5050) → DeepSeek API
                                     → 豆包Seedance API
                                     → 微信公众号API
```

- **服务器**: 阿里云 ECS 47.110.126.148
- **进程管理**: systemd (`yongyimoshi.service`)
- **反向代理**: Nginx 剥离 `/marketing/` 前缀
- **环境变量**: `.env` 文件管理 AI_API_KEY/AI_API_BASE/AI_MODEL
- **认证**: Flask Session + 密码 (`liu201314`)

## 六、API端点全览 (34个)

| 类别 | 端点数 | 关键端点 |
|------|--------|---------|
| 认证 | 3 | login, logout, check-auth |
| 关键词 | 4 | keywords CRUD, ai-mine, agent-mine, mined-pool |
| 内容生成 | 2 | generate, generate/all-platforms |
| 内容管理 | 2 | contents (GET/DELETE) |
| 竞品分析 | 2 | competitors, analysis |
| 报告 | 1 | report |
| 视频 | 3 | video/create, video/status/:id, video/tasks |
| 发布审核 | 7 | submit, batch-submit, queue, approve, reject, publish, stats |
| 效果跟踪 | 5 | record, dashboard, content/:id, records, platform-stats |
| 微信 | 2 | wechat/message |
| 系统 | 2 | /, health |

## 七、关键技术决策

| 决策 | 理由 |
|------|------|
| JSON文件存储 | 轻量、零依赖、直接可读、适合中小规模 |
| AI+Mock双轨制 | AI不可用时自动回退，保证服务100%可用 |
| Session认证 | 简单可靠，白名单机制保护公开端点 |
| 多轮Agent挖掘 | 比单次Prompt产出更全面，覆盖语义/长尾/问答/竞品 |
| 状态机审核流 | 明确的流转规则，防止越权操作 |
| 手动效果录入 | 通用方案，后续可扩展各平台API自动抓取 |

## 八、扩展方向

- **真实平台对接**: 抖音开放平台OAuth → 直接发布
- **自动化调度**: APScheduler定时挖掘+定时发布
- **微信通知**: 审核状态变更 → 管理员微信提醒
- **数据可视化**: ECharts图表替换纯文本统计
- **用户权限**: 多角色(管理员/编辑/审核员)
