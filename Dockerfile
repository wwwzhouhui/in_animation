# 使用官方 Python 3.11 基础镜像
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 设置工作目录
WORKDIR /app

# 安装系统依赖（包含 FFmpeg 与中文字体，便于视频导出）
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

# 安装 Python 依赖并预装 Playwright 浏览器
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 运行依赖并拉取 Chromium 浏览器
RUN playwright install-deps chromium \
    && playwright install chromium

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
