#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微信公众号消息处理模块 - 安全模式"""
import hashlib, time, json, xml.etree.ElementTree as ET
from flask import request, make_response

TOKEN = "1xz1SEubZIDxmo16LG1l"
ENCODING_AES_KEY = "hRJeBerJceA6gU5wtfeiesWYgEfOGZoJt7Dnb5aiTG2"
APP_ID = "wxe6d7e3ee6c4eb2d6"

def verify_signature(signature, timestamp, nonce):
    """验证微信服务器签名"""
    arr = sorted([TOKEN, timestamp, nonce])
    return hashlib.sha1(''.join(arr).encode()).hexdigest() == signature

def parse_xml(xml_str):
    """解析微信XML消息"""
    root = ET.fromstring(xml_str)
    msg = {}
    for child in root:
        msg[child.tag] = child.text
    return msg

def build_text_xml(to_user, from_user, content, timestamp=None):
    """构建文本回复XML"""
    if timestamp is None:
        timestamp = str(int(time.time()))
    return f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""

def build_article_xml(to_user, from_user, articles, timestamp=None):
    """构建图文回复XML"""
    if timestamp is None:
        timestamp = str(int(time.time()))
    items = ''
    for a in articles:
        items += f"""<item>
<Title><![CDATA[{a.get('title','')}]]></Title>
<Description><![CDATA[{a.get('description','')}]]></Description>
<PicUrl><![CDATA[{a.get('picurl','')}]]></PicUrl>
<Url><![CDATA[{a.get('url','')}]]></Url>
</item>"""
    return f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[news]]></MsgType>
<ArticleCount>{len(articles)}</ArticleCount>
<Articles>{items}</Articles>
</xml>"""

def handle_message(msg):
    """处理用户消息"""
    msg_type = msg.get('MsgType', '')
    content = msg.get('Content', '')
    from_user = msg.get('FromUserName', '')
    to_user = msg.get('ToUserName', '')
    
    if msg_type == 'text':
        # 关键词回复
        if any(kw in content for kw in ['磨石', '地坪', '价格', '施工']):
            reply = ("您好！欢迎咨询永颐金磨石！\n\n"
                     "🏢 专注金磨石15年，服务500+项目\n\n"
                     "📞 咨询电话：16624603959\n"
                     "🌐 了解更多：https://ai.jinmojianshe.com/marketing/\n\n"
                     "回复关键词了解更多：\n"
                     "【产品】查看产品介绍\n"
                     "【案例】查看工程案例\n"
                     "【联系】获取联系方式")
            return build_text_xml(from_user, to_user, reply)
        elif '产品' in content:
            reply = ("永颐金磨石产品系列：\n\n"
                     "1️⃣ 无机磨石 - 强度高、耐磨、防火A级\n"
                     "2️⃣ 环氧磨石 - 色彩丰富、无缝一体\n"
                     "3️⃣ 金磨石 - 高端定制地面系统\n\n"
                     "更多信息请访问：https://ai.jinmojianshe.com/marketing/")
            return build_text_xml(from_user, to_user, reply)
        elif '案例' in content:
            reply = ("永颐金磨石部分案例：\n\n"
                     "🏥 医院项目\n"
                     "🏫 学校项目\n"
                     "🏬 商场项目\n"
                     "🏢 办公项目\n\n"
                     "回复【联系】获取详细案例资料")
            return build_text_xml(from_user, to_user, reply)
        elif '联系' in content or '电话' in content:
            reply = ("📞 联系人：辉哥\n"
                     "📱 电话：16624603959\n"
                     "🌐 官网：www.jinmojianshe.com\n"
                     "📍 地址：永颐金磨石")
            return build_text_xml(from_user, to_user, reply)
        else:
            reply = ("感谢您关注永颐金磨石！\n\n"
                     "我们专注金磨石地面系统15年，\n"
                     "为您提供高品质地面解决方案。\n\n"
                     "回复关键词：\n"
                     "【产品】产品介绍\n"
                     "【案例】工程案例\n"
                     "【联系】联系方式\n"
                     "【价格】获取报价")
            return build_text_xml(from_user, to_user, reply)
    
    elif msg_type == 'event':
        event = msg.get('Event', '')
        if event == 'subscribe':
            reply = ("欢迎关注永颐金磨石！🎉\n\n"
                     "我们致力于为您提供最优质的金磨石地面系统。\n\n"
                     "15年专注 · 500+项目 · 匠心品质\n\n"
                     "回复关键词了解更多：\n"
                     "【产品】产品介绍\n"
                     "【案例】工程案例\n"
                     "【联系】联系方式")
            return build_text_xml(from_user, to_user, reply)
        elif event == 'unsubscribe':
            return 'success'
    
    return 'success'


def wechat_handler():
    """微信消息入口 - Flask路由函数"""
    if request.method == 'GET':
        # 服务器URL验证
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')
        
        if verify_signature(signature, timestamp, nonce):
            return echostr
        return 'Invalid signature', 403
    
    elif request.method == 'POST':
        # 处理消息
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        
        if not verify_signature(signature, timestamp, nonce):
            return 'Invalid signature', 403
        
        xml_str = request.data.decode('utf-8')
        msg = parse_xml(xml_str)
        reply = handle_message(msg)
        
        resp = make_response(reply)
        resp.content_type = 'application/xml'
        return resp
