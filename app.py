#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 AI营销系统 Flask App - v5.5.0 (密码保护)
注意：Nginx proxy_pass http://127.0.0.1:5050/ 会剥离 /marketing/ 前缀
Flask 实际收到的路径是 /, /api/*, /wechat/* 等"""
import sys, os, json, logging, uuid
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from flask import Flask, jsonify, request, render_template, session
from docs.marketing_system import KeywordEngine, CompetitorAnalyzer, MarketingReport
from docs.video_generator import VideoGenerator
from docs.content_store import ContentStore
from docs.wechat_handler import wechat_handler as wechat_route

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
    return jsonify({"status":"ok","service":"yongyi-marketing","version":"5.5.0","time":datetime.now().isoformat()})

# ===== 仪表盘统计 =====

@app.route("/api/stats")
def stats():
    kws = ke.get_kws()
    kw_count = sum(len(v) for v in kws.values())
    content_stats = cs.get_stats()
    comps = ca.get_comps()
    video_tasks = vg.get_all_tasks()
    return jsonify({
        "keywords": kw_count,
        "contents": content_stats["total"],
        "competitors": len(comps),
        "reports": content_stats["daily"],
        "videos": len(video_tasks)
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
