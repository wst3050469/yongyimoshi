"""
永颐无机磨石 - SQLite数据库模块
提供项目管理和数据持久化支持
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DB_DIR, 'yongyi.db')


def get_db() -> sqlite3.Connection:
    """获取数据库连接"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT '默认项目',
            area REAL NOT NULL DEFAULT 100,
            base_thickness REAL NOT NULL DEFAULT 50,
            surface_thickness REAL NOT NULL DEFAULT 15,
            start_date TEXT NOT NULL DEFAULT (date('now')),
            status TEXT NOT NULL DEFAULT '进行中',
            location TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            weather TEXT DEFAULT '晴',
            temperature TEXT DEFAULT '20~25',
            workers INTEGER DEFAULT 5,
            work_content TEXT DEFAULT '',
            materials_used TEXT DEFAULT '',
            issues TEXT DEFAULT '无',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS quality_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            test_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            standard_value TEXT NOT NULL,
            actual_value TEXT DEFAULT '',
            is_pass INTEGER DEFAULT 0,
            test_date TEXT DEFAULT (date('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS checklist_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            item_id TEXT NOT NULL,
            item_text TEXT NOT NULL,
            is_checked INTEGER DEFAULT 0,
            phase TEXT DEFAULT '',
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            phase TEXT NOT NULL DEFAULT '',
            description TEXT DEFAULT '',
            filename TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS material_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            material_name TEXT NOT NULL,
            quantity_kg REAL DEFAULT 0,
            quantity_packages REAL DEFAULT 0,
            unit_price REAL DEFAULT 0,
            total_cost REAL DEFAULT 0,
            record_date TEXT DEFAULT (date('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            materials TEXT DEFAULT '[]',
            rating INTEGER DEFAULT 3,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS supplier_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            material_name TEXT NOT NULL,
            unit_price REAL NOT NULL DEFAULT 0,
            price_date TEXT NOT NULL DEFAULT (date('now')),
            notes TEXT DEFAULT '',
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS curing_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            record_date TEXT NOT NULL DEFAULT (date('now')),
            weather TEXT DEFAULT '晴',
            temp_min REAL DEFAULT 20,
            temp_max REAL DEFAULT 25,
            humidity REAL DEFAULT 60,
            wind_level TEXT DEFAULT '',
            curing_measure TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            leader TEXT DEFAULT '',
            member_count INTEGER DEFAULT 0,
            specialty TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            role TEXT DEFAULT '工人',
            team_id INTEGER DEFAULT 0,
            hourly_rate REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS work_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            work_date TEXT NOT NULL,
            hours REAL DEFAULT 8,
            work_type TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS budget_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            planned_amount REAL DEFAULT 0,
            actual_amount REAL DEFAULT 0,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT DEFAULT '',
            is_read INTEGER DEFAULT 0,
            due_date TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()


# ============================================================
# 项目管理
# ============================================================

def create_project(name: str = "新建项目", area: float = 100,
                   base_thickness: float = 50, surface_thickness: float = 15,
                   start_date: str = "", location: str = "") -> int:
    """创建新项目"""
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO projects (name, area, base_thickness, surface_thickness, start_date, location)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, area, base_thickness, surface_thickness, start_date, location))
    pid = cursor.lastrowid

    # 为新项目初始化检查清单
    _init_checklist_for_project(pid, conn)
    # 初始化质量检测项
    _init_quality_tests_for_project(pid, conn)

    conn.commit()
    conn.close()
    return pid


def _init_checklist_for_project(pid: int, conn: sqlite3.Connection):
    """为新项目初始化检查清单"""
    from materials_calc import CHECKLIST_ITEMS
    cursor = conn.cursor()
    for cat in CHECKLIST_ITEMS:
        for item in cat["items"]:
            cursor.execute("""
                INSERT INTO checklist_state (project_id, category, item_id, item_text, phase)
                VALUES (?, ?, ?, ?, ?)
            """, (pid, cat["category"], item["id"], item["text"], cat.get("phase", "")))


def _init_quality_tests_for_project(pid: int, conn: sqlite3.Connection):
    """为新项目初始化质量检测项"""
    from materials_calc import QUALITY_TESTS
    cursor = conn.cursor()
    for t in QUALITY_TESTS:
        cursor.execute("""
            INSERT INTO quality_tests (project_id, test_id, test_name, standard_value)
            VALUES (?, ?, ?, ?)
        """, (pid, t["id"], t["name"], t["standard"]))


def get_projects() -> List[Dict]:
    """获取所有项目"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT p.*,
            (SELECT COUNT(*) FROM checklist_state WHERE project_id = p.id AND is_checked = 1) as checked_items,
            (SELECT COUNT(*) FROM checklist_state WHERE project_id = p.id) as total_items,
            (SELECT COUNT(*) FROM daily_logs WHERE project_id = p.id) as log_count
        FROM projects p ORDER BY p.updated_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project(pid: int) -> Optional[Dict]:
    """获取单个项目"""
    conn = get_db()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_project(pid: int, **kwargs) -> bool:
    """更新项目信息"""
    allowed = ['name', 'area', 'base_thickness', 'surface_thickness',
               'start_date', 'status', 'location', 'notes']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    updates['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [pid]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def delete_project(pid: int) -> bool:
    """删除项目"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (pid,))
    conn.commit()
    conn.close()
    return True


# ============================================================
# 日志管理
# ============================================================

def save_daily_log(project_id: int, data: Dict) -> int:
    """保存施工日志"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO daily_logs (project_id, log_date, weather, temperature,
            workers, work_content, materials_used, issues)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (project_id, data.get('date', ''), data.get('weather', '晴'),
          data.get('temperature', ''), int(data.get('workers', 5)),
          data.get('work_content', ''), data.get('materials_used', ''),
          data.get('issues', '无')))
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def get_daily_logs(project_id: int) -> List[Dict]:
    """获取项目的施工日志"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM daily_logs WHERE project_id = ? ORDER BY log_date DESC
    """, (project_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# 检查清单
# ============================================================

def get_checklist(project_id: int) -> List[Dict]:
    """获取项目的检查清单（按category分组）"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM checklist_state WHERE project_id = ? ORDER BY id
    """, (project_id,)).fetchall()
    conn.close()

    # 按category分组
    categories = {}
    for r in rows:
        d = dict(r)
        cat = d['category']
        if cat not in categories:
            categories[cat] = {"category": cat, "phase": d['phase'], "items": []}
        categories[cat]["items"].append({
            "id": d['item_id'],
            "text": d['item_text'],
            "checked": bool(d['is_checked']),
        })
    return list(categories.values())


def update_checklist(project_id: int, checklist_data: List[Dict]):
    """更新检查清单状态"""
    conn = get_db()
    cursor = conn.cursor()
    for cat in checklist_data:
        for item in cat.get('items', []):
            cursor.execute("""
                UPDATE checklist_state SET is_checked = ? 
                WHERE project_id = ? AND item_id = ?
            """, (1 if item.get('checked') else 0, project_id, item.get('id')))
    conn.commit()
    conn.close()


# ============================================================
# 质量检测
# ============================================================

def get_quality_tests(project_id: int) -> Dict:
    """获取项目的质量检测数据"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM quality_tests WHERE project_id = ? ORDER BY id
    """, (project_id,)).fetchall()
    conn.close()

    from materials_calc import QUALITY_TESTS
    results = {}
    for r in rows:
        d = dict(r)
        results[d['test_id']] = d['actual_value']
        results[d['test_id'] + '_pass'] = bool(d['is_pass'])

    return {
        "templates": QUALITY_TESTS,
        "results": results,
    }


def save_quality_tests(project_id: int, results: Dict):
    """保存质量检测结果"""
    conn = get_db()
    cursor = conn.cursor()
    from materials_calc import QUALITY_TESTS
    for t in QUALITY_TESTS:
        val = results.get(t['id'], '')
        is_pass = 1 if results.get(t['id'] + '_pass', False) else 0
        cursor.execute("""
            UPDATE quality_tests SET actual_value = ?, is_pass = ?, test_date = date('now')
            WHERE project_id = ? AND test_id = ?
        """, (val, is_pass, project_id, t['id']))
    conn.commit()
    conn.close()


# ============================================================
# 项目看板数据
# ============================================================

def get_dashboard_data(project_id: int) -> Dict:
    """获取项目看板数据"""
    conn = get_db()
    cursor = conn.cursor()

    # 检查清单进度
    rows = cursor.execute("""
        SELECT phase, COUNT(*) as total,
               SUM(CASE WHEN is_checked = 1 THEN 1 ELSE 0 END) as checked
        FROM checklist_state WHERE project_id = ?
        GROUP BY phase
    """, (project_id,)).fetchall()

    total_items = 0
    checked_items = 0
    phase_progress = {}
    for r in rows:
        d = dict(r)
        total = d['total']
        checked = d['checked'] or 0
        total_items += total
        checked_items += checked
        phase_progress[d['phase']] = {
            "total": total,
            "checked": checked,
            "percent": round(checked / total * 100, 1) if total > 0 else 0,
        }

    overall_pct = round(checked_items / total_items * 100, 1) if total_items > 0 else 0

    # 日志数量
    log_count = cursor.execute(
        "SELECT COUNT(*) FROM daily_logs WHERE project_id = ?", (project_id,)
    ).fetchone()[0]

    conn.close()

    return {
        "overall_progress": overall_pct,
        "total_items": total_items,
        "checked_items": checked_items,
        "phase_progress": phase_progress,
        "log_count": log_count,
    }


# ============================================================
# 项目报告
# ============================================================

def generate_report(project_id: int) -> Dict:
    """生成项目综合报告"""
    project = get_project(project_id)
    if not project:
        return {"error": "项目不存在"}

    dashboard = get_dashboard_data(project_id)
    logs = get_daily_logs(project_id)
    quality = get_quality_tests(project_id)
    checklist = get_checklist(project_id)

    # 材料用量估算
    from materials_calc import calculate_all
    calc = calculate_all(project['area'], project['base_thickness'], project['surface_thickness'])

    return {
        "project": project,
        "dashboard": dashboard,
        "logs": logs,
        "quality": quality,
        "materials": calc,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# 初始化数据库
init_db()


# ============================================================
# 材料库存管理
# ============================================================

def add_material_record(project_id: int, material_name: str,
                        quantity_kg: float, unit_price: float = 0,
                        record_type: str = "入库",
                        record_date: str = "") -> int:
    """添加材料入库/出库记录"""
    if not record_date:
        record_date = datetime.now().strftime("%Y-%m-%d")
    packages = 0
    total_cost = quantity_kg * unit_price
    from materials_calc import PACKAGING_SPECS
    spec = PACKAGING_SPECS.get(material_name)
    if spec:
        import math
        packages = math.ceil(quantity_kg / spec["per_package"])

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO material_records 
        (project_id, material_name, quantity_kg, quantity_packages, 
         unit_price, total_cost, record_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (project_id, material_name, quantity_kg, packages,
          unit_price, total_cost, record_date))
    rid = cursor.lastrowid
    conn.commit()
    conn.close()
    return rid


def get_material_inventory(project_id: int) -> List[Dict]:
    """获取项目材料库存汇总"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT material_name,
               SUM(quantity_kg) as total_kg,
               SUM(quantity_packages) as total_packages,
               SUM(total_cost) as total_cost,
               COUNT(*) as record_count
        FROM material_records
        WHERE project_id = ?
        GROUP BY material_name
        ORDER BY material_name
    """, (project_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_material_records(project_id: int, limit: int = 50) -> List[Dict]:
    """获取项目的材料进出记录"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM material_records
        WHERE project_id = ?
        ORDER BY record_date DESC, id DESC
        LIMIT ?
    """, (project_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# 供应商管理
# ============================================================

def add_supplier(name: str, contact_person: str = "", phone: str = "",
                 address: str = "", materials: str = "[]",
                 rating: int = 3, notes: str = "") -> int:
    """添加供应商"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO suppliers (name, contact_person, phone, address, materials, rating, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, contact_person, phone, address, materials, rating, notes))
    sid = cursor.lastrowid
    conn.commit()
    conn.close()
    return sid


def get_suppliers() -> List[Dict]:
    """获取所有供应商"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT s.*,
            (SELECT COUNT(*) FROM supplier_prices WHERE supplier_id = s.id) as price_count
        FROM suppliers s ORDER BY s.updated_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_supplier(sid: int) -> Optional[Dict]:
    """获取单个供应商"""
    conn = get_db()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM suppliers WHERE id = ?", (sid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_supplier(sid: int, **kwargs) -> bool:
    """更新供应商信息"""
    allowed = ['name', 'contact_person', 'phone', 'address', 'materials', 'rating', 'notes']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    updates['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [sid]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE suppliers SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def delete_supplier(sid: int) -> bool:
    """删除供应商"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM supplier_prices WHERE supplier_id = ?", (sid,))
    cursor.execute("DELETE FROM suppliers WHERE id = ?", (sid,))
    conn.commit()
    conn.close()
    return True


# ============================================================
# 供应商报价管理
# ============================================================

def add_supplier_price(supplier_id: int, material_name: str,
                       unit_price: float, price_date: str = "",
                       notes: str = "") -> int:
    """添加供应商报价记录"""
    if not price_date:
        price_date = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO supplier_prices (supplier_id, material_name, unit_price, price_date, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (supplier_id, material_name, unit_price, price_date, notes))
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_supplier_prices(supplier_id: int) -> List[Dict]:
    """获取供应商的报价历史"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM supplier_prices
        WHERE supplier_id = ?
        ORDER BY price_date DESC, id DESC
    """, (supplier_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_best_prices(material_name: str) -> List[Dict]:
    """获取某种材料的最优报价（按价格升序）"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT sp.*, s.name as supplier_name, s.phone, s.contact_person
        FROM supplier_prices sp
        JOIN suppliers s ON sp.supplier_id = s.id
        WHERE sp.material_name = ?
        ORDER BY sp.unit_price ASC
    """, (material_name,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# 养护记录管理
# ============================================================

def add_curing_record(project_id: int, record_date: str = "",
                      weather: str = "晴", temp_min: float = 20,
                      temp_max: float = 25, humidity: float = 60,
                      wind_level: str = "", curing_measure: str = "",
                      notes: str = "") -> int:
    """添加养护记录"""
    if not record_date:
        record_date = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO curing_records (project_id, record_date, weather,
            temp_min, temp_max, humidity, wind_level, curing_measure, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (project_id, record_date, weather, temp_min, temp_max,
          humidity, wind_level, curing_measure, notes))
    rid = cursor.lastrowid
    conn.commit()
    conn.close()
    return rid


def get_curing_records(project_id: int) -> List[Dict]:
    """获取项目的养护记录"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM curing_records
        WHERE project_id = ?
        ORDER BY record_date DESC, id DESC
    """, (project_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_curing_record(rid: int) -> bool:
    """删除养护记录"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM curing_records WHERE id = ?", (rid,))
    conn.commit()
    conn.close()
    return True


# ============================================================
# 班组管理
# ============================================================

def add_team(name: str, leader: str = "", specialty: str = "") -> int:
    """添加班组"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO teams (name, leader, specialty) VALUES (?, ?, ?)",
                   (name, leader, specialty))
    tid = cursor.lastrowid
    conn.commit()
    conn.close()
    return tid


def get_teams() -> List[Dict]:
    """获取所有班组"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT t.*, (SELECT COUNT(*) FROM workers WHERE team_id = t.id) as actual_members
        FROM teams t ORDER BY t.id
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_team(tid: int) -> bool:
    """删除班组"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE workers SET team_id = 0 WHERE team_id = ?", (tid,))
    cursor.execute("DELETE FROM teams WHERE id = ?", (tid,))
    conn.commit()
    conn.close()
    return True


# ============================================================
# 工人管理
# ============================================================

def add_worker(name: str, phone: str = "", role: str = "工人",
               team_id: int = 0, hourly_rate: float = 0, notes: str = "") -> int:
    """添加工人"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO workers (name, phone, role, team_id, hourly_rate, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, phone, role, team_id, hourly_rate, notes))
    wid = cursor.lastrowid
    # 更新班组人数
    if team_id:
        cursor.execute("UPDATE teams SET member_count = (SELECT COUNT(*) FROM workers WHERE team_id = ?) WHERE id = ?",
                       (team_id, team_id))
    conn.commit()
    conn.close()
    return wid


def get_workers(team_id: int = 0) -> List[Dict]:
    """获取工人列表"""
    conn = get_db()
    cursor = conn.cursor()
    if team_id:
        rows = cursor.execute("""
            SELECT w.*, t.name as team_name FROM workers w
            LEFT JOIN teams t ON w.team_id = t.id
            WHERE w.team_id = ? ORDER BY w.name
        """, (team_id,)).fetchall()
    else:
        rows = cursor.execute("""
            SELECT w.*, t.name as team_name FROM workers w
            LEFT JOIN teams t ON w.team_id = t.id
            ORDER BY w.team_id, w.name
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_worker(wid: int) -> Optional[Dict]:
    """获取单个工人"""
    conn = get_db()
    cursor = conn.cursor()
    row = cursor.execute("""
        SELECT w.*, t.name as team_name FROM workers w
        LEFT JOIN teams t ON w.team_id = t.id WHERE w.id = ?
    """, (wid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_worker(wid: int, **kwargs) -> bool:
    """更新工人信息"""
    allowed = ['name', 'phone', 'role', 'team_id', 'hourly_rate', 'notes']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [wid]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE workers SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def delete_worker(wid: int) -> bool:
    """删除工人"""
    conn = get_db()
    cursor = conn.cursor()
    worker = cursor.execute("SELECT team_id FROM workers WHERE id = ?", (wid,)).fetchone()
    cursor.execute("DELETE FROM workers WHERE id = ?", (wid,))
    if worker and worker['team_id']:
        cursor.execute("UPDATE teams SET member_count = (SELECT COUNT(*) FROM workers WHERE team_id = ?) WHERE id = ?",
                       (worker['team_id'], worker['team_id']))
    conn.commit()
    conn.close()
    return True


# ============================================================
# 工时管理
# ============================================================

def add_work_hours(project_id: int, worker_id: int, work_date: str = "",
                   hours: float = 8, work_type: str = "", notes: str = "") -> int:
    """添加工时记录"""
    if not work_date:
        work_date = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO work_hours (project_id, worker_id, work_date, hours, work_type, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (project_id, worker_id, work_date, hours, work_type, notes))
    wid = cursor.lastrowid
    conn.commit()
    conn.close()
    return wid


def get_work_hours(project_id: int) -> List[Dict]:
    """获取项目的工时记录"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT wh.*, w.name as worker_name, w.role, t.name as team_name
        FROM work_hours wh
        JOIN workers w ON wh.worker_id = w.id
        LEFT JOIN teams t ON w.team_id = t.id
        WHERE wh.project_id = ?
        ORDER BY wh.work_date DESC, wh.id DESC
    """, (project_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_work_hours_summary(project_id: int) -> Dict:
    """获取项目工时汇总"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT wh.work_type, COUNT(DISTINCT wh.worker_id) as worker_count,
               SUM(wh.hours) as total_hours,
               SUM(wh.hours * w.hourly_rate) as total_cost
        FROM work_hours wh
        JOIN workers w ON wh.worker_id = w.id
        WHERE wh.project_id = ?
        GROUP BY wh.work_type
    """, (project_id,)).fetchall()

    total_hours = 0
    total_cost = 0
    details = []
    for r in rows:
        d = dict(r)
        total_hours += d['total_hours'] or 0
        total_cost += d['total_cost'] or 0
        details.append(d)

    conn.close()
    return {"total_hours": round(total_hours, 1), "total_cost": round(total_cost, 2),
            "details": details}


# ============================================================
# 成本预算管理
# ============================================================

def add_budget_item(project_id: int, category: str, planned_amount: float = 0,
                    actual_amount: float = 0, description: str = "") -> int:
    """添加预算项"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO budget_items (project_id, category, planned_amount, actual_amount, description)
        VALUES (?, ?, ?, ?, ?)
    """, (project_id, category, planned_amount, actual_amount, description))
    bid = cursor.lastrowid
    conn.commit()
    conn.close()
    return bid


def get_budget_items(project_id: int) -> List[Dict]:
    """获取项目的预算项"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT * FROM budget_items WHERE project_id = ? ORDER BY id
    """, (project_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_budget_summary(project_id: int) -> Dict:
    """获取项目预算汇总"""
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT category,
               SUM(planned_amount) as planned,
               SUM(actual_amount) as actual
        FROM budget_items WHERE project_id = ?
        GROUP BY category ORDER BY category
    """, (project_id,)).fetchall()

    categories = []
    total_planned = 0
    total_actual = 0
    for r in rows:
        d = dict(r)
        categories.append(d)
        total_planned += d['planned'] or 0
        total_actual += d['actual'] or 0

    conn.close()
    return {
        "total_planned": round(total_planned, 2),
        "total_actual": round(total_actual, 2),
        "variance": round(total_planned - total_actual, 2),
        "categories": categories,
    }


def update_budget_item(bid: int, **kwargs) -> bool:
    """更新预算项"""
    allowed = ['planned_amount', 'actual_amount', 'description']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [bid]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE budget_items SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def delete_budget_item(bid: int) -> bool:
    """删除预算项"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM budget_items WHERE id = ?", (bid,))
    conn.commit()
    conn.close()
    return True


# ============================================================
# 通知提醒系统
# ============================================================

def add_notification(project_id: int, notif_type: str, title: str,
                     message: str = "", due_date: str = "") -> int:
    """添加通知"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (project_id, type, title, message, due_date)
        VALUES (?, ?, ?, ?, ?)
    """, (project_id, notif_type, title, message, due_date))
    nid = cursor.lastrowid
    conn.commit()
    conn.close()
    return nid


def get_notifications(project_id: int = 0, unread_only: bool = False) -> List[Dict]:
    """获取通知列表"""
    conn = get_db()
    cursor = conn.cursor()
    if project_id:
        if unread_only:
            rows = cursor.execute("""
                SELECT n.*, p.name as project_name FROM notifications n
                JOIN projects p ON n.project_id = p.id
                WHERE n.project_id = ? AND n.is_read = 0
                ORDER BY n.created_at DESC
            """, (project_id,)).fetchall()
        else:
            rows = cursor.execute("""
                SELECT n.*, p.name as project_name FROM notifications n
                JOIN projects p ON n.project_id = p.id
                WHERE n.project_id = ?
                ORDER BY n.created_at DESC LIMIT 50
            """, (project_id,)).fetchall()
    else:
        if unread_only:
            rows = cursor.execute("""
                SELECT n.*, p.name as project_name FROM notifications n
                JOIN projects p ON n.project_id = p.id
                WHERE n.is_read = 0 ORDER BY n.created_at DESC
            """).fetchall()
        else:
            rows = cursor.execute("""
                SELECT n.*, p.name as project_name FROM notifications n
                JOIN projects p ON n.project_id = p.id
                ORDER BY n.created_at DESC LIMIT 100
            """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_notification_read(nid: int) -> bool:
    """标记通知为已读"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (nid,))
    conn.commit()
    conn.close()
    return True


def mark_all_notifications_read(project_id: int = 0) -> int:
    """标记所有通知为已读"""
    conn = get_db()
    cursor = conn.cursor()
    if project_id:
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE project_id = ? AND is_read = 0",
                       (project_id,))
    else:
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE is_read = 0")
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count


def delete_notification(nid: int) -> bool:
    """删除通知"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notifications WHERE id = ?", (nid,))
    conn.commit()
    conn.close()
    return True


def create_curing_reminder(project_id: int) -> int:
    """自动创建养护提醒"""
    project = get_project(project_id)
    if not project:
        return 0
    title = f"🔔 {project['name']} - 养护提醒"
    message = f"项目「{project['name']}」已达到养护阶段，请检查养护措施并记录养护日志。"
    return add_notification(project_id, "curing_reminder", title, message)


def create_quality_test_reminder(project_id: int) -> int:
    """自动创建质量检测提醒"""
    project = get_project(project_id)
    if not project:
        return 0
    title = f"🧪 {project['name']} - 质量检测提醒"
    message = f"项目「{project['name']}」需进行质量检测，请安排检测并记录结果。"
    return add_notification(project_id, "test_reminder", title, message)


# ============================================================
# 数据导出
# ============================================================

def export_project_data(project_id: int) -> Dict:
    """导出项目的完整数据"""
    project = get_project(project_id)
    if not project:
        return {"error": "项目不存在"}

    conn = get_db()
    cursor = conn.cursor()

    # 日志
    logs = [dict(r) for r in cursor.execute(
        "SELECT * FROM daily_logs WHERE project_id = ? ORDER BY log_date",
        (project_id,)).fetchall()]

    # 检查清单
    checklist = [dict(r) for r in cursor.execute(
        "SELECT * FROM checklist_state WHERE project_id = ? ORDER BY id",
        (project_id,)).fetchall()]

    # 质量检测
    quality = [dict(r) for r in cursor.execute(
        "SELECT * FROM quality_tests WHERE project_id = ? ORDER BY id",
        (project_id,)).fetchall()]

    # 材料记录
    materials = [dict(r) for r in cursor.execute(
        "SELECT * FROM material_records WHERE project_id = ? ORDER BY record_date",
        (project_id,)).fetchall()]

    # 养护记录
    curing = [dict(r) for r in cursor.execute(
        "SELECT * FROM curing_records WHERE project_id = ? ORDER BY record_date",
        (project_id,)).fetchall()]

    # 预算
    budget = [dict(r) for r in cursor.execute(
        "SELECT * FROM budget_items WHERE project_id = ? ORDER BY id",
        (project_id,)).fetchall()]

    # 工时记录
    work_hours_data = [dict(r) for r in cursor.execute(
        "SELECT wh.*, w.name as worker_name FROM work_hours wh "
        "JOIN workers w ON wh.worker_id = w.id "
        "WHERE wh.project_id = ? ORDER BY wh.work_date",
        (project_id,)).fetchall()]

    conn.close()

    # 材料用量计算
    from materials_calc import calculate_all, calc_purchase_list
    calc = calculate_all(project['area'], project['base_thickness'], project['surface_thickness'])
    purchase = calc_purchase_list(calc['summary'])

    return {
        "export_version": "3.9.0",
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project": dict(project),
        "statistics": {
            "log_count": len(logs),
            "checklist_count": len(checklist),
            "checked_count": sum(1 for c in checklist if c['is_checked']),
            "quality_count": len(quality),
            "passed_count": sum(1 for q in quality if q['is_pass']),
            "material_records": len(materials),
            "curing_records": len(curing),
            "budget_items": len(budget),
            "work_hours": len(work_hours_data),
            "total_material_kg": calc['total_weight_kg'],
        },
        "daily_logs": logs,
        "checklist": checklist,
        "quality_tests": quality,
        "material_records": materials,
        "curing_records": curing,
        "budget_items": budget,
        "work_hours": work_hours_data,
        "material_calculation": calc,
        "purchase_list": purchase,
    }


def backup_database() -> str:
    """备份数据库，返回备份文件路径"""
    import shutil
    backup_dir = os.path.join(os.path.dirname(__file__), 'data', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"yongyi_backup_{timestamp}.db")

    conn = get_db()
    conn.execute("VACUUM")
    conn.close()

    shutil.copy2(DB_PATH, backup_path)
    return backup_path


# ============================================================
# 施工照片管理
# ============================================================

import base64
import uuid

PHOTO_DIR = os.path.join(os.path.dirname(__file__), 'data', 'photos')


def _ensure_photo_dir():
    """确保照片存储目录存在"""
    os.makedirs(PHOTO_DIR, exist_ok=True)


def add_photo(project_id: int, phase: str, description: str,
              image_data: str) -> Dict:
    """
    添加施工照片

    参数:
        project_id: 项目ID
        phase: 施工阶段 (如: 基层处理, 抗裂砂浆施工, 面层施工, 打磨抛光, 密封固化)
        description: 照片描述
        image_data: base64编码的图片数据 (data:image/...;base64,...)

    返回:
        照片记录
    """
    _ensure_photo_dir()

    # 解析base64
    import re
    match = re.match(r'data:image/(\w+);base64,(.+)', image_data)
    if not match:
        # 如果没有data URL前缀，直接当纯base64处理
        fmt = 'png'
        b64_data = image_data
    else:
        fmt = match.group(1)
        b64_data = match.group(2)

    # 生成唯一文件名
    filename = f"{uuid.uuid4().hex}.{fmt}"
    filepath = os.path.join(PHOTO_DIR, filename)

    # 解码并保存
    try:
        img_bytes = base64.b64decode(b64_data)
        with open(filepath, 'wb') as f:
            f.write(img_bytes)
    except Exception as e:
        return {"error": f"图片解码失败: {str(e)}"}

    file_size = os.path.getsize(filepath)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO photos (project_id, phase, description, filename, file_size)
        VALUES (?, ?, ?, ?, ?)
    """, (project_id, phase, description, filename, file_size))
    photo_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": photo_id,
        "filename": filename,
        "file_size": file_size,
        "url": f"/api/photo/{photo_id}",
    }


def get_photos(project_id: int, phase: str = "") -> List[Dict]:
    """获取项目的照片列表"""
    conn = get_db()
    cursor = conn.cursor()
    if phase:
        rows = cursor.execute("""
            SELECT * FROM photos WHERE project_id = ? AND phase = ?
            ORDER BY created_at DESC
        """, (project_id, phase)).fetchall()
    else:
        rows = cursor.execute("""
            SELECT * FROM photos WHERE project_id = ?
            ORDER BY created_at DESC
        """, (project_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_photo_by_id(photo_id: int) -> Optional[Dict]:
    """获取单张照片信息"""
    conn = get_db()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_photo(photo_id: int) -> bool:
    """删除照片"""
    photo = get_photo_by_id(photo_id)
    if not photo:
        return False
    # 删除文件
    filepath = os.path.join(PHOTO_DIR, photo['filename'])
    if os.path.exists(filepath):
        os.remove(filepath)
    # 删除记录
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
    conn.commit()
    conn.close()
    return True


# ============================================================
# 甘特图时间轴数据
# ============================================================

def get_timeline_data(project_id: int) -> Dict:
    """
    获取项目时间轴数据（用于甘特图）
    结合进度计划和实际日志生成时间轴
    """
    from materials_calc import generate_schedule

    project = get_project(project_id)
    if not project:
        return {"error": "项目不存在"}

    # 获取计划时间
    start_date = project.get('start_date', '')
    schedule = generate_schedule(start_date)

    # 获取实际施工日志
    logs = get_daily_logs(project_id)
    actual_dates = set()
    for log in logs:
        actual_dates.add(log['log_date'])

    # 获取检查清单进度
    checklist = get_checklist(project_id)
    phase_progress = {}
    for cat in checklist:
        phase = cat.get('phase', '')
        items = cat['items']
        checked = sum(1 for i in items if i['checked'])
        total = len(items)
        if phase:
            phase_progress[phase] = {
                "progress": round(checked / total * 100, 1) if total > 0 else 0,
                "checked": checked,
                "total": total,
            }

    # 构建时间轴
    timeline = []
    for phase in schedule:
        timeline.append({
            "phase": phase['phase'],
            "planned_start": phase['start'],
            "planned_end": phase['end'],
            "days": phase['days'],
            "actual_days": sum(1 for d in actual_dates if phase['start'] <= d <= phase['end']),
            "progress": phase_progress.get(phase['phase'], {}).get('progress', 0),
        })

    return {
        "project": project['name'],
        "start_date": start_date,
        "timeline": timeline,
        "total_planned_days": sum(p['days'] for p in timeline),
        "total_actual_days": len(actual_dates),
    }


# ============================================================
# 性能优化
# ============================================================

def optimize_database():
    """数据库性能优化: 创建索引 + VACUUM"""
    conn = get_db()
    cursor = conn.cursor()

    # 创建索引
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_checklist_project ON checklist_state(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_checklist_phase ON checklist_state(phase)",
        "CREATE INDEX IF NOT EXISTS idx_logs_project ON daily_logs(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_logs_date ON daily_logs(log_date)",
        "CREATE INDEX IF NOT EXISTS idx_quality_project ON quality_tests(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_photos_project ON photos(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_photos_phase ON photos(phase)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_project ON material_records(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_name ON material_records(material_name)",
        "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
        "CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(name)",
        "CREATE INDEX IF NOT EXISTS idx_supplier_prices_supplier ON supplier_prices(supplier_id)",
        "CREATE INDEX IF NOT EXISTS idx_supplier_prices_material ON supplier_prices(material_name)",
        "CREATE INDEX IF NOT EXISTS idx_curing_project ON curing_records(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_curing_date ON curing_records(record_date)",
        "CREATE INDEX IF NOT EXISTS idx_workers_team ON workers(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_work_hours_project ON work_hours(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_work_hours_worker ON work_hours(worker_id)",
        "CREATE INDEX IF NOT EXISTS idx_work_hours_date ON work_hours(work_date)",
        "CREATE INDEX IF NOT EXISTS idx_budget_project ON budget_items(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_budget_category ON budget_items(category)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_project ON notifications(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)",
    ]
    for idx in indexes:
        cursor.execute(idx)

    # 分析优化
    cursor.execute("ANALYZE")

    conn.commit()
    conn.close()
    return {"indexes_created": len(indexes)}


def get_db_stats() -> Dict:
    """获取数据库统计信息"""
    conn = get_db()
    cursor = conn.cursor()

    stats = {}
    tables = ["projects", "daily_logs", "quality_tests", "checklist_state",
              "material_records", "photos", "suppliers", "supplier_prices",
              "curing_records", "workers", "teams", "work_hours",
              "budget_items", "notifications"]
    for table in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        stats[table] = count

    # 数据库大小
    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    stats["db_size_bytes"] = db_size
    stats["db_size_mb"] = round(db_size / 1024 / 1024, 2)

    conn.close()
    return stats


# ============================================================
# 数据导入
# ============================================================

def import_project(data: Dict) -> Dict:
    """
    从导出的数据导入项目（含所有关联数据）

    参数:
        data: export_project_data() 导出的字典

    返回:
        导入结果
    """
    project_data = data.get('project', {})
    if not project_data:
        return {"error": "无项目数据"}

    # 创建项目
    pid = create_project(
        name=project_data.get('name', '导入项目'),
        area=float(project_data.get('area', 100)),
        base_thickness=float(project_data.get('base_thickness', 50)),
        surface_thickness=float(project_data.get('surface_thickness', 15)),
        start_date=project_data.get('start_date', ''),
        location=project_data.get('location', ''),
    )

    conn = get_db()
    cursor = conn.cursor()

    import_count = {"logs": 0, "quality": 0, "materials": 0}

    # 导入施工日志
    for log in data.get('daily_logs', []):
        cursor.execute("""
            INSERT INTO daily_logs (project_id, log_date, weather, temperature,
                workers, work_content, materials_used, issues)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, log.get('log_date', ''), log.get('weather', '晴'),
              log.get('temperature', ''), int(log.get('workers', 5)),
              log.get('work_content', ''), log.get('materials_used', ''),
              log.get('issues', '无')))
        import_count["logs"] += 1

    # 导入质量检测
    for qt in data.get('quality_tests', []):
        cursor.execute("""
            INSERT INTO quality_tests (project_id, test_id, test_name,
                standard_value, actual_value, is_pass)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pid, qt.get('test_id', ''), qt.get('test_name', ''),
              qt.get('standard_value', ''), qt.get('actual_value', ''),
              1 if qt.get('is_pass') else 0))
        import_count["quality"] += 1

    # 导入材料记录
    for mat in data.get('material_records', []):
        cursor.execute("""
            INSERT INTO material_records (project_id, material_name,
                quantity_kg, quantity_packages, unit_price, total_cost, record_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pid, mat.get('material_name', ''), float(mat.get('quantity_kg', 0)),
              float(mat.get('quantity_packages', 0)), float(mat.get('unit_price', 0)),
              float(mat.get('total_cost', 0)), mat.get('record_date', '')))
        import_count["materials"] += 1

    # 导入预算
    for bi in data.get('budget_items', []):
        cursor.execute("""
            INSERT INTO budget_items (project_id, category, planned_amount, actual_amount, description)
            VALUES (?, ?, ?, ?, ?)
        """, (pid, bi.get('category', ''), float(bi.get('planned_amount', 0)),
              float(bi.get('actual_amount', 0)), bi.get('description', '')))
        import_count["budget"] = import_count.get("budget", 0) + 1

    # 导入养护记录
    for cr in data.get('curing_records', []):
        cursor.execute("""
            INSERT INTO curing_records (project_id, record_date, weather,
                temp_min, temp_max, humidity, wind_level, curing_measure, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, cr.get('record_date', ''), cr.get('weather', '晴'),
              float(cr.get('temp_min', 20)), float(cr.get('temp_max', 25)),
              float(cr.get('humidity', 60)), cr.get('wind_level', ''),
              cr.get('curing_measure', ''), cr.get('notes', '')))
        import_count["curing"] = import_count.get("curing", 0) + 1

    conn.commit()
    conn.close()

    return {
        "project_id": pid,
        "project_name": project_data.get('name', ''),
        "imported": import_count,
    }
