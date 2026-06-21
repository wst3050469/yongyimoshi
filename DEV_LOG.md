# 永颐金磨石 AI内容营销系统 - 开发日志

## v5.2.0 (2026-06-21)
### 新增功能
- 🎴 **视频卡片视图**: 视频列表从表格改为卡片式布局
- 🔍 **视频详情弹窗**: 点击卡片弹出详情，含播放器、下载、复制链接
- 💾 **内容持久化**: 生成的营销内容自动保存到 data/content_history.json
- 📋 **内容历史管理**: 面板新增历史区域，支持查看/复制/删除
- 📊 **统计自动加载**: 页面加载时通过 /api/stats 自动填充统计数字

### 文件变更
- `app.py` - 新增 /api/stats, /api/contents 路由
- `docs/content_store.py` - 新建内容持久化模块
- `templates/marketing_dashboard.html` - 全面升级UI (474行)

### 访问地址
- 管理面板: https://ai.jinmojianshe.com/marketing/
- GitHub: https://github.com/wst3050469/yongyimoshi

## v5.1.0 (之前)
- 集成豆包 Seedance 视频生成 API
- VideoGenerator 持久化存储 + 后台轮询
- 管理面板集成视频生成功能
