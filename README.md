# Instructional Animation - AI Educational Animation Generator


**AI-Powered Educational Animation Generator**

[中文](./README_CN.md) | English

[Project source code address](https://github.com/wwwzhouhui/in_animation):

---

### 📖 Project Overview

Instructional Animation is an AI-powered educational animation generator that automatically creates visually stunning and interactive HTML5 animations based on educational topics. It supports exporting to MP4 videos and GIF formats.

### 🎬 Video Demo

Watch a quick demonstration of the animation generator in action:

<div align="center">
<video src="https://github.com/wwwzhouhui/in_animation/raw/main/examples/演示.mp4" controls="controls" width="100%" style="max-width: 800px;">
  Your browser does not support the video tag.
</video>

**GIF Preview**

![Demo Animation](./examples/demo.gif)

**Online Demo**: http://115.190.165.156:8000/

</div>

> 💡 **Viewing Tips**:
> - Click the video above to play directly on GitHub
> - Or download the [MP4 file](./examples/演示.mp4) for offline viewing
> - GIF preview loads automatically but may have lower quality

### ✨ Key Features

- **🤖 AI-Powered**: Automatically generates educational animations using large language models
- **🎨 Beautiful Visuals**: 2K resolution (1280×720), light theme, professional visual effects
- **🌐 Bilingual Support**: Chinese/English UI and subtitles
- **🎬 One-Click Export**: Export to HTML, MP4 video, or GIF format
- **⚡ Streaming Generation**: Real-time SSE streaming output
- **🎯 Multi-Turn Dialogue**: Iterative optimization through conversation
- **🐳 Containerized Deployment**: Docker and Docker Compose support
- **🔧 Multi-Model Support**: Support for Anthropic Claude, OpenAI-compatible LLMs, DeepSeek, and more
- **✅ Connection Testing**: Built-in API connection validation with visual feedback
- **📦 Dynamic Configuration**: Real-time API configuration via settings modal

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

Copy the example configuration file:
```bash
cp .env.example .env
```

Then edit `.env` and fill in your actual values:

```env
API_KEY=your-api-key-here
BASE_URL=https://api.example.com/v1
MODEL=your-model-name
```

2. **Start Service**

```bash
docker-compose up -d
```

3. **Access Application**

Open browser: `http://localhost:8000`

#### Method 1.2: Deploy from Image Registry (Docker Hub)

We provide an official image for easy deployment from Docker Hub: `hub.docker.com/r/wwwzhouhui569/in_animation`

1. **Pull the image**

```bash
docker pull wwwzhouhui569/in_animation:latest
```

2. **Prepare configuration file** (create `.env` in the current directory)

```env
API_KEY=your-api-key
BASE_URL=https://api.example.com/v1
MODEL=your-model-name
```

3. **Run the container** (recommended with volume mounts)

```bash
docker run -d \
  --name in_animation \
  -p 8000:8000 \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/logs:/app/logs \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  wwwzhouhui569/in_animation:latest
```

**Volume Mount Explanation**:
- `-v $(pwd)/.env:/app/.env:ro` - Mount configuration file (read-only)
- `-v $(pwd)/output:/app/output` - Mount output directory (videos and GIF files)
- `-v $(pwd)/logs:/app/logs` - Mount logs directory (optional)
- `-e TZ=Asia/Shanghai` - Set timezone to Shanghai
- `--restart unless-stopped` - Auto-restart container on failure

4. **Access the application**

Open the browser: `http://localhost:8000`

5. **View logs**

```bash
# View container runtime logs
docker logs -f in_animation

# View application logs (if logs directory is mounted)
python view_logs.py
```

6. **Stop and manage container**

```bash
# Stop container
docker stop in_animation

# Start container
docker start in_animation

# Restart container
docker restart in_animation

# Remove container
docker rm -f in_animation
```

**Advanced Configuration**:

To customize more environment variables, use the following parameters:

```bash
docker run -d \
  --name in_animation \
  -p 8000:8000 \
  -v $(pwd)/.env:/app/.env:ro \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/logs:/app/logs \
  -e TZ=Asia/Shanghai \
  -e FFMPEG_PATH=/usr/bin/ffmpeg \
  -e API_KEY=your-api-key \
  -e BASE_URL=https://api.example.com/v1 \
  -e MODEL=your-model-name \
  --restart unless-stopped \
  wwwzhouhui569/in_animation:latest
```

**Environment Variable Priority**:
1. `-e` environment variables (highest priority)
2. `.env` file
3. `credentials.json` (deprecated, backward compatible)

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

Copy the example file and configure:
```bash
cp .env.example .env
```

Edit `.env` and fill in your API key, or use the web interface settings modal (⚙️) to configure at runtime

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
- **Export as GIF**: Generate animated GIF (requires FFmpeg)

#### 4. Settings & Configuration

Click the settings button (⚙️) in the top-left corner to open the settings modal:

**Configuration Options**:
- **API Key**: Enter your LLM API key (required)
- **Base URL**: API service address (optional, leave blank for default)
- **Model Name**: Select model from dropdown list (required)

**Test Connection**:
- Click "Test Connection" button to validate API configuration
- System displays visual feedback with success✓ or failure✗ icons
- Success shows: "Test successful! Model 'xxx' is accessible"
- Failure shows specific error messages (invalid API key, model not found, etc.)

**Save Settings**:
- After validation, click "Save Settings"
- Configuration is automatically saved to `.env` file
- Takes effect immediately, no server restart required

#### 5. Topic Suggestions

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
  "gif": true,
  "end_event": "recording:finished",
  "end_timeout": 180000,
  "gif_fps": 10,
  "gif_width": 720,
  "gif_dither": "sierra2_4a"
}
```

#### POST /config

Get or update API configuration

**Get Configuration (GET)**:
```bash
curl http://localhost:7860/config
```

**Update Configuration (POST)**:
```bash
curl -X POST http://localhost:7860/config \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-api-key",
    "base_url": "https://api.example.com/v1",
    "model": "your-model"
  }'
```

#### POST /test-config

Test API connection

**Request Body**:
```json
{
  "api_key": "your-api-key",
  "base_url": "https://api.example.com/v1",
  "model": "your-model"
}
```

**Response (Success)**:
```json
{
  "ok": true,
  "message": "Test successful! Model 'your-model' is accessible",
  "model": "your-model"
}
```

**Response (Failure)**:
```json
{
  "ok": false,
  "error": "Test failed: Invalid API key"
}
```

### 🐛 Troubleshooting

#### API Key Error
**Solution**:
- Check `.env` file exists and contains valid API key
- Or use the settings button (⚙️) in the top-left corner to configure via the web interface
- Click "Test Connection" to validate your API key before saving

#### FFmpeg Not Found
**Solution**: Install FFmpeg or set `FFMPEG_PATH` environment variable

#### Playwright Browser Not Installed
**Solution**: Run `playwright install chromium`

#### Model Not Supported
**Solution**: Check the settings modal for supported models including:
- ZhipuAI/GLM-4.6
- minimax-m2
- deepseek-ai/DeepSeek-V3.2-Exp
- claude-haiku-4-5-20251001
- Qwen/Qwen3-Coder-480B-A35B-Instruct

#### Configuration Not Taking Effect
**Solution**:
- Configuration changes are saved to `.env` file and take effect immediately
- No server restart required
- Use the settings modal to update configuration at runtime

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



### 📝 Changelog

#### v2.1.0 (2025-10-30)

**New Features**:
- ✨ Added Settings Modal for web-based API configuration
- ✨ Added Connection Testing with real-time API validation
- ✨ Added Multi-Model Support: minimax-m2, DeepSeek-V3.2-Exp, Claude Haiku, Qwen3-Coder
- ✨ Added GIF Export functionality for animated GIF format
- 🎨 Enhanced Visual Feedback: Connection test shows ✓/✗ icons with animations
- 📦 Added `.env` file support with hot-reload, no server restart needed
- 📄 Added `.env.example` configuration template file

**Improvements**:
- 🔄 Enhanced recording with more parameters (gif_fps, gif_width, gif_dither)
- 🎯 Better error handling and user feedback
- 📱 Optimized frontend user experience

**Configuration Changes**:
- 🆕 Prefer `.env` file over `credentials.json`
- 🔄 Configuration priority: Environment variables > `.env` > `credentials.json` (backward compatible)
- ✅ Recommend using `.env` or web interface settings, both support hot-reload

**API Changes**:
- New `/config` endpoint: Get and update configuration
- New `/test-config` endpoint: Test API connection
- Enhanced `/record` endpoint: Support GIF export parameters

#### v2.0.0

- 🤖 Initial release
- 🎬 AI-powered educational animation generation
- 📹 MP4 video export support
- 🌍 Bilingual support

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
