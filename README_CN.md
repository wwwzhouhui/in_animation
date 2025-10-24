# Instructional Animation - AI 教学动画生成器


中文 ｜ [English](./README.md)

[项目源码地址](https://github.com/wwwzhouhui/in_animation)：

---

### 📖 项目简介

Instructional Animation 是一个基于大语言模型的教学动画生成工具，能够根据用户输入的知识点主题，自动生成视觉精美、交互流畅的 HTML5 动画页面，并支持导出为 MP4 视频和 GIF 格式。

### ✨ 核心特性

- **🤖 AI 驱动生成**：基于大语言模型自动生成符合教学需求的动画内容
- **🎨 视觉精美**：2K 分辨率（1280×720），浅色主题配色方案，专业视觉效果
- **🌐 双语支持**：中英文界面切换，双语字幕显示
- **🎬 一键导出**：支持导出为 HTML、MP4 视频、GIF 格式
- **⚡ 流式生成**：Server-Sent Events (SSE) 实时流式输出生成过程
- **🎯 多轮对话**：支持对生成结果进行迭代优化和调整
- **🐳 容器化部署**：Docker 一键部署，支持 Docker Compose

### 🎯 应用场景

- **教育教学**：为学生讲解复杂概念（数学、物理、化学、生物等）
- **知识分享**：制作科普视频和教程动画
- **演示文稿**：生成动态演示效果，提升 PPT 表现力
- **在线课程**：快速制作课程配套动画素材

### 🛠️ 技术栈

#### 后端
- **FastAPI** - 现代高性能 Web 框架
- **OpenAI API** - 兼容 OpenAI 接口的大语言模型
- **Playwright** - 浏览器自动化与页面录制
- **FFmpeg** - 视频转码与处理
- **Python 3.11** - 核心开发语言

#### 前端
- **HTML5 / CSS3 / JavaScript** - 原生 Web 技术栈
- **GSAP** - 高性能动画库
- **Jinja2** - 模板引擎

### 📋 系统要求

- **Python**: 3.11+
- **FFmpeg**: 用于视频导出功能
- **Chromium**: Playwright 浏览器引擎
- **操作系统**: Linux / macOS / Windows (WSL2)

### 🚀 快速开始

#### 方式一：Docker 部署（推荐）

1. **配置 API 密钥**

创建 `credentials.json` 文件：

```json
{
  "API_KEY": "your-api-key-here",
  "BASE_URL": "https://api.example.com/v1",
  "MODEL": "your-model-name"
}
```

2. **启动服务**

```bash
docker-compose up -d
```

3. **访问应用**

打开浏览器访问：`http://localhost:8000`

#### 方式一.二：从镜像仓库拉取部署（Docker Hub）

我们提供了官方镜像，便于用户直接从镜像仓库获取并部署：`hub.docker.com/r/wwwzhouhui569/in_animation`

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

#### 方式二：本地开发部署

1. **克隆仓库**

```bash
git clone https://github.com/wwwzhouhui/in_animation.git
cd in_animation
```

2. **创建虚拟环境**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

3. **安装依赖**

```bash
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
```

4. **安装 FFmpeg**

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 下载 FFmpeg 并添加到 PATH
```

5. **配置 API 密钥**

创建 `credentials.json`（参考上方配置）

6. **启动服务**

```bash
python app.py
# 或
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

7. **访问应用**

打开浏览器访问：`http://localhost:8000`

### 📁 项目结构

```
in_animation/
├── app.py                  # FastAPI 主应用
├── requirements.txt        # Python 依赖
├── credentials.json        # API 配置（需自行创建）
├── Dockerfile             # Docker 镜像构建文件
├── docker-compose.yml     # Docker Compose 配置
├── templates/             # Jinja2 模板
│   └── index.html        # 前端主页面
├── static/               # 静态资源
│   ├── script.js         # 前端 JavaScript
│   ├── style.css         # 样式文件
│   ├── logo.svg          # Logo 图标
│   └── favicon.svg       # 网站图标
├── scripts/              # 工具脚本
│   └── record_media.py   # 页面录制与视频导出
├── .generated_html/      # 生成的临时 HTML 文件
├── .recordings/          # WebM 录制文件
└── output/               # 导出的视频文件（MP4/GIF）
```

### 🔧 配置说明

#### credentials.json

```json
{
  "API_KEY": "sk-xxxxxxxxxx",           // LLM API 密钥（必填）
  "BASE_URL": "https://api.example.com/v1",  // API 基础 URL（可选）
  "MODEL": "ZhipuAI/GLM-4.6"            // 模型名称（可选）
}
```

支持的 LLM 提供商：
- OpenAI API
- 智谱 AI (ZhipuAI)
- ModelScope
- 其他兼容 OpenAI API 的服务

#### 环境变量

Docker Compose 支持的环境变量：

```bash
HOST_PORT=8000          # 主机端口映射
TZ=Asia/Shanghai        # 时区设置
FFMPEG_PATH=/usr/bin/ffmpeg  # FFmpeg 路径（可选）
```

### 📖 使用指南

#### 1. 生成动画

1. 在主页输入框输入知识点主题（如"勾股定理"、"光的折射"）
2. 点击发送或按 Enter 键
3. 等待 AI 生成动画代码（通常需要 10-60 秒）
4. 预览生成的动画效果

#### 2. 多轮对话优化

在聊天框中输入修改意见，例如：
- "请增加更多示例"
- "动画速度太快，请放慢一些"
- "增加对定理证明过程的说明"

#### 3. 导出动画

- **在新窗口打开**：独立窗口预览动画
- **保存为 HTML**：下载完整的 HTML 文件
- **导出为视频**：生成 MP4 视频（需要 FFmpeg）

#### 4. 话题建议

系统提供多个学科的话题建议：
- 算法（冒泡排序、快速排序、Dijkstra 算法等）
- 物理（光的折射、量子隧穿、电磁感应等）
- 化学（酸碱中和、氧化还原反应等）
- 数学（勾股定理、微积分基本定理等）
- 生物（DNA 复制、光合作用等）

### 🔌 API 接口

#### POST /generate

生成教学动画（SSE 流式响应）

**请求体**：
```json
{
  "topic": "知识点主题",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**响应**：Server-Sent Events 流

```
data: {"token": "<!DOCTYPE html>"}
data: {"token": "<html>..."}
...
data: {"event": "[DONE]"}
```

#### POST /record

录制页面并导出视频

**请求体**：
```json
{
  "html_text": "<html>...</html>",
  "width": 1280,
  "height": 720,
  "fps": 24,
  "mp4": true,
  "gif": false,
  "end_event": "recording:finished",
  "end_timeout": 180000
}
```

**响应**：
```json
{
  "ok": true,
  "webm": "/path/to/recording.webm",
  "webm_url": "/recordings/recording.webm",
  "mp4": "/path/to/output.mp4",
  "mp4_url": "/output/output.mp4"
}
```

### 🎨 生成动画规范

生成的 HTML 动画遵循以下规范：

1. **分辨率**：固定 1280×720 像素容器
2. **结构**：开场（5-10秒）→ 讲解（30-60秒）→ 收尾（5-10秒）
3. **字幕**：双语字幕（中文 + 英文）
4. **配色**：浅色主题，和谐易读
5. **自动播放**：页面加载后自动开始
6. **完结标记**：动画结束时调用 `markAnimationFinished()`

### 🐛 常见问题

#### 1. API 密钥错误

**错误信息**：`请在 credentials.json 里配置正确的 API_KEY`

**解决方案**：
- 检查 `credentials.json` 文件是否存在
- 确认 `API_KEY` 不是 `sk-REPLACE_ME`
- 验证 API 密钥是否有效

#### 2. FFmpeg 未找到

**错误信息**：`未找到 ffmpeg，可执行不在 PATH 中`

**解决方案**：
```bash
# 安装 FFmpeg
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS

# 或设置环境变量
export FFMPEG_PATH=/path/to/ffmpeg
```

#### 3. Playwright 浏览器未安装

**错误信息**：`未安装 Playwright 录制组件`

**解决方案**：
```bash
pip install playwright
playwright install chromium
playwright install-deps chromium
```

#### 4. 生成的 HTML 无效

**错误信息**：`返回的动画代码解析失败`

**解决方案**：
- 调整提示词，使其更加明确
- 尝试重新生成
- 检查模型返回是否完整

### 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

### 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

### 🙏 致谢

- [fogsight](https://github.com/fogsightai/fogsight) - 雾象是一款由大型语言模型（LLM）驱动的动画引擎 agent 
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Web 框架
- [Playwright](https://playwright.dev/) - 浏览器自动化
- [FFmpeg](https://ffmpeg.org/) - 视频处理
- [GSAP](https://greensock.com/gsap/) - 动画库



### 📞 联系我们

  📬 **联系我**：

- 邮箱：[75271002@qq.com](mailto:75271002@qq.com)

🔗 **社交媒体**：

- 个人页：[wwwzhouhui](https://github.com/wwwzhouhui)
- 公众号：[wwzhouhui](https://mp.weixin.qq.com/cgi-bin/settingpage?t=setting/index&action=index&token=1416320806&lang=zh_CN)
- Bilibili：[我的B站主页](https://space.bilibili.com/1527002698)

​        微信号：

​        ![image-20250906175827828](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20250906175827828.png)

<div align="center">

**如果这个项目对你有帮助，请给我们一个 ⭐ Star！**
