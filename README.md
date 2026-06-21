# 永颐金磨石 AI智能内容营销系统 v5.0.0

永颐金磨石品牌AI智能内容营销系统，自动生成多平台营销内容。

## 功能模块

### 关键词引擎
- 6大分类：品牌词/产品词/场景词/工艺词/痛点词/竞品词
- 30+种子关键词，支持动态添加
- 自动生成多平台内容

### AI内容生成
- **抖音脚本**: 爆款标题+口播文案+行动号召
- **公众号文章**: 深度解析+施工流程+核心优势
- **小红书笔记**: 种草文案+话题标签

### 竞品分析
- 默认3个竞品跟踪
- 优势/劣势对比分析
- 超越策略建议
- ROI预估

### 综合报告
- 周报/月报/季报/年报
- 关键词覆盖统计
- 内容产出分析
- ROI投资回报评估

## 技术架构

| 组件 | 技术 |
|------|------|
| 后端 | Flask (Python3) |
| 前端 | 原生HTML + JavaScript |
| 部署 | systemd + Nginx反向代理 |
| 服务器 | 47.110.126.148:5050 |
| 域名 | https://ai.jinmojianshe.com/marketing/ |

## API文档

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/` | GET | 管理面板 |
| `/api/keywords` | GET/POST | 关键词管理 |
| `/api/generate` | POST | 内容生成 |
| `/api/competitors` | GET/POST | 竞品管理 |
| `/api/analysis` | GET | 竞品分析 |
| `/api/report` | POST | 综合报告 |

## 快速部署

```bash
# 启动服务
systemctl start yongyi-marketing.service

# 查看状态
systemctl status yongyi-marketing.service

# 查看日志
journalctl -u yongyi-marketing.service -f
```

## 开发信息

- 仓库: https://github.com/wst3050469/yongyimoshi
- 版本: v5.0.0
- 授权: 永颐科技
