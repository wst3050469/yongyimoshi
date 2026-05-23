"""
永颐无机磨石 - API集成测试
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
from database import init_db, get_users, add_user
from werkzeug.security import generate_password_hash
import tempfile
import pytest


@pytest.fixture
def client():
    """测试客户端（自动创建默认管理员）"""
    app.config['TESTING'] = True
    init_db()
    if len(get_users()) == 0:
        add_user('admin', generate_password_hash('admin123'), '系统管理员', role='admin')
    with app.test_client() as client:
        yield client


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
        """获取单张照片"""
        rv = client.get('/api/photo/1')
        assert rv.status_code == 200


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
