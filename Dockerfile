FROM python:3.11-slim

# 安装系统编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends gcc git && rm -rf /var/lib/apt/lists/*

# 引入uv二进制
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 复制项目所有文件
COPY . .

# 1. 复制env模板（容器内构建阶段生成.env，避免程序启动缺配置）
RUN cp .env.example .env

# 2. uv同步全部依赖（对应文档 uv sync）
RUN uv sync --frozen

# 启动命令匹配文档：uv run freebuff2api
CMD ["uv", "run", "freebuff2api"]
