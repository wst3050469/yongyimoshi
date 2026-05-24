"""
永颐无机磨石 · Webhook通知模块测试
"""

import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['SECRET_KEY'] = 'test-webhook'

from webhook import (
    send_wechat_webhook,
    send_dingtalk_webhook,
    send_notification,
    format_phase_update,
    format_daily_log,
    format_safety_issue,
    format_quality_test,
)


class TestFormatFunctions(unittest.TestCase):
    """测试通知格式化函数"""

    def test_format_phase_update(self):
        """测试工序更新格式化"""
        title, msg = format_phase_update("测试项目", "基层处理", "in_progress", "not_started")
        self.assertIn("基层处理", title)
        self.assertIn("测试项目", msg)
        self.assertIn("🔵 进行中", msg)

    def test_format_phase_update_no_old(self):
        """测试无旧状态的工序更新"""
        title, msg = format_phase_update("项目A", "面层浇筑", "completed")
        self.assertIn("面层浇筑", title)
        self.assertIn("✅ 已完成", msg)

    def test_format_daily_log(self):
        """测试施工日志格式化"""
        title, msg = format_daily_log("项目B", "今日完成面层浇筑50㎡", "张三")
        self.assertIn("项目B", msg)
        self.assertIn("张三", msg)
        self.assertIn("50㎡", msg)

    def test_format_safety_issue_high(self):
        """测试安全问题格式化（高严重度）"""
        title, msg = format_safety_issue("项目C", "脚手架未固定", "high")
        self.assertIn("🔴", title)
        self.assertIn("脚手架", msg)

    def test_format_safety_issue_low(self):
        """测试安全问题格式化（低严重度）"""
        title, msg = format_safety_issue("项目D", "安全帽佩戴不规范", "low")
        self.assertIn("🟢", title)

    def test_format_quality_test_passed(self):
        """测试质量检测通过"""
        title, msg = format_quality_test("项目E", "光泽度检测", "光泽度72GU", True)
        self.assertIn("✅", msg)
        self.assertIn("光泽度72GU", msg)

    def test_format_quality_test_failed(self):
        """测试质量检测未通过"""
        title, msg = format_quality_test("项目F", "抗压强度检测", "强度45MPa", False)
        self.assertIn("❌", msg)
        self.assertIn("45MPa", msg)


class TestSendFunctions(unittest.TestCase):
    """测试Webhook发送函数"""

    @patch('webhook.urlopen')
    def test_send_wechat_success(self, mock_urlopen):
        """测试企业微信发送成功"""
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"errcode": 0, "errmsg": "ok"}'
        mock_urlopen.return_value = mock_resp

        result = send_wechat_webhook(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test",
            "测试标题",
            "测试消息"
        )
        self.assertTrue(result)

    @patch('webhook.urlopen')
    def test_send_wechat_fail(self, mock_urlopen):
        """测试企业微信发送失败"""
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"errcode": 40001, "errmsg": "invalid key"}'
        mock_urlopen.return_value = mock_resp

        result = send_wechat_webhook(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=bad",
            "测试",
            "测试"
        )
        self.assertFalse(result)

    def test_send_wechat_invalid_url(self):
        """测试无效的企业微信URL"""
        result = send_wechat_webhook("https://example.com/", "标题", "内容")
        self.assertFalse(result)

    def test_send_wechat_empty_url(self):
        """测试空URL"""
        result = send_wechat_webhook("", "标题", "内容")
        self.assertFalse(result)

    @patch('webhook.urlopen')
    def test_send_dingtalk_success(self, mock_urlopen):
        """测试钉钉发送成功"""
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"errcode": 0, "errmsg": "ok"}'
        mock_urlopen.return_value = mock_resp

        result = send_dingtalk_webhook(
            "https://oapi.dingtalk.com/robot/send?access_token=test",
            "测试标题",
            "测试消息"
        )
        self.assertTrue(result)

    def test_send_dingtalk_invalid_url(self):
        """测试无效的钉钉URL"""
        result = send_dingtalk_webhook("https://example.com/", "标题", "内容")
        self.assertFalse(result)


class TestSendNotification(unittest.TestCase):
    """测试综合通知函数"""

    @patch('config.get_config')
    @patch('webhook.send_wechat_webhook')
    @patch('webhook.send_dingtalk_webhook')
    def test_send_both_channels(self, mock_ding, mock_wechat, mock_config):
        """测试同时推送到两个渠道"""
        mock_config.side_effect = lambda section, key: {
            ("webhook", "wechat_url"): "https://qyapi.weixin.qq.com/test",
            ("webhook", "dingtalk_url"): "https://oapi.dingtalk.com/test",
            ("webhook", "enabled"): True,
            ("webhook", "notify_on"): ["general"],
        }.get((section, key), "")
        mock_wechat.return_value = True
        mock_ding.return_value = True

        result = send_notification("测试通知", "测试内容", "general", "项目X")
        self.assertTrue(result["wechat"])
        self.assertTrue(result["dingtalk"])

    @patch('config.get_config')
    @patch('webhook.send_wechat_webhook')
    def test_send_wechat_only(self, mock_wechat, mock_config):
        """测试只推送企业微信"""
        mock_config.side_effect = lambda section, key: {
            ("webhook", "wechat_url"): "https://qyapi.weixin.qq.com/test",
            ("webhook", "dingtalk_url"): "",
            ("webhook", "enabled"): True,
            ("webhook", "notify_on"): ["general"],
        }.get((section, key), "")
        mock_wechat.return_value = True

        result = send_notification("测试", "内容", "general")
        self.assertTrue(result["wechat"])
        self.assertFalse(result["dingtalk"])

    @patch('config.get_config')
    def test_no_webhook_configured(self, mock_config):
        """测试没有配置Webhook"""
        mock_config.side_effect = lambda section, key: {
            ("webhook", "wechat_url"): "",
            ("webhook", "dingtalk_url"): "",
            ("webhook", "enabled"): True,
            ("webhook", "notify_on"): ["general"],
        }.get((section, key), "")

        result = send_notification("测试", "内容")
        self.assertFalse(result["wechat"])
        self.assertFalse(result["dingtalk"])

    @patch('config.get_config')
    @patch('webhook.send_wechat_webhook')
    @patch('webhook.send_dingtalk_webhook')
    def test_with_project_name(self, mock_ding, mock_wechat, mock_config):
        """测试带项目名称的通知"""
        mock_config.side_effect = lambda section, key: {
            ("webhook", "wechat_url"): "https://qyapi.weixin.qq.com/test",
            ("webhook", "dingtalk_url"): "https://oapi.dingtalk.com/test",
            ("webhook", "enabled"): True,
            ("webhook", "notify_on"): ["phase_update"],
        }.get((section, key), "")
        mock_wechat.return_value = True
        mock_ding.return_value = True

        result = send_notification("工序更新", "基层处理完成", "phase_update", "酒店项目")
        self.assertTrue(result["wechat"])
        # 验证项目名出现在消息中
        call_args = mock_wechat.call_args[0]
        self.assertIn("酒店项目", call_args[2])


if __name__ == '__main__':
    unittest.main()
