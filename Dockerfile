# ============================================
# 永颐无机磨石 · 施工管理平台
# Dockerfile - 多阶段构建
# ============================================

# ---- 构建阶段 ----
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- 运行阶段 ----
FROM python:3.12-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已安装的包
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p data/photos data/backups logs

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen("http://localhost:5000/api/health")

# 启动
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
