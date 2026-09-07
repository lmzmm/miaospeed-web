from fastapi import FastAPI

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