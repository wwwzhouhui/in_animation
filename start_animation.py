
import webbrowser
import subprocess
import threading
import time
import os

HOST = "127.0.0.1"  
PORT = 8000

def start_backend():
    """启动 FastAPI (Instructional Animation) 服务器。"""
    print(f"--- Instructional Animation 后端启动中，请访问 http://{HOST}:{PORT} ---")
    subprocess.run([
        os.sys.executable,
        "-m", "uvicorn",
        "app:app",
        f"--host={HOST}",
        f"--port={PORT}"
    ])

def open_frontend():
    """在默认浏览器中打开 Instructional Animation 前端页面。"""
    time.sleep(2)
    url = f"http://{HOST}:{PORT}"
    print(f"--- 打开前端: {url} ---")
    webbrowser.open(url)

if __name__ == "__main__":

    backend_thread = threading.Thread(target=start_backend)
    backend_thread.daemon = True 
    backend_thread.start()
    open_frontend()


    try:
        backend_thread.join()
    except KeyboardInterrupt:
        print("\n--- 程序已关闭 ---")
        os._exit(0)
