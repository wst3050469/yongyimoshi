"""
永颐无机磨石 - 施工管理平台 v3.2
Flask + SQLite + 29个API端点
"""

from flask import Flask, render_template, request, jsonify, make_response
from datetime import datetime
from validation import (
    validate_project_data, validate_inventory_data,
    validate_required, api_error, api_success, ValidationError,
    VALID_MATERIALS, VALID_PHASES
)
from materials_calc import (
    calculate_all, generate_schedule, calc_purchase_list,
    calc_cost, QUALITY_TESTS
)
from database import (
    create_project, get_projects, get_project, update_project, delete_project,
    save_daily_log, get_daily_logs,
    get_checklist, update_checklist,
    get_quality_tests, save_quality_tests,
    get_dashboard_data, generate_report,
    add_material_record, get_material_inventory, get_material_records,
    export_project_data, backup_database,
    add_photo, get_photos, get_photo_by_id, delete_photo,
    get_timeline_data,
)
import json

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


# ============================================================
# 项目管理
# ============================================================

@app.route('/api/projects', methods=['GET'])
def api_projects_list():
    return jsonify(get_projects())


@app.route('/api/projects', methods=['POST'])
def api_project_create():
    data = request.get_json()
    if not data:
        return api_error("请求数据为空")
    errors = validate_project_data(data)
    if errors:
        return api_error("数据验证失败", details={"fields": errors})
    pid = create_project(
        name=data.get('name', '新建项目'),
        area=float(data.get('area', 100)),
        base_thickness=float(data.get('base_thickness', 50)),
        surface_thickness=float(data.get('surface_thickness', 15)),
        start_date=data.get('start_date', ''),
        location=data.get('location', ''),
    )
    return jsonify({"id": pid, "status": "created"})


@app.route('/api/projects/<int:pid>', methods=['GET'])
def api_project_get(pid):
    project = get_project(pid)
    return jsonify(project) if project else (jsonify({"error": "not found"}), 404)


@app.route('/api/projects/<int:pid>', methods=['PUT'])
def api_project_update(pid):
    data = request.get_json()
    ok = update_project(pid, **data)
    return jsonify({"status": "ok" if ok else "no changes"})


@app.route('/api/projects/<int:pid>', methods=['DELETE'])
def api_project_delete(pid):
    ok = delete_project(pid)
    return jsonify({"status": "deleted" if ok else "error"})


# ============================================================
# 材料计算
# ============================================================

@app.route('/api/calc', methods=['POST'])
def api_calc():
    data = request.get_json()
    result = calculate_all(
        float(data.get('area', 100)),
        float(data.get('thickness_base', 50)),
        float(data.get('thickness_surface', 15)),
    )
    return jsonify(result)


@app.route('/api/purchase', methods=['POST'])
def api_purchase():
    data = request.get_json()
    result = calculate_all(
        float(data.get('area', 100)),
        float(data.get('thickness_base', 50)),
        float(data.get('thickness_surface', 15)),
    )
    from materials_calc import PACKAGING_SPECS
    return jsonify({
        "area": result['area'],
        "purchase_list": calc_purchase_list(result["summary"]),
        "packaging_specs": PACKAGING_SPECS,
    })


@app.route('/api/cost', methods=['POST'])
def api_cost():
    data = request.get_json()
    area = float(data.get('area', 100))
    result = calculate_all(area,
        float(data.get('thickness_base', 50)),
        float(data.get('thickness_surface', 15)))
    purchase = calc_purchase_list(result["summary"])
    return jsonify(calc_cost(area, purchase))


@app.route('/api/materials-list')
def api_materials_list():
    from materials_calc import PACKAGING_SPECS, UNIT_PRICES
    result = []
    for name, spec in PACKAGING_SPECS.items():
        price = UNIT_PRICES.get(name, {})
        result.append({"name": name, "unit": spec["unit"],
                       "per_package": spec["per_package"],
                       "note": spec["note"],
                       "unit_price": price.get("price", 0)})
    return jsonify(result)


# ============================================================
# 进度计划
# ============================================================

@app.route('/api/schedule', methods=['GET'])
def api_schedule():
    from datetime import datetime
    start = request.args.get('start', datetime.now().strftime('%Y-%m-%d'))
    return jsonify(generate_schedule(start))


# ============================================================
# 检查清单
# ============================================================

@app.route('/api/checklist', methods=['GET'])
def api_checklist_get():
    pid = request.args.get('project_id', 1, type=int)
    try:
        return jsonify(get_checklist(pid))
    except Exception:
        from materials_calc import CHECKLIST_ITEMS
        return jsonify(CHECKLIST_ITEMS)


@app.route('/api/checklist', methods=['POST'])
def api_checklist_save():
    data = request.get_json()
    update_checklist(int(data.get('project_id', 1)),
                     data.get('items', data))
    return jsonify({"status": "ok"})


# ============================================================
# 施工日志
# ============================================================

@app.route('/api/daily-log', methods=['POST'])
def api_daily_log():
    data = request.get_json()
    if not data:
        return api_error("请求数据为空")
    err = validate_required(data, ['date'])
    if err:
        return api_error(err)
    log_id = save_daily_log(int(data.get('project_id', 1)), data)
    return jsonify({"status": "ok", "id": log_id})


@app.route('/api/daily-logs', methods=['GET'])
def api_daily_logs():
    pid = request.args.get('project_id', 1, type=int)
    return jsonify(get_daily_logs(pid))


# ============================================================
# 质量检测
# ============================================================

@app.route('/api/quality-tests', methods=['GET'])
def api_quality_tests_get():
    pid = request.args.get('project_id', 1, type=int)
    try:
        return jsonify(get_quality_tests(pid))
    except Exception:
        return jsonify({"templates": QUALITY_TESTS, "results": {}})


@app.route('/api/quality-tests', methods=['POST'])
def api_quality_tests_save():
    data = request.get_json()
    save_quality_tests(int(data.get('project_id', 1)),
                       data.get('results', data))
    return jsonify({"status": "ok"})


# ============================================================
# 施工照片
# ============================================================

@app.route('/api/photos', methods=['GET'])
def api_photos_get():
    pid = request.args.get('project_id', 1, type=int)
    phase = request.args.get('phase', '')
    return jsonify(get_photos(pid, phase))


@app.route('/api/photos', methods=['POST'])
def api_photos_add():
    data = request.get_json()
    result = add_photo(
        project_id=int(data.get('project_id', 1)),
        phase=data.get('phase', ''),
        description=data.get('description', ''),
        image_data=data.get('image_data', ''),
    )
    return jsonify(result)


@app.route('/api/photo/<int:photo_id>')
def api_photo_get_file(photo_id):
    photo = get_photo_by_id(photo_id)
    if not photo:
        return jsonify({"error": "not found"}), 404
    from flask import send_file
    import os
    path = os.path.join(os.path.dirname(__file__), 'data', 'photos', photo['filename'])
    if os.path.exists(path):
        ext = photo['filename'].split('.')[-1]
        return send_file(path, mimetype=f'image/{ext}')
    return jsonify({"error": "file not found"}), 404


@app.route('/api/photos/<int:photo_id>', methods=['DELETE'])
def api_photo_delete(photo_id):
    return jsonify({"status": "deleted" if delete_photo(photo_id) else "error"})


# ============================================================
# 库存管理
# ============================================================

@app.route('/api/inventory', methods=['GET'])
def api_inventory_get():
    pid = request.args.get('project_id', 1, type=int)
    return jsonify({
        "inventory": get_material_inventory(pid),
        "records": get_material_records(pid),
    })


@app.route('/api/inventory', methods=['POST'])
def api_inventory_add():
    data = request.get_json()
    if not data:
        return api_error("请求数据为空")
    errors = validate_inventory_data(data)
    if errors:
        return api_error("数据验证失败", details={"fields": errors})
    rid = add_material_record(
        project_id=int(data.get('project_id', 1)),
        material_name=data.get('material_name', ''),
        quantity_kg=float(data.get('quantity_kg', 0)),
        unit_price=float(data.get('unit_price', 0)),
        record_date=data.get('record_date', ''),
    )
    return jsonify({"status": "ok", "id": rid})


# ============================================================
# 时间轴
# ============================================================

@app.route('/api/timeline/<int:pid>')
def api_timeline(pid):
    return jsonify(get_timeline_data(pid))


# ============================================================
# 看板 & 报告
# ============================================================

@app.route('/project/<int:pid>/dashboard')
def project_dashboard(pid):
    """项目总览仪表盘页面"""
    from database import get_project, get_dashboard_data, get_quality_tests, get_daily_logs
    from materials_calc import calculate_all
    
    project = get_project(pid)
    if not project:
        return api_error("项目不存在", code=404)
    
    dashboard = get_dashboard_data(pid)
    quality = get_quality_tests(pid)
    logs = get_daily_logs(pid)[:5]
    calc = calculate_all(project['area'], project['base_thickness'], project['surface_thickness'])
    
    # 阶段进度
    phase_progress = dashboard.get('phase_progress', {})
    
    # 质量检测数据
    quality_tests = []
    for t in quality.get('templates', []):
        quality_tests.append({
            "test_name": t['name'],
            "standard_value": t['standard'],
            "actual_value": quality['results'].get(t['id'], ''),
            "is_pass": quality['results'].get(t['id'] + '_pass', False),
        })
    
    # 统计
    stats = {
        "total_items": dashboard.get('total_items', 0),
        "log_count": dashboard.get('log_count', 0),
        "photo_count": len(get_photos(pid)),
        "quality_total": len(quality_tests),
    }
    
    from datetime import datetime
    return render_template('project_dashboard.html',
        project=project,
        dashboard=dashboard,
        phase_progress=phase_progress,
        quality_tests=quality_tests,
        recent_logs=logs,
        materials=calc['summary'],
        materials_total=calc['total_weight_kg'],
        stats=stats,
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M'),
    )


@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    pid = request.args.get('project_id', 1, type=int)
    try:
        return jsonify(get_dashboard_data(pid))
    except Exception:
        return jsonify({"overall_progress": 0})


@app.route('/api/report/<int:pid>')
def api_report(pid):
    return jsonify(generate_report(pid))


# ============================================================
# 数据导出 & 备份
# ============================================================

@app.route('/api/export/<int:pid>')
def api_export(pid):
    return jsonify(export_project_data(pid))


@app.route('/api/import', methods=['POST'])
def api_import():
    """从JSON导入项目"""
    from database import import_project
    data = request.get_json()
    if not data:
        return jsonify({"error": "无数据"}), 400
    result = import_project(data)
    return jsonify(result)


@app.route('/api/backup', methods=['POST'])
def api_backup():
    path = backup_database()
    return jsonify({"status": "ok", "backup_path": path})


# ============================================================
# 技术参数
# ============================================================

@app.route('/api/params')
def api_params():
    return jsonify({
        "environment": {"temperature": "5~30℃", "humidity": "40~70%",
                        "base_moisture": "≤8%（基层）/ ≤6%（面层）"},
        "base_layer": {"thickness": "30~50mm", "density": "2200 kg/m³",
                       "curing_days": 7, "strength_7d": "≥25MPa"},
        "surface_layer": {"thickness": "15mm", "curing_days": 7, "strength_3d": "≥25MPa"},
        "final_acceptance": {"strength_28d": "≥50MPa", "gloss_uncoated": "≥40 GU",
                            "gloss_coated": "≥70 GU", "wear_resistance": "≤0.05 g/cm²",
                            "anti_slip": "R10"},
    })


# ============================================================
# API文档
# ============================================================

@app.route('/api/docs-page')
def api_docs_page():
    rules = []
    stats = {"GET": 0, "POST": 0, "PUT": 0, "DELETE": 0}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static' and not rule.rule.startswith('/api/docs'):
            methods = sorted(rule.methods - {'HEAD', 'OPTIONS'})
            for m in methods:
                stats[m] = stats.get(m, 0) + 1
            rules.append({"path": rule.rule, "methods": methods, "endpoint": rule.endpoint})
    rules.sort(key=lambda r: r['path'])
    return render_template('api_docs.html', endpoints=rules, stats=stats)


@app.route('/api/docs')
def api_docs():
    rules = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static' and not rule.rule.startswith('/api/docs'):
            rules.append({
                "path": rule.rule,
                "methods": sorted(rule.methods - {'HEAD', 'OPTIONS'}),
                "endpoint": rule.endpoint,
            })
    return jsonify({"title": "永颐无机磨石 · API文档", "version": "3.2.0",
                    "endpoints": sorted(rules, key=lambda r: r['path'])})




# ============================================================
# 系统管理
# ============================================================

@app.route('/api/system/optimize', methods=['POST'])
def api_system_optimize():
    """数据库性能优化"""
    from database import optimize_database
    result = optimize_database()
    return jsonify({"status": "ok", "result": result})


@app.route('/api/system/stats')
def api_system_stats():
    """系统统计数据"""
    from database import get_db_stats
    return jsonify(get_db_stats())



# ============================================================
# 系统配置 & 管理
# ============================================================

from config import load_config, save_config, get_config, update_config, get_system_status, cleanup_old_data


@app.route('/api/config', methods=['GET'])
def api_config_get():
    """获取系统配置"""
    section = request.args.get('section', '')
    return jsonify(get_config(section))


@app.route('/api/config', methods=['PUT'])
def api_config_update():
    """更新系统配置"""
    data = request.get_json()
    if not data:
        return api_error("请求数据为空")
    section = data.get('section', '')
    updates = data.get('updates', {})
    if not section or not updates:
        return api_error("缺少 section 或 updates")
    ok = update_config(section, updates)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/system/status')
def api_system_status():
    """系统运行状态"""
    return jsonify(get_system_status())


@app.route('/api/system/cleanup', methods=['POST'])
def api_system_cleanup():
    """清理旧数据"""
    data = request.get_json() or {}
    days = int(data.get('days', 90))
    result = cleanup_old_data(days)
    return jsonify({"status": "ok", "result": result})


@app.route('/admin')
def admin_page():
    """系统管理页面"""
    return render_template('admin.html')


# ============================================================
# 批量操作
# ============================================================

@app.route('/api/projects/batch', methods=['POST'])
def api_projects_batch():
    """批量操作项目"""
    from database import delete_project
    data = request.get_json()
    action = data.get('action', '')
    ids = data.get('ids', [])

    if not ids:
        return api_error("未选择项目")

    results = {"success": 0, "failed": 0}

    if action == 'delete':
        for pid in ids:
            try:
                delete_project(pid)
                results["success"] += 1
            except:
                results["failed"] += 1
    elif action == 'export':
        from database import export_project_data
        exports = []
        for pid in ids:
            try:
                exports.append(export_project_data(pid))
                results["success"] += 1
            except:
                results["failed"] += 1
        return jsonify({"status": "ok", "action": action, "exports": exports, "results": results})
    else:
        return api_error(f"不支持的操作: {action}")

    return jsonify({"status": "ok", "action": action, "results": results})


# ============================================================
# 供应商管理
# ============================================================

from database import (
    add_supplier, get_suppliers, get_supplier, update_supplier, delete_supplier,
    add_supplier_price, get_supplier_prices, get_best_prices,
    add_curing_record, get_curing_records, delete_curing_record,
)


@app.route('/suppliers')
def suppliers_page():
    """供应商管理页面"""
    return render_template('suppliers.html')


@app.route('/api/suppliers', methods=['GET'])
def api_suppliers_list():
    """供应商列表"""
    return jsonify(get_suppliers())


@app.route('/api/suppliers', methods=['POST'])
def api_suppliers_add():
    """添加供应商"""
    data = request.get_json()
    if not data or not data.get('name'):
        return api_error("供应商名称不能为空")
    sid = add_supplier(
        name=data['name'],
        contact_person=data.get('contact_person', ''),
        phone=data.get('phone', ''),
        address=data.get('address', ''),
        materials=json.dumps(data.get('materials', []), ensure_ascii=False),
        rating=int(data.get('rating', 3)),
        notes=data.get('notes', ''),
    )
    return jsonify({"status": "ok", "id": sid})


@app.route('/api/suppliers/<int:sid>', methods=['GET'])
def api_suppliers_get(sid):
    """获取供应商详情"""
    s = get_supplier(sid)
    if not s:
        return api_error("供应商不存在")
    # 解析materials JSON
    try:
        s['materials_list'] = json.loads(s.get('materials', '[]'))
    except:
        s['materials_list'] = []
    return jsonify(s)


@app.route('/api/suppliers/<int:sid>', methods=['PUT'])
def api_suppliers_update(sid):
    """更新供应商"""
    data = request.get_json() or {}
    if 'materials' in data:
        data['materials'] = json.dumps(data['materials'], ensure_ascii=False)
    ok = update_supplier(sid, **data)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/suppliers/<int:sid>', methods=['DELETE'])
def api_suppliers_delete(sid):
    """删除供应商"""
    ok = delete_supplier(sid)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/suppliers/<int:sid>/prices', methods=['GET'])
def api_supplier_prices(sid):
    """供应商报价历史"""
    return jsonify(get_supplier_prices(sid))


@app.route('/api/suppliers/<int:sid>/prices', methods=['POST'])
def api_supplier_prices_add(sid):
    """添加报价记录"""
    data = request.get_json()
    if not data or not data.get('material_name') or not data.get('unit_price'):
        return api_error("材料名称和单价必填")
    pid = add_supplier_price(
        supplier_id=sid,
        material_name=data['material_name'],
        unit_price=float(data['unit_price']),
        price_date=data.get('price_date', ''),
        notes=data.get('notes', ''),
    )
    return jsonify({"status": "ok", "id": pid})


@app.route('/api/prices/best/<material_name>')
def api_best_prices(material_name):
    """获取材料最优报价"""
    return jsonify(get_best_prices(material_name))


# ============================================================
# 养护记录管理
# ============================================================

@app.route('/api/curing', methods=['GET'])
def api_curing_list():
    """养护记录列表"""
    project_id = request.args.get('project_id', 0, type=int)
    if not project_id:
        return api_error("缺少 project_id 参数")
    return jsonify(get_curing_records(project_id))


@app.route('/api/curing', methods=['POST'])
def api_curing_add():
    """添加养护记录"""
    data = request.get_json()
    if not data or not data.get('project_id'):
        return api_error("缺少 project_id")
    rid = add_curing_record(
        project_id=int(data['project_id']),
        record_date=data.get('record_date', ''),
        weather=data.get('weather', '晴'),
        temp_min=float(data.get('temp_min', 20)),
        temp_max=float(data.get('temp_max', 25)),
        humidity=float(data.get('humidity', 60)),
        wind_level=data.get('wind_level', ''),
        curing_measure=data.get('curing_measure', ''),
        notes=data.get('notes', ''),
    )
    return jsonify({"status": "ok", "id": rid})


@app.route('/api/curing/<int:rid>', methods=['DELETE'])
def api_curing_delete(rid):
    """删除养护记录"""
    ok = delete_curing_record(rid)
    return jsonify({"status": "ok" if ok else "error"})


# ============================================================
# 打印报告
# ============================================================

@app.route('/project/<int:pid>/report')
def print_report(pid):
    """施工方案打印报告"""
    from database import generate_report
    report = generate_report(pid)
    if 'error' in report:
        return api_error(report['error'])
    return render_template('print_report.html', report=report)


# ============================================================
# 班组 & 工人管理
# ============================================================

from database import (
    add_team, get_teams, delete_team,
    add_worker, get_workers, get_worker, update_worker, delete_worker,
    add_work_hours, get_work_hours, get_work_hours_summary,
    add_budget_item, get_budget_items, get_budget_summary,
    update_budget_item, delete_budget_item,
    add_notification, get_notifications, mark_notification_read,
    mark_all_notifications_read, delete_notification,
    create_curing_reminder, create_quality_test_reminder,
)


@app.route('/workers')
def workers_page():
    """工人管理页面"""
    return render_template('workers.html')


@app.route('/api/teams', methods=['GET'])
def api_teams_list():
    return jsonify(get_teams())


@app.route('/api/teams', methods=['POST'])
def api_teams_add():
    data = request.get_json()
    if not data or not data.get('name'):
        return api_error("班组名称不能为空")
    tid = add_team(name=data['name'], leader=data.get('leader', ''),
                   specialty=data.get('specialty', ''))
    return jsonify({"status": "ok", "id": tid})


@app.route('/api/teams/<int:tid>', methods=['DELETE'])
def api_teams_delete(tid):
    delete_team(tid)
    return jsonify({"status": "ok"})


@app.route('/api/workers', methods=['GET'])
def api_workers_list():
    team_id = request.args.get('team_id', 0, type=int)
    return jsonify(get_workers(team_id))


@app.route('/api/workers', methods=['POST'])
def api_workers_add():
    data = request.get_json()
    if not data or not data.get('name'):
        return api_error("工人姓名不能为空")
    wid = add_worker(
        name=data['name'], phone=data.get('phone', ''),
        role=data.get('role', '工人'),
        team_id=int(data.get('team_id', 0)),
        hourly_rate=float(data.get('hourly_rate', 0)),
        notes=data.get('notes', ''),
    )
    return jsonify({"status": "ok", "id": wid})


@app.route('/api/workers/<int:wid>', methods=['GET'])
def api_workers_get(wid):
    w = get_worker(wid)
    if not w:
        return api_error("工人不存在")
    return jsonify(w)


@app.route('/api/workers/<int:wid>', methods=['PUT'])
def api_workers_update(wid):
    data = request.get_json() or {}
    ok = update_worker(wid, **data)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/workers/<int:wid>', methods=['DELETE'])
def api_workers_delete(wid):
    ok = delete_worker(wid)
    return jsonify({"status": "ok" if ok else "error"})


# ============================================================
# 工时管理
# ============================================================

@app.route('/api/work-hours', methods=['GET'])
def api_work_hours_list():
    project_id = request.args.get('project_id', 0, type=int)
    if not project_id:
        return api_error("缺少 project_id")
    return jsonify(get_work_hours(project_id))


@app.route('/api/work-hours', methods=['POST'])
def api_work_hours_add():
    data = request.get_json()
    if not data or not data.get('project_id') or not data.get('worker_id'):
        return api_error("缺少 project_id 或 worker_id")
    wid = add_work_hours(
        project_id=int(data['project_id']),
        worker_id=int(data['worker_id']),
        work_date=data.get('work_date', ''),
        hours=float(data.get('hours', 8)),
        work_type=data.get('work_type', ''),
        notes=data.get('notes', ''),
    )
    return jsonify({"status": "ok", "id": wid})


@app.route('/api/work-hours/summary')
def api_work_hours_summary():
    project_id = request.args.get('project_id', 0, type=int)
    if not project_id:
        return api_error("缺少 project_id")
    return jsonify(get_work_hours_summary(project_id))


# ============================================================
# 成本预算管理
# ============================================================

@app.route('/api/budget', methods=['GET'])
def api_budget_list():
    project_id = request.args.get('project_id', 0, type=int)
    if not project_id:
        return api_error("缺少 project_id")
    return jsonify(get_budget_items(project_id))


@app.route('/api/budget', methods=['POST'])
def api_budget_add():
    data = request.get_json()
    if not data or not data.get('project_id') or not data.get('category'):
        return api_error("缺少 project_id 或 category")
    bid = add_budget_item(
        project_id=int(data['project_id']),
        category=data['category'],
        planned_amount=float(data.get('planned_amount', 0)),
        actual_amount=float(data.get('actual_amount', 0)),
        description=data.get('description', ''),
    )
    return jsonify({"status": "ok", "id": bid})


@app.route('/api/budget/<int:bid>', methods=['PUT'])
def api_budget_update(bid):
    data = request.get_json() or {}
    ok = update_budget_item(bid, **data)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/budget/<int:bid>', methods=['DELETE'])
def api_budget_delete(bid):
    delete_budget_item(bid)
    return jsonify({"status": "ok"})


@app.route('/api/budget/summary')
def api_budget_summary():
    project_id = request.args.get('project_id', 0, type=int)
    if not project_id:
        return api_error("缺少 project_id")
    return jsonify(get_budget_summary(project_id))


# ============================================================
# 通知提醒系统
# ============================================================

@app.route('/notifications')
def notifications_page():
    """通知中心页面"""
    return render_template('notifications.html')


@app.route('/api/notifications', methods=['GET'])
def api_notifications_list():
    project_id = request.args.get('project_id', 0, type=int)
    unread_only = request.args.get('unread_only', '').lower() in ('1', 'true', 'yes')
    return jsonify(get_notifications(project_id, unread_only))


@app.route('/api/notifications', methods=['POST'])
def api_notifications_add():
    """手动创建通知"""
    data = request.get_json()
    if not data or not data.get('project_id') or not data.get('title'):
        return api_error("缺少 project_id 或 title")
    nid = add_notification(
        project_id=int(data['project_id']),
        notif_type=data.get('type', 'manual'),
        title=data['title'],
        message=data.get('message', ''),
        due_date=data.get('due_date', ''),
    )
    return jsonify({"status": "ok", "id": nid})


@app.route('/api/notifications/remind/curing', methods=['POST'])
def api_notify_curing():
    """创建养护提醒"""
    data = request.get_json()
    pid = int(data.get('project_id', 0))
    if not pid:
        return api_error("缺少 project_id")
    nid = create_curing_reminder(pid)
    return jsonify({"status": "ok", "id": nid})


@app.route('/api/notifications/remind/test', methods=['POST'])
def api_notify_test():
    """创建检测提醒"""
    data = request.get_json()
    pid = int(data.get('project_id', 0))
    if not pid:
        return api_error("缺少 project_id")
    nid = create_quality_test_reminder(pid)
    return jsonify({"status": "ok", "id": nid})


@app.route('/api/notifications/<int:nid>/read', methods=['POST'])
def api_notifications_read(nid):
    mark_notification_read(nid)
    return jsonify({"status": "ok"})


@app.route('/api/notifications/read-all', methods=['POST'])
def api_notifications_read_all():
    data = request.get_json() or {}
    project_id = int(data.get('project_id', 0))
    count = mark_all_notifications_read(project_id)
    return jsonify({"status": "ok", "marked_read": count})


@app.route('/api/notifications/<int:nid>', methods=['DELETE'])
def api_notifications_delete(nid):
    delete_notification(nid)
    return jsonify({"status": "ok"})


@app.route('/api/notifications/unread-count')
def api_notifications_unread_count():
    """未读通知数量（全局首页角标用）"""
    notifs = get_notifications(project_id=0, unread_only=True)
    return jsonify({"count": len(notifs)})


# ============================================================
# 设备管理
# ============================================================

from database import (
    add_equipment, get_equipment, update_equipment, delete_equipment,
    add_equipment_usage, get_equipment_usage,
    add_acceptance, get_acceptances, get_acceptance,
    update_acceptance, update_acceptance_item, delete_acceptance,
    export_to_csv,
)


@app.route('/equipment')
def equipment_page():
    """设备管理页面"""
    return render_template('equipment.html')


@app.route('/api/equipment', methods=['GET'])
def api_equipment_list():
    return jsonify(get_equipment())


@app.route('/api/equipment', methods=['POST'])
def api_equipment_add():
    data = request.get_json()
    if not data or not data.get('name'):
        return api_error("设备名称不能为空")
    eid = add_equipment(
        name=data['name'], type_=data.get('type', ''),
        model=data.get('model', ''), quantity=int(data.get('quantity', 1)),
        unit=data.get('unit', '台'), status=data.get('status', '可用'),
        purchase_date=data.get('purchase_date', ''),
        next_maintenance=data.get('next_maintenance', ''),
        notes=data.get('notes', ''),
    )
    return jsonify({"status": "ok", "id": eid})


@app.route('/api/equipment/<int:eid>', methods=['GET'])
def api_equipment_get(eid):
    eq = get_equipment(eid)
    if not eq:
        return api_error("设备不存在")
    return jsonify(eq)


@app.route('/api/equipment/<int:eid>', methods=['PUT'])
def api_equipment_update(eid):
    data = request.get_json() or {}
    ok = update_equipment(eid, **data)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/equipment/<int:eid>', methods=['DELETE'])
def api_equipment_delete(eid):
    delete_equipment(eid)
    return jsonify({"status": "ok"})


@app.route('/api/equipment-usage', methods=['GET'])
def api_equipment_usage_list():
    project_id = request.args.get('project_id', 0, type=int)
    return jsonify(get_equipment_usage(project_id))


@app.route('/api/equipment-usage', methods=['POST'])
def api_equipment_usage_add():
    data = request.get_json()
    if not data or not data.get('equipment_id') or not data.get('project_id'):
        return api_error("缺少 equipment_id 或 project_id")
    uid = add_equipment_usage(
        equipment_id=int(data['equipment_id']),
        project_id=int(data['project_id']),
        quantity_used=int(data.get('quantity_used', 1)),
        start_date=data.get('start_date', ''),
        end_date=data.get('end_date', ''),
        operator=data.get('operator', ''),
        notes=data.get('notes', ''),
    )
    return jsonify({"status": "ok", "id": uid})


# ============================================================
# 验收管理
# ============================================================

@app.route('/acceptance')
def acceptance_page():
    """验收管理页面"""
    return render_template('acceptance.html')


@app.route('/api/acceptance', methods=['GET'])
def api_acceptance_list():
    project_id = request.args.get('project_id', 0, type=int)
    if not project_id:
        return api_error("缺少 project_id")
    return jsonify(get_acceptances(project_id))


@app.route('/api/acceptance', methods=['POST'])
def api_acceptance_add():
    data = request.get_json()
    if not data or not data.get('project_id') or not data.get('acceptance_type'):
        return api_error("缺少 project_id 或 acceptance_type")
    aid = add_acceptance(
        project_id=int(data['project_id']),
        acceptance_type=data['acceptance_type'],
        check_date=data.get('check_date', ''),
        inspector=data.get('inspector', ''),
        result=data.get('result', '待定'),
        defects=data.get('defects', ''),
        score=float(data.get('score', 0)),
        notes=data.get('notes', ''),
    )
    return jsonify({"status": "ok", "id": aid})


@app.route('/api/acceptance/<int:aid>', methods=['GET'])
def api_acceptance_get(aid):
    acc = get_acceptance(aid)
    if not acc:
        return api_error("验收记录不存在")
    return jsonify(acc)


@app.route('/api/acceptance/<int:aid>', methods=['PUT'])
def api_acceptance_update(aid):
    data = request.get_json() or {}
    ok = update_acceptance(aid, **data)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/acceptance/<int:aid>', methods=['DELETE'])
def api_acceptance_delete(aid):
    delete_acceptance(aid)
    return jsonify({"status": "ok"})


@app.route('/api/acceptance/item/<int:item_id>', methods=['PUT'])
def api_acceptance_item_update(item_id):
    data = request.get_json() or {}
    is_pass = 1 if data.get('is_pass') else 0
    actual_value = data.get('actual_value', '')
    update_acceptance_item(item_id, is_pass, actual_value)
    return jsonify({"status": "ok"})


# ============================================================
# CSV 导出
# ============================================================

@app.route('/api/export/csv/<table_name>')
def api_export_csv(table_name):
    """导出CSV数据"""
    project_id = request.args.get('project_id', 0, type=int)
    allowed_tables = ['logs', 'materials', 'quality', 'budget', 'work_hours', 'curing']
    if table_name not in allowed_tables:
        return api_error(f"不支持的表: {table_name}，支持: {', '.join(allowed_tables)}")

    csv_data = export_to_csv(project_id, table_name)
    if not csv_data:
        return api_error("无数据可导出")

    # 中文文件名
    filename_map = {
        'logs': '施工日志', 'materials': '材料记录',
        'quality': '质量检测', 'budget': '成本预算',
        'work_hours': '工时记录', 'curing': '养护记录',
    }
    filename = f"{filename_map.get(table_name, table_name)}_{datetime.now().strftime('%Y%m%d')}.csv"

    from flask import make_response
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    # Use ASCII-only filename for compatibility, encode Chinese in URL
    safe_filename = f"yongyi_{table_name}_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers['Content-Disposition'] = f'attachment; filename={safe_filename}'
    return response


# ============================================================
# 安全管理
# ============================================================

from database import (
    add_safety_check, get_safety_checks, get_safety_check, delete_safety_check,
    get_safety_check_templates,
    add_safety_incident, get_safety_incidents, update_safety_incident,
    delete_safety_incident,
    add_document, get_documents, get_document, delete_document,
)


@app.route('/safety')
def safety_page():
    return render_template('safety.html')


@app.route('/documents')
def documents_page():
    return render_template('documents.html')


@app.route('/calendar')
def calendar_page():
    return render_template('calendar.html')


@app.route('/api/safety/templates')
def api_safety_templates():
    return jsonify(get_safety_check_templates())


@app.route('/api/safety/checks', methods=['GET'])
def api_safety_checks_list():
    pid = request.args.get('project_id', 0, type=int)
    if not pid:
        return api_error("缺少 project_id")
    return jsonify(get_safety_checks(pid))


@app.route('/api/safety/checks', methods=['POST'])
def api_safety_checks_add():
    import json as _json
    data = request.get_json()
    if not data or not data.get('project_id'):
        return api_error("缺少 project_id")
    items = data.get('items', [])
    sid = add_safety_check(
        project_id=int(data['project_id']),
        check_date=data.get('check_date', ''),
        inspector=data.get('inspector', ''),
        check_type=data.get('check_type', '日常检查'),
        items=_json.dumps(items, ensure_ascii=False),
        result=data.get('result', '合格'),
        rectification=data.get('rectification', ''),
        notes=data.get('notes', ''),
    )
    return jsonify({"status": "ok", "id": sid})


@app.route('/api/safety/checks/<int:sid>', methods=['GET'])
def api_safety_check_get(sid):
    sc = get_safety_check(sid)
    if not sc:
        return api_error("记录不存在")
    import json as _json
    try:
        sc['items_list'] = _json.loads(sc.get('items', '[]'))
    except:
        sc['items_list'] = []
    return jsonify(sc)


@app.route('/api/safety/checks/<int:sid>', methods=['DELETE'])
def api_safety_check_delete(sid):
    delete_safety_check(sid)
    return jsonify({"status": "ok"})


@app.route('/api/safety/incidents', methods=['GET'])
def api_safety_incidents_list():
    pid = request.args.get('project_id', 0, type=int)
    if not pid:
        return api_error("缺少 project_id")
    return jsonify(get_safety_incidents(pid))


@app.route('/api/safety/incidents', methods=['POST'])
def api_safety_incidents_add():
    data = request.get_json()
    if not data or not data.get('project_id'):
        return api_error("缺少 project_id")
    iid = add_safety_incident(
        project_id=int(data['project_id']),
        incident_date=data.get('incident_date', ''),
        incident_type=data.get('incident_type', '其他'),
        severity=data.get('severity', '轻微'),
        description=data.get('description', ''),
        injured_person=data.get('injured_person', ''),
        treatment=data.get('treatment', ''),
        root_cause=data.get('root_cause', ''),
        preventive_measures=data.get('preventive_measures', ''),
    )
    return jsonify({"status": "ok", "id": iid})


@app.route('/api/safety/incidents/<int:iid>', methods=['PUT'])
def api_safety_incidents_update(iid):
    data = request.get_json() or {}
    ok = update_safety_incident(iid, **data)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/safety/incidents/<int:iid>', methods=['DELETE'])
def api_safety_incidents_delete(iid):
    delete_safety_incident(iid)
    return jsonify({"status": "ok"})


@app.route('/api/documents', methods=['GET'])
def api_documents_list():
    pid = request.args.get('project_id', 0, type=int)
    doc_type = request.args.get('type', '')
    return jsonify(get_documents(pid, doc_type))


@app.route('/api/documents', methods=['POST'])
def api_documents_upload():
    pid = request.form.get('project_id', 0, type=int)
    title = request.form.get('title', '未命名文档')
    doc_type = request.form.get('doc_type', 'other')
    description = request.form.get('description', '')
    version = request.form.get('version', 'v1.0')
    tags = request.form.get('tags', '[]')
    file = request.files.get('file')
    if not file or not file.filename:
        return api_error("请选择文件")
    file_data = file.read()
    result = add_document(
        project_id=pid, title=title, doc_type=doc_type,
        description=description, filename=file.filename,
        file_data=file_data, version=version, tags=tags,
    )
    return jsonify({"status": "ok", "document": result})


@app.route('/api/documents/<int:did>/download')
def api_documents_download(did):
    doc = get_document(did)
    if not doc:
        return api_error("文档不存在")
    filepath = os.path.join(os.path.dirname(__file__), 'data', 'documents', doc['filename'])
    if not os.path.exists(filepath):
        return api_error("文件不存在")
    from flask import send_file
    return send_file(filepath, as_attachment=True,
                     download_name=doc['filename'].split('_', 1)[-1] if '_' in doc['filename'] else doc['filename'])


@app.route('/api/documents/<int:did>', methods=['DELETE'])
def api_documents_delete(did):
    delete_document(did)
    return jsonify({"status": "ok"})


@app.route('/api/calendar')
def api_calendar():
    from database import get_projects, get_daily_logs, get_acceptances
    events = []
    for proj in get_projects():
        pid = proj['id']
        events.append({
            "id": f"p_start_{pid}", "title": f"🔨 {proj['name']}",
            "start": proj['start_date'], "end": proj['start_date'],
            "color": "#2980b9", "project_id": pid, "type": "milestone",
        })
        for acc in get_acceptances(pid):
            events.append({
                "id": f"acc_{acc['id']}",
                "title": f"📋 {acc['acceptance_type']}",
                "start": acc['check_date'], "end": acc['check_date'],
                "color": "#27ae60" if acc['result']=='合格' else "#e74c3c",
                "project_id": pid, "type": "acceptance",
            })
        log_dates = {}
        for log in get_daily_logs(pid):
            d = log['log_date']
            if d not in log_dates:
                log_dates[d] = {"count": 0, "weathers": set()}
            log_dates[d]["count"] += 1
            log_dates[d]["weathers"].add(log.get('weather',''))
        for date_str, info in log_dates.items():
            events.append({
                "id": f"log_{pid}_{date_str}",
                "title": f"👷 {proj['name']}",
                "start": date_str, "end": date_str,
                "color": "#8e44ad", "project_id": pid, "type": "work_day",
            })
    return jsonify(events)


# ============================================================
# 错误处理器
# ============================================================

@app.errorhandler(404)
def not_found(e):
    return api_error("接口不存在", code=404)

@app.errorhandler(405)
def method_not_allowed(e):
    return api_error("请求方法不允许", code=405)

@app.errorhandler(500)
def server_error(e):
    return api_error("服务器内部错误", code=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
