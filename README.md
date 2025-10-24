# Instructional Animation - AI Educational Animation Generator

<div align="center">

**AI-Powered Educational Animation Generator**

English documentation. For Chinese, see `README_CN.md`.

</div>

---

### 📖 Project Overview

Instructional Animation is an AI-powered educational animation generator that automatically creates visually stunning and interactive HTML5 animations based on educational topics. It supports exporting to MP4 videos and GIF formats.

### ✨ Key Features

- **🤖 AI-Powered**: Automatically generates educational animations using large language models
- **🎨 Beautiful Visuals**: 2K resolution (1280×720), light theme, professional visual effects
- **🌐 Bilingual Support**: Chinese/English UI and subtitles
- **🎬 One-Click Export**: Export to HTML, MP4 video, or GIF format
- **⚡ Streaming Generation**: Real-time SSE streaming output
- **🎯 Multi-Turn Dialogue**: Iterative optimization through conversation
- **🐳 Containerized Deployment**: Docker and Docker Compose support

### 🎯 Use Cases

- **Education**: Explain complex concepts (math, physics, chemistry, biology)
- **Knowledge Sharing**: Create educational videos and tutorials
- **Presentations**: Generate dynamic effects for PowerPoint
- **Online Courses**: Quickly produce course materials

### 🛠️ Tech Stack

#### Backend
- **FastAPI** - Modern high-performance web framework
- **OpenAI API** - OpenAI-compatible LLM interface
- **Playwright** - Browser automation and recording
- **FFmpeg** - Video transcoding
- **Python 3.11** - Core language

#### Frontend
- **HTML5 / CSS3 / JavaScript** - Native web stack
- **GSAP** - High-performance animation library
- **Jinja2** - Template engine

### 📋 Requirements

- **Python**: 3.11+
- **FFmpeg**: For video export
- **Chromium**: Playwright browser engine
- **OS**: Linux / macOS / Windows (WSL2)

### 🚀 Quick Start

#### Method 1: Docker Deployment (Recommended)

1. **Configure API Key**

Create `credentials.json`:

```json
{
  "API_KEY": "your-api-key-here",
  "BASE_URL": "https://api.example.com/v1",
  "MODEL": "your-model-name"
}
```

2. **Start Service**

```bash
docker-compose up -d
```

3. **Access Application**

Open browser: `http://localhost:8000`

#### 方法 1.2：从镜像仓库拉取部署（Docker Hub）

我们提供官方镜像，便于直接从镜像仓库获取并部署：`hub.docker.com/r/wwwzhouhui569/in_animation`

1. 拉取镜像

```bash
docker pull wwwzhouhui569/in_animation:latest
```

2. 准备配置文件（在当前目录创建 `credentials.json`）

```json
{
  "API_KEY": "你的API密钥",
  "BASE_URL": "https://api.example.com/v1",
  "MODEL": "你的模型名称"
}
```

3. 运行容器（将当前目录挂载到容器内）

```bash
docker run -d \
  --name in_animation \
  -p 8000:8000 \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  -v $(pwd)/output:/app/output \
  -e TZ=Asia/Shanghai \
  wwwzhouhui569/in_animation:latest
```

4. 访问应用

打开浏览器访问：`http://localhost:8000`

可选：如需自定义 `ffmpeg` 路径或时区，可通过环境变量传入，例如：

```bash
docker run -d \
  -p 8000:8000 \
  -e FFMPEG_PATH=/usr/bin/ffmpeg \
  -e TZ=Asia/Shanghai \
  wwwzhouhui569/in_animation:latest
```

#### Method 2: Local Development

1. **Clone Repository**

```bash
git clone https://github.com/wwwzhouhui/in_animation.git
cd in_animation
```

2. **Create Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

4. **Install FFmpeg**

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download FFmpeg and add to PATH
```

5. **Configure API Key**

Create `credentials.json` (see above)

6. **Start Service**

```bash
python app.py
# or
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

7. **Access Application**

Open browser: `http://localhost:8000`

### 📖 Usage Guide

#### 1. Generate Animation

1. Enter educational topic (e.g., "Pythagorean Theorem", "Light Refraction")
2. Click send or press Enter
3. Wait for AI to generate animation (10-60 seconds)
4. Preview the generated animation

#### 2. Iterative Optimization

Enter modification requests in the chat, such as:
- "Add more examples"
- "Slow down the animation"
- "Add explanation of the proof process"

#### 3. Export Animation

- **Open in New Window**: Preview in standalone window
- **Save as HTML**: Download complete HTML file
- **Export as Video**: Generate MP4 video (requires FFmpeg)

### 🔌 API Reference

#### POST /generate

Generate educational animation (SSE streaming response)

**Request Body**:
```json
{
  "topic": "Educational topic",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

#### POST /record

Record page and export video

**Request Body**:
```json
{
  "html_text": "<html>...</html>",
  "width": 1280,
  "height": 720,
  "fps": 24,
  "mp4": true,
  "end_event": "recording:finished",
  "end_timeout": 180000
}
```

### 🐛 Troubleshooting

#### API Key Error
**Solution**: Check `credentials.json` exists and contains valid API key

#### FFmpeg Not Found
**Solution**: Install FFmpeg or set `FFMPEG_PATH` environment variable

#### Playwright Browser Not Installed
**Solution**: Run `playwright install chromium`

### 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Submit Pull Request

### 📄 License

This project is licensed under the [MIT License](LICENSE).

### 🙏 Acknowledgments

- [fogsight](https://github.com/fogsightai/fogsight) - fogsight is an animation engine agent driven by a large language model (LLM).
- [FastAPI](https://fastapi.tiangolo.com/)
- [Playwright](https://playwright.dev/)
- [FFmpeg](https://ffmpeg.org/)
- [GSAP](https://greensock.com/gsap/)

---

<div align="center">
**Made with ❤️ for Education**

</div>

### Contact Us

📬 Contact:

- Email: [75271002@qq.com](mailto:75271002@qq.com)

🔗 Social Media:

- GitHub: [wwwzhouhui](https://github.com/wwwzhouhui)
- WeChat Official Account: [wwzhouhui](https://mp.weixin.qq.com/cgi-bin/settingpage?t=setting/index&action=index&token=1416320806&lang=zh_CN)
- Bilibili: [My Bilibili page](https://space.bilibili.com/1527002698)

WeChat:

![WeChat QR code](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20250906175827828.png)

<div align="center">

If this project is helpful to you, please give us a ⭐ Star!
