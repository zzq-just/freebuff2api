# ========== 构建阶段：仅用来装依赖、编译，最后丢弃 ==========
FROM python:3.11-slim AS builder

# 仅构建需要的编译工具
RUN apt-get update && apt-get install -y --no-install-recommends gcc git \
    && rm -rf /var/lib/apt/lists/*

# 导入uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 分层优化：先只复制依赖文件，缓存锁定
COPY pyproject.toml uv.lock ./

# 预创建虚拟环境，安装所有依赖（只生成文件，不带缓存）
RUN uv sync --frozen --no-dev --no-cache

# 再拷贝业务代码
COPY . .
RUN cp .env.example .env

# ========== 运行阶段：无gcc/git、无构建缓存、干净环境 ==========
FROM python:3.11-slim AS final

# 只拷贝运行必需的 uv 工具
COPY --from=builder /bin/uv /bin/uvx /bin/
WORKDIR /app

# 从构建层拷贝：虚拟环境 + 源码 + .env
COPY --from=builder /app ./

# 清理系统无用缓存
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# 启动，和原来逻辑完全不变
CMD ["uv", "run", "freebuff2api"]
