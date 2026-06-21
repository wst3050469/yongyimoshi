#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""永颐金磨石 AI营销系统 Flask App - v5.0.0"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from flask import Flask, jsonify, request, render_template
from docs.marketing_system import KeywordEngine, CompetitorAnalyzer, MarketingReport

app = Flask(__name__)
ke = KeywordEngine()
ca = CompetitorAnalyzer()

@app.route("/")
def index():
    return render_template("marketing_dashboard.html")

@app.route("/api/keywords", methods=["GET", "POST"])
def keywords():
    if request.method == "POST":
        data = request.get_json() or {}
        action = data.get("action", "")
        keyword = data.get("keyword", "")
        if action == "add" and keyword:
            ke.add_keyword(keyword)
            return jsonify({"status": "ok", "keyword": keyword})
        return jsonify({"status": "error", "message": "invalid"})
    return jsonify({"keywords": ke.get_kws()})

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    kw = data.get("keyword", "") or "磨石"
    grp = data.get("group", "产品词")
    return jsonify({
        "video": ke.gen_video(kw, grp),
        "article": ke.gen_article(kw, grp)
    })

@app.route("/api/competitors", methods=["GET", "POST"])
def competitors():
    if request.method == "POST":
        data = request.get_json() or {}
        url = data.get("url", "")
        if url:
            ca.add_comp(url)
            return jsonify({"status": "ok", "url": url})
        return jsonify({"status": "error"})
    return jsonify({"competitors": ca.get_comps()})

@app.route("/api/analysis")
def analysis():
    comps = ca.get_comps()
    plan = ca.surpass(comps)
    return jsonify({"analysis": plan, "report": plan})

@app.route("/api/report", methods=["POST"])
def report():
    data = request.get_json() or {}
    kws = ke.get_kws()
    comps = ca.get_comps()
    summary_info = MarketingReport.summary(len(kws), 28, len(comps))
    return jsonify({"report": summary_info, "summary": summary_info})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
