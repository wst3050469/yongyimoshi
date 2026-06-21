#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 AI营销系统 Flask App - v5.1.0 (集成豆包视频生成)"""
import sys, os, json, logging
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))
from flask import Flask, jsonify, request, render_template
from docs.marketing_system import KeywordEngine, CompetitorAnalyzer, MarketingReport
from docs.video_generator import VideoGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

app = Flask(__name__)

@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return resp

# ===== 核心引擎实例 =====
ke = KeywordEngine()
ca = CompetitorAnalyzer()
vg = VideoGenerator()

# ===== 基础路由 =====

@app.route("/")
def index():
    return render_template("marketing_dashboard.html")

@app.route("/health")
def health():
    return jsonify({"status":"ok","service":"yongyi-marketing","version":"5.1.0","time":datetime.now().isoformat()})

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
    return jsonify({
        "video": ke.gen_video(kw, grp),
        "article": ke.gen_article(kw, grp),
        "xhs": ke.gen_xhs(kw, grp)
    })

# ===== 竞品管理 =====

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
    summary_info = MarketingReport.summary(len(kws), 28, len(comps))
    return jsonify({"report": summary_info, "summary": summary_info})

# ===== 豆包视频生成 =====

@app.route("/api/video/create", methods=["POST"])
def video_create():
    """创建视频生成任务"""
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    keyword = data.get("keyword", "")
    group = data.get("group", "产品词")
    
    # 如果没有提供prompt，自动生成
    if not prompt and keyword:
        prompt = vg.generate_prompt(keyword, group)
    if not prompt:
        return jsonify({"status": "error", "message": "请输入prompt或关键词"})
    
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
    """查询视频任务状态"""
    result = vg.query_task(task_id)
    return jsonify(result)

@app.route("/api/video/tasks")
def video_tasks():
    """获取所有视频任务列表"""
    return jsonify({"tasks": vg.get_all_tasks()})

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
