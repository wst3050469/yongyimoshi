# 永颐无机磨石 v3.8.0 技术规格

---

## 功能一：移动端响应式适配优化

### 概述
重构CSS和模板视图，使施工管理平台在手机/平板上有良好的操作体验。

### 现状问题
- style.css 625行中仅2处媒体查询
- 首页 index.html 82KB无响应式布局
- 表格在手机上无法横向滚动
- 导航栏按钮在小屏幕上堆叠
- 表单元素在手机上难以操作

### 改动方案
1. **CSS全局响应式** (`static/style.css`)
   - 添加3个断点：768px(平板)、576px(大屏手机)、400px(小屏手机)
   - header 在小屏上折叠导航
   - table 添加横向滚动容器
   - 按钮/表单元素最小触控尺寸44px
   - 卡片网格自适应列数

2. **首页模板** (`templates/index.html`)
   - 导航tab添加滚动容器
   - 输入框组在小屏上垂直排列
   - 图表容器自适应宽度

### 影响文件
| 文件 | 变更 |
|------|------|
| `static/style.css` | 大幅重构，添加响应式规则 |
| `templates/index.html` | 导航/表单/表格响应式包装 |

---

## 功能二：测试覆盖增强

### 概述
为现有未测试模块添加测试用例，提升代码质量。

### 未覆盖模块
| 模块 | 数据库函数数 | 当前测试数 | 目标测试数 |
|------|:-----------:|:---------:|:---------:|
| 供应商管理 | 6 | 0 | 4 |
| 设备管理 | 4 | 0 | 4 |
| 安全检查 | 4 | 0 | 3 |
| 安全管理(事件) | 4 | 0 | 3 |
| 文档管理 | 4 | 0 | 3 |
| 材料申购 | 4 | 0 | 3 |
| 分包商 | 4 | 0 | 2 |
| 项目模板 | 3 | 0 | 2 |
| 验收管理 | 6 | 0 | 3 |
| 预算管理 | 4 | 0 | 2 |
| 通知管理 | 6 | 0 | 3 |

### 影响文件
| 文件 | 变更 |
|------|------|
| `tests/test_api.py` | 添加10+个新测试类 |
| `tests/test_calculations.py` | 添加边界测试 |

---

## 功能三：工序状态机

### 概述
为项目添加阶段状态流转校验，确保施工按照正确顺序进行。

### 状态定义
```
基层处理 → 抗裂砂浆施工 → 基层养护 → 面层界面处理
→ 面层浇筑 → 面层养护 → 打磨抛光 → 密封固化 → 最终验收
```

### 数据结构
```sql
-- project_phases 表
CREATE TABLE project_phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    phase_name TEXT NOT NULL,
    phase_order INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending/in_progress/completed/skipped
    started_at TEXT,
    completed_at TEXT,
    notes TEXT DEFAULT '',
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
```

### API接口
```
GET  /api/projects/<pid>/phases    - 获取阶段状态
PUT  /api/projects/<pid>/phases/<phase> - 更新阶段状态(自动校验)
```

### 影响文件
| 文件 | 变更 |
|------|------|
| `database.py` | 新增project_phases表+CRUD+状态校验 |
| `app.py` | 新增阶段管理路由 |
| `templates/index.html` | 进度面板增加阶段状态显示 |

---

## 风险与测试点
1. 响应式CSS不破坏现有桌面布局
2. 新测试不影响已有测试（独立fixture）
3. 状态机向后兼容旧项目（无阶段数据时降级）
