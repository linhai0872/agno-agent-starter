# AgentOS Dockerfile
# 多阶段构建，优化镜像体积

# ============== 构建阶段 ==============
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 安装构建依赖（部分包需要编译）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖到虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============== 运行阶段 ==============
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 仅安装运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制配置文件
COPY configuration.yaml .

# 复制应用代码
COPY app/ ./app/

# 暴露端口 (AgentOS 默认 7777)
EXPOSE 7777

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:7777/health || exit 1

# 启动命令
CMD ["python", "-m", "app.main"]
