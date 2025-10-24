import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
import shutil

try:
    import imageio_ffmpeg
except Exception:  # imageio-ffmpeg 可选，失败时继续尝试其他路径
    imageio_ffmpeg = None

try:
    from playwright.async_api import async_playwright
except Exception:
    async_playwright = None


def _resolve_ffmpeg_path() -> Optional[str]:
    # 优先读取环境变量
    ffmpeg_env = os.environ.get("FFMPEG_PATH")
    if ffmpeg_env:
        return ffmpeg_env

    # 其次使用系统 PATH
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return ffmpeg_in_path

    # 最后尝试 imageio_ffmpeg 提供的内置二进制
    if imageio_ffmpeg is not None:
        try:
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass

    return None


FFMPEG_BIN = _resolve_ffmpeg_path()


def which(cmd: str) -> Optional[str]:
    if cmd == "ffmpeg" and FFMPEG_BIN:
        return FFMPEG_BIN
    return shutil.which(cmd)


def run_ffmpeg(args: List[str]) -> None:
    if not FFMPEG_BIN:
        raise RuntimeError("未检测到 FFmpeg，可设置环境变量 FFMPEG_PATH 或安装 ffmpeg/imageio-ffmpeg")

    proc = subprocess.run(
        [FFMPEG_BIN, "-y", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg 失败: {proc.stderr.splitlines()[-1] if proc.stderr else 'unknown error'}")


async def load_page_and_record(
    url: str,
    out_dir: Path,
    width: int,
    height: int,
    fps: int,
    headless: bool,
    slow_mo: int,
    wait_until: str,
    timeout: int,
    start_delay: float,
    duration: float,
    background: Optional[str],
    script_steps: Optional[List[Dict[str, Any]]],
    end_selector: Optional[str] = None,
    end_event: Optional[str] = None,
    end_function: Optional[str] = None,
    end_timeout: Optional[int] = None,
) -> Path:
    if async_playwright is None:
        raise RuntimeError("未安装 Playwright，请先 pip install playwright 并 playwright install chromium")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=slow_mo)
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            record_video_dir=str(out_dir),
            record_video_size={"width": width, "height": height},
            color_scheme="light",
        )
        page = await context.new_page()
        page.set_default_timeout(timeout)
        await page.goto(url, wait_until=wait_until)

        if background:
            await page.evaluate("(color) => { document.body.style.background = color }", background)

        # 执行脚本步骤
        if script_steps:
            try:
                for step in script_steps:
                    if "wait" in step:
                        s = step["wait"]
                        state = s.get("state", "load")
                        t = s.get("timeout", timeout)
                        await page.wait_for_load_state(state, timeout=t)
                    elif "click" in step:
                        sel = step["click"]["selector"]
                        await page.wait_for_selector(sel, timeout=timeout)
                        await page.click(sel, timeout=timeout)
                    elif "hover" in step:
                        sel = step["hover"]["selector"]
                        await page.wait_for_selector(sel, timeout=timeout)
                        await page.hover(sel, timeout=timeout)
                    elif "type" in step:
                        sel = step["type"]["selector"]
                        text = step["type"]["text"]
                        await page.wait_for_selector(sel, timeout=timeout)
                        await page.fill(sel, "", timeout=timeout)
                        await page.type(sel, text, timeout=timeout)
                    elif "scroll" in step:
                        x = step["scroll"].get("x", 0)
                        y = step["scroll"].get("y", 0)
                        await page.evaluate("({x,y}) => window.scrollTo(x,y)", {"x": x, "y": y})
                    elif "waitFor" in step:
                        sel = step["waitFor"].get("selector")
                        t = step["waitFor"].get("timeout", timeout)
                        await page.wait_for_selector(sel, timeout=t)
                    elif "delay" in step:
                        await asyncio.sleep(float(step["delay"]))
            except Exception as e:
                # 失败时保存截图便于诊断
                try:
                    snap = out_dir / "error.png"
                    await page.screenshot(path=str(snap))
                except Exception:
                    pass
                raise

        # 开始延时与持续录制窗口生命周期
        if start_delay > 0:
            await asyncio.sleep(start_delay)

        # 结束条件：优先使用 end_* 参数，其次使用固定 duration
        used_timeout = end_timeout or timeout
        if end_selector:
            await page.wait_for_selector(end_selector, timeout=used_timeout)
        elif end_function:
            # 使用 Playwright 原生 wait_for_function（表达式返回 truthy 即通过）
            await page.wait_for_function(end_function, timeout=used_timeout)
        elif end_event:
            # 在页面内注入等待自定义事件的 Promise（以单一参数对象传入）
            await page.evaluate(
                "({name, timeout}) => new Promise((resolve, reject) => { const t = setTimeout(() => reject('timeout'), timeout); window.addEventListener(name, () => { clearTimeout(t); resolve(true); }, { once: true }); })",
                {"name": end_event, "timeout": used_timeout},
            )
        else:
            if duration > 0:
                await asyncio.sleep(duration)

        await context.close()  # 关闭后视频文件才会写入目录
        await browser.close()

        # 取视频文件（Playwright 默认生成 .webm 文件在 context 目录）
        vids = list(out_dir.glob("**/*.webm"))
        if not vids:
            raise RuntimeError("未生成 webm 文件，请检查录制配置")
        latest = max(vids, key=lambda p: p.stat().st_mtime)
        return latest


def main() -> None:
    parser = argparse.ArgumentParser(description="基于 Playwright 将 HTML/URL 录制为视频并生成 GIF")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="要录制的 URL")
    src.add_argument("--html", help="本地 HTML 文件路径")
    parser.add_argument("--base", help="静态资源根目录（本地 HTML 时可选）")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--start-delay", type=float, default=0.0)
    parser.add_argument("--wait-until", default="networkidle", choices=["load", "domcontentloaded", "networkidle"])
    parser.add_argument("--timeout", type=int, default=30000)
    parser.add_argument("--background", default=None)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--slow-mo", type=int, default=0)
    parser.add_argument("--script", help="交互步骤 YAML/JSON 文件")
    parser.add_argument("--out", help="输出文件路径（mp4/gif/webm 自动推断）")
    parser.add_argument("--mp4", action="store_true", help="生成 mp4")
    parser.add_argument("--gif", action="store_true", help="生成 gif")
    parser.add_argument("--gif-fps", type=int, default=10)
    parser.add_argument("--gif-width", type=int, default=720)
    parser.add_argument("--gif-dither", default="sierra2_4a")
    parser.add_argument("--end-selector", help="录制结束时等待出现的选择器")
    parser.add_argument("--end-event", help="录制结束时等待的自定义窗口事件名")
    parser.add_argument("--end-function", help="录制结束时等待的表达式（truthy 即结束），例如 'window.playFinished === true' 或 '() => window.done'")
    parser.add_argument("--end-timeout", type=int, help="录制结束条件的超时（默认继承 --timeout）")

    args = parser.parse_args()

    # 准备 URL（本地 HTML 使用 file:// 或建议内置服务，V1 简化为 file://）
    url = args.url
    if args.html:
        html_path = Path(args.html).resolve()
        if not html_path.exists():
            print(f"本地 HTML 不存在: {html_path}", file=sys.stderr)
            sys.exit(1)
        # 使用 as_uri() 生成跨平台 file:// URL（Windows 将转为 file:///C:/...）
        url = html_path.as_uri()

    # 加载脚本
    steps: Optional[List[Dict[str, Any]]] = None
    if args.script:
        fp = Path(args.script)
        if not fp.exists():
            print(f"脚本文件不存在: {fp}", file=sys.stderr)
            sys.exit(1)
        if fp.suffix.lower() in (".yml", ".yaml"):
            steps = yaml.safe_load(fp.read_text()).get("steps", [])
        elif fp.suffix.lower() == ".json":
            steps = json.loads(fp.read_text()).get("steps", [])
        else:
            print("仅支持 YAML/JSON 脚本", file=sys.stderr)
            sys.exit(1)

    out_dir = Path(".recordings")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 录制
    webm_path = asyncio.run(
        load_page_and_record(
            url=url,
            out_dir=out_dir,
            width=args.width,
            height=args.height,
            fps=args.fps,
            headless=args.headless,
            slow_mo=args.slow_mo,
            wait_until=args.wait_until,
            timeout=args.timeout,
            start_delay=args.start_delay,
            duration=args.duration,
            background=args.background,
            script_steps=steps,
            end_selector=args.end_selector,
            end_event=args.end_event,
            end_function=args.end_function,
            end_timeout=args.end_timeout,
        )
    )
    print(f"生成 webm: {webm_path}")

    # 推断输出基名
    ts = time.strftime("%Y%m%d-%H%M%S")
    base = Path(args.out).with_suffix("") if args.out else Path(f"capture-{ts}")

    # mp4 转码
    if args.mp4:
        if not which("ffmpeg"):
            print("未找到 ffmpeg，可执行不在 PATH 中", file=sys.stderr)
            sys.exit(2)
        mp4_path = base.with_suffix(".mp4")
        run_ffmpeg(["-i", str(webm_path), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(mp4_path)])
        print(f"生成 mp4: {mp4_path}")

    # gif 生成（palettegen + paletteuse）
    if args.gif:
        if not which("ffmpeg"):
            print("未找到 ffmpeg，可执行不在 PATH 中", file=sys.stderr)
            sys.exit(2)
        palette = base.with_suffix(".png")
        gif_path = base.with_suffix(".gif")
        run_ffmpeg([
            "-i", str(webm_path),
            "-vf", f"fps={args.gif_fps},scale={args.gif_width}:-1:flags=lanczos,palettegen",
            str(palette),
        ])
        run_ffmpeg([
            "-i", str(webm_path),
            "-i", str(palette),
            "-lavfi", f"fps={args.gif_fps},scale={args.gif_width}:-1:flags=lanczos,paletteuse=dither={args.gif_dither}",
            str(gif_path),
        ])
        print(f"生成 gif: {gif_path}")


if __name__ == "__main__":
    main()
