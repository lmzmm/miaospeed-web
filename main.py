import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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


@app.get("/")
async def root():

    return {
        "name":
            "MiaoSpeed SpeedTest",

        "version":
            "1.0.0",
    }


@app.get("/health")
async def health():

    return {
        "status":
            "ok"
    }


# ============================================================
# 直接启动
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )