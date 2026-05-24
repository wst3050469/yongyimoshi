"""永颐无机磨石 · SEO/内容管理API测试"""
import sys, os, json, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['SECRET_KEY'] = 'test-seo-api'
from app import app

class TestSEOAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        # Login as admin
        self.app.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
    
    def test_seo_status(self):
        """GET /api/seo/status 返回系统状态"""
        resp = self.app.get('/api/seo/status')
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertIn('sitemap_urls', data)
        self.assertIn('content_plans', data)
        self.assertIn('backup_count', data)
        self.assertIn('webhook', data)
        self.assertIn('baidu_push_configured', data)
        self.assertIsInstance(data['sitemap_urls'], int)
    
    def test_seo_status_has_version(self):
        """SEO状态包含版本号"""
        resp = self.app.get('/api/seo/status')
        data = resp.get_json()
        self.assertIn('version', data)
        self.assertTrue(len(data['version']) > 0)
    
    def test_seo_push_returns_json(self):
        """POST /api/seo/push 返回JSON"""
        app2 = app.test_client()
        resp = app2.post('/api/seo/push')
        self.assertIn("status", resp.get_json())
    
    def test_health_check(self):
        """GET /api/health 返回正常"""
        resp = self.app.get('/api/health')
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['database'], 'connected')
        self.assertIn('endpoints', data)
        self.assertIn('version', data)
    
    def test_health_check_without_auth(self):
        """GET /api/health 无需认证"""
        app2 = app.test_client()
        resp = app2.get('/api/health')
        self.assertEqual(resp.status_code, 200)
    
    def test_health_check_detailed(self):
        """健康检查包含详细字段"""
        resp = self.app.get('/api/health')
        data = resp.get_json()
        self.assertIn('database_size_mb', data)
        self.assertIn('uptime', data)
        self.assertIn('timestamp', data)
        self.assertIsInstance(data['endpoints'], int)
    
    def test_content_plan_preview(self):
        """GET /api/content/plan-preview 返回排期信息"""
        resp = self.app.get('/api/content/plan-preview')
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertIn('has_plan', data)
        self.assertIn('total_scripts', data)
        self.assertIn('total_days', data)
    
    def test_content_plan_preview_has_days(self):
        """预览中的天数和脚本数应为正数"""
        resp = self.app.get('/api/content/plan-preview')
        data = resp.get_json()
        if data.get('has_plan'):
            self.assertGreater(data['total_days'], 0)
            self.assertGreater(data['total_scripts'], 0)
    
    def test_webhook_config_get(self):
        """GET /api/webhook/config 返回配置"""
        resp = self.app.get('/api/webhook/config')
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertIn('wechat_url', data)
        self.assertIn('dingtalk_url', data)
        self.assertIn('enabled', data)
    
    def test_webhook_config_save_and_clear(self):
        """PUT /api/webhook/config 保存并清除配置"""
        # Save test config
        resp = self.app.put('/api/webhook/config', json={
            'wechat_url': 'https://qyapi.weixin.qq.com/test',
            'dingtalk_url': 'https://oapi.dingtalk.com/test',
        })
        self.assertEqual(resp.status_code, 200)
    
    def test_content_plan_generate(self):
        """POST /api/content/plan 生成排期"""
        resp = self.app.post('/api/content/plan')
        data = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertIn('status', data)
    
    def test_admin_page_loads(self):
        """管理页面可访问"""
        resp = self.app.get('/admin')
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode('utf-8')
        self.assertIn('系统管理中心', html)


class TestContentPlanAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
    
    def test_plan_preview_without_auth(self):
        """排期预览无需认证"""
        app2 = app.test_client()
        resp = app2.get('/api/content/plan-preview')
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        if json_data.get('has_plan'):
            self.assertIn('next_day_preview', json_data)
            self.assertIsInstance(json_data['next_day_preview'], str)
        data = resp.get_json()


if __name__ == '__main__':
    unittest.main()
