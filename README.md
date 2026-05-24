# 🏗️ 永颐无机磨石 · 施工管理平台

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-green)
![SQLite](https://img.shields.io/badge/SQLite-3-orange)
![Tests](https://img.shields.io/badge/Tests-142%20passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Version](https://img.shields.io/badge/Version-4.4.1-red)

**浙江永颐装饰工程有限公司 · 无机磨石施工全过程数字化管理平台**

[功能概览](#-功能概览) • [快速开始](#-快速开始) • [技术栈](#-技术栈) • [项目结构](#-项目结构) • [API文档](#-api文档) • [部署指南](#-部署指南)

</div>

---

## 📖 项目简介

永颐无机磨石施工管理平台是一款专为**无机磨石 / 金磨石地坪工程**打造的数字化施工管理工具。系统覆盖从材料计算、进度管理、质量检测到竣工验收的全流程，帮助施工团队提升效率、保障质量。

### 适用场景

- 🏨 **酒店/民宿** — 大堂、走廊、客房区域磨石施工
- 🏥 **医院** — 洁净地坪施工管理
- 🏛️ **展厅/展馆** — 大面积艺术磨石工程
- 🏢 **商业空间** — 商场、办公楼地坪项目

---

## ✨ 功能概览

### 📐 施工前
| 功能 | 说明 |
|------|------|
| **材料自动计算** | 输入面积、厚度，自动计算基层/面层材料用量 |
| **采购清单生成** | 一键生成材料采购清单 |
| **进度计划编排** | 22天标准工期计划，支持自定义 |

### 📝 施工中
| 功能 | 说明 |
|------|------|
| **施工日志** | 每日施工记录，支持文字+照片 |
| **工序看板** | 9道标准工序可视化流转（卡片式看板） |
| **质量检测** | 检测记录录入 + 数据趋势图表 |
| **环境监测** | 温湿度/含水率记录与趋势图表 |
| **照片墙** | 施工照片管理，支持批量上传 + Lightbox 查看 |
| **安全检查** | 安全检查记录与整改追踪 |

### 📊 施工后
| 功能 | 说明 |
|------|------|
| **项目仪表盘** | 一页尽览项目全局（面积/进度/质量） |
| **PDF报告导出** | 施工方案一键导出为PDF |
| **数据可视化** | Chart.js 交互式图表（仪表盘 + 分析看板） |
| **CSV数据导出** | 项目/日志/材料/工人等9种数据导出 |

### 👥 管理功能
| 功能 | 说明 |
|------|------|
| **工人班组管理** | 工人信息、班组管理、花名册导出 |
| **供应商管理** | 供应商信息、合作记录 |
| **设备管理** | 施工设备台账 |
| **分包商管理** | 分包商评估与管理 |
| **材料库存** | 材料入库/出库/盘点 |
| **成本预算追踪** | 预算编制与执行跟踪 |
| **通知提醒系统** | 养护提醒、检测提醒 |

### 🔧 系统功能
| 功能 | 说明 |
|------|------|
| **用户认证** | 登录/登出、角色权限控制（管理员/普通用户） |
| **全局搜索** | 跨模块统一搜索（项目/日志/供应商/工人/设备） |
| **暗色模式** | 全页面暗色/浅色主题切换，零闪烁 |
| **响应式设计** | 3层断点适配桌面/平板/手机 |
| **数据恢复** | 自动备份 + 一键恢复 + 完整性检查 |
| **CSV导入导出** | 批量数据导入导出 |

---

## 🛠️ 技术栈

| 层次 | 技术 |
|:----|:-----|
| **后端** | Python 3.12 + Flask 3.0 |
| **数据库** | SQLite 3（23张表，支持自动备份） |
| **前端** | 原生 HTML/CSS/JS + Chart.js 4.4 |
| **服务部署** | Gunicorn + Nginx + Docker |
| **测试** | pytest（112个测试用例） |
| **认证** | Werkzeug 密码哈希 + Session |

---

## 🚀 快速开始

### 方式一：直接运行

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/yongyi-terrazzo.git
cd yongyi-terrazzo

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置 SECRET_KEY

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
export SECRET_KEY="your-secure-key"
gunicorn -w 2 -b 0.0.0.0:5000 app:app

# 5. 访问 http://localhost:5000
# 默认管理员: admin / admin123（首次启动自动创建）
```

### 方式二：Docker 部署

```bash
# 配置环境变量
cp .env.example .env

# 启动
docker compose up -d --build

# 访问 http://localhost:5000
```

### 方式三：一键部署脚本

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📁 项目结构

```
yongyi-terrazzo/
├── app.py                 # Flask 主应用（路由、API、视图）
├── config.py              # 系统配置与管理
├── database.py            # 数据库模型与CRUD操作（3422行）
├── materials_calc.py      # 材料计算引擎
├── validation.py          # 输入验证模块
├── requirements.txt       # Python 依赖
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── deploy.sh              # 一键部署脚本
├── .env.example           # 环境变量模板
├── LICENSE                # MIT 许可证
├── README.md              # 本文件
│
├── templates/             # HTML 模板（21个）
│   ├── sidebar.html       #   全局侧边栏组件
│   ├── index.html         #   首页
│   ├── admin.html         #   管理后台
│   ├── phases.html        #   工序看板
│   ├── 404.html           #   404 错误页
│   ├── 500.html           #   500 错误页
│   └── ...                #   其他页面
│
├── static/                # 静态资源
│   └── style.css          #   全局样式
│
├── tests/                 # 测试
│   └── test_api.py        #   112个API测试
│
├── data/                  # 运行时数据（gitignore）
│   ├── yongyi.db          #   SQLite 数据库
│   ├── backups/           #   数据库备份
│   ├── photos/            #   上传照片
│   └── system_config.json #   系统配置
│
├── docs/                  # 文档
│   ├── 01-overview.md     #   项目概述
│   ├── 02-base-layer.md   #   基层施工方案
│   └── ...
│
└── logs/                  # 运行日志（gitignore）
```

---

## 🔌 API 文档

系统提供 **160+ RESTful API 端点**，涵盖所有业务模块：

| 模块 | 端点 | 说明 |
|:----|:-----|:-----|
| 🔐 认证 | `POST /api/auth/login` | 用户登录 |
| | `POST /api/auth/logout` | 退出登录 |
| | `PUT /api/auth/password` | 修改密码 |
| 📋 项目 | `GET/POST /api/projects` | 项目列表/创建 |
| | `GET/PUT/DELETE /api/projects/<id>` | 项目详情/更新/删除 |
| 📝 日志 | `GET/POST /api/projects/<id>/logs` | 施工日志 |
| 📐 材料 | `POST /api/projects/<id>/calc-materials` | 材料计算 |
| ✅ 质检 | `GET/POST /api/projects/<id>/quality` | 质量检测 |
| 📸 照片 | `GET/POST /api/projects/<id>/photos` | 照片管理 |
| 🔄 工序 | `GET/PUT /api/projects/<id>/phases` | 工序看板 |
| 🔔 通知 | `GET /api/notifications` | 通知列表 |
| 🔍 搜索 | `GET /api/search?q=keyword` | 全局搜索 |
| 📊 统计 | `GET /api/stats` | 系统统计 |
| 💾 备份 | `GET /api/backup/list` | 备份列表 |
| | `POST /api/restore` | 数据恢复 |
| 🏥 健康 | `GET /api/health` | 健康检查 |
| 📤 导出 | `GET /api/export/<table>` | CSV导出 |

---

## 🧪 测试

```bash
# 运行全部测试
pytest tests/ -v

# 运行指定测试
pytest tests/test_api.py -v -k "test_project"

# 测试覆盖率
pytest tests/ --cov=app --cov=database
```

当前测试覆盖：**112 个测试全部通过** ✅

---

## 🐳 部署架构

```
┌─────────┐     ┌─────────┐     ┌──────────┐
│ 用户浏览器 │────▶│  Nginx   │────▶│ Gunicorn  │
└─────────┘     │ (反代+SSL)│     │ (Flask app)│
                └─────────┘     └──────┬───┘
                                       │
                                ┌──────▼───┐
                                │  SQLite   │
                                │  数据库   │
                                └──────────┘
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: 添加某个功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范
- Python: 遵循 PEP 8
- 提交信息: 遵循 Conventional Commits (`feat:` / `fix:` / `docs:` / `refactor:`)

---

## 📄 许可证

[MIT License](LICENSE) © 2026 浙江永颐装饰工程有限公司

---

## 📞 联系我们

- **公司**: 浙江永颐装饰工程有限公司
- **网站**: [www.jinmojianshe.com](https://www.jinmojianshe.com)
- **邮箱**: info@jinmojianshe.com
- **电话**: 13357048951
- **领域**: 无机磨石 · 环氧磨石 · 大型工装地坪工程

---

<div align="center">
  <sub>Built with ❤️ by 浙江永颐装饰工程有限公司 · 永颐无机磨石团队</sub>
</div>
