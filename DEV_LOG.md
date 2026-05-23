# 永颐无机磨石 · 施工管理平台 开发日志

## v3.7.0 (认证 + PDF导出 + 环境监测 + 可视化版) ✅ 已发布

### 🆕 新增功能
- **🔐 用户认证与权限管理系统**
  - 用户注册/登录/登出（Flask Session + werkzeug.security 密码哈希）
  - 角色权限：admin(管理员)、manager(项目经理)、worker(施工员)、inspector(质检员)
  - API认证保护装饰器 `@login_required` 和 `@admin_required`
  - 登录页面 `/login`，管理员页面 `/admin`
  - 首页用户状态栏显示用户名和角色
  - 默认管理员: admin / admin123（首次启动自动创建）

- **📄 PDF报告导出**
  - 施工方案PDF下载：`GET /api/report/<pid>/pdf`
  - 基于 weasyprint 从HTML渲染PDF
  - 需登录后才能导出

- **🌡️ 环境监测记录模块**
  - 独立页面 `/environment` + 嵌入首页Tab
  - 记录温度、湿度、基层含水率、地表温度等
  - Chart.js 温度/湿度趋势折线图
  - 统计数据卡片（平均温度、湿度范围等）

- **📊 数据可视化增强**
  - 项目仪表盘：材料用量饼图、成本构成环形图、质量检测柱状图、阶段进度横向柱状图
  - 分析看板：项目状态分布环形图、项目预算对比柱状图
  - 基于 Chart.js 4.x CDN

### 📈 测试覆盖
| 测试类别 | 数量 | 状态 |
|---------|:----:|:----:|
| 原有测试 | 46 | ✅ 全部通过 |
| 新增认证测试 | 5 | ✅ 全部通过 |
| 新增环境监测测试 | 3 | ✅ 全部通过 |
| 新增PDF导出测试 | 2 | ✅ 全部通过 |
| **总计** | **56** | **✅ 全部通过** |

### 📁 变更文件清单
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `database.py` | ✅ 修改 | 新增 users 表 + 环境监测表 + CRUD函数 |
| `app.py` | ✅ 修改 | 新增认证路由 + 环境监测路由 + PDF导出 + 保护装饰器 |
| `validation.py` | - | 未修改（已有用户验证函数） |
| `requirements.txt` | ✅ 修改 | 添加 weasyprint |
| `templates/login.html` | 🆕 新建 | 登录页面 |
| `templates/environment.html` | 🆕 新建 | 环境监测页面 |
| `templates/index.html` | ✅ 修改 | 添加用户状态栏 + 环境监测Tab |
| `templates/project_dashboard.html` | ✅ 修改 | 添加4个Chart.js图表 |
| `templates/analytics.html` | ✅ 修改 | 添加跨项目图表 |
| `tests/test_api.py` | ✅ 修改 | 添加10个新测试用例 |
| `DEV_LOG.md` | 🆕 新建 | 开发日志 |
| `SPEC.md` | 🆕 新建 | 技术规格文档 |

### 🛡️ 安全措施
- 密码使用 pbkdf2:sha256 哈希存储
- Session 使用 Flask 签名Cookie
- 管理API限 admin 角色
- 敏感接口（配置、用户管理、PDF导出）需登录
- 未登录返回 401 JSON 响应
