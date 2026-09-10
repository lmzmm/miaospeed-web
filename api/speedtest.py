from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from clash import load_clash_proxies_source
from models import Node, TestItem
from renderer import RESULT_DIR
from service import SpeedTestService
from task.manager import (
    TaskManager,
    serialize_result,
)


# ============================================================
# 排序映射
# ============================================================

SORT_MAPPING = {
    "rtt": "RTT",

    "http_delay": "HTTPS延迟",
    "https_delay": "HTTPS延迟",

    "max_speed": "最大速度",

    "avg_speed": "平均速度",

    "subscription_order": "订阅原序",
}


def normalize_sort_by(
    value: str,
) -> str:
    """
    API 对外使用英文参数，
    内部继续使用 ResultCleaner 原来的中文列名。
    """

    value = (
        str(value)
        .strip()
        .lower()
    )

    result = SORT_MAPPING.get(
        value
    )

    if result is None:

        raise ValueError(
            "sort_by 必须是: "
            "rtt、http_delay、"
            "max_speed、avg_speed、"
            "subscription_order"
        )

    return result


# ============================================================
# Request
# ============================================================

class SpeedTestRequest(BaseModel):

    # Clash / Mihomo 订阅 URL
    subscription: str

    # 可选：
    # 用于下载 subscription 的 HTTP/HTTPS 代理
    proxy: str | None = None

    # 测试项目
    tests: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )

    # 排序字段
    #
    # rtt
    # http_delay
    # max_speed
    # avg_speed
    # subscription_order
    #
    sort_by: str = "avg_speed"

    # false = 正序
    # true  = 倒序
    reverse: bool = False

    # 可选：
    # 只测试指定下标的节点（下标来自 /parse 返回的 index）。
    # None 表示测试全部节点。
    node_indices: list[int] | None = None


# ============================================================
# ParseRequest
# ============================================================

class ParseRequest(BaseModel):

    # Clash / Mihomo 订阅 URL
    subscription: str

    # 可选：用于下载订阅的代理
    proxy: str | None = None


def serialize_node(
    node: Node,
) -> dict[str, Any]:

    return {
        "index": node.index,
        "name": node.name,
        "type": node.type,
        "server": node.server,
        "port": node.port,
        "address": node.address,
    }


# ============================================================
# TestItem
# ============================================================

def parse_test_items(
    raw_tests: list[
        dict[str, Any]
    ],
) -> list[TestItem]:

    items: list[TestItem] = []

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


# ============================================================
# URL 校验
# ============================================================

def validate_subscription_url(
    value: str,
):
    parsed = urlparse(
        value
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "subscription 必须是 "
                "http 或 https URL"
            ),
        )

    if not parsed.netloc:

        raise HTTPException(
            status_code=400,
            detail="subscription URL 无效",
        )


def validate_proxy(
    value: str | None,
):
    if not value:
        return

    parsed = urlparse(
        value
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "proxy 目前仅支持 "
                "http / https"
            ),
        )

    if not parsed.netloc:

        raise HTTPException(
            status_code=400,
            detail="proxy 地址无效",
        )


# ============================================================
# Router
# ============================================================

def create_router(
    task_manager: TaskManager,
    service: SpeedTestService,
):

    router = APIRouter(
        prefix="/api/speedtest",
        tags=["speedtest"],
    )

    # ========================================================
    # 解析订阅，返回节点列表
    # ========================================================

    @router.post("/parse")
    async def parse_subscription(
        request: ParseRequest,
    ):

        validate_subscription_url(
            request.subscription
        )

        validate_proxy(
            request.proxy
        )

        try:

            nodes = (
                await load_clash_proxies_source(
                    request.subscription,
                    proxy=request.proxy,
                )
            )

        except Exception as e:

            raise HTTPException(
                status_code=400,
                detail=f"订阅解析失败: {e}",
            ) from e

        if not nodes:

            raise HTTPException(
                status_code=400,
                detail="没有找到有效节点",
            )

        return {
            "nodes": [
                serialize_node(node)
                for node in nodes
            ],
        }

    # ========================================================
    # 创建测速任务
    # ========================================================

    @router.post("")
    async def create_speedtest(
        request: SpeedTestRequest,
    ):

        # ----------------------------------------------------
        # subscription URL
        # ----------------------------------------------------

        validate_subscription_url(
            request.subscription
        )

        # ----------------------------------------------------
        # proxy
        # ----------------------------------------------------

        validate_proxy(
            request.proxy
        )

        # ----------------------------------------------------
        # sort
        # ----------------------------------------------------

        try:

            sort_by = normalize_sort_by(
                request.sort_by
            )

        except ValueError as e:

            raise HTTPException(
                status_code=400,
                detail=str(e),
            ) from e

        # ----------------------------------------------------
        # tests
        # ----------------------------------------------------

        items = parse_test_items(
            request.tests
        )

        if not items:

            raise HTTPException(
                status_code=400,
                detail="至少需要一个测试项",
            )

        # ----------------------------------------------------
        # node_indices
        # ----------------------------------------------------

        if (
            request.node_indices is not None
            and not request.node_indices
        ):

            raise HTTPException(
                status_code=400,
                detail="至少选择一个节点",
            )

        # ----------------------------------------------------
        # 创建任务
        # ----------------------------------------------------

        task = (
            await task_manager.create_task()
        )

        # ----------------------------------------------------
        # 后台测速
        # ----------------------------------------------------

        asyncio.create_task(
            service.run_task(
                task_id=task.task_id,

                file_path=request.subscription,

                items=items,

                sort_by=sort_by,

                reverse=request.reverse,

                proxy=request.proxy,

                node_indices=request.node_indices,
            )
        )

        return {
            "task_id":
                task.task_id,

            "status":
                task.status,

            "sort_by":
                request.sort_by,

            "reverse":
                request.reverse,

            "image":
                f"/api/speedtest/"
                f"{task.task_id}/image",
        }

    # ========================================================
    # 获取任务状态
    # ========================================================

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

            "image":
                (
                    f"/api/speedtest/"
                    f"{task_id}/image"
                    if task.status
                    == "completed"
                    else None
                ),

            "results": [
                serialize_result(
                    result
                )
                for result in task.results
            ],
        }

    # ========================================================
    # 获取最终 PNG
    # ========================================================

    @router.get(
        "/{task_id}/image"
    )
    async def get_result_image(
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

        if task.status != "completed":

            raise HTTPException(
                status_code=409,
                detail=(
                    "测速尚未完成"
                ),
            )

        report_file = (
            task.report_file
            or task_id
        )

        image_path = (
            Path(RESULT_DIR)
            / f"{report_file}.png"
        )

        if not image_path.exists():

            raise HTTPException(
                status_code=404,
                detail=(
                    "测速图片不存在"
                ),
            )

        return FileResponse(
            path=image_path,
            media_type="image/png",
            filename=(
                f"{report_file}.png"
            ),
        )

    # ========================================================
    # WebSocket
    # ========================================================

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

            # ------------------------------------------------
            # 当前状态
            # ------------------------------------------------

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

                    "image":
                        (
                            f"/api/speedtest/"
                            f"{task_id}/image"
                            if task.status
                            == "completed"
                            else None
                        ),
                }
            )

            # ------------------------------------------------
            # 已经结束
            # ------------------------------------------------

            if task.status in {
                "completed",
                "failed",
                "cancelled",
            }:

                return

            # ------------------------------------------------
            # 实时消息
            # ------------------------------------------------

            while True:

                message = (
                    await queue.get()
                )

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