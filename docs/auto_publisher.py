#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全自动化发布引擎 v5.7.0 — Playwright浏览器自动化核心 + 会话管理"""
import json, os, time, random
from datetime import datetime
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PROFILE_DIR = os.path.join(DATA_DIR, 'browser_profiles')
os.makedirs(PROFILE_DIR, exist_ok=True)

# 各平台发布页配置
PLATFORM_CONFIG = {
    'douyin': {
        'name': '抖音', 'url': 'https://creator.douyin.com/creator-micro/content/upload',
        'title_selector': '[class*="title"] input, input[placeholder*="标题"], input:not([type="hidden"]):not([type="tel"]):not([type="checkbox"])',
        'content_selector': '[data-slate-editor], [contenteditable="true"], .public-DraftEditor-content, [class*="editor"]',
        'publish_btn': 'button:has-text("发布"), button:has-text("提交"), [class*="publish"]',
        'login_wall_texts': ['登录/注册', '登录', '手机号登录', '扫码登录'],
        'max_title_chars': 55
    },
    'xhs': {
        'name': '小红书', 'url': 'https://creator.xiaohongshu.com/publish/publish',
        'title_selector': 'input[placeholder*="标题"]', 'content_selector': 'div[contenteditable]',
        'publish_btn': 'button:has-text("发布")', 'max_title_chars': 20
    },
    'baijiahao': {
        'name': '百家号', 'url': 'https://baijiahao.baidu.com/builder/rc/edit',
        'title_selector': 'input[placeholder*="标题"]', 'content_selector': 'div.editor-content',
        'publish_btn': 'button:has-text("发布")', 'max_title_chars': 30
    },
    'zhihu': {
        'name': '知乎', 'url': 'https://zhuanlan.zhihu.com/write',
        'title_selector': 'textarea[placeholder*="标题"]', 'content_selector': 'div[contenteditable]',
        'publish_btn': 'button:has-text("发布")', 'max_title_chars': 50
    },
    'weibo': {
        'name': '微博', 'url': 'https://weibo.com/',
        'title_selector': None, 'content_selector': 'textarea[placeholder*="微博"]',
        'publish_btn': 'a:has-text("发布")', 'max_title_chars': 140
    },
    'wechat': {
        'name': '公众号', 'url': 'https://mp.weixin.qq.com/',
        'title_selector': 'input[placeholder*="标题"]', 'content_selector': 'div[contenteditable]',
        'publish_btn': 'button:has-text("保存")', 'max_title_chars': 64
    },
}

SESSION_FILE = os.path.join(PROFILE_DIR, 'sessions.json')


class AutoPublisher:
    """全自动发布器 — Playwright浏览器驱动"""

    def __init__(self):
        self.playwright = None
        self.browsers: Dict[str, Browser] = {}
        self.contexts: Dict[str, BrowserContext] = {}
        self.sessions = self._load_sessions()

    def _load_sessions(self) -> Dict:
        try:
            if os.path.exists(SESSION_FILE):
                with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def _save_sessions(self):
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.sessions, f, ensure_ascii=False, indent=2)

    # ===== 浏览器生命周期 =====

    def _ensure_playwright(self):
        if self.playwright is None:
            self.playwright = sync_playwright().start()

    def get_session(self, platform: str) -> Optional[Dict]:
        return self.sessions.get(platform)

    def get_all_sessions(self) -> Dict:
        result = {}
        for p, cfg in PLATFORM_CONFIG.items():
            sess = self.sessions.get(p, {})
            result[p] = {
                'name': cfg['name'], 'url': cfg['url'],
                'logged_in': bool(sess.get('cookies')),
                'last_login': sess.get('last_login', ''),
                'expires_in_days': sess.get('expires_in_days', 0)
            }
        return result

    def _get_context(self, platform: str) -> BrowserContext:
        """获取或创建平台的浏览器上下文（带会话持久化）"""
        profile_path = os.path.join(PROFILE_DIR, platform)
        os.makedirs(profile_path, exist_ok=True)

        self._ensure_playwright()
        browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox', '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage', '--disable-gpu',
            ]
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='zh-CN', timezone_id='Asia/Shanghai',
            storage_state=os.path.join(profile_path, 'state.json') if os.path.exists(
                os.path.join(profile_path, 'state.json')) else None,
        )
        # 反自动化检测
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN','zh','en']});
            window.chrome = {runtime: {}};
        """)

        self.browsers[platform] = browser
        self.contexts[platform] = context
        return context

    # ===== 手动登录（首次/会话过期） =====

    def manual_login(self, platform: str, timeout_seconds: int = 300) -> Dict:
        """打开浏览器让用户手动扫码登录，然后保存会话"""
        if platform not in PLATFORM_CONFIG:
            return {'success': False, 'error': f'不支持的平台: {platform}'}

        cfg = PLATFORM_CONFIG[platform]
        self._ensure_playwright()

        # 使用非headless模式打开浏览器
        browser = self.playwright.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            locale='zh-CN', timezone_id='Asia/Shanghai'
        )
        page = context.new_page()
        page.goto(cfg['url'], wait_until='networkidle', timeout=60000)

        print(f"[AutoPublisher] 请在浏览器中手动登录 {cfg['name']} (超时{timeout_seconds}秒)...")
        start = time.time()
        login_detected = False

        while time.time() - start < timeout_seconds:
            time.sleep(3)
            # 简单检测：URL不再是登录页
            current_url = page.url
            if 'login' not in current_url.lower() and 'passport' not in current_url.lower():
                login_detected = True
                break

        if login_detected:
            profile_path = os.path.join(PROFILE_DIR, platform)
            os.makedirs(profile_path, exist_ok=True)
            state_path = os.path.join(profile_path, 'state.json')
            context.storage_state(path=state_path)

            self.sessions[platform] = {
                'cookies': True,
                'last_login': datetime.now().isoformat(),
                'expires_in_days': 25
            }
            self._save_sessions()

            context.close()
            browser.close()
            return {'success': True, 'message': f'{cfg["name"]} 登录成功，会话已保存', 'platform': platform}
        else:
            context.close()
            browser.close()
            return {'success': False, 'error': f'登录超时，请在{timeout_seconds}秒内完成登录'}

    def import_session(self, platform: str, cookies_json: str) -> Dict:
        """
        导入浏览器cookies（从浏览器导出的JSON格式）
        管理员在自己的浏览器登录后，导出cookies JSON上传到服务器。
        
        支持的cookie格式:
        1. Playwright storage_state格式: {"cookies": [...], "origins": [...]}
        2. 纯cookies数组: [{"name":"...","value":"...","domain":"..."}, ...]
        3. Netscape格式文本（自动解析）
        """
        if platform not in PLATFORM_CONFIG:
            return {'success': False, 'error': f'不支持的平台: {platform}'}
        
        cfg = PLATFORM_CONFIG[platform]
        
        try:
            import json as _json
            data = _json.loads(cookies_json) if isinstance(cookies_json, str) else cookies_json
            
            # 规范化cookies
            if isinstance(data, dict) and 'cookies' in data:
                cookies = data['cookies']
                origins = data.get('origins', [])
            elif isinstance(data, list):
                cookies = data
                origins = []
            else:
                return {'success': False, 'error': '无法解析cookie格式，需要JSON数组或{cookies:[...]}对象'}
            
            # 验证cookie格式
            valid_cookies = []
            for c in cookies:
                if isinstance(c, dict) and 'name' in c and 'value' in c:
                    valid_cookies.append({
                        'name': c['name'],
                        'value': c['value'],
                        'domain': c.get('domain', ''),
                        'path': c.get('path', '/'),
                        'httpOnly': c.get('httpOnly', False),
                        'secure': c.get('secure', False),
                        'sameSite': c.get('sameSite', 'Lax')
                    })
            
            if not valid_cookies:
                return {'success': False, 'error': '没有有效的cookie条目'}
            
            # 保存为Playwright storage_state格式
            profile_path = os.path.join(PROFILE_DIR, platform)
            os.makedirs(profile_path, exist_ok=True)
            state_path = os.path.join(profile_path, 'state.json')
            
            state = {'cookies': valid_cookies, 'origins': origins}
            with open(state_path, 'w', encoding='utf-8') as f:
                _json.dump(state, f, ensure_ascii=False, indent=2)
            
            self.sessions[platform] = {
                'cookies': True,
                'last_login': datetime.now().isoformat(),
                'expires_in_days': 25,
                'cookie_count': len(valid_cookies),
                'import_method': 'manual_upload'
            }
            self._save_sessions()
            
            return {
                'success': True,
                'platform': platform,
                'platform_name': cfg['name'],
                'cookie_count': len(valid_cookies),
                'message': f'{cfg["name"]} 会话已导入 ({len(valid_cookies)}个cookies)'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'导入失败: {str(e)}'}

    # ===== 自动发布核心 =====

    def publish(self, platform: str, title: str, content: str,
                media_path: Optional[str] = None, dry_run: bool = False) -> Dict:
        """自动发布内容到指定平台"""
        if platform not in PLATFORM_CONFIG:
            return {'success': False, 'error': f'不支持的平台: {platform}'}

        cfg = PLATFORM_CONFIG[platform]

        # dry_run模式：不启动浏览器，返回模拟结果
        if dry_run:
            return {
                'success': True,
                'platform': platform,
                'platform_name': cfg['name'],
                'title': title[:cfg['max_title_chars']],
                'content_length': len(content),
                'dry_run': True,
                'published_at': datetime.now().isoformat(),
                'message': f'[DRY_RUN] 将在 {cfg["name"]}({cfg["url"]}) 发布，标题: {title[:50]}'
            }

        sess = self.sessions.get(platform, {})

        # 公众号走API通道
        if platform == 'wechat':
            return self._publish_wechat_api(title, content)

        # 检查登录状态（dry_run模式跳过）
        if not sess.get('cookies') and not dry_run:
            return {
                'success': False,
                'error': f'{cfg["name"]}未登录，请先调用 manual_login',
                'need_login': True, 'platform': platform
            }

        context = None
        try:
            context = self._get_context(platform)
            page = context.new_page()
            page.set_default_timeout(30000)

            # 1. 打开发布页
            try:
                page.goto(cfg['url'], wait_until='networkidle', timeout=60000)
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                pass

            # 1.5 检测登录墙（页面内嵌登录界面）
            login_wall = False
            login_texts = cfg.get('login_wall_texts', ['登录/注册', '登录', '手机号登录'])
            for lt in login_texts:
                try:
                    if page.locator(f'text="{lt}"').count() > 0:
                        login_wall = True
                        break
                except:
                    pass
            if 'login' in page.url.lower() or 'passport' in page.url.lower():
                login_wall = True

            if login_wall:
                try:
                    screenshot_path = os.path.join(DATA_DIR, f'loginwall_{platform}_{int(time.time())}.png')
                    page.screenshot(path=screenshot_path, full_page=False)
                except:
                    screenshot_path = ''
                context.close()
                return {
                    'success': False, 'platform': platform, 'platform_name': cfg['name'],
                    'login_wall': True, 'need_login': True,
                    'error': f'{cfg["name"]}需要登录！请先导入Cookie',
                    'screenshot': screenshot_path
                }

            # 2. 填入标题
            if cfg['title_selector'] and title:
                try:
                    title_input = page.wait_for_selector(cfg['title_selector'], timeout=10000)
                    title_input.click()
                    # 模拟人类打字
                    short_title = title[:cfg['max_title_chars']]
                    for char in short_title:
                        title_input.type(char, delay=random.randint(50, 150))
                        time.sleep(random.uniform(0.01, 0.05))
                    time.sleep(1)
                except Exception as e:
                    pass  # 标题字段可能不存在于某些平台

            # 3. 填入内容
            if cfg['content_selector'] and content:
                try:
                    content_area = page.wait_for_selector(cfg['content_selector'], timeout=10000)
                    content_area.click()
                    # 分段输入以模拟人类
                    chunks = content.split('\n')
                    for chunk in chunks:
                        if chunk.strip():
                            page.keyboard.type(chunk.strip(), delay=30)
                            page.keyboard.press('Enter')
                            time.sleep(random.uniform(0.1, 0.3))
                except Exception as e:
                    pass

            time.sleep(1)

            # 4. 上传媒体文件(如有)
            if media_path and os.path.exists(media_path):
                try:
                    file_input = page.locator('input[type="file"]').first
                    if file_input:
                        file_input.set_input_files(media_path)
                        time.sleep(5)  # 等待上传
                except:
                    pass

            # 5. 截图保存
            screenshot_path = os.path.join(DATA_DIR, f'publish_{platform}_{int(time.time())}.png')
            page.screenshot(path=screenshot_path, full_page=False)

            # 6. 点击发布
            if not dry_run:
                try:
                    publish_btn = page.wait_for_selector(cfg['publish_btn'], timeout=5000)
                    publish_btn.click()
                    time.sleep(3)
                    # 可能有确认弹窗
                    confirm_btn = page.locator('button:has-text("确定"), button:has-text("确认")')
                    if confirm_btn.count() > 0:
                        confirm_btn.first.click()
                        time.sleep(2)
                except Exception as e:
                    pass

            # 7. 保存cookies
            profile_path = os.path.join(PROFILE_DIR, platform)
            state_path = os.path.join(profile_path, 'state.json')
            context.storage_state(path=state_path)

            return {
                'success': True,
                'platform': platform,
                'platform_name': cfg['name'],
                'title': title[:cfg['max_title_chars']],
                'content_length': len(content),
                'screenshot': screenshot_path,
                'dry_run': dry_run,
                'published_at': datetime.now().isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': str(e), 'platform': platform}
        finally:
            if context:
                try:
                    context.close()
                except:
                    pass

    def _publish_wechat_api(self, title: str, content: str) -> Dict:
        """通过微信API发布到草稿箱"""
        try:
            from docs.wechat_publisher import WeChatPublisher, PublishExporter
            wp = WeChatPublisher()
            html = PublishExporter.export_html_article(title, content)
            result = wp.create_draft(title, html)
            return {
                'success': result.get('success', False),
                'platform': 'wechat',
                'platform_name': '公众号',
                'media_id': result.get('media_id', ''),
                'error': result.get('error', ''),
                'channel': 'api'
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'platform': 'wechat'}

    # ===== 批量发布 =====

    def batch_publish(self, platforms: List[str], title: str, content: str,
                      media_path: Optional[str] = None, dry_run: bool = False) -> List[Dict]:
        """同一内容批量发布到多平台"""
        results = []
        for p in platforms:
            r = self.publish(p, title, content, media_path, dry_run)
            results.append(r)
            time.sleep(random.uniform(2, 5))  # 平台间间隔
        return results

    # ===== 会话管理 =====

    def check_session(self, platform: str) -> Dict:
        """快速检测平台登录状态"""
        if platform not in PLATFORM_CONFIG:
            return {'success': False, 'error': f'未知平台: {platform}'}

        cfg = PLATFORM_CONFIG[platform]
        sess = self.sessions.get(platform, {})
        if not sess.get('cookies'):
            return {'platform': platform, 'name': cfg['name'], 'logged_in': False,
                    'message': '未登录，请调用 manual_login'}

        # 快速访问检测
        try:
            context = self._get_context(platform)
            page = context.new_page()
            page.goto(cfg['url'], wait_until='domcontentloaded', timeout=20000)
            current_url = page.url
            logged_in = 'login' not in current_url.lower()
            context.close()

            if not logged_in:
                self.sessions.pop(platform, None)
                self._save_sessions()

            return {
                'platform': platform, 'name': cfg['name'],
                'logged_in': logged_in,
                'last_login': sess.get('last_login', ''),
                'expires_in_days': sess.get('expires_in_days', 0)
            }
        except Exception as e:
            return {'platform': platform, 'name': cfg['name'],
                    'logged_in': True,  # 假设仍有效
                    'last_login': sess.get('last_login', ''),
                    'note': f'检测异常: {str(e)[:100]}'}

    def cleanup(self):
        """清理所有浏览器资源"""
        for ctx in self.contexts.values():
            try: ctx.close()
            except: pass
        for browser in self.browsers.values():
            try: browser.close()
            except: pass
        if self.playwright:
            try: self.playwright.stop()
            except: pass
        self.contexts = {}
        self.browsers = {}
        self.playwright = None


# 全局单例
auto_publisher = AutoPublisher()
