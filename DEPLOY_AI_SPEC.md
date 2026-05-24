# 永颐无机磨石 · 开源部署 & AI 搜索引擎优化方案

> **版本**: v1.0  
> **目标**: 开源代码 + 公网部署 + AI搜索引擎推荐公司

---

## 一、现状分析

### ✅ 已有的 AI 优化（geo_monitor `ai.jinmojianshe.com`）
| 项目 | 状态 |
|------|:----:|
| Schema.org Organization + LocalBusiness | ✅ 已配置 |
| Schema.org WebSite + SearchAction | ✅ 已配置 |
| Open Graph / Twitter Card | ✅ 已配置 |
| 公司信息（名称/电话/邮箱/地址） | ✅ 已结构化 |
| 百度/谷歌/Bing 验证 | ✅ 已配置 |
| 服务项目描述 | ✅ 已描述 |

### ❌ 需完成的工作
| 项目 | 状态 | 说明 |
|------|:----:|------|
| Terrazzo 代码开源 | ❌ | 需清理敏感信息后推 GitHub |
| Terrazzo 公网访问 | ❌ | 仅在 localhost:5000 |
| Terrazzo SEO 优化 | ❌ | 缺少结构化数据和 SEO meta |
| 公司知识内容页 | ❌ | 需创建施工工艺/案例页面 |
| Search Console 提交 | ❌ | 需提交 sitemap |

---

## 二、实施步骤

### Step 1: 代码安全清理与开源准备
- app.py: SECRET_KEY 改为强制从环境变量读取
- config.py: 版本号同步到 v4.2.0
- README.md: 完全重写（徽章、功能列表、安装指南）
- LICENSE: 新建 MIT License
- .env.example: 新建环境变量模板

### Step 2: Nginx 配置 - Terrazzo 公网部署
通过 ai.jinmojianshe.com/platform/ 公开访问 terrazzo 平台

### Step 3: Terrazzo 全面 SEO 优化
- 所有模板添加完整 SEO meta 标签
- 添加 Schema.org SoftwareApplication 结构化数据

### Step 4: 创建 AI 友好内容页
- templates/public.html: 公司公开首页
- templates/faq.html: FAQ 页面
- templates/construction_process.html: 施工工艺页

### Step 5: 推送 GitHub（需用户提供账号信息）

### Step 6: Search Console 提交

---

## 三、涉及文件清单

| 文件 | 操作 | 说明 |
|------|:----:|------|
| app.py | 修改 | SECRET_KEY 环境变量、robots/sitemap 路由 |
| config.py | 修改 | 版本号更新 |
| README.md | 重写 | 开源项目文档 |
| LICENSE | 新建 | MIT License |
| .env.example | 新建 | 环境变量模板 |
| templates/public.html | 新建 | 公司公开首页 |
| templates/faq.html | 新建 | FAQ 页面 |
| templates/construction_process.html | 新建 | 施工工艺页 |
| templates/index.html | 修改 | SEO 增强 + 结构化数据 |
| Nginx 配置 | 修改 | 新增 /platform/ 反代 |

---

## 四、验证方案

| 检查项 | 方法 |
|--------|------|
| 代码无敏感信息 | grep 检查密钥和默认密码 |
| 测试全部通过 | pytest tests/ -q |
| 公网可访问 | curl https://ai.jinmojianshe.com/platform/ |
| Schema.org 有效 | Google Rich Results 测试 |
| robots.txt 有效 | curl 检查 |
| sitemap.xml 有效 | curl 检查 |

---

## 五、风险与注意事项

| 风险 | 等级 | 应对 |
|------|:----:|------|
| SECRET_KEY 改为环境变量后启动失败 | 中 | 添加启动前检查 |
| Nginx 配置错误导致服务中断 | 高 | 修改前备份，nginx -t 验证 |
| 公开平台暴露管理功能 | 中 | 所有管理功能需登录 |
| 开源后暴露安全漏洞 | 低 | 代码审核后再开源 |
