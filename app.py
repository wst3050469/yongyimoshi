#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 AI营销系统 Flask App - v5.7.0 (全自动化发布)
注意：Nginx proxy_pass http://127.0.0.1:5050/ 会剥离 /marketing/ 前缀
Flask 实际收到的路径是 /, /api/*, /wechat/* 等"""
import sys, os, json, logging, uuid
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from flask import Flask, jsonify, request, render_template, session
from docs.marketing_system import KeywordEngine, CompetitorAnalyzer, MarketingReport
from docs.video_generator import VideoGenerator
from docs.content_store import ContentStore
from docs.keyword_miner import KeywordMiner
from docs.publish_engine import PublishEngine
from docs.analytics_tracker import AnalyticsTracker
from docs.ai_quality import AIQualityEngine
from docs.wechat_publisher import WeChatPublisher, PublishExporter, PublishedStore
from docs.wechat_handler import wechat_handler as wechat_route
from docs.auto_publisher import AutoPublisher
from docs.publish_pipeline import PublishPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

app = Flask(__name__)

# ===== 认证配置 =====
app.secret_key = os.environ.get('FLASK_SECRET_KEY', uuid.uuid4().hex)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'liu201314')

# 无需认证的路径前缀（白名单）- 注意：Nginx 剥离了 /marketing/ 前缀
AUTH_WHITELIST = ['/api/login', '/api/check-auth', '/health', '/wechat']

@app.before_request
def auth_check():
    """对所有需要保护的路径进行登录验证"""
    path = request.path
    # 白名单路径放行
    for wl in AUTH_WHITELIST:
        if path.startswith(wl):
            return None
    # 检查登录状态
    if not session.get('authenticated'):
        # API 请求返回 401 JSON
        if path.startswith('/api/'):
            return jsonify({"status": "error", "message": "未登录"}), 401
        # 页面请求显示登录页
        return render_template("login.html"), 403

@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, DELETE'
    return resp

# ===== 全局实例 =====
ke = KeywordEngine()
ca = CompetitorAnalyzer()
vg = VideoGenerator()
cs = ContentStore()
km = KeywordMiner()
pe = PublishEngine()
at = AnalyticsTracker()
aq = AIQualityEngine()
wcp = WeChatPublisher()
pse = PublishedStore()
apb = AutoPublisher()
ppl = PublishPipeline()

# ===== 登录/登出 =====

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    password = data.get("password", "")
    if password == ADMIN_PASSWORD:
        session['authenticated'] = True
        session['login_time'] = datetime.now().isoformat()
        log.info("Admin login successful")
        return jsonify({"status": "ok", "message": "登录成功"})
    log.warning("Admin login failed")
    return jsonify({"status": "error", "message": "密码错误"}), 401

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    log.info("Admin logout")
    return jsonify({"status": "ok", "message": "已登出"})

@app.route("/api/check-auth")
def check_auth():
    return jsonify({"authenticated": session.get('authenticated', False)})

# ===== 首页 =====

@app.route("/")
def index():
    return render_template("marketing_dashboard.html")

@app.route("/health")
def health():
    return jsonify({"status":"ok","service":"yongyi-marketing","version":"5.7.0","time":datetime.now().isoformat()})

# ===== 仪表盘统计 =====

@app.route("/api/stats")
def stats():
    kws = ke.get_kws()
    kw_count = sum(len(v) for v in kws.values())
    content_stats = cs.get_stats()
    comps = ca.get_comps()
    video_tasks = vg.get_all_tasks()
    publish_stats = pe.get_stats()
    analytics_stats = at.get_platform_stats()
    return jsonify({
        "keywords": kw_count,
        "contents": content_stats["total"],
        "competitors": len(comps),
        "reports": content_stats["daily"],
        "videos": len(video_tasks),
        "pending_review": publish_stats["by_status"]["pending"],
        "published": publish_stats["by_status"]["published"],
        "total_views": analytics_stats.get("total_views", 0)
    })

# ===== 关键词管理 =====

@app.route("/api/keywords", methods=["GET", "POST"])
def keywords():
    if request.method == "POST":
        data = request.get_json() or {}
        action = data.get("action", "")
        keyword = data.get("keyword", "")
        if action == "add" and keyword:
            ke.add_keyword(keyword)
            log.info(f"Keyword added: {keyword}")
            return jsonify({"status": "ok", "keyword": keyword})
        return jsonify({"status": "error", "message": "invalid"})
    return jsonify({"keywords": ke.get_kws()})

# ===== 内容生成 =====

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    kw = data.get("keyword", "") or "磨石"
    grp = data.get("group", "产品词")
    log.info(f"Generating content: keyword={kw}, group={grp}")
    
    video_script = ke.gen_video(kw, grp)
    article = ke.gen_article(kw, grp)
    xhs = ke.gen_xhs(kw, grp)
    
    cs.save("video_script", kw, grp, video_script)
    cs.save("article", kw, grp, article)
    cs.save("xhs_note", kw, grp, xhs)
    
    return jsonify({
        "video": video_script,
        "article": article,
        "xhs": xhs
    })

# ===== 内容历史管理 =====

@app.route("/api/contents", methods=["GET", "DELETE"])
def contents():
    if request.method == "DELETE":
        data = request.get_json() or {}
        cid = data.get("id", "")
        if cid and cs.delete(cid):
            log.info(f"Content deleted: {cid}")
            return jsonify({"status": "ok"})
        return jsonify({"status": "error", "message": "not found"}), 404
    content_type = request.args.get("type", "")
    if content_type:
        return jsonify({"contents": cs.get_by_type(content_type)})
    return jsonify({"contents": cs.get_all()})

# ===== 竞品分析 =====

@app.route("/api/competitors", methods=["GET", "POST"])
def competitors():
    if request.method == "POST":
        data = request.get_json() or {}
        url = data.get("url", "")
        if url:
            ca.add_comp(url)
            log.info(f"Competitor added: {url}")
            return jsonify({"status": "ok", "url": url})
        return jsonify({"status": "error"})
    return jsonify({"competitors": ca.get_comps()})

@app.route("/api/analysis")
def analysis():
    comps = ca.get_comps()
    plan = ca.surpass(comps)
    return jsonify({"analysis": plan, "report": plan})

# ===== 综合报告 =====

@app.route("/api/report", methods=["POST"])
def report():
    data = request.get_json() or {}
    kws = ke.get_kws()
    comps = ca.get_comps()
    content_stats = cs.get_stats()
    summary_info = MarketingReport.summary(len(kws), content_stats["daily"], len(comps))
    return jsonify({"report": summary_info, "summary": summary_info})

# ===== 视频生成 =====

@app.route("/api/video/create", methods=["POST"])
def video_create():
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    keyword = data.get("keyword", "")
    group = data.get("group", "产品词")
    
    if not prompt and keyword:
        prompt = vg.generate_prompt(keyword, group)
    if not prompt:
        return jsonify({"status": "error", "message": "请提供prompt或关键词"})
    
    ref_images = data.get("ref_images", None)
    ref_video = data.get("ref_video", None)
    ref_audio = data.get("ref_audio", None)
    ratio = data.get("ratio", "16:9")
    duration = data.get("duration", 11)
    
    result = vg.create_task(prompt, ref_images, ref_video, ref_audio, ratio, duration)
    log.info(f"Video task created: {result.get('task_id', 'failed')}")
    return jsonify(result)

@app.route("/api/video/status/<task_id>")
def video_status(task_id):
    result = vg.query_task(task_id)
    return jsonify(result)

@app.route("/api/video/tasks")
def video_tasks():
    return jsonify({"tasks": vg.get_all_tasks()})

# ===== AI关键词挖掘 =====

@app.route("/api/keywords/ai-mine", methods=["POST"])
def ai_mine_keywords():
    data = request.get_json() or {}
    platforms = data.get("platforms", ["douyin", "xhs", "baidu"])
    if isinstance(platforms, str):
        platforms = [platforms]
    count = data.get("count", 10)
    
    log.info(f"Mining keywords from: {platforms}")
    keywords = km.get_trending(platforms, count)
    batch = km.save_mined(keywords)
    
    return jsonify({
        "status": "ok",
        "keywords": keywords,
        "batch_id": batch["id"],
        "platforms": platforms,
        "count": len(keywords)
    })

@app.route("/api/keywords/mined-history")
def mined_history():
    return jsonify({"history": km.get_mined_history()})

@app.route("/api/keywords/agent-mine", methods=["POST"])
def agent_mine():
    """AI Agent 全量深度挖掘：语义扩展 + 长尾词 + 问答 + 竞品 + 平台"""
    data = request.get_json() or {}
    seed_words = data.get("seeds", None)
    platforms = data.get("platforms", ["douyin", "xhs", "baidu"])
    rounds = data.get("rounds", None)  # None = all 4 agent rounds
    
    log.info(f"Agent deep mining: seeds={seed_words}, platforms={platforms}, rounds={rounds}")
    result = km.deep_mine(seed_words=seed_words, platforms=platforms, rounds=rounds)
    return jsonify({"status": "ok", "data": result})

@app.route("/api/keywords/mined-pool")
def mined_pool():
    """获取持久化关键词池（去重累积）"""
    pool = km.get_mined_pool()
    return jsonify({"status": "ok", "total": len(pool), "keywords": pool})


# ===== 全平台内容生成 =====

@app.route("/api/generate/all-platforms", methods=["POST"])
def generate_all_platforms():
    data = request.get_json() or {}
    kw = data.get("keyword", "") or "磨石"
    grp = data.get("group", "产品词")
    log.info(f"Generating ALL platforms: keyword={kw}, group={grp}")
    
    results = ke.gen_all_platforms(kw)
    
    # 保存各平台内容
    type_map = {
        "douyin": "video_script",
        "wechat_article": "article",
        "xhs": "xhs_note",
        "baijiahao": "baijiahao",
        "zhihu": "zhihu",
        "weibo": "weibo"
    }
    for platform, content in results.items():
        cs.save(type_map.get(platform, platform), kw, grp, content)
    
    return jsonify({"status": "ok", "keyword": kw, "contents": results})


# ===== 发布审核工作流 =====

@app.route("/api/publish/submit", methods=["POST"])
def publish_submit():
    data = request.get_json() or {}
    content = data.get("content", "")
    platform = data.get("platform", "wechat_article")
    keyword = data.get("keyword", "")
    title = data.get("title", "")
    note = data.get("note", "")
    
    if not content:
        return jsonify({"status": "error", "message": "内容不能为空"})
    
    result = pe.submit_for_review(content, platform, keyword, title, note)
    log.info(f"Publish submitted: {result['id']} -> {platform}")
    return jsonify({"status": "ok", "data": result})

@app.route("/api/publish/batch-submit", methods=["POST"])
def publish_batch_submit():
    data = request.get_json() or {}
    items = data.get("items", [])
    if not items:
        return jsonify({"status": "error", "message": "提交列表不能为空"})
    results = pe.batch_submit(items)
    log.info(f"Batch submit: {len(results)} items")
    return jsonify({"status": "ok", "count": len(results), "data": results})

@app.route("/api/publish/queue")
def publish_queue():
    status = request.args.get("status", "")
    items = pe.get_queue(status)
    return jsonify({"status": "ok", "queue": items, "stats": pe.get_stats()})

@app.route("/api/publish/stats")
def publish_stats():
    return jsonify({"status": "ok", "stats": pe.get_stats()})

@app.route("/api/publish/approve", methods=["POST"])
def publish_approve():
    data = request.get_json() or {}
    pid = data.get("id", "")
    comment = data.get("comment", "审核通过")
    if not pid:
        return jsonify({"status": "error", "message": "缺少发布ID"})
    result = pe.approve(pid, comment)
    log.info(f"Publish approved: {pid}")
    return jsonify(result)

@app.route("/api/publish/reject", methods=["POST"])
def publish_reject():
    data = request.get_json() or {}
    pid = data.get("id", "")
    reason = data.get("reason", "已驳回")
    if not pid:
        return jsonify({"status": "error", "message": "缺少发布ID"})
    result = pe.reject(pid, reason)
    log.info(f"Publish rejected: {pid}")
    return jsonify(result)

@app.route("/api/publish/publish", methods=["POST"])
def publish_do():
    data = request.get_json() or {}
    pid = data.get("id", "")
    url = data.get("url", "")
    if not pid:
        return jsonify({"status": "error", "message": "缺少发布ID"})
    result = pe.publish(pid, url)
    log.info(f"Published: {pid}")
    return jsonify(result)

@app.route("/api/publish/detail/<pid>")
def publish_detail(pid):
    item = pe.get_item(pid)
    if item:
        return jsonify({"status": "ok", "data": item})
    return jsonify({"status": "error", "message": "未找到"}), 404


# ===== 效果数据跟踪 =====

@app.route("/api/analytics/record", methods=["POST"])
def analytics_record():
    data = request.get_json() or {}
    pid = data.get("publish_id", "")
    if not pid:
        return jsonify({"status": "error", "message": "缺少publish_id"})
    record = at.record_metrics(
        publish_id=pid,
        platform=data.get("platform", ""),
        views=data.get("views", 0),
        likes=data.get("likes", 0),
        comments=data.get("comments", 0),
        shares=data.get("shares", 0),
        saves=data.get("saves", 0),
        extra=data.get("extra")
    )
    log.info(f"Analytics recorded: {pid}")
    return jsonify({"status": "ok", "data": record})

@app.route("/api/analytics/dashboard")
def analytics_dashboard():
    return jsonify({"status": "ok", "dashboard": at.get_dashboard()})

@app.route("/api/analytics/content/<pid>")
def analytics_content(pid):
    perf = at.get_content_performance(pid)
    if perf:
        return jsonify({"status": "ok", "data": perf})
    return jsonify({"status": "error", "message": "未找到效果数据"}), 404

@app.route("/api/analytics/records")
def analytics_records():
    platform = request.args.get("platform", "")
    days = int(request.args.get("days", 30))
    records = at.get_all_records(platform, days)
    return jsonify({"status": "ok", "records": records, "count": len(records)})

@app.route("/api/analytics/platform-stats")
def analytics_platform_stats():
    platform = request.args.get("platform", "")
    stats = at.get_platform_stats(platform)
    return jsonify({"status": "ok", "stats": stats})


# ===== v5.6.2 AI质量评估 =====

@app.route("/api/ai-quality/score", methods=["POST"])
def ai_score():
    data = request.get_json() or {}
    content = data.get("content", "")
    platform = data.get("platform", "wechat_article")
    keyword = data.get("keyword", "")
    if not content:
        return jsonify({"status": "error", "message": "内容不能为空"})
    scores = aq.score_content(content, platform, keyword)
    return jsonify({"status": "ok", "scores": scores})

@app.route("/api/ai-quality/suggest", methods=["POST"])
def ai_suggest():
    data = request.get_json() or {}
    content = data.get("content", "")
    platform = data.get("platform", "wechat_article")
    scores = data.get("scores")
    if not content:
        return jsonify({"status": "error", "message": "内容不能为空"})
    result = aq.suggest_improvements(content, platform, scores)
    return jsonify({"status": "ok", "suggestions": result.get("suggestions", [])})

@app.route("/api/ai-quality/optimize", methods=["POST"])
def ai_optimize():
    data = request.get_json() or {}
    content = data.get("content", "")
    platform = data.get("platform", "wechat_article")
    keyword = data.get("keyword", "")
    if not content:
        return jsonify({"status": "error", "message": "内容不能为空"})
    result = aq.optimize_content(content, platform, keyword)
    return jsonify({"status": "ok", "optimized": result.get("optimized", content)})

@app.route("/api/ai-quality/full-review", methods=["POST"])
def ai_full_review():
    data = request.get_json() or {}
    content = data.get("content", "")
    platform = data.get("platform", "wechat_article")
    keyword = data.get("keyword", "")
    if not content:
        return jsonify({"status": "error", "message": "内容不能为空"})
    result = aq.full_review(content, platform, keyword)
    return jsonify({"status": "ok", "review": result})

@app.route("/api/ai-quality/insight", methods=["POST"])
def ai_insight():
    data = request.get_json() or {}
    analytics = data.get("analytics", {})
    result = aq.analyze_performance(analytics)
    return jsonify({"status": "ok", "insight": result})

@app.route("/api/ai-quality/strategy", methods=["POST"])
def ai_strategy():
    data = request.get_json() or {}
    history = data.get("history", {})
    result = aq.recommend_strategy(history)
    return jsonify({"status": "ok", "strategy": result})


# ===== v5.6.2 真实发布通道 =====

@app.route("/api/publish/to-wechat", methods=["POST"])
def publish_to_wechat():
    """发布到微信公众号草稿箱"""
    data = request.get_json() or {}
    title = data.get("title", "")
    content = data.get("content", "")
    keyword = data.get("keyword", "")
    pid = data.get("publish_id", "")
    
    if not content:
        return jsonify({"status": "error", "message": "内容不能为空"})
    
    # 转HTML格式
    html_content = PublishExporter.export_html_article(title or keyword, content)
    
    # 尝试发布到微信草稿箱
    result = wcp.create_draft(title=title or keyword, content=html_content)
    
    # 记录发布结果
    if pid:
        pse.add(pid, "wechat_article", result)
        if result.get("success"):
            pe.publish(pid, url=f"wechat://draft/{result.get('media_id', '')}")
    
    log.info(f"WeChat publish: {title}, success={result.get('success')}")
    return jsonify({
        "status": "ok" if result.get("success") else "partial",
        "result": result,
        "hint": result.get("hint", ""),
        "ready_to_paste": result.get("ready_to_paste", False)
    })

@app.route("/api/publish/export", methods=["POST"])
def publish_export():
    """为指定平台导出格式化发布包"""
    data = request.get_json() or {}
    content = data.get("content", "")
    platform = data.get("platform", "wechat_article")
    title = data.get("title", "")
    keyword = data.get("keyword", "")
    
    if not content:
        return jsonify({"status": "error", "message": "内容不能为空"})
    
    pkg = PublishExporter.export_for_platform(content, platform, title or keyword, keyword)
    return jsonify({"status": "ok", "package": pkg})

@app.route("/api/publish/export-all", methods=["POST"])
def publish_export_all():
    """全平台格式化导出"""
    data = request.get_json() or {}
    contents = data.get("contents", {})
    keyword = data.get("keyword", "")
    
    if not contents:
        return jsonify({"status": "error", "message": "没有内容可导出"})
    
    packages = PublishExporter.export_all_platforms(contents, keyword)
    return jsonify({"status": "ok", "packages": packages, "count": len(packages)})

@app.route("/api/publish/history")
def published_history():
    """已发布记录"""
    return jsonify({"status": "ok", "records": pse.get_all(), "stats": pse.get_stats()})

@app.route("/api/publish/wechat/drafts")
def wechat_drafts():
    """获取微信草稿列表"""
    result = wcp.get_draft_list()
    return jsonify({"status": "ok" if result.get("item") else "partial", "drafts": result})


# ===== v5.7.0 全自动化发布 =====

@app.route("/api/auto-publish/start", methods=["POST"])
def auto_publish_start():
    """一键启动全自动化流水线：挖词 → 生成 → 发布"""
    data = request.get_json() or {}
    platforms = data.get("platforms", ["douyin"])
    seed_keywords = data.get("seed_keywords")
    auto_pub = data.get("auto_publish", True)
    max_count = data.get("max_count", 3)

    if not platforms:
        return jsonify({"status": "error", "message": "请指定目标平台"})

    log.info(f"AutoPublish start: platforms={platforms}, seeds={seed_keywords}, auto={auto_pub}")
    job = ppl.start(
        platforms=platforms,
        seed_keywords=seed_keywords,
        auto_publish=auto_pub,
        max_count=max_count
    )
    return jsonify({"status": "ok", "job": job})


@app.route("/api/auto-publish/status/<job_id>")
def auto_publish_status(job_id):
    """查询流水线进度"""
    job = ppl.get_status(job_id)
    if not job:
        return jsonify({"status": "error", "message": "任务不存在"}), 404
    return jsonify({"status": "ok", "job": job})


@app.route("/api/auto-publish/jobs")
def auto_publish_jobs():
    """流水线历史记录"""
    limit = request.args.get("limit", 20, type=int)
    jobs = ppl.get_all_jobs(limit)
    return jsonify({"status": "ok", "jobs": jobs, "stats": ppl.get_stats()})


@app.route("/api/auto-publish/authorize", methods=["POST"])
def auto_publish_authorize():
    """
    授权登录 — 输入账号密码，系统自动登录并保存会话
    
    请求体:
    {
        "platform": "weibo",
        "username": "your_account",
        "password": "your_password"
    }
    
    扫码平台(抖音/小红书)留空账号密码即可, 系统会返回二维码图片
    """
    data = request.get_json() or {}
    platform = data.get("platform", "")
    username = data.get("username", "")
    password = data.get("password", "")
    
    if not platform:
        return jsonify({"status": "error", "message": "请指定平台"})
    
    log.info(f"Auth request: platform={platform}, user={username[:3] if username else '(QR)'}***")
    result = apb.auto_login(platform, username, password)
    
    return jsonify({
        "status": "ok" if result.get("success") else "error",
        "result": result
    })


@app.route("/api/auto-publish/import-session", methods=["POST"])
def auto_publish_import():
    """备用: 导入浏览器Cookie JSON"""
    data = request.get_json() or {}
    platform = data.get("platform", "")
    cookies_data = data.get("cookies", "")
    
    if not platform or not cookies_data:
        return jsonify({"status": "error", "message": "平台和cookies不能为空"})
    
    log.info(f"Session import: platform={platform}")
    result = apb.import_session(platform, cookies_data)
    return jsonify({
        "status": "ok" if result.get("success") else "error",
        "result": result
    })


@app.route("/api/auto-publish/sessions")
def auto_publish_sessions():
    """查看各平台登录会话状态"""
    sessions = apb.get_all_sessions()
    return jsonify({"status": "ok", "sessions": sessions})


@app.route("/api/auto-publish/check-session/<platform>")
def auto_publish_check_session(platform):
    """检测指定平台登录状态"""
    result = apb.check_session(platform)
    return jsonify({"status": "ok", "session": result})


@app.route("/api/auto-publish/publish-one", methods=["POST"])
def auto_publish_one():
    """手动触发单条内容自动发布到指定平台"""
    data = request.get_json() or {}
    platform = data.get("platform", "")
    title = data.get("title", "")
    content = data.get("content", "")
    media_path = data.get("media_path")
    dry_run = data.get("dry_run", False)

    if not platform or not content:
        return jsonify({"status": "error", "message": "平台和内容不能为空"})

    result = apb.publish(platform, title, content, media_path, dry_run)

    # 记录到已发布
    if result.get("success") and not dry_run:
        pse.add(str(int(datetime.now().timestamp())), platform, result)

    return jsonify({
        "status": "ok" if result.get("success") else "error",
        "result": result
    })


@app.route("/api/auto-publish/batch", methods=["POST"])
def auto_publish_batch():
    """批量发布同一内容到多平台"""
    data = request.get_json() or {}
    platforms = data.get("platforms", [])
    title = data.get("title", "")
    content = data.get("content", "")
    media_path = data.get("media_path")
    dry_run = data.get("dry_run", False)

    if not platforms or not content:
        return jsonify({"status": "error", "message": "平台和内容不能为空"})

    results = apb.batch_publish(platforms, title, content, media_path, dry_run)

    # 批量记录
    for r in results:
        if r.get("success") and not dry_run:
            pse.add(str(int(datetime.now().timestamp())), r.get("platform", "unknown"), r)

    succeed = len([r for r in results if r.get("success")])
    return jsonify({
        "status": "ok", "total": len(results), "succeed": succeed,
        "results": results
    })


# ===== 微信公众号（公开访问，不受认证保护）=====

@app.route("/api/wechat/message", methods=["GET", "POST"])
def wechat_message():
    return wechat_route()

@app.route("/wechat/message", methods=["GET", "POST"])
def wechat_message_short():
    return wechat_route()

# ===== 错误处理 =====

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "not found", "status": "error"}), 404

@app.errorhandler(500)
def server_error(e):
    log.error(f"Server error: {e}")
    return jsonify({"error": "internal server error", "status": "error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
