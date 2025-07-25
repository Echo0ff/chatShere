# ChatSphere 后端 Dockerfile
# 支持多阶段构建和多环境部署

# 基础镜像 - 使用官方Python镜像
FROM python:3.11-slim AS base

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 配置更快的APT源（使用阿里云镜像）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 一次性安装所有系统依赖，减少层数和时间
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# 安装 uv (更快的 Python 包管理器) - 使用官方安装脚本更快
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.bashrc && \
    /root/.local/bin/uv --version
ENV PATH="/root/.local/bin:$PATH"

# 复制依赖文件和 README（构建包时需要）
COPY pyproject.toml uv.lock README.md ./

# 开发环境阶段
FROM base AS development

# 安装开发依赖（使用缓存优化）
RUN --mount=type=cache,target=/root/.cache/uv \
    /root/.local/bin/uv sync --dev

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 8000

# 开发环境启动命令
CMD ["/root/.local/bin/uv", "run", "uvicorn", "src.chatSphere.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 测试环境阶段
FROM base AS testing

# 安装所有依赖（包括测试依赖）- 使用缓存
RUN --mount=type=cache,target=/root/.cache/uv \
    /root/.local/bin/uv sync --dev

# 复制源代码
COPY . .

# 运行测试
RUN /root/.local/bin/uv run pytest tests/ -v

# 暴露端口
EXPOSE 8000

# 测试环境启动命令
CMD ["/root/.local/bin/uv", "run", "uvicorn", "src.chatSphere.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 生产环境阶段
FROM base AS production

# 只安装生产依赖 - 使用缓存
RUN --mount=type=cache,target=/root/.cache/uv \
    /root/.local/bin/uv sync --no-dev

# 创建非root用户并设置 home 目录
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser

# 复制源代码
COPY . .

# 创建必要的目录并设置权限
RUN mkdir -p /app/logs /app/uploads /home/appuser/.cache && \
    chown -R appuser:appuser /app /home/appuser

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 生产环境启动命令
CMD ["/root/.local/bin/uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
