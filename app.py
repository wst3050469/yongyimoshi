"""
永颐无机磨石 - 施工管理平台 v3.2
Flask + SQLite + 29个API端点
"""

from flask import Flask, render_template, request, jsonify, make_response, session, redirect, url_for
from datetime import datetime
from functools import wraps
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
    export_project_data, backup_database, restore_database, get_backup_list,
    add_photo, get_photos, get_photo_by_id, delete_photo,
    get_timeline_data,
    get_user_by_username, get_user_by_id, get_users,
    add_user, update_user, delete_user, update_last_login,
    add_environment_record, get_environment_records,
    delete_environment_record, get_environment_stats,
)
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

app = Flask(__name__)

# ============================================================
# 全局模板上下文 - SEO/GEO 配置注入
# ============================================================
@app.context_processor
def inject_seo_config():
    """向所有模板注入SEO/GEO配置"""
    from config import get_config
    seo = get_config("seo", {})
    return {
        "seo_company_name": "浙江永颐装饰工程有限公司",
        "seo_company_telephone": seo.get("company_telephone", "13357048951"),
        "seo_company_email": seo.get("company_email", "info@jinmojianshe.com"),
        "seo_company_address": seo.get("company_address", "浙江省杭州市"),
        "seo_company_area_served": seo.get("company_area_served", "全国"),
        "seo_company_founding_date": seo.get("company_founding_date", "2018"),
        "seo_baidu_tongji_id": seo.get("baidu_tongji_id", ""),
        "seo_site_url": "https://ai.jinmojianshe.com",
        "seo_site_name": "永颐无机磨石 · 施工管理平台",
    }
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError(
        "❌ SECRET_KEY 环境变量未设置！\n"
        "   请在运行前设置: export SECRET_KEY='your-secure-random-key-here'\n"
        "   或创建 .env 文件并添加: SECRET_KEY=your-secure-random-key-here"
    )


# ============================================================
# 反向代理路径前缀支持（用于 Nginx 子路径部署）
# ============================================================

class PrefixMiddleware:
    """WSGI 中间件：处理反向代理的路径前缀"""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ.get('PATH_INFO', '')
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]
        return self.app(environ, start_response)

app.wsgi_app = PrefixMiddleware(app.wsgi_app)


# ============================================================
# 认证装饰器
# ============================================================

def login_required(f):
    """需要登录才能访问"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return api_error("未登录，请先登录", code=401)
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """需要管理员权限"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return api_error("未登录，请先登录", code=401)
        if session.get('role') != 'admin':
            return api_error("需要管理员权限", code=403)
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """获取当前登录用户"""
    if 'user_id' in session:
        return get_user_by_id(session['user_id'])
    return None


@app.route('/')
def index():
    user = get_current_user()
    return render_template('index.html', user=user)


# ============================================================
# 用户认证
# ============================================================

@app.route('/login')
def login_page():
    """登录页面"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    """用户登录"""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return api_error("用户名和密码不能为空")

    user = get_user_by_username(data['username'])
    if not user:
        return api_error("用户名或密码错误")
    if not user.get('is_active', 1):
        return api_error("账号已被禁用")
    if not check_password_hash(user['password_hash'], data['password']):
        return api_error("用户名或密码错误")

    session['user_id'] = user['id']
    session['username'] = user['username']
    session['display_name'] = user['display_name']
    session['role'] = user['role']
    update_last_login(user['id'])

    return jsonify({
        "status": "ok",
        "user": {
            "id": user['id'],
            "username": user['username'],
            "display_name": user['display_name'],
            "role": user['role'],
        }
    })


@app.route('/api/auth/logout', methods=['POST'])
def api_auth_logout():
    """用户登出"""
    session.clear()
    return jsonify({"status": "ok"})


@app.route('/api/auth/me')
@login_required
def api_auth_me():
    """当前用户信息"""
    user = get_current_user()
    if not user:
        session.clear()
        return api_error("用户不存在", code=401)
    return jsonify({
        "id": user['id'],
        "username": user['username'],
        "display_name": user['display_name'],
        "role": user['role'],
        "phone": user.get('phone', ''),
        "email": user.get('email', ''),
        "last_login": user.get('last_login', ''),
    })


@app.route('/api/auth/password', methods=['PUT'])
@login_required
def api_auth_password():
    """修改密码"""
    data = request.get_json()
    if not data or not data.get('old_password') or not data.get('new_password'):
        return api_error("旧密码和新密码不能为空")
    if len(data['new_password']) < 6:
        return api_error("新密码至少6位")

    user = get_user_by_id(session['user_id'])
    if not check_password_hash(user['password_hash'], data['old_password']):
        return api_error("旧密码错误")

    new_hash = generate_password_hash(data['new_password'])
    update_user(user['id'], password_hash=new_hash)
    return jsonify({"status": "ok", "message": "密码已修改"})


# ============================================================
# 用户管理 (管理员)
# ============================================================

@app.route('/api/users', methods=['GET'])
@admin_required
def api_users_list():
    """用户列表"""
    return jsonify(get_users())


@app.route('/api/users', methods=['POST'])
@admin_required
def api_users_add():
    """创建用户"""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return api_error("用户名和密码不能为空")
    if len(data['password']) < 6:
        return api_error("密码至少6位")

    password_hash = generate_password_hash(data['password'])
    uid = add_user(
        username=data['username'],
        password_hash=password_hash,
        display_name=data.get('display_name', data['username']),
        role=data.get('role', 'worker'),
        phone=data.get('phone', ''),
        email=data.get('email', ''),
    )
    if uid == -1:
        return api_error("用户名已存在")
    return jsonify({"status": "ok", "id": uid})


@app.route('/api/users/<int:uid>', methods=['PUT'])
@admin_required
def api_users_update(uid):
    """更新用户"""
    data = request.get_json() or {}
    if 'password' in data and data['password']:
        if len(data['password']) < 6:
            return api_error("密码至少6位")
        data['password_hash'] = generate_password_hash(data['password'])
        del data['password']
    ok = update_user(uid, **data)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/users/<int:uid>', methods=['DELETE'])
@admin_required
def api_users_delete(uid):
    """删除用户"""
    if uid == session.get('user_id'):
        return api_error("不能删除自己")
    ok = delete_user(uid)
    return jsonify({"status": "ok" if ok else "error"})

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
# 工序状态机
# ============================================================

from database import get_project_phases, update_phase_status, PHASE_ORDER


@app.route('/phases')
def phases_page():
    """工序看板页面"""
    return render_template('phases.html')


@app.route('/api/projects/<int:pid>/phases', methods=['GET'])
def api_project_phases(pid):
    """获取项目工序状态"""
    phases = get_project_phases(pid)
    return jsonify({
        "project_id": pid,
        "phases": phases,
        "phase_order": PHASE_ORDER,
    })


@app.route('/api/projects/<int:pid>/phases/<phase_name>', methods=['PUT'])
def api_project_phase_update(pid, phase_name):
    """更新工序状态（自动校验流转合法性）"""
    from urllib.parse import unquote
    phase_name = unquote(phase_name)
    data = request.get_json() or {}
    new_status = data.get('status', '')
    if not new_status:
        return api_error("缺少 status 字段")
    result = update_phase_status(pid, phase_name, new_status)
    if not result.get('ok'):
        return api_error(result.get('error', '状态更新失败'))
    return jsonify(result)


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


@app.route('/api/backup/list', methods=['GET'])
@login_required
def api_backup_list():
    backups = get_backup_list()
    return jsonify(backups)


@app.route('/api/restore', methods=['POST'])
@login_required
@admin_required
def api_restore():
    """从备份文件恢复数据库"""
    data = request.get_json() or {}
    backup_path = data.get('backup_path', '')
    if not backup_path:
        return api_error("请指定备份文件路径")

    result = restore_database(backup_path)
    if 'error' in result:
        return api_error(result['error'])
    return jsonify(result)


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
@login_required
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
@login_required
def admin_page():
    """系统管理页面"""
    return render_template('admin.html', user=get_current_user())


# ============================================================
# 环境监测
# ============================================================

@app.route('/environment')
def environment_page():
    """环境监测页面"""
    return render_template('environment.html')


@app.route('/api/environment', methods=['GET'])
def api_environment_list():
    """环境记录列表"""
    project_id = request.args.get('project_id', 0, type=int)
    if not project_id:
        return api_error("缺少 project_id")
    days = request.args.get('days', 30, type=int)
    return jsonify(get_environment_records(project_id, days))


@app.route('/api/environment', methods=['POST'])
def api_environment_add():
    """添加环境记录"""
    data = request.get_json()
    if not data or not data.get('project_id'):
        return api_error("缺少 project_id")
    rid = add_environment_record(
        project_id=int(data['project_id']),
        record_date=data.get('record_date', ''),
        record_time=data.get('record_time', ''),
        temperature=float(data.get('temperature', 0)),
        humidity=float(data.get('humidity', 0)),
        base_moisture=float(data['base_moisture']) if data.get('base_moisture') else None,
        surface_temp=float(data['surface_temp']) if data.get('surface_temp') else None,
        wind_speed=float(data['wind_speed']) if data.get('wind_speed') else None,
        weather_condition=data.get('weather_condition', ''),
        recorder=data.get('recorder', ''),
        notes=data.get('notes', ''),
    )
    return jsonify({"status": "ok", "id": rid})


@app.route('/api/environment/<int:rid>', methods=['DELETE'])
def api_environment_delete(rid):
    """删除环境记录"""
    ok = delete_environment_record(rid)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/environment/stats')
def api_environment_stats():
    """环境统计"""
    project_id = request.args.get('project_id', 0, type=int)
    if not project_id:
        return api_error("缺少 project_id")
    return jsonify(get_environment_stats(project_id))

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


@app.route('/api/report/<int:pid>/pdf')
@login_required
def api_report_pdf(pid):
    """导出施工方案PDF报告"""
    try:
        from weasyprint import HTML
    except ImportError:
        return api_error("PDF导出功能未安装（需要 weasyprint 库）")

    from database import generate_report
    report = generate_report(pid)
    if 'error' in report:
        return api_error(report['error'])

    html_str = render_template('print_report.html', report=report)
    pdf_bytes = HTML(string=html_str).write_pdf()

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    safe_name = report.get('project_name', f'project_{pid}').replace(' ', '_')
    response.headers['Content-Disposition'] = f'attachment; filename={safe_name}_施工报告.pdf'
    return response


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
    # 自动推送到企业微信/钉钉
    auto_push_webhook(
        notif_type=data.get('type', 'manual'),
        title=data['title'],
        message=data.get('message', ''),
        project_name=data.get('project_name', ''),
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
# Webhook 通知（企业微信/钉钉）
# ============================================================
@app.route('/api/webhook/test', methods=['POST'])
def api_webhook_test():
    """测试 webhook 配置"""
    from webhook import send_notification
    data = request.get_json() or {}
    title = data.get('title', '🔔 永颐无机磨石 · 测试通知')
    message = data.get('message', '如果您收到这条消息，说明Webhook配置成功！\n\n---\n永颐无机磨石 · 施工管理平台')
    result = send_notification(title, message, 'manual', '')
    return jsonify({"status": "ok", "result": result})


@app.route('/api/webhook/config', methods=['GET'])
def api_webhook_config_get():
    """获取 webhook 配置"""
    from config import get_config
    return jsonify({
        "wechat_url": get_config("webhook", "wechat_url") or "",
        "dingtalk_url": get_config("webhook", "dingtalk_url") or "",
        "enabled": get_config("webhook", "enabled") or True,
        "notify_on": get_config("webhook", "notify_on") or [],
    })


@app.route('/api/webhook/config', methods=['PUT'])
def api_webhook_config_update():
    """更新 webhook 配置"""
    from config import update_config
    data = request.get_json()
    if not data:
        return api_error("缺少配置数据")
    updates = {}
    if "wechat_url" in data:
        updates["wechat_url"] = data["wechat_url"].strip()
    if "dingtalk_url" in data:
        updates["dingtalk_url"] = data["dingtalk_url"].strip()
    if "enabled" in data:
        updates["enabled"] = bool(data["enabled"])
    if "notify_on" in data:
        updates["notify_on"] = data["notify_on"]
    update_config("webhook", updates)
    return jsonify({"status": "ok"})


def auto_push_webhook(notif_type: str, title: str, message: str, project_name: str = ""):
    """自动推送通知到 webhook（内部调用）"""
    try:
        from config import get_config
        enabled = get_config("webhook", "enabled")
        if not enabled:
            return
        notify_on = get_config("webhook", "notify_on") or []
        if notif_type not in notify_on:
            return
        from webhook import send_notification
        send_notification(title, message, notif_type, project_name)
    except Exception as e:
        app.logger.error(f"Webhook 自动推送失败: {e}")
# ============================================================

# ============================================================
# 百度站长推送
# ============================================================
@app.route('/api/seo/push', methods=['POST'])
def api_seo_push():
    """手动触发百度站长推送"""
    try:
        from config import get_config
        import urllib.request
        
        token = get_config("seo", "baidu_push_token")
        if not token:
            return jsonify({"status": "error", "message": "未配置百度推送Token"})
        
        site = "https://ai.jinmojianshe.com"
        baidu_api = f"http://data.zz.baidu.com/urls?site={site}&token={token}"
        
        # 获取当前sitemap中的URL
        sitemap_resp = urllib.request.urlopen(f"{site}/platform/sitemap.xml", timeout=10)
        sitemap_xml = sitemap_resp.read().decode('utf-8')
        
        import re
        urls = re.findall(r'<loc>(.*?)</loc>', sitemap_xml)
        
        if not urls:
            return jsonify({"status": "error", "message": "Sitemap中未找到URL"})
        
        # 推送到百度
        data = "\n".join(urls).encode('utf-8')
        req = urllib.request.Request(
            baidu_api,
            data=data,
            headers={'Content-Type': 'text/plain'},
            method='POST'
        )
        resp = urllib.request.urlopen(req, timeout=30)
        result = resp.read().decode('utf-8')
        
        return jsonify({
            "status": "ok",
            "pushed": len(urls),
            "result": result
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/api/seo/status', methods=['GET'])
def api_seo_status():
    """获取SEO/内容状态概览"""
    import os
    from config import get_config
    from datetime import datetime
    
    # Sitemap中的URL数
    sitemap_count = 0
    try:
        import urllib.request
        import re
        resp = urllib.request.urlopen("https://ai.jinmojianshe.com/platform/sitemap.xml", timeout=5)
        xml = resp.read().decode('utf-8')
        sitemap_count = len(re.findall(r'<loc>', xml))
    except:
        try:
            # 直接生成
            resp = urllib.request.urlopen("http://localhost:5000/sitemap.xml", timeout=5)
            xml = resp.read().decode('utf-8')
            sitemap_count = len(re.findall(r'<loc>', xml))
        except:
            sitemap_count = 0
    
    # 内容计划文件
    content_dir = os.path.join(os.path.dirname(__file__), 'docs', 'content')
    plan_files = []
    if os.path.exists(content_dir):
        plan_files = [f for f in os.listdir(content_dir) if f.endswith('.md')]
    
    # 备份状态
    backup_dir = os.path.join(os.path.dirname(__file__), 'data', 'backups')
    backup_count = 0
    if os.path.exists(backup_dir):
        backup_count = len([f for f in os.listdir(backup_dir) if f.endswith('.db')])
    
    # Webhook配置
    wechat_configured = bool(get_config("webhook", "wechat_url"))
    dingtalk_configured = bool(get_config("webhook", "dingtalk_url"))
    webhook_enabled = bool(get_config("webhook", "enabled"))
    
    return jsonify({
        "version": get_config("system", "version") or "4.4.1",
        "sitemap_urls": sitemap_count,
        "content_plans": len(plan_files),
        "backup_count": backup_count,
        "webhook": {
            "wechat": wechat_configured,
            "dingtalk": dingtalk_configured,
            "enabled": webhook_enabled
        },
        "baidu_push_configured": bool(get_config("seo", "baidu_push_token")),
        "last_push_log": _get_last_push_time(),
        "time": datetime.now().strftime('%Y-%m-%d %H:%M')
    })


def _get_last_push_time():
    """获取最近一次百度推送时间"""
    import os
    log_file = "/var/log/yongyi-terrazzo/push.log"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            for line in reversed(lines):
                if '推送' in line or '完成' in line:
                    return line.strip()[:50]
        except:
            pass
    return "暂无记录"


# ============================================================
# 内容排期生成
# ============================================================
@app.route('/api/content/plan', methods=['POST'])
def api_content_plan():
    """生成下周内容排期"""
    try:
        import subprocess
        import os
        import sys
        
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'content_planner.py')
        if not os.path.exists(script_path):
            return jsonify({"status": "error", "message": "排期脚本不存在"})
        
        # 执行脚本生成排期
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(__file__)
        )
        
        # 查找生成的周排期文件
        content_dir = os.path.join(os.path.dirname(__file__), 'docs', 'content')
        plan_files = [f for f in os.listdir(content_dir) if f.startswith('week-') and f.endswith('.md')]
        plan_files.sort(reverse=True)
        
        # 统计脚本数
        script_count = 0
        latest_plan = ""
        if plan_files:
            latest_plan = plan_files[0]
            with open(os.path.join(content_dir, latest_plan), 'r') as pf:
                content_text = pf.read()
                script_count = content_text.count('### 🔴') + content_text.count('### 🟡') + content_text.count('### 🟢') + content_text.count('### 🔵')
        
        # 推送到Webhook（如果已配置）
        push_result = {"wechat": False, "dingtalk": False}
        try:
            from webhook import send_notification
            plan_preview = ""
            if latest_plan:
                with open(os.path.join(content_dir, latest_plan), 'r') as pf:
                    plan_preview = pf.read()[:600]
            if plan_preview:
                push_result = send_notification(
                    title=f"📅 下周内容排期已生成（{script_count}条脚本）",
                    message=plan_preview + "\n\n完整排期见管理后台",
                    notif_type="daily_log"
                )
        except Exception as webhook_err:
            push_result = {"error": str(webhook_err)}
        
        return jsonify({
            "status": "ok",
            "count": script_count or 28,
            "file": latest_plan,
            "webhook_push": push_result,
            "output": result.stdout[:200] if result.stdout else ""
        })
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "message": "生成超时"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ============================================================
# 健康检查端点（用于负载均衡/监控系统）
# ============================================================
@app.route('/health')
@app.route('/api/health')
def health_check():
    """健康检查 - 用于监控系统和服务发现"""
    import datetime
    
    # 检查数据库
    db_ok = False
    db_size = 0
    try:
        from database import get_db, check_database_integrity
        conn = get_db()
        conn.execute("SELECT 1").fetchone()
        db_ok = True
        
        # 数据库大小
        import os
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'yongyi.db')
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
        
        conn.close()
    except Exception as e:
        db_ok = False
    
    # 系统运行时间
    import os
    uptime = "unknown"
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            uptime = f"{days}d {hours}h"
    except:
        pass
    
    status_code = 200 if db_ok else 503
    return jsonify({
        "status": "ok" if db_ok else "error",
        "app": "yongyi-terrazzo",
        "version": "4.4.1",
        "database": "connected" if db_ok else "disconnected",
        "database_size_mb": round(db_size / (1024 * 1024), 2) if db_size else 0,
        "uptime": uptime,
        "timestamp": datetime.datetime.now().isoformat(),
        "endpoints": len([r for r in app.url_map.iter_rules() if not r.rule.startswith('/static')])
    }), status_code


@app.route('/api/content/plan-preview', methods=['GET'])
def api_content_plan_preview():
    """获取最新内容排期预览"""
    import os
    content_dir = os.path.join(os.path.dirname(__file__), 'docs', 'content')
    if not os.path.exists(content_dir):
        return jsonify({"status": "error", "message": "无排期文件"})
    
    files = [f for f in os.listdir(content_dir) if f.startswith('week-') and f.endswith('.md')]
    files.sort(reverse=True)
    
    if not files:
        return jsonify({"status": "ok", "has_plan": False, "message": "暂无排期，请先生成"})
    
    latest = files[0]
    with open(os.path.join(content_dir, latest), 'r') as f:
        content_text = f.read()
    
    # 统计各账号脚本数
    lines = content_text.split('\n')
    days = sum(1 for l in lines if l.startswith('## '))
    script_count = content_text.count('### 🔴') + content_text.count('### 🟡') + content_text.count('### 🟢') + content_text.count('### 🔵')
    
    # 提取明日内容预览（如果有）
    preview_lines = []
    in_first_day = False
    for l in lines:
        if l.startswith('## ') and not in_first_day:
            in_first_day = True
            preview_lines.append(l)
        elif l.startswith('## ') and in_first_day:
            break
        elif in_first_day:
            preview_lines.append(l)
    
    return jsonify({
        "status": "ok",
        "has_plan": True,
        "file": latest,
        "total_scripts": script_count,
        "total_days": days,
        "next_day_preview": "\n".join(preview_lines[:20]),
    })


@app.route('/content-calendar')
def content_calendar_page():
    """内容日历页面"""
    return app.send_static_file('content-calendar.html')

@app.route('/weekly-sheet')
def weekly_sheet_page():
    """打印版拍摄单"""
    return app.send_static_file('weekly-sheet.html')

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
    allowed_tables = ['logs', 'materials', 'quality', 'budget', 'work_hours', 'curing', 'workers', 'suppliers', 'equipment']
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
        'workers': '工人花名册', 'suppliers': '供应商清单',
        'equipment': '设备清单',
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
# 材料申购
# ============================================================

from database import (
    add_material_request, get_material_requests, get_material_request,
    update_material_request, delete_material_request,
    add_subcontractor, get_subcontractors, update_subcontractor,
    delete_subcontractor, get_analytics,
)


@app.route('/purchase-requests')
def purchase_requests_page():
    return render_template('purchase_requests.html')


@app.route('/subcontractors')
def subcontractors_page():
    return render_template('subcontractors.html')


@app.route('/analytics')
def analytics_page():
    return render_template('analytics.html')


@app.route('/api/material-requests', methods=['GET'])
def api_material_requests_list():
    pid = request.args.get('project_id', 0, type=int)
    return jsonify(get_material_requests(pid))


@app.route('/api/material-requests', methods=['POST'])
def api_material_requests_add():
    data = request.get_json()
    if not data or not data.get('project_id'):
        return api_error("缺少 project_id")
    rid = add_material_request(
        project_id=int(data['project_id']),
        applicant=data.get('applicant', ''),
        request_date=data.get('request_date', ''),
        notes=data.get('notes', ''),
        items=data.get('items', []),
    )
    return jsonify({"status": "ok", "id": rid})


@app.route('/api/material-requests/<int:rid>', methods=['GET'])
def api_material_requests_get(rid):
    req = get_material_request(rid)
    if not req:
        return api_error("申购单不存在")
    return jsonify(req)


@app.route('/api/material-requests/<int:rid>', methods=['PUT'])
def api_material_requests_update(rid):
    data = request.get_json() or {}
    ok = update_material_request(rid, **data)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/material-requests/<int:rid>', methods=['DELETE'])
def api_material_requests_delete(rid):
    delete_material_request(rid)
    return jsonify({"status": "ok"})


# 分包商
@app.route('/api/subcontractors', methods=['GET'])
def api_subcontractors_list():
    return jsonify(get_subcontractors())


@app.route('/api/subcontractors', methods=['POST'])
def api_subcontractors_add():
    data = request.get_json()
    if not data or not data.get('name'):
        return api_error("分包商名称不能为空")
    sid = add_subcontractor(**data)
    return jsonify({"status": "ok", "id": sid})


@app.route('/api/subcontractors/<int:sid>', methods=['PUT'])
def api_subcontractors_update(sid):
    data = request.get_json() or {}
    ok = update_subcontractor(sid, **data)
    return jsonify({"status": "ok" if ok else "error"})


@app.route('/api/subcontractors/<int:sid>', methods=['DELETE'])
def api_subcontractors_delete(sid):
    delete_subcontractor(sid)
    return jsonify({"status": "ok"})


# 分析看板
@app.route('/api/analytics')
def api_analytics():
    return jsonify(get_analytics())


# ============================================================
# 项目模板 & 材料对比 & 日报 & 搜索
# ============================================================

from database import (
    add_project_template, get_project_templates, delete_project_template,
    set_material_consumption, get_material_consumption,
    generate_daily_report, global_search,
)


@app.route('/templates')
def templates_page():
    return render_template('templates.html')


@app.route('/api/templates', methods=['GET'])
def api_templates_list():
    return jsonify(get_project_templates())


@app.route('/api/templates', methods=['POST'])
def api_templates_add():
    data = request.get_json()
    if not data or not data.get('name'):
        return api_error("模板名称不能为空")
    tid = add_project_template(name=data['name'], description=data.get('description',''), config=data.get('config',{}))
    return jsonify({"status": "ok", "id": tid})


@app.route('/api/templates/<int:tid>', methods=['DELETE'])
def api_templates_delete(tid):
    delete_project_template(tid)
    return jsonify({"status": "ok"})


@app.route('/api/projects/from-template/<int:tid>', methods=['POST'])
def api_projects_from_template(tid):
    from database import get_project_templates, create_project
    tmpl = next((t for t in get_project_templates() if t['id'] == tid), None)
    if not tmpl:
        return api_error("模板不存在")
    import json as _json
    try:
        config = _json.loads(tmpl['config'])
    except:
        config = {}
    pid = create_project(name=tmpl['name']+' - 新项目', area=float(config.get('area',100)),
                         base_thickness=float(config.get('base_thickness',50)),
                         surface_thickness=float(config.get('surface_thickness',15)),
                         location=config.get('location',''))
    return jsonify({"status":"ok","project_id":pid})


@app.route('/api/material-consumption', methods=['GET'])
def api_material_consumption_list():
    pid = request.args.get('project_id', 0, type=int)
    if not pid:
        return api_error("缺少 project_id")
    return jsonify(get_material_consumption(pid))


@app.route('/api/material-consumption', methods=['POST'])
def api_material_consumption_set():
    data = request.get_json()
    if not data or not data.get('project_id') or not data.get('material_name'):
        return api_error("缺少 project_id 或 material_name")
    cid = set_material_consumption(project_id=int(data['project_id']), material_name=data['material_name'],
                                   planned_kg=float(data.get('planned_kg',0)), actual_kg=float(data.get('actual_kg',0)),
                                   unit=data.get('unit','kg'), notes=data.get('notes',''))
    return jsonify({"status":"ok","id":cid})


@app.route('/api/daily-report')
def api_daily_report():
    pid = request.args.get('project_id', 0, type=int)
    date = request.args.get('date', '')
    if not pid:
        return api_error("缺少 project_id")
    report = generate_daily_report(pid, date)
    if 'error' in report:
        return api_error(report['error'])
    return jsonify(report)


@app.route('/project/<int:pid>/daily-report')
def daily_report_page(pid):
    report = generate_daily_report(pid)
    if 'error' in report:
        return api_error(report['error'])
    return render_template('daily_report.html', report=report)


@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 1:
        return jsonify({})
    return jsonify(global_search(q))


# ============================================================
# 公开页面 & SEO
# ============================================================

@app.route('/public')
def page_public():
    """公司公开介绍页（无需登录）"""
    return render_template('public.html')


@app.route('/faq')
def page_faq():
    """无机磨石施工FAQ页面（无需登录）"""
    return render_template('faq.html')


@app.route('/construction-process')
def page_construction():
    """无机磨石施工工艺流程页面（无需登录）"""
    return render_template('construction_process.html')


@app.route('/cases')
def page_cases():
    """施工案例页面（无需登录）"""
    return render_template('cases.html')


@app.route('/guide-compare')
def page_guide_compare():
    """磨石地坪选购指南（无需登录）"""
    return render_template('guide-compare.html')


@app.route('/guide-maintenance')
def page_guide_maintenance():
    """磨石地坪养护指南（无需登录）"""
    return render_template('guide-maintenance.html')


@app.route('/guide-budget')
def page_guide_budget():
    """磨石地坪预算指南（无需登录）"""
    return render_template('guide-budget.html')


@app.route('/knowledge-base')
def page_knowledge_base():
    """无机磨石知识百科（无需登录）"""
    return render_template('knowledge-base.html')


@app.route('/robots.txt')
def robots_txt():
    """搜索引擎爬虫规则"""
    return """User-agent: *
Allow: /
Allow: /platform/
Allow: /platform/public
Allow: /platform/faq
Disallow: /admin/
Disallow: /api/auth/
Disallow: /api/admin/

Sitemap: https://ai.jinmojianshe.com/sitemap.xml
""", 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/sitemap.xml')
def sitemap_xml():
    """站点地图"""
    from datetime import date
    today = date.today().isoformat()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://ai.jinmojianshe.com/platform/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://ai.jinmojianshe.com/platform/public</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://ai.jinmojianshe.com/platform/faq</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ai.jinmojianshe.com/platform/construction-process</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ai.jinmojianshe.com/platform/cases</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://ai.jinmojianshe.com/platform/guide-compare</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://ai.jinmojianshe.com/platform/guide-maintenance</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://ai.jinmojianshe.com/platform/guide-budget</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://ai.jinmojianshe.com/platform/knowledge-base</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
""", 200, {'Content-Type': 'application/xml; charset=utf-8'}


# ============================================================
# 错误处理器
# ============================================================

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return api_error("接口不存在", code=404)
    return render_template('404.html'), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return api_error("请求方法不允许", code=405)

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith('/api/'):
        return api_error("服务器内部错误", code=500)
    return render_template('500.html'), 500

@app.errorhandler(401)
def unauthorized(e):
    if request.path.startswith('/api/'):
        return api_error("未登录，请先登录", code=401)
    return render_template('404.html'), 401

@app.errorhandler(403)
def forbidden(e):
    if request.path.startswith('/api/'):
        return api_error("权限不足", code=403)
    return render_template('404.html'), 403

if __name__ == '__main__':
    # 初始化数据库并创建默认管理员
    from database import init_db, get_users, add_user
    init_db()
    if len(get_users()) == 0:
        # 默认管理员密码可通过环境变量设置，开发环境默认 admin123
        default_pwd = os.environ.get('DEFAULT_ADMIN_PWD', 'admin123')
        add_user('admin', generate_password_hash(default_pwd), '系统管理员', role='admin')
        print(f"✅ 已创建默认管理员: admin / {default_pwd}")
        print("   ⚠️ 生产环境请通过环境变量 DEFAULT_ADMIN_PWD 设置强密码")
    app.run(host='0.0.0.0', port=5000, debug=True)
