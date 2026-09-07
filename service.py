import asyncio
import json

from clash import load_clash_proxies
from miaospeed_client import MiaoSpeedClient
from models import (
    TestItem,
    TestResult,
)
from result import (
    collect_record,
    ResultCleaner,
)
from renderer import ResultRenderer
from task.manager import (
    TaskManager,
    serialize_result,
)


class SpeedTestService:

    def __init__(
        self,
        task_manager: TaskManager,
    ):

        self.client = (
            MiaoSpeedClient()
        )

        self.task_manager = (
            task_manager
        )

    async def run_task(
        self,
        task_id: str,
        file_path: str,
        items: list[TestItem],
        sort_by: str = "订阅原序",
        reverse: bool = False,
    ):

        try:

            await self.task_manager.update_status(
                task_id,
                "running",
            )

            # -----------------------------
            # 读取节点
            # -----------------------------
            nodes = load_clash_proxies(
                file_path
            )

            if not nodes:

                raise ValueError(
                    "没有找到有效节点"
                )

            await self.task_manager.set_total(
                task_id,
                len(nodes),
            )

            print(
                f"[{task_id}] "
                f"有效节点: {len(nodes)}"
            )

            # -----------------------------
            # 按 MiaoSpeed Index 保存
            # -----------------------------
            results: list[
                TestResult | None
            ] = [
                None
            ] * len(nodes)

            task_error = None

            async def on_message(
                raw: str,
            ) -> bool:

                nonlocal task_error

                try:

                    data = json.loads(
                        raw
                    )

                except json.JSONDecodeError:

                    print(
                        f"[{task_id}] "
                        "收到非法 JSON"
                    )

                    return False

                # =========================
                # 全局 Error
                # =========================
                error = data.get(
                    "Error"
                )

                if error:

                    task_error = str(
                        error
                    )

                    await self.task_manager.update_status(
                        task_id,
                        "failed",
                        task_error,
                    )

                    return True

                # =========================
                # Progress
                # =========================
                progress = data.get(
                    "Progress"
                )

                if progress is not None:

                    index = progress.get(
                        "Index",
                        -1,
                    )

                    record = progress.get(
                        "Record"
                    )

                    if not isinstance(
                        index,
                        int,
                    ):
                        return False

                    if not (
                        0
                        <= index
                        < len(nodes)
                    ):
                        return False

                    if not isinstance(
                        record,
                        dict,
                    ):
                        return False

                    result = collect_record(
                        record=record,

                        node=nodes[
                            index
                        ],

                        index=index,

                        items=items,
                    )

                    results[index] = result

                    completed = sum(
                        x is not None
                        for x in results
                    )

                    await self.task_manager.publish(
                        task_id,
                        {
                            "type":
                                "progress",

                            "task_id":
                                task_id,

                            "completed":
                                completed,

                            "total":
                                len(nodes),

                            "result":
                                serialize_result(
                                    result
                                ),
                        },
                    )

                    print(
                        f"[{task_id}] "
                        f"{completed}/"
                        f"{len(nodes)} "
                        f"{result.node.name}"
                    )

                    return False

                # =========================
                # Final Result
                # =========================
                final_result = data.get(
                    "Result"
                )

                if final_result is not None:

                    records = (
                        final_result.get(
                            "Results"
                        )
                        or []
                    )

                    for index, record in enumerate(
                        records
                    ):

                        if index >= len(
                            nodes
                        ):
                            break

                        if not isinstance(
                            record,
                            dict,
                        ):
                            continue

                        results[index] = (
                            collect_record(
                                record=record,

                                node=nodes[
                                    index
                                ],

                                index=index,

                                items=items,
                            )
                        )

                    final_results = [
                        result
                        for result in results
                        if result is not None
                    ]

                    # ----------------------
                    # ResultCleaner
                    # ----------------------
                    cleaner = ResultCleaner(
                        final_results
                    )

                    table = cleaner.clean(
                        sort_by=sort_by,
                        reverse=reverse,
                    )

                    # ----------------------
                    # 保存最终结果
                    # ----------------------
                    await self.task_manager.set_results(
                        task_id,
                        table.results,
                    )

                    # ----------------------
                    # PNG + JSON
                    # ----------------------
                    renderer = ResultRenderer(
                        table=table,

                        title=(
                            "MiaoSpeed 节点测速"
                        ),
                    )

                    image_path = (
                        renderer.render()
                    )

                    json_path = (
                        renderer.save_json()
                    )

                    # ----------------------
                    # 完成消息
                    # ----------------------
                    await self.task_manager.publish(
                        task_id,
                        {
                            "type":
                                "completed",

                            "task_id":
                                task_id,

                            "status":
                                "completed",

                            "total":
                                table.statistics[
                                    "total"
                                ],

                            "completed":
                                table.statistics[
                                    "available"
                                ],

                            "columns":
                                table.columns,

                            "rows":
                                table.rows,

                            "statistics":
                                table.statistics,

                            "image":
                                str(
                                    image_path
                                ),

                            "json":
                                str(
                                    json_path
                                ),
                        },
                    )

                    await self.task_manager.update_status(
                        task_id,
                        "completed",
                    )

                    return True

                return False

            # -----------------------------
            # 执行 MiaoSpeed
            # -----------------------------
            await self.client.run(
                nodes=nodes,
                items=items,
                on_message=on_message,
            )

            # -----------------------------
            # 没有 Result
            # -----------------------------
            if task_error:
                return

            task = await (
                self.task_manager.get_task(
                    task_id
                )
            )

            if (
                task
                and task.status == "running"
            ):

                final_results = [
                    result
                    for result in results
                    if result is not None
                ]

                cleaner = ResultCleaner(
                    final_results
                )

                table = cleaner.clean(
                    sort_by=sort_by,
                    reverse=reverse,
                )

                await self.task_manager.set_results(
                    task_id,
                    table.results,
                )

                renderer = ResultRenderer(
                    table=table,

                    title=(
                        "MiaoSpeed 节点测速"
                    ),
                )

                image_path = (
                    renderer.render()
                )

                json_path = (
                    renderer.save_json()
                )

                await self.task_manager.publish(
                    task_id,
                    {
                        "type":
                            "completed",

                        "task_id":
                            task_id,

                        "status":
                            "completed",

                        "total":
                            table.statistics[
                                "total"
                            ],

                        "completed":
                            table.statistics[
                                "available"
                            ],

                        "columns":
                            table.columns,

                        "rows":
                            table.rows,

                        "statistics":
                            table.statistics,

                        "image":
                            str(
                                image_path
                            ),

                        "json":
                            str(
                                json_path
                            ),
                    },
                )

                await self.task_manager.update_status(
                    task_id,
                    "completed",
                )

        except Exception as e:

            print(
                f"[{task_id}] "
                f"测速失败: {e}"
            )

            await self.task_manager.update_status(
                task_id,
                "failed",
                str(e),
            )