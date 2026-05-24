"""
永颐无机磨石 · 综合数据报告引擎 v4.5.0
提供项目对比分析、全平台概览和报告生成功能
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from database import (
    get_db, get_projects, get_project, get_dashboard_data,
    get_daily_logs, get_checklist,
    get_material_records, get_budget_summary
)


def _get_quality_stats_by_project(project_id: int):
    """获取项目质量检测统计数据"""
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    total = cursor.execute(
        "SELECT COUNT(*) FROM quality_tests WHERE project_id=? AND actual_value IS NOT NULL AND actual_value != ''",
        (project_id,)
    ).fetchone()[0]
    passed = cursor.execute(
        "SELECT COUNT(*) FROM quality_tests WHERE project_id=? AND actual_value IS NOT NULL AND actual_value != '' AND is_pass=1",
        (project_id,)
    ).fetchone()[0]
    conn.close()
    return total, passed, total - passed


def _get_quality_test_details(project_id: int):
    """获取项目质量检测详情列表"""
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT test_name, actual_value, is_pass, test_date FROM quality_tests WHERE project_id=? AND actual_value IS NOT NULL AND actual_value != '' ORDER BY test_date DESC",
        (project_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _get_quality_stats_all():
    """获取全局质量检测统计数据"""
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()
    total = cursor.execute(
        "SELECT COUNT(*) FROM quality_tests WHERE actual_value IS NOT NULL AND actual_value != ''"
    ).fetchone()[0]
    passed = cursor.execute(
        "SELECT COUNT(*) FROM quality_tests WHERE actual_value IS NOT NULL AND actual_value != '' AND is_pass=1"
    ).fetchone()[0]
    conn.close()
    return total, passed

def generate_project_compare(project_ids: List[int]) -> Dict:
    """多项目对比分析"""
    projects_data = []
    for pid in project_ids:
        project = get_project(pid)
        if not project:
            continue
        dashboard = get_dashboard_data(pid)
        budget = get_budget_summary(pid)
        logs = get_daily_logs(pid)
        materials = get_material_records(pid)

        quality_total, quality_passed, quality_failed = _get_quality_stats_by_project(pid)
        quality_rate = round(quality_passed / quality_total * 100, 1) if quality_total > 0 else 0

        budget_rate = 0
        if budget.get("planned", 0) > 0:
            budget_rate = round(budget["actual"] / budget["planned"] * 100, 1)

        projects_data.append({
            "id": pid,
            "name": project.get("name", f"项目#{pid}"),
            "area": project.get("area", 0),
            "status": project.get("status", "未知"),
            "base_thickness": project.get("base_thickness", 0),
            "surface_thickness": project.get("surface_thickness", 0),
            "progress": dashboard.get("overall_progress", 0),
            "log_count": len(logs),
            "material_count": len(materials),
            "quality": {
                "total": quality_total,
                "passed": quality_passed,
                "failed": quality_failed,
                "pass_rate": quality_rate,
            },
            "budget": {
                "planned": budget.get("planned", 0),
                "actual": budget.get("actual", 0),
                "execution_rate": budget_rate,
            },
            "created_at": project.get("created_at", ""),
        })

    return {
        "type": "project_compare",
        "count": len(projects_data),
        "projects": projects_data,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def generate_overview() -> Dict:
    """全平台数据概览"""
    conn = get_db()
    cursor = conn.cursor()

    projects = get_projects()
    total_projects = len(projects)
    status_distribution = {}
    for p in projects:
        status = p.get("status", "未知")
        status_distribution[status] = status_distribution.get(status, 0) + 1

    total_area = sum(p.get("area", 0) for p in projects)

    six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    rows = cursor.execute("""
        SELECT substr(log_date, 1, 7) as month, COUNT(*) as count
        FROM daily_logs
        WHERE log_date >= ?
        GROUP BY month
        ORDER BY month
    """, (six_months_ago,)).fetchall()
    log_trend = [{"month": r["month"], "count": r["count"]} for r in rows]

    quality_total, quality_passed = _get_quality_stats_all()

    tables_stats = {}
    for table in ["daily_logs", "quality_tests", "material_records", "photos",
                  "safety_checks", "curing_records", "suppliers", "workers", "equipment"]:
        try:
            tables_stats[table] = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except Exception:
            tables_stats[table] = 0

    conn.close()

    return {
        "type": "overview",
        "total_projects": total_projects,
        "total_area": total_area,
        "status_distribution": status_distribution,
        "log_trend": log_trend,
        "quality": {
            "total": quality_total,
            "passed": quality_passed,
            "pass_rate": round(quality_passed / quality_total * 100, 1) if quality_total > 0 else 0,
        },
        "tables": tables_stats,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def generate_project_report(project_id: int) -> Optional[Dict]:
    """生成单个项目完整报告"""
    from database import generate_report as _gen_report

    base_report = _gen_report(project_id)
    if "error" in base_report:
        return None

    project = base_report["project"]
    dashboard = base_report["dashboard"]
    budget = get_budget_summary(project_id)
    materials = get_material_records(project_id)
    quality_total, quality_passed, quality_failed = _get_quality_stats_by_project(project_id)
    quality_tests_list = _get_quality_test_details(project_id)

    total_material_cost = sum(m.get("total_cost", 0) for m in materials)
    material_breakdown = {}
    for m in materials:
        name = m.get("material_name", "其他")
        material_breakdown[name] = material_breakdown.get(name, 0) + m.get("total_cost", 0)

    return {
        "project": {
            "id": project.get("id"),
            "name": project.get("name"),
            "area": project.get("area", 0),
            "base_thickness": project.get("base_thickness", 0),
            "surface_thickness": project.get("surface_thickness", 0),
            "status": project.get("status", "未知"),
            "created_at": project.get("created_at", ""),
        },
        "progress": {
            "overall": dashboard.get("overall_progress", 0),
            "checked_items": dashboard.get("checked_items", 0),
            "total_items": dashboard.get("total_items", 0),
            "phase_progress": dashboard.get("phase_progress", {}),
        },
        "logs": {
            "count": dashboard.get("log_count", 0),
            "recent": base_report.get("logs", [])[-5:] if base_report.get("logs") else [],
        },
        "quality": {
            "total": quality_total,
            "passed": quality_passed,
            "failed": quality_failed,
            "pass_rate": round(quality_passed / quality_total * 100, 1) if quality_total > 0 else 0,
            "recent_tests": quality_tests_list[-5:] if quality_tests_list else [],
        },
        "materials": {
            "calculation": base_report.get("materials", {}),
            "records_count": len(materials),
            "total_cost": round(total_material_cost, 2),
            "cost_breakdown": {k: round(v, 2) for k, v in material_breakdown.items()},
        },
        "budget": {
            "planned": budget.get("planned", 0),
            "actual": budget.get("actual", 0),
            "execution_rate": round(budget["actual"] / budget["planned"] * 100, 1) if budget.get("planned", 0) > 0 else 0,
        },
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def generate_report_html(project_id: int) -> Optional[str]:
    """生成项目报告的HTML"""
    report = generate_project_report(project_id)
    if not report:
        return None

    p = report["project"]
    progress = report["progress"]
    logs = report["logs"]
    quality = report["quality"]
    materials = report["materials"]
    budget = report["budget"]

    phase_bars = ""
    for phase_name, phase_data in progress.get("phase_progress", {}).items():
        pct = phase_data.get("percent", 0)
        color = "#27ae60" if pct == 100 else "#2980b9" if pct > 0 else "#95a5a6"
        phase_bars += f"""
        <tr>
            <td style="padding:4px 8px;border-bottom:1px solid #eee;">{phase_name}</td>
            <td style="padding:4px 8px;border-bottom:1px solid #eee;">
                <div style="background:#f0f0f0;border-radius:4px;height:20px;overflow:hidden;">
                    <div style="background:{color};width:{pct}%;height:100%;"></div>
                </div>
            </td>
            <td style="padding:4px 8px;border-bottom:1px solid #eee;text-align:right;">{pct}%</td>
        </tr>"""

    log_items = ""
    for log in logs.get("recent", []):
        date = log.get("log_date", "")
        content = log.get("content", "")[:80]
        log_items += f"<li style='margin:4px 0;color:#555;'><strong>{date}</strong>: {content}</li>"

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>项目报告 - {p["name"]}</title>
<style>
body {{ font-family: 'Microsoft YaHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 20px; color: #333; }}
h1 {{ color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 8px; }}
h2 {{ color: #2c3e50; margin-top: 24px; }}
table {{ width: 100%; border-collapse: collapse; }}
th {{ background: #1a5276; color: white; padding: 8px; text-align: left; }}
td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
.card {{ background: #f8f9fa; border-radius: 8px; padding: 16px; margin: 12px 0; text-align: center; }}
.metric {{ font-size: 1.8rem; font-weight: 700; color: #1a5276; }}
.label {{ font-size: 0.8rem; color: #888; }}
.footer {{ margin-top: 40px; text-align: center; color: #aaa; font-size: 0.8rem; border-top: 1px solid #eee; padding-top: 16px; }}
</style>
</head>
<body>
<h1>📋 {p["name"]}</h1>
<p style="color:#888;">报告生成时间: {report["generated_at"]}</p>

<h2>📊 项目概况</h2>
<div style="display:flex;gap:16px;flex-wrap:wrap;">
    <div class="card"><div class="metric">{p["area"]}</div><div class="label">面积 (m²)</div></div>
    <div class="card"><div class="metric">{p["status"]}</div><div class="label">状态</div></div>
    <div class="card"><div class="metric">{progress["overall"]}%</div><div class="label">总进度</div></div>
    <div class="card"><div class="metric">{logs["count"]}</div><div class="label">施工日志</div></div>
</div>

<h2>📐 施工参数</h2>
<table>
<tr><th>参数</th><th>数值</th></tr>
<tr><td>基层厚度</td><td>{p["base_thickness"]} mm</td></tr>
<tr><td>面层厚度</td><td>{p["surface_thickness"]} mm</td></tr>
<tr><td>检查项进度</td><td>{progress["checked_items"]}/{progress["total_items"]}</td></tr>
</table>

<h2>🔍 各阶段进度</h2>
<table>
<tr><th>阶段</th><th>进度</th><th>百分比</th></tr>
{phase_bars}
</table>

<h2>✅ 质量检测</h2>
<div style="display:flex;gap:16px;flex-wrap:wrap;">
    <div class="card"><div class="metric">{quality["total"]}</div><div class="label">总检测数</div></div>
    <div class="card"><div class="metric" style="color:#27ae60;">{quality["pass_rate"]}%</div><div class="label">合格率</div></div>
    <div class="card"><div class="metric" style="color:#e74c3c;">{quality["failed"]}</div><div class="label">不合格数</div></div>
</div>

<h2>💰 材料与预算</h2>
<table>
<tr><th>项目</th><th>金额</th></tr>
<tr><td>材料总成本</td><td>¥{materials["total_cost"]}</td></tr>
<tr><td>预算总额</td><td>¥{budget["planned"]}</td></tr>
<tr><td>实际支出</td><td>¥{budget["actual"]}</td></tr>
<tr><td>预算执行率</td><td>{budget["execution_rate"]}%</td></tr>
</table>

<h2>📝 最近施工日志</h2>
<ul>{log_items}</ul>

<div class="footer">
    永颐无机磨石 · 施工管理平台 v4.5.0 | 浙江永颐装饰工程有限公司
</div>
</body>
</html>'''
    return html


def generate_pdf_report(project_id: int, output_path: Optional[str] = None) -> Optional[bytes]:
    """生成项目报告PDF"""
    html = generate_report_html(project_id)
    if not html:
        return None
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        return pdf_bytes
    except ImportError:
        return html.encode('utf-8')
    except Exception:
        return html.encode('utf-8')
