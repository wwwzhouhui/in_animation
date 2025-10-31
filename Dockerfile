# 使用官方 Python 3.11 基础镜像
FROM python:3.11-slim

# 环境变量配置
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    TZ=Asia/Shanghai

# 设置工作目录
WORKDIR /app

# 安装系统依赖（包含 FFmpeg、中文字体和 Playwright 运行依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        fonts-noto-cjk \
        libgtk-4-1 \
        libevent-2.1-7 \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        flite \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt ./

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 运行依赖并拉取 Chromium 浏览器
RUN playwright install-deps chromium \
    && playwright install chromium

# 复制应用代码
COPY . .

# 创建必要的工作目录
RUN mkdir -p logs output .recordings .generated_html static templates scripts

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000').read()" || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
