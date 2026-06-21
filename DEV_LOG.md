# 永颐金磨石 AI内容营销系统 - 开发日志

## v5.4.0 (2026-06-21) - 密码保护
### 新增
- 🔐 **管理面板密码保护**: `https://ai.jinmojianshe.com/marketing/` 需要密码登录
  - Flask Session 认证 + 自定义登录页面
  - 密码: `liu201314`
  - 未登录 API 返回 401，页面返回登录页
  - 微信回调、health 检查不受影响（白名单）
  - 新增登录/登出/检查认证 API

### 技术要点
- Nginx `proxy_pass http://127.0.0.1:5050/` 会剥离 `/marketing/` 前缀
- Flask `before_request` 保护所有路由，白名单放行
- 微信回调 `Invalid signature` 是微信 handler 自身验证，非认证拦截

### 文件变更
- `app.py` - 添加 before_request 认证、登录/登出 API，版本升至 v5.4.0
- `templates/login.html` - 新建登录页面模板
- Nginx 配置无需修改

## v5.5.0 (2026-06-21) - DeepSeek AI + 内容引擎升级
### 新增
- 🤖 **DeepSeek AI 接入**: 内容生成从 Mock 模板升级为真实 AI 创作
  - API Key 已配置，AIClient 自动调用
  - 文案质量大幅提升（视频 ~260字、文章 ~1500字、小红书 ~330字）
  - 带 temperature=0.8 参数，内容多样化
  - AI 不可用时自动回退 Mock 模板
- 🔧 **内容引擎升级**: 增强 Prompt 设计 + 扩充 Mock 模板池
  - 抖音脚本: 10套模板（原3套）
  - 公众号文章: 5套模板（原2套），含案例/选购/趋势
  - 小红书笔记: 6套模板（原2套），多种风格
  - AI Prompt 优化：角色化设定、输出格式约束、品牌自然植入

### 技术要点
- systemd 服务配置完成，EnvironmentFile 加载 .env
- .env 文件管理 AI_API_KEY/API_BASE/MODEL
- sed 版本号替换需注意文件中文字符编码

### 文件变更
- `docs/marketing_system.py` - AI Prompt 优化 + 模板池扩充，版本 v5.5.0
- `.env` - 新建，存放 AI 密钥
- `/etc/systemd/system/yongyimoshi.service` - 新建 systemd 服务

## v5.4.0 (2026-06-21) - 密码保护
### 新增
- 🔐 **管理面板密码保护**: Flask Session 认证 + 自定义登录页
  - 密码: `liu201314`

### 访问
- 管理面板: https://ai.jinmojianshe.com/marketing/
- GitHub: https://github.com/wst3050469/yongyimoshi
