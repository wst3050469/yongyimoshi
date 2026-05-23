# 永颐无机磨石 v3.7.0 技术规格

---

## 功能一：用户认证与权限管理系统

### 概述
为平台添加用户认证系统，包含注册、登录、登出、密码管理和基于角色的权限控制。

### 架构设计
- **认证方式**: Flask Session + 密码哈希 (werkzeug.security)
- **用户角色**: admin(管理员), manager(项目经理), worker(施工员), inspector(质检员)
- **权限粒度**: 页面级 + API级

### 数据结构
```sql
-- users 表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'worker',
    phone TEXT DEFAULT '',
    email TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 影响文件
| 文件 | 变更 |
|------|------|
| `database.py` | 新增 users 表CRUD + 认证相关函数 |
| `validation.py` | 新增用户数据验证 |
| `app.py` | 新增认证路由 + 登录/登出 + 装饰器保护API |
| 新建 `templates/login.html` | 登录页面 |
| 新建 `templates/profile.html` | 用户管理页面 |
| `templates/index.html` | 添加用户状态栏 |
| `requirements.txt` | 无需新增依赖 |

### API接口
```
POST /api/auth/login    - 登录
POST /api/auth/logout   - 登出
GET  /api/auth/me       - 当前用户信息
GET  /api/users         - 用户列表(管理员)
POST /api/users         - 创建用户(管理员)
PUT  /api/users/<id>    - 更新用户(管理员)
DELETE /api/users/<id>  - 删除用户(管理员)
PUT  /api/auth/password - 修改密码
```

### 安全措施
- 密码使用 pbkdf2:sha256 哈希存储
- Session 使用 Flask 默认签名Cookie
- 敏感API需登录后才能访问
- 管理API限 admin 角色

---

## 功能二：PDF报告导出

### 概述
将施工方案报告从HTML渲染为可下载的PDF文件，替代浏览器打印。

### 架构设计
- **方案A**: 使用 `weasyprint` 库（纯Python，无需系统依赖wkhtmltopdf）
- **方案B**: 使用 `pdfkit`（需要 wkhtmltopdf 系统包）

选用方案A（weasyprint），纯Python无系统依赖问题。

### 影响文件
| 文件 | 变更 |
|------|------|
| `app.py` | 新增PDF导出路由 |
| `requirements.txt` | 添加 weasyprint |
| `templates/print_report.html` | 优化打印样式适配PDF |

### API接口
```
GET  /api/report/<pid>/pdf  - 下载施工方案PDF报告
```

---

## 功能三：环境监测数据记录模块

### 概述
为项目施工过程中的环境条件（温度、湿度、基层含水率等）提供专用记录、查询和趋势展示。

### 数据结构
```sql
CREATE TABLE environment_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    record_date TEXT NOT NULL,
    record_time TEXT DEFAULT '',
    temperature REAL DEFAULT 0,        -- 温度 ℃
    humidity REAL DEFAULT 0,           -- 湿度 %
    base_moisture REAL DEFAULT NULL,   -- 基层含水率 %
    surface_temp REAL DEFAULT NULL,    -- 地表温度 ℃
    wind_speed REAL DEFAULT NULL,      -- 风速 m/s
    weather_condition TEXT DEFAULT '',  -- 天气状况
    recorder TEXT DEFAULT '',           -- 记录人
    notes TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### 影响文件
| 文件 | 变更 |
|------|------|
| `database.py` | 新增环境监测CRUD函数 |
| `app.py` | 新增环境监测API路由 |
| 新建 `templates/environment.html` | 环境监测页面 |
| `templates/index.html` | 添加导航链接 |

### API接口
```
GET    /api/environment?project_id=N   - 环境记录列表
POST   /api/environment                - 添加环境记录
DELETE /api/environment/<id>           - 删除记录
GET    /api/environment/stats?project_id=N - 环境统计数据
```

---

## 功能四：数据可视化增强

### 概述
使用 Chart.js 在仪表盘和分析页面添加交互式图表，提升数据可读性。

### 架构设计
- 引入 Chart.js CDN（无需npm）
- 图表类型：饼图(成本构成)、柱状图(材料用量)、折线图(进度趋势)、雷达图(质量检测)

### 影响文件
| 文件 | 变更 |
|------|------|
| `templates/project_dashboard.html` | 添加成本饼图 + 材料用量柱状图 |
| `templates/analytics.html` | 添加跨项目统计图表 |

---

## 风险与测试点

### 潜在风险
1. **认证系统**: Session安全、CSRF防护、密码强度
2. **PDF导出**: 中文字体渲染、weasyprint系统兼容性
3. **环境监测**: 数据有效性校验
4. **可视化**: CDN加载失败降级

### 测试要点
- 用户注册/登录/登出流程
- 无权限访问API返回403
- PDF文件生成完整性验证
- 环境监测数据CRUD验证
- Chart.js在无数据时展示空状态
