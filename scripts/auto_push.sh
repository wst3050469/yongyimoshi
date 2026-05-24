#!/bin/bash
SITE="https://ai.jinmojianshe.com"
TOKEN="Wv8PCYReXqOVNXYg"
BAIDU_API="http://data.zz.baidu.com/urls?site=${SITE}&token=${TOKEN}"
SITEMAP_URL="${SITE}/platform/sitemap.xml"

echo "[$(date)] 开始推送..."
URLS=$(curl -s -k "$SITEMAP_URL" 2>/dev/null | grep -oP '(?<=<loc>).*?(?=</loc>)')
COUNT=$(echo "$URLS" | wc -l)
echo "发现 $COUNT 个 URL"

echo "$URLS" | curl -s -H 'Content-Type:text/plain' --data-binary @- "$BAIDU_API"
echo ""
echo "[$(date)] 推送完成"
