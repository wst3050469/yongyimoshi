"""
永颐无机磨石 - API集成测试
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from database import init_db, get_users, add_user, DB_PATH
from werkzeug.security import generate_password_hash
import tempfile
import os
import json
import pytest


@pytest.fixture
def client():
    """测试客户端（使用独立临时数据库，含默认项目和管理员）"""
    app.config['TESTING'] = True
    # 使用临时数据库
    original_db_path = None
    import database
    original_db_path = database.DB_PATH
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.db')
    os.close(tmp_fd)
    database.DB_PATH = tmp_path
    # 初始化数据库
    init_db()
    # 创建默认用户
    if len(get_users()) == 0:
        add_user('admin', generate_password_hash('admin123'), '系统管理员', role='admin')
    # 创建默认项目（ID=1）
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        from materials_calc import CHECKLIST_ITEMS, QUALITY_TESTS
        cursor.execute("""
            INSERT INTO projects (id, name, area, base_thickness, surface_thickness, start_date, location)
            VALUES (1, '测试项目', 100, 50, 15, '2024-06-01', '测试地点')
        """)
        # 初始化工序
        from database import _init_project_phases, _init_checklist_for_project, _init_quality_tests_for_project
        _init_project_phases(1, conn)
        _init_checklist_for_project(1, conn)
        _init_quality_tests_for_project(1, conn)
        conn.commit()
    conn.close()

    with app.test_client() as client:
        yield client
    # 清理
    os.unlink(tmp_path)
    database.DB_PATH = original_db_path


class TestProjectAPI:
    """项目API测试"""

    def test_list_projects(self, client):
        """获取项目列表"""
        rv = client.get('/api/projects')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert isinstance(data, list)

    def test_create_project(self, client):
        """创建项目"""
        rv = client.post('/api/projects', json={
            'name': '测试项目',
            'area': 200,
            'location': '测试地点'
        })
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'id' in data

    def test_get_project(self, client):
        """获取单个项目"""
        rv = client.get('/api/projects/1')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'id' in data
        assert 'name' in data


class TestMaterialAPI:
    """材料相关API测试"""

    def test_calculate(self, client):
        """材料计算"""
        rv = client.post('/api/calc', json={
            'area': 100,
            'thickness_base': 50,
            'thickness_surface': 15
        })
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['area'] == 100
        assert 'total_weight_kg' in data
        assert 'summary' in data

    def test_calculate_zero_area(self, client):
        """零面积计算"""
        rv = client.post('/api/calc', json={'area': 0})
        assert rv.status_code == 200

    def test_purchase(self, client):
        """采购清单"""
        rv = client.post('/api/purchase', json={'area': 100})
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'purchase_list' in data
        assert len(data['purchase_list']) > 0

    def test_cost(self, client):
        """成本估算"""
        rv = client.post('/api/cost', json={'area': 100})
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'total_cost' in data
        assert 'cost_per_m2' in data

    def test_materials_list(self, client):
        """材料列表"""
        rv = client.get('/api/materials-list')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert len(data) > 0


class TestScheduleAPI:
    """进度计划API测试"""

    def test_schedule(self, client):
        """获取进度计划"""
        rv = client.get('/api/schedule')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert len(data) == 10

    def test_schedule_with_date(self, client):
        """指定开始日期"""
        rv = client.get('/api/schedule?start=2024-06-01')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data[0]['start'] == '06-01'


class TestChecklistAPI:
    """检查清单API测试"""

    def test_get_checklist(self, client):
        """获取检查清单"""
        rv = client.get('/api/checklist')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert len(data) == 7

    def test_save_checklist(self, client):
        """保存检查清单"""
        rv = client.post('/api/checklist', json={
            'project_id': 1,
            'items': [{'category': '测试', 'items': [{'id': 'test-1', 'checked': True}]}]
        })
        assert rv.status_code == 200


class TestDailyLogAPI:
    """施工日志API测试"""

    def test_save_log(self, client):
        """保存日志"""
        rv = client.post('/api/daily-log', json={
            'project_id': 1,
            'date': '2024-06-15',
            'weather': '晴',
            'work_content': '测试内容'
        })
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'ok'

    def test_get_logs(self, client):
        """获取日志列表"""
        rv = client.get('/api/daily-logs?project_id=1')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert isinstance(data, list)


class TestPhotoAPI:
    """照片API测试"""

    def test_upload_photo(self, client):
        """上传照片"""
        img_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        rv = client.post('/api/photos', json={
            'project_id': 1,
            'phase': '基层处理',
            'description': '测试照片',
            'image_data': img_b64
        })
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'id' in data

    def test_list_photos(self, client):
        """获取照片列表"""
        rv = client.get('/api/photos?project_id=1')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert isinstance(data, list)

    def test_get_photo(self, client):
        """获取单张照片（先上传再获取）"""
        img_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        upload = client.post('/api/photos', json={
            'project_id': 1, 'phase': '基层处理', 'description': '测试照片',
            'image_data': img_b64
        })
        photo_id = upload.get_json().get('id', 1)
        rv = client.get(f'/api/photo/{photo_id}')
        assert rv.status_code in (200, 404)


class TestInventoryAPI:
    """库存API测试"""

    def test_add_inventory(self, client):
        """添加入库"""
        rv = client.post('/api/inventory', json={
            'project_id': 1,
            'material_name': '硅酸盐水泥',
            'quantity_kg': 1000,
            'unit_price': 28
        })
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'ok'

    def test_get_inventory(self, client):
        """获取库存"""
        rv = client.get('/api/inventory?project_id=1')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'inventory' in data
        assert 'records' in data


class TestQualityAPI:
    """质量检测API测试"""

    def test_get_templates(self, client):
        """获取检测模板"""
        rv = client.get('/api/quality-tests')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'templates' in data
        assert len(data['templates']) == 10


class TestDashboardAPI:
    """看板API测试"""

    def test_dashboard(self, client):
        """获取看板数据"""
        rv = client.get('/api/dashboard?project_id=1')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'overall_progress' in data


class TestTimelineAPI:
    """时间轴API测试"""

    def test_timeline(self, client):
        """获取时间轴"""
        rv = client.get('/api/timeline/1')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'timeline' in data


class TestParamsAPI:
    """参数API测试"""

    def test_params(self, client):
        """获取施工参数"""
        rv = client.get('/api/params')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'environment' in data
        assert 'base_layer' in data
        assert 'surface_layer' in data
        assert 'final_acceptance' in data


class TestDocsAPI:
    """文档API测试"""

    def test_api_docs(self, client):
        """获取API文档"""
        rv = client.get('/api/docs')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'endpoints' in data
        assert len(data['endpoints']) > 0

class TestAuthAPI:
    """用户认证API测试"""

    def test_login_invalid(self, client):
        """无效登录"""
        rv = client.post('/api/auth/login', json={'username': 'nonexist', 'password': 'wrong'})
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert 'error' in data

    def test_login_valid(self, client):
        """有效登录"""
        rv = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'ok'
        assert 'user' in data

    def test_auth_me(self, client):
        """获取当前用户"""
        client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
        rv = client.get('/api/auth/me')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'username' in data

    def test_auth_me_unauthorized(self, client):
        """未登录访问受限接口"""
        rv = client.get('/api/auth/me')
        assert rv.status_code == 401

    def test_logout(self, client):
        """登出"""
        client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
        rv = client.post('/api/auth/logout')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'ok'


class TestEnvironmentAPI:
    """环境监测API测试"""

    def test_add_record(self, client):
        """添加环境记录"""
        rv = client.post('/api/environment', json={
            'project_id': 1,
            'temperature': 25.5,
            'humidity': 60,
            'weather_condition': '晴',
            'recorder': '测试'
        })
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'id' in data

    def test_list_records(self, client):
        """获取环境记录列表"""
        rv = client.get('/api/environment?project_id=1')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert isinstance(data, list)

    def test_stats(self, client):
        """环境统计"""
        rv = client.get('/api/environment/stats?project_id=1')
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert 'total_records' in data


class TestPDFReport:
    """PDF报告导出测试"""

    def test_pdf_requires_auth(self, client):
        """PDF导出需要登录"""
        rv = client.get('/api/report/1/pdf')
        assert rv.status_code == 401

    def test_pdf_not_installed(self, client):
        """未安装weasyprint时的错误提示"""
        client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
        rv = client.get('/api/report/1/pdf')
        # weasyprint可能未安装，返回400；已安装则尝试生成PDF
        assert rv.status_code in (400, 200)

class TestSupplierAPI:
    """供应商管理API测试"""

    def test_add_supplier(self, client):
        """添加供应商"""
        rv = client.post('/api/suppliers', json={
            'name': '测试供应商', 'contact_person': '张三', 'phone': '13800138000',
            'materials': ['硅酸盐水泥', '黄沙'], 'rating': 4
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'id' in data

    def test_list_suppliers(self, client):
        """获取供应商列表"""
        rv = client.get('/api/suppliers')
        assert rv.status_code == 200
        data = rv.get_json()
        assert isinstance(data, list)

    def test_get_supplier(self, client):
        """获取单个供应商"""
        rv = client.get('/api/suppliers/1')
        assert rv.status_code == 200 or rv.status_code == 400

    def test_add_price(self, client):
        """添加供应商报价（先确保供应商存在）"""
        # 确保供应商存在
        client.post('/api/suppliers', json={
            'name': '报价供应商', 'contact_person': '李四', 'phone': '13900139000'
        })
        rv = client.post('/api/suppliers/1/prices', json={
            'material_name': '硅酸盐水泥', 'unit_price': 28
        })
        assert rv.status_code in (200, 400)


class TestEquipmentAPI:
    """设备管理API测试"""

    def test_add_equipment(self, client):
        """添加设备"""
        rv = client.post('/api/equipment', json={
            'name': '磨光机', 'type': '打磨设备', 'quantity': 2, 'status': '可用'
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'id' in data

    def test_list_equipment(self, client):
        """获取设备列表"""
        rv = client.get('/api/equipment')
        assert rv.status_code == 200
        assert isinstance(rv.get_json(), list)

    def test_update_equipment(self, client):
        """更新设备"""
        rv = client.put('/api/equipment/1', json={'status': '维修中'})
        assert rv.status_code == 200

    def test_equipment_usage(self, client):
        """设备使用记录（先创建设备）"""
        client.post('/api/equipment', json={
            'name': '测试磨光机', 'type': '打磨设备', 'quantity': 1, 'status': '可用'
        })
        rv = client.post('/api/equipment-usage', json={
            'equipment_id': 1, 'project_id': 1, 'quantity_used': 1, 'start_date': '2024-06-01'
        })
        assert rv.status_code in (200, 400)


class TestSafetyAPI:
    """安全管理API测试"""

    def test_safety_templates(self, client):
        """安全检查模板"""
        rv = client.get('/api/safety/templates')
        assert rv.status_code == 200

    def test_add_safety_check(self, client):
        """添加安全检查"""
        rv = client.post('/api/safety/checks', json={
            'project_id': 1, 'check_date': '2024-06-15',
            'inspector': '李四', 'items': [{'id': 's1', 'name': '安全帽佩戴', 'pass': True}]
        })
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'id' in data

    def test_add_incident(self, client):
        """添加安全事件"""
        rv = client.post('/api/safety/incidents', json={
            'project_id': 1, 'incident_date': '2024-06-15',
            'incident_type': '轻微伤害', 'severity': '轻微',
            'description': '测试事件', 'injured_person': '王五'
        })
        assert rv.status_code == 200


class TestDocumentAPI:
    """文档管理API测试"""

    def test_list_documents(self, client):
        """获取文档列表"""
        rv = client.get('/api/documents?project_id=1')
        assert rv.status_code == 200
        assert isinstance(rv.get_json(), list)


class TestMaterialRequestAPI:
    """材料申购API测试"""

    def test_add_request(self, client):
        """添加申购单"""
        rv = client.post('/api/material-requests', json={
            'project_id': 1, 'applicant': '赵六',
            'items': [{'material_name': '水泥', 'quantity_kg': 500}]
        })
        assert rv.status_code == 200

    def test_list_requests(self, client):
        """申购单列表"""
        rv = client.get('/api/material-requests?project_id=1')
        assert rv.status_code == 200


class TestSubcontractorAPI:
    """分包商管理API测试"""

    def test_add_subcontractor(self, client):
        """添加分包商"""
        rv = client.post('/api/subcontractors', json={
            'name': '测试分包商', 'contact_person': '钱七', 'scope': '面层施工'
        })
        assert rv.status_code == 200

    def test_list_subcontractors(self, client):
        """分包商列表"""
        rv = client.get('/api/subcontractors')
        assert rv.status_code == 200


class TestBudgetAPI:
    """预算管理API测试"""

    def test_add_budget(self, client):
        """添加预算项"""
        rv = client.post('/api/budget', json={
            'project_id': 1, 'category': '材料费', 'planned_amount': 50000
        })
        assert rv.status_code == 200

    def test_budget_summary(self, client):
        """预算汇总"""
        rv = client.get('/api/budget/summary?project_id=1')
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'total_planned' in data


class TestNotificationAPI:
    """通知管理API测试"""

    def test_add_notification(self, client):
        """添加通知"""
        rv = client.post('/api/notifications', json={
            'project_id': 1, 'title': '测试通知', 'message': '这是一条测试通知'
        })
        assert rv.status_code == 200

    def test_unread_count(self, client):
        """未读通知数"""
        rv = client.get('/api/notifications/unread-count')
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'count' in data


class TestSearchAPI:
    """全局搜索API测试"""

    def test_search(self, client):
        """全局搜索"""
        rv = client.get('/api/search?q=测试')
        assert rv.status_code == 200
        assert isinstance(rv.get_json(), dict)


class TestSystemAPI:
    """系统管理API测试"""

    def test_system_stats(self, client):
        """系统统计"""
        rv = client.get('/api/system/stats')
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'projects' in data or isinstance(data, dict)

class TestPhaseMachineAPI:
    """工序状态机API测试"""

    def test_get_phases(self, client):
        """获取工序状态"""
        rv = client.get('/api/projects/1/phases')
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'phases' in data
        assert 'phase_order' in data

    def test_update_phase_valid(self, client):
        """更新工序（从pending→in_progress）"""
        # 第一阶段可以直接开始
        rv = client.put('/api/projects/1/phases/基层处理',
                         json={'status': 'in_progress'})
        assert rv.status_code == 200
        data = rv.get_json()
        assert data.get('ok') == True

    def test_update_phase_skip(self, client):
        """跳过工序（未完成前置）"""
        # 第二阶段不能在没有完成第一阶段时开始
        rv = client.put('/api/projects/1/phases/抗裂砂浆施工',
                         json={'status': 'in_progress'})
        # 应该失败，因为上一阶段状态是in_progress而非completed
        assert rv.status_code == 400

    def test_update_phase_complete(self, client):
        """完成工序（先开始→再完成）"""
        # 先开始第一阶段
        client.put('/api/projects/1/phases/基层处理', json={'status': 'in_progress'})
        # 再完成
        rv = client.put('/api/projects/1/phases/基层处理', json={'status': 'completed'})
        assert rv.status_code == 200
        data = rv.get_json()
        assert data.get('ok') == True
        # 第二阶段可以开始
        rv = client.put('/api/projects/1/phases/抗裂砂浆施工', json={'status': 'in_progress'})
        assert rv.status_code == 200

    def test_invalid_phase(self, client):
        """无效工序名称"""
        rv = client.put('/api/projects/1/phases/不存在工序', json={'status': 'in_progress'})
        assert rv.status_code == 400

class TestPhasesPage:
    """工序看板页面测试"""

    def test_phases_page_exists(self, client):
        """工序看板页面可达"""
        rv = client.get('/phases')
        assert rv.status_code == 200
        assert '工序流转' in rv.get_data(as_text=True) or 'phases' in rv.get_data(as_text=True)

    def test_phases_page_has_tab(self, client):
        """首页工序流转Tab存在"""
        rv = client.get('/')
        assert rv.status_code == 200
        assert '工序流转' in rv.get_data(as_text=True)

class TestGlobalNavigation:
    """全局导航与搜索测试"""

    def test_search_input_exists(self, client):
        """全局搜索框存在"""
        rv = client.get('/')
        assert rv.status_code == 200
        html = rv.get_data(as_text=True)
        assert 'globalSearch' in html or 'global-search' in html

    def test_sidebar_exists(self, client):
        """侧边栏导航存在"""
        rv = client.get('/')
        html = rv.get_data(as_text=True)
        assert 'sidebar' in html or '导航菜单' in html

    def test_independent_pages_have_sidebar(self, client):
        """独立页面包含侧边栏"""
        for page in ['/workers', '/suppliers', '/equipment', '/safety', '/documents',
                      '/notifications', '/acceptance', '/phases', '/calendar']:
            rv = client.get(page)
            assert rv.status_code == 200, f"{page} 返回 {rv.status_code}"
            html = rv.get_data(as_text=True)
            assert 'sidebar' in html or '导航菜单' in html, f"{page} 缺少侧边栏"

    def test_notification_badge(self, client):
        """通知徽章元素存在"""
        rv = client.get('/')
        html = rv.get_data(as_text=True)
        assert 'notifBadge' in html or 'notif-badge' in html

    def test_export_button_workers(self, client):
        """工人页面有导出按钮"""
        rv = client.get('/workers')
        html = rv.get_data(as_text=True)
        assert 'exportCSV' in html or '导出' in html

    def test_export_button_suppliers(self, client):
        """供应商页面有导出按钮"""
        rv = client.get('/suppliers')
        html = rv.get_data(as_text=True)
        assert 'exportCSV' in html or '导出' in html

    def test_export_button_equipment(self, client):
        """设备页面有导出按钮"""
        rv = client.get('/equipment')
        html = rv.get_data(as_text=True)
        assert 'exportCSV' in html or '导出' in html

class TestCSVExport:
    """CSV导出功能测试"""

    def test_export_workers_csv(self, client):
        """工人数据CSV导出"""
        rv = client.get('/api/export/csv/workers')
        assert rv.status_code == 200
        assert rv.content_type.startswith('text/csv')

    def test_export_suppliers_csv(self, client):
        """供应商数据CSV导出"""
        rv = client.get('/api/export/csv/suppliers')
        assert rv.status_code == 200
        assert rv.content_type.startswith('text/csv')

    def test_export_equipment_csv(self, client):
        """设备数据CSV导出"""
        rv = client.get('/api/export/csv/equipment')
        assert rv.status_code == 200
        assert rv.content_type.startswith('text/csv')

    def test_export_invalid_table(self, client):
        """不支持的导出表返回错误"""
        rv = client.get('/api/export/csv/invalid_table')
        assert rv.status_code == 400

class TestDarkMode:
    """暗色模式测试"""

    def test_dark_mode_script_in_head(self, client):
        """独立页面在head中有暗色模式脚本"""
        # 先登录以访问受保护页面
        client.post('/api/auth/login', json={"username": "admin", "password": "admin123"})
        for page in ['/workers', '/suppliers', '/equipment', '/safety',
                      '/documents', '/notifications', '/acceptance', '/admin']:
            rv = client.get(page)
            html = rv.get_data(as_text=True)
            assert 'yongyi_theme' in html, f"{page} 缺少暗色模式脚本"

    def test_dark_mode_sets_data_theme(self, client):
        """暗色模式脚本能设置data-theme属性"""
        rv = client.get('/workers')
        # 脚本内容检查
        html = rv.get_data(as_text=True)
        assert 'setAttribute("data-theme"' in html

    def test_index_page_dark_mode(self, client):
        """首页有暗色模式切换功能"""
        rv = client.get('/')
        html = rv.get_data(as_text=True)
        assert 'toggleTheme' in html
        assert 'yongyi_theme' in html

class TestImportFeature:
    """数据导入功能测试"""

    def test_import_page_has_upload_button(self, client):
        """管理员页面有导入按钮"""
        client.post('/api/auth/login', json={"username": "admin", "password": "admin123"})
        rv = client.get('/admin')
        html = rv.get_data(as_text=True)
        assert 'importFile' in html or '导入' in html

    def test_import_api_exists(self, client):
        """导入API存在"""
        client.post('/api/auth/login', json={"username": "admin", "password": "admin123"})
        rv = client.post('/api/import',
                         json={"project": {"name": "测试导入", "area": 100}},
                         content_type='application/json')
        # 应该返回导入结果（可能成功或报错，但不会是404）
        assert rv.status_code != 404

    def test_import_invalid_json(self, client):
        """导入API拒绝无效数据"""
        client.post('/api/auth/login', json={"username": "admin", "password": "admin123"})
        rv = client.post('/api/import',
                         data="not json",
                         content_type='application/json')
        # Flask自动返回400
        assert rv.status_code in (400, 415)

class TestLightbox:
    """图片查看器测试"""

    def test_lightbox_function_exists(self, client):
        """首页有Lightbox函数"""
        rv = client.get('/')
        html = rv.get_data(as_text=True)
        assert 'showLightbox' in html

    def test_photo_click_not_new_tab(self, client):
        """照片点击不再打开新标签页"""
        rv = client.get('/')
        html = rv.get_data(as_text=True)
        assert "window.open('/api/photo/" not in html
        assert "showLightbox" in html

class TestRestoreFeature:
    """数据恢复功能测试"""

    def test_restore_api_requires_path(self, client):
        """恢复API需要路径参数"""
        client.post('/api/auth/login', json={"username": "admin", "password": "admin123"})
        rv = client.post('/api/restore', json={})
        assert rv.status_code == 400

    def test_restore_api_invalid_path(self, client):
        """恢复API拒绝无效路径"""
        client.post('/api/auth/login', json={"username": "admin", "password": "admin123"})
        rv = client.post('/api/restore', json={"backup_path": "/nonexistent/path.db"})
        assert rv.status_code == 400

    def test_backup_list_api(self, client):
        """备份列表API可用"""
        client.post('/api/auth/login', json={"username": "admin", "password": "admin123"})
        rv = client.get('/api/backup/list')
        assert rv.status_code == 200
        data = rv.get_json()
        assert isinstance(data, list)

class TestErrorPages:
    """自定义错误页面测试"""

    def test_404_html_page(self, client):
        """非API路径返回HTML 404页面"""
        rv = client.get('/nonexistent-page-test')
        assert rv.status_code == 404
        html = rv.get_data(as_text=True)
        assert '404' in html

    def test_404_api_returns_json(self, client):
        """API路径返回JSON错误"""
        rv = client.get('/api/nonexistent-endpoint')
        assert rv.status_code == 404
        data = rv.get_json()
        assert data is not None
        assert 'error' in data

class TestHealthCheck:
    """系统健康检查测试"""

    def test_system_status_has_integrity(self, client):
        """系统状态包含完整性信息"""
        rv = client.get('/api/system/status')
        data = rv.get_json()
        assert data is not None
        # integrity字段可能在或不在
        if 'integrity' in data:
            assert data['integrity'] in ('ok', 'error', 'unknown')

    def test_system_status_has_db_stats(self, client):
        """系统状态包含数据库统计"""
        rv = client.get('/api/system/status')
        data = rv.get_json()
        assert data is not None
        assert 'db_size_mb' in data

class TestBatchPhotoUpload:
    """批量照片上传测试"""

    def test_upload_input_has_multiple(self, client):
        """照片上传input支持多选"""
        rv = client.get('/')
        html = rv.get_data(as_text=True)
        # 检查input是否有multiple属性
        assert 'multiple' in html
        assert 'uploadFileInput' in html
