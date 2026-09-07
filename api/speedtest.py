import asyncio
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field

from models import TestItem
from service import SpeedTestService
from task.manager import (
    TaskManager,
)


class SpeedTestRequest(BaseModel):

    subscription: str

    tests: list[dict[str, Any]] = (
        Field(
            default_factory=list
        )
    )

    sort_by: str = "订阅原序"

    reverse: bool = False


def parse_test_items(
    raw_tests: list[dict[str, Any]],
) -> list[TestItem]:

    items = []

    for raw in raw_tests:

        name = str(
            raw.get("name") or ""
        ).strip()

        if not name:
            continue

        items.append(
            TestItem(
                name=name,

                title=str(
                    raw.get(
                        "title",
                        name,
                    )
                ),

                kind=str(
                    raw.get(
                        "kind",
                        "matrix",
                    )
                ),

                params=str(
                    raw.get(
                        "params",
                        "",
                    )
                ),

                script_name=raw.get(
                    "script_name"
                ),
            )
        )

    return items


def create_router(
    task_manager: TaskManager,
    service: SpeedTestService,
):

    router = APIRouter(
        prefix="/api/speedtest",
        tags=["speedtest"],
    )

    @router.post("")
    async def create_speedtest(
        request: SpeedTestRequest,
    ):

        file_path = Path(
            request.subscription
        )

        if not file_path.exists():

            raise HTTPException(
                status_code=400,
                detail=(
                    "订阅文件不存在: "
                    f"{file_path}"
                ),
            )

        items = parse_test_items(
            request.tests
        )

        if not items:

            raise HTTPException(
                status_code=400,
                detail="至少需要一个测试项",
            )

        task = (
            await task_manager.create_task()
        )

        asyncio.create_task(
            service.run_task(
                task_id=task.task_id,

                file_path=str(
                    file_path
                ),

                items=items,

                sort_by=request.sort_by,

                reverse=request.reverse,
            )
        )

        return {
            "task_id":
                task.task_id,

            "status":
                task.status,
        }

    @router.get(
        "/{task_id}"
    )
    async def get_task(
        task_id: str,
    ):

        task = (
            await task_manager.get_task(
                task_id
            )
        )

        if task is None:

            raise HTTPException(
                status_code=404,
                detail="任务不存在",
            )

        from task.manager import (
            serialize_result,
        )

        return {
            "task_id":
                task.task_id,

            "status":
                task.status,

            "total":
                task.total,

            "completed":
                task.completed,

            "error":
                task.error,

            "results": [
                serialize_result(
                    result
                )
                for result in task.results
            ],
        }

    @router.websocket(
        "/ws/{task_id}"
    )
    async def websocket_task(
        websocket: WebSocket,
        task_id: str,
    ):

        task = (
            await task_manager.get_task(
                task_id
            )
        )

        if task is None:

            await websocket.close(
                code=1008,
                reason="任务不存在",
            )

            return

        await websocket.accept()

        queue = (
            await task_manager.subscribe(
                task_id
            )
        )

        try:

            # 当前状态
            await websocket.send_json(
                {
                    "type":
                        "status",

                    "task_id":
                        task_id,

                    "status":
                        task.status,

                    "total":
                        task.total,

                    "completed":
                        task.completed,

                    "error":
                        task.error,
                }
            )

            # 任务已经结束
            if task.status in {
                "completed",
                "failed",
                "cancelled",
            }:

                return

            while True:

                message = await queue.get()

                await websocket.send_json(
                    message
                )

                if message.get(
                    "type"
                ) in {
                    "completed",
                    "error",
                }:

                    break

        except WebSocketDisconnect:

            pass

        finally:

            await task_manager.unsubscribe(
                task_id,
                queue,
            )

    return router