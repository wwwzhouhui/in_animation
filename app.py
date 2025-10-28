import asyncio
import json
import logging
import os
from datetime import datetime
from uuid import uuid4
from typing import AsyncGenerator, List, Optional, Dict, Any

import pytz
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 导入 Anthropic 客户端
from AnthropicClient import AnthropicClient, anthropic_stream_to_sse

# 录制与转码工具（Playwright + FFmpeg）
try:
    from scripts.record_media import load_page_and_record, run_ffmpeg, which
except Exception:
    load_page_and_record = None
    run_ffmpeg = None
    which = None

# -----------------------------------------------------------------------
# 0. 配置
# -----------------------------------------------------------------------
shanghai_tz = pytz.timezone("Asia/Shanghai")

# 配置日志系统
def setup_logger():
    """配置日志输出到控制台和文件"""
    logger = logging.getLogger("ai_animation")
    logger.setLevel(logging.INFO)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 日志格式
    log_format = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # 文件处理器 - 按日期命名
    log_file = log_dir / f"app_{datetime.now(shanghai_tz).strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    logger.info("=" * 60)
    logger.info("日志系统初始化完成")
    logger.info(f"日志文件: {log_file}")
    logger.info("=" * 60)

    return logger

logger = setup_logger()

credentials = json.load(open("credentials.json"))
API_KEY = credentials["API_KEY"]
BASE_URL = credentials.get("BASE_URL", "")
MODEL = credentials.get("MODEL", "ZhipuAI/GLM-4.6")

if not API_KEY or API_KEY == "sk-REPLACE_ME":
    raise RuntimeError("请在 credentials.json 里配置正确的 API_KEY")

# 判断使用哪种接口：根据模型名称自动识别
def is_anthropic_model(model_name: str) -> bool:
    """判断是否是 Anthropic Claude 模型"""
    return "claude" in model_name.lower()

# 初始化客户端
if is_anthropic_model(MODEL):
    # 使用 Anthropic 客户端
    anthropic_client = AnthropicClient(
        api_key=API_KEY,
        base_url=BASE_URL if BASE_URL else "https://api.anthropic.com"
    )
    openai_client = None
    logger.info(f"使用 Anthropic 接口，模型: {MODEL}")
else:
    # 使用 OpenAI 兼容客户端
    openai_client = AsyncOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )
    anthropic_client = None
    logger.info(f"使用 OpenAI 兼容接口，模型: {MODEL}")

templates = Jinja2Templates(directory="templates")

# -----------------------------------------------------------------------
# 1. FastAPI 初始化
# -----------------------------------------------------------------------
app = FastAPI(title="Instructional Animation Backend", version="1.0.0")

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("应用启动中...")
    logger.info(f"FastAPI 版本: {FastAPI.__version__ if hasattr(FastAPI, '__version__') else 'unknown'}")
    logger.info(f"配置的模型: {MODEL}")
    logger.info(f"API Base URL: {BASE_URL if BASE_URL else '默认'}")
    logger.info("=" * 60)

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 60)
    logger.info("应用正在关闭...")
    logger.info("=" * 60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

logger.info("CORS 中间件已配置")

app.mount("/static", StaticFiles(directory="static"), name="static")
# 挂载录制输出目录，便于前端直接下载
try:
    Path(".recordings").mkdir(parents=True, exist_ok=True)
    app.mount("/recordings", StaticFiles(directory=".recordings"), name="recordings")
    logger.info("挂载录制目录: .recordings")

    Path("output").mkdir(parents=True, exist_ok=True)
    app.mount("/output", StaticFiles(directory="output"), name="output")
    logger.info("挂载输出目录: output")
except Exception as e:
    logger.warning(f"挂载静态目录失败: {str(e)}")
    pass

class ChatRequest(BaseModel):
    topic: str
    history: Optional[List[dict]] = None

class RecordRequest(BaseModel):
    url: Optional[str] = None
    html: Optional[str] = None
    html_text: Optional[str] = None  # 直接传入的 HTML 文本
    base: Optional[str] = None
    width: int = 1280
    height: int = 720
    fps: int = 24
    duration: float = 10.0
    start_delay: float = 0.0
    wait_until: str = "networkidle"  # load | domcontentloaded | networkidle
    timeout: int = 30000
    background: Optional[str] = None
    headless: bool = True
    slow_mo: int = 0
    script_steps: Optional[List[Dict[str, Any]]] = None
    out: Optional[str] = None
    mp4: bool = False
    gif: bool = False
    gif_fps: int = 10
    gif_width: int = 720
    gif_dither: str = "sierra2_4a"
    end_selector: Optional[str] = None
    end_event: Optional[str] = None
    end_function: Optional[str] = None
    end_timeout: Optional[int] = None

# -----------------------------------------------------------------------
# 2. 核心：流式生成器 (现在会使用 history，支持双接口)
# -----------------------------------------------------------------------
async def llm_event_stream(
    topic: str,
    history: Optional[List[dict]] = None,
    model: str = None,
) -> AsyncGenerator[str, None]:
    """
    使用 OpenAI 或 Anthropic 接口生成流式响应
    根据模型名称自动选择接口
    """
    history = history or []

    # 使用配置的模型，如果未指定
    if model is None:
        model = MODEL

    # 系统提示词（结构化角色设定 + 约束 + 输出格式）
    system_prompt = f"""# Role: 精美动态动画生成专家

## Profile
- author: 周辉
- version: 2.0
- language: 中文
- description: 专注于生成符合2K分辨率标准的、视觉精美的、自动播放的教育动画HTML页面，确保所有元素正确布局且无视觉缺陷

## Skills
1. 精通HTML5、CSS3、JavaScript和SVG技术栈
2. 擅长响应式布局和固定分辨率容器设计
3. 熟练掌握动画时间轴编排和视觉叙事
4. 精通浅色配色方案和现代UI设计美学
5. 能够实现双语字幕和旁白式文字解说系统

## Background
用户需要生成一个完整的单文件HTML动画，用于知识点讲解。该动画必须在固定的2K分辨率容器（1280px × 720px）中完美呈现，避免任何布局错误、元素穿模或字幕遮挡问题。

## Goals
1. 生成视觉精美、设计感强的动态动画页面
2. 确保所有元素在1280px × 720px容器内正确定位
3. 实现清晰的开场、讲解过程和收尾结构
4. 提供双语字幕和旁白式解说
5. 在动画结束时插入完结标记供录制判断

## Constraints
1. 分辨率约束：所有内容必须在固定的1280px宽 × 720px高的容器内呈现
2. 视觉完整性：禁止出现元素穿模、字幕遮挡、图形位置错误
3. 技术栈：仅使用HTML + CSS + JS + SVG，不依赖外部库，资源尽量内嵌
4. 自动播放：页面加载后立即开始播放，无交互按钮
5. 单文件输出：所有资源内嵌在一个HTML文件中
6. 完结标记：动画结束时必须执行指定的JavaScript完结逻辑

## OutputFormat
请严格输出以下结构的完整HTML文档，并使用代码块包裹（```html 开头，``` 结尾）：
```html
<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\"> 
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>{{{{主题标题}}}}</title>
  <style>
    /* 确保容器固定为2K分辨率 */
    :root {{
      --bg: #f6f7fb;
      --panel: #ffffff;
      --text: #223;
      --accent: #4a90e2;
      --sub: #7b8ba8;
    }}
    html, body {{ height: 100%; }}
    body {{
      margin: 0; padding: 0; display: flex; justify-content: center; align-items: center;
      min-height: 100vh; background: var(--bg); overflow: hidden; color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
    }}
    #animation-container {{
      position: relative; width: 1280px; height: 720px; background: var(--panel); overflow: hidden;
      box-shadow: 0 0 50px rgba(0,0,0,0.08); border-radius: 20px;
    }}
    /* 建议的字幕区域（底部居中，150-200px 高） */
    .subtitles {{ position: absolute; left: 0; right: 0; bottom: 40px; height: 180px; display: flex; align-items: center; justify-content: center; pointer-events: none; }}
    .subtitles .line {{
      background: rgba(255,255,255,0.85); color: #111; border-radius: 12px; padding: 18px 24px; font-size: 40px; line-height: 1.3; max-width: 80%; text-align: center; box-shadow: 0 8px 24px rgba(0,0,0,.08);
    }}
    /* 其他样式... */
  </style>
  </head>
  <body>
    <div id=\"animation-container\">
      <!-- 在此放置SVG/图形/讲解元素，确保关键视觉位于中心区域的60-70%，保留20-30px安全边距 -->
      <div class=\"subtitles\"><div id=\"sub-cn\" class=\"line\"></div></div>
      <div class=\"subtitles\" style=\"bottom: 240px;\"><div id=\"sub-en\" class=\"line\"></div></div>
    </div>
    <script>
      // 动画逻辑示例：请在此实现开场(5-10s) → 讲解(30-60s) → 收尾(5-10s) 的时间轴
      // 并确保元素动画流畅、无穿模，与字幕同步。

      function setSubtitles(cn, en) {{
        const cnEl = document.getElementById('sub-cn');
        const enEl = document.getElementById('sub-en');
        if (cnEl) cnEl.textContent = cn || '';
        if (enEl) enEl.textContent = en || '';
      }}

      // 动画结束时的完结标记（必须包含）
      function markAnimationFinished() {{
        try {{
          window.playFinished = true;
          window.dispatchEvent(new Event('recording:finished'));
          var flag = document.createElement('div');
          flag.id = 'finished-flag';
          flag.style.display = 'none';
          document.body.appendChild(flag);
        }} catch (e) {{ /* no-op */ }}
      }}

      // 请在最后一个动画结束后调用 markAnimationFinished();
      // markAnimationFinished();
    </script>
  </body>
</html>
```

## Workflows
1. 接收主题：获取用户指定的知识点主题（本次主题：{topic}）。
2. 结构规划：设计开场（5-10秒）→ 核心讲解（30-60秒）→ 收尾（5-10秒）的时间轴。
3. 视觉设计：选择和谐浅色配色，精准布局到 1280×720 容器，字幕区域底部居中。
4. 动画编排：用CSS动画/JS控制时间轴，保证流畅与无穿模，字幕与视觉同步。
5. 完结逻辑：在最后一个动画完成后必须调用 markAnimationFinished()。
6. 质量检查：元素不越界、字幕不遮挡关键视觉、配色和谐易读。
7. 输出交付：仅输出完整单文件HTML，并用 ```html 代码块包裹。

## Suggestions
1. 使用CSS Grid或Flexbox精确控制1280×720容器内的布局。
2. 字幕字号建议32-48px，确保2K分辨率下清晰可读。
3. 关键视觉元素应占据容器中心区域的60-70%。
4. 使用CSS变量统一管理配色方案。
5. 动画总时长建议40-90秒。
6. 关键内容保持20-30px安全边距，防止溢出。

## Output Rule
- 仅输出完整、可直接保存为 .html 的单文件源码。
- 必须使用 ```html 代码块包裹；不得输出说明文字或多余内容。
"""

    # 构建消息列表
    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": topic},
    ]

    # 根据模型类型选择接口
    if is_anthropic_model(model):
        # 使用 Anthropic 接口
        logger.info(f"使用 Anthropic 接口生成内容，模型: {model}")
        logger.info(f"主题: {topic[:100]}...")  # 只记录前100个字符
        try:
            async for sse_chunk in anthropic_stream_to_sse(
                client=anthropic_client,
                model=model,
                messages=messages,
                temperature=0.8,
                max_tokens=4096,
            ):
                yield sse_chunk
            logger.info("Anthropic 接口流式响应完成")
        except Exception as e:
            logger.error(f"Anthropic 接口调用失败: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    else:
        # 使用 OpenAI 兼容接口
        logger.info(f"使用 OpenAI 兼容接口生成内容，模型: {model}")
        logger.info(f"主题: {topic[:100]}...")  # 只记录前100个字符
        try:
            response = await openai_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=0.8,
            )
        except OpenAIError as e:
            logger.error(f"OpenAI 接口调用失败: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        # 流式输出
        async for chunk in response:
            token = chunk.choices[0].delta.content or ""
            if token:
                payload = json.dumps({"token": token}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
                await asyncio.sleep(0.001)

        logger.info("OpenAI 接口流式响应完成")
        yield 'data: {"event":"[DONE]"}\n\n'

# -----------------------------------------------------------------------
# 3. 路由 (CHANGED: Now a POST request)
# -----------------------------------------------------------------------
@app.post("/generate")
async def generate(
    chat_request: ChatRequest, # CHANGED: Use the Pydantic model
    request: Request,
):
    """
    Main endpoint: POST /generate
    Accepts a JSON body with "topic" and optional "history".
    Returns an SSE stream.
    """
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"收到生成请求 - 来自: {client_host}")
    logger.info(f"主题长度: {len(chat_request.topic)} 字符")
    logger.info(f"历史消息数: {len(chat_request.history) if chat_request.history else 0}")

    accumulated_response = ""  # for caching flow results

    async def event_generator():
        nonlocal accumulated_response
        try:
            async for chunk in llm_event_stream(chat_request.topic, chat_request.history):
                accumulated_response += chunk
                if await request.is_disconnected():
                    logger.warning(f"客户端 {client_host} 断开连接")
                    break
                yield chunk
        except Exception as e:
            logger.error(f"事件生成器错误: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"


    async def wrapped_stream():
        async for chunk in event_generator():
            yield chunk
        logger.info(f"请求完成 - 来自: {client_host}")

    headers = {
        "Cache-Control": "no-store",
        "Content-Type": "text/event-stream; charset=utf-8",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(wrapped_stream(), headers=headers)

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse(
        "index.html", {
            "request": request,
            "time": datetime.now(shanghai_tz).strftime("%Y%m%d%H%M%S")})

# -----------------------------------------------------------------------
# 3.1 录制与导出：POST /record
# -----------------------------------------------------------------------

@app.post("/record")
async def record_media(req: RecordRequest):
    if load_page_and_record is None:
        return JSONResponse({
            "ok": False,
            "error": "未安装 Playwright 录制组件，请安装: pip install playwright && playwright install chromium",
        }, status_code=500)

    # 规范化 URL（本地 HTML 简化为 file://）或接收原始 HTML 文本
    url = req.url
    temp_html_path: Optional[Path] = None
    if req.html_text:
        try:
            temp_dir = Path(".generated_html").resolve()
            temp_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(shanghai_tz).strftime("%Y%m%d-%H%M%S")
            temp_html_path = (temp_dir / f"generated-{ts}-{uuid4().hex[:8]}.html").resolve()
            temp_html_path.write_text(req.html_text, encoding="utf-8")
            url = temp_html_path.as_uri()
            logger.info("[record_media] 已保存临时 HTML: %s", temp_html_path)
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"写入临时 HTML 失败: {e}"}, status_code=500)
    elif req.html:
        html_path = Path(req.html).resolve()
        if not html_path.exists():
            return JSONResponse({"ok": False, "error": f"本地 HTML 不存在: {html_path}"}, status_code=400)
        url = html_path.as_uri()
        logger.info("[record_media] 使用本地 HTML: %s", html_path)

    if not url:
        return JSONResponse({"ok": False, "error": "必须提供 url 或 html"}, status_code=400)

    out_dir = Path(".recordings")
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("[record_media] 开始录制，加载 URL: %s", url)

    try:
        webm_path = await load_page_and_record(
            url=url,
            out_dir=out_dir,
            width=req.width,
            height=req.height,
            fps=req.fps,
            headless=req.headless,
            slow_mo=req.slow_mo,
            wait_until=req.wait_until,
            timeout=req.timeout,
            start_delay=req.start_delay,
            duration=req.duration,
            background=req.background,
            script_steps=req.script_steps,
            end_selector=req.end_selector,
            end_event=req.end_event,
            end_function=req.end_function,
            end_timeout=req.end_timeout,
        )
    except Exception as e:
        logger.error("[record_media] 录制失败: %s", e)
        return JSONResponse({"ok": False, "error": f"录制失败: {e}"}, status_code=500)

    # 输出基名：MP4 固定输出到 output 目录下
    if req.out:
        base_name = Path(req.out).with_suffix("").name
    else:
        base_name = f"capture-{datetime.now(shanghai_tz).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:8]}"
    # 生成可下载 URL（通过 /recordings 挂载）
    webm_name = Path(webm_path).name
    result: Dict[str, Any] = {"ok": True, "webm": str(webm_path), "webm_url": f"/recordings/{webm_name}"}

    output_dir: Optional[Path] = None

    # mp4
    if req.mp4:
        if which is None or which("ffmpeg") is None:
            return JSONResponse({"ok": False, "error": "未找到 ffmpeg，可执行不在 PATH 中"}, status_code=500)
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)
        mp4_path = output_dir / f"{base_name}.mp4"
        try:
            run_ffmpeg(["-i", str(webm_path), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(mp4_path)])
        except Exception as e:
            logger.error("[record_media] mp4 转码失败: %s", e)
            return JSONResponse({"ok": False, "error": f"mp4 转码失败: {e}"}, status_code=500)
        # 额外的生成完成校验：文件必须存在且非空
        try:
            if (not mp4_path.exists()) or mp4_path.stat().st_size <= 0:
                return JSONResponse({"ok": False, "error": "mp4 文件生成异常：文件不存在或大小为0"}, status_code=500)
        except Exception:
            return JSONResponse({"ok": False, "error": "mp4 文件生成校验失败"}, status_code=500)
        logger.info("[record_media] 生成 mp4: %s", mp4_path)
        result["mp4"] = str(mp4_path)
        result["mp4_url"] = f"/output/{mp4_path.name}"

    # gif
    if req.gif:
        if which is None or which("ffmpeg") is None:
            return JSONResponse({"ok": False, "error": "未找到 ffmpeg，可执行不在 PATH 中"}, status_code=500)
        if output_dir is None:
            output_dir = Path("output")
            output_dir.mkdir(parents=True, exist_ok=True)
        base_path = output_dir / base_name
        palette = base_path.with_suffix(".png")
        gif_path = base_path.with_suffix(".gif")
        try:
            run_ffmpeg([
                "-i", str(webm_path),
                "-vf", f"fps={req.gif_fps},scale={req.gif_width}:-1:flags=lanczos,palettegen",
                str(palette),
            ])
            run_ffmpeg([
                "-i", str(webm_path),
                "-i", str(palette),
                "-lavfi", f"fps={req.gif_fps},scale={req.gif_width}:-1:flags=lanczos,paletteuse=dither={req.gif_dither}",
                str(gif_path),
            ])
        except Exception as e:
            logger.error("[record_media] gif 生成失败: %s", e)
            return JSONResponse({"ok": False, "error": f"gif 生成失败: {e}"}, status_code=500)
        logger.info("[record_media] 生成 gif: %s", gif_path)
        result["gif"] = str(gif_path)
        result["gif_url"] = f"/recordings/{gif_path.name}"

    return JSONResponse(result)

# -----------------------------------------------------------------------
# 4. 本地启动命令
# -----------------------------------------------------------------------
# uvicorn app:app --reload --host 0.0.0.0 --port 8000


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
