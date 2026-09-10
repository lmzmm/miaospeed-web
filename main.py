import atexit
import os
import subprocess
import sys
import signal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


# ============================================================
# Windows 控制台编码
#
# 默认 GBK 无法编码节点名中的 emoji（如国旗 🇭🇰），
# 会导致 print 抛 UnicodeEncodeError 使任务失败。
# 统一改为 UTF-8，编码失败时用替换符兜底，避免崩溃。
# ============================================================

if sys.stdout and hasattr(sys.stdout, "reconfigure"):

    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace",
    )

if sys.stderr and hasattr(sys.stderr, "reconfigure"):

    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="replace",
    )

from api.speedtest import (
    create_router,
)

from service import (
    SpeedTestService,
)

from task.manager import (
    TaskManager,
)


def resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径，兼容 PyInstaller 打包后的临时目录。"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


# ============================================================
# MiaoSpeed 服务端管理
#
# 自动启动内置的 miaospeed 服务端进程，
# 程序退出时自动清理。
# ============================================================

MIAOSPEED_BIND = "127.0.0.1:8765"
MIAOSPEED_TOKEN = "9876543210"

_miaospeed_process: subprocess.Popen | None = None


def start_miaospeed():
    """启动 MiaoSpeed 服务端子进程。"""
    global _miaospeed_process

    binary = resource_path("miaospeed-windows-amd64.exe")

    if not os.path.isfile(binary):
        print(f"[MiaoSpeed] 未找到服务端: {binary}，跳过自动启动")
        return

    cmd = [
        binary, "server",
        "-bind", MIAOSPEED_BIND,
        "-token", MIAOSPEED_TOKEN,
    ]

    print(f"[MiaoSpeed] 启动服务端: {' '.join(cmd)}")

    _miaospeed_process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=(
            subprocess.CREATE_NO_WINDOW
            if sys.platform == "win32"
            else 0
        ),
    )

    print(f"[MiaoSpeed] 服务端已启动 (PID: {_miaospeed_process.pid})")


def stop_miaospeed():
    """停止 MiaoSpeed 服务端子进程。"""
    global _miaospeed_process

    if _miaospeed_process is None:
        return

    if _miaospeed_process.poll() is not None:
        print("[MiaoSpeed] 服务端已退出")
        _miaospeed_process = None
        return

    print("[MiaoSpeed] 正在停止服务端...")

    if sys.platform == "win32":
        _miaospeed_process.terminate()
    else:
        _miaospeed_process.send_signal(signal.SIGTERM)

    try:
        _miaospeed_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _miaospeed_process.kill()

    print("[MiaoSpeed] 服务端已停止")
    _miaospeed_process = None


# 注册退出清理
atexit.register(stop_miaospeed)

# 信号处理（Ctrl+C / kill）
def _signal_handler(sig, frame):
    stop_miaospeed()
    sys.exit(0)

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


app = FastAPI(
    title="MiaoSpeed SpeedTest",
    version="1.0.0",
)


# ============================================================
# CORS
#
# 前端（如 http://localhost:3000）与后端不同源，
# 浏览器会先发 OPTIONS 预检请求，必须配置 CORS 才能访问。
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


task_manager = TaskManager()

speed_test_service = (
    SpeedTestService(
        task_manager
    )
)


app.include_router(
    create_router(
        task_manager,
        speed_test_service,
    )
)


@app.get("/health")
async def health():

    return {
        "status":
            "ok"
    }


# ============================================================
# 前端静态文件
#
# 放在所有 API 路由之后，确保 /api/* 和 /health 优先匹配。
# html=True 时，未匹配到文件的路径会回退到 index.html（SPA 行为）。
# ============================================================

frontend_dir = resource_path("front/out")

if os.path.isdir(frontend_dir):

    app.mount(
        "/",
        StaticFiles(directory=frontend_dir, html=True),
        name="frontend",
    )


# ============================================================
# 直接启动
# ============================================================

if __name__ == "__main__":

    import uvicorn

    start_miaospeed()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )