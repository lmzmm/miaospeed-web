from __future__ import annotations

import json
from dataclasses import replace

from clash import load_clash_proxies_source
from miaospeed_client import MiaoSpeedClient
from models import (
    Node,
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
        proxy: str | None = None,
        node_indices: list[int] | None = None,
    ):

        try:

            await self.task_manager.update_status(
                task_id,
                "running",
            )

            # =================================================
            # 加载节点
            #
            # file_path 可以是：
            #
            # 1. 本地 Clash/Mihomo YAML
            # 2. http/https 订阅 URL
            #
            # proxy 只用于下载订阅。
            # =================================================

            nodes = await load_clash_proxies_source(
                file_path,
                proxy=proxy,
            )

            # -------------------------------------------------
            # 过滤节点
            #
            # node_indices 来自 /parse 返回的 index，
            # 过滤后重新编号，保证后续按顺序测速。
            # -------------------------------------------------

            if node_indices is not None:

                filtered: list[Node] = []

                for new_index, old_index in enumerate(
                    node_indices
                ):

                    if 0 <= old_index < len(nodes):

                        filtered.append(
                            replace(
                                nodes[old_index],
                                index=new_index,
                            )
                        )

                nodes = filtered

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

            if proxy:

                print(
                    f"[{task_id}] "
                    f"订阅下载代理: {proxy}"
                )

            # =================================================
            # 按 MiaoSpeed Index 保存结果
            # =================================================

            results: list[
                TestResult | None
            ] = [
                None
            ] * len(nodes)

            task_error = None

            # =================================================
            # MiaoSpeed 消息处理
            # =================================================

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

                # =================================================
                # Global Error
                # =================================================

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

                # =================================================
                # Progress
                # =================================================

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

                # =================================================
                # Final Result
                # =================================================

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

                    # =================================================
                    # 清洗
                    # =================================================

                    cleaner = ResultCleaner(
                        final_results
                    )

                    table = cleaner.clean(
                        sort_by=sort_by,
                        reverse=reverse,
                    )

                    # =================================================
                    # 保存最终结果
                    # =================================================

                    await self.task_manager.set_results(
                        task_id,
                        table.results,
                    )

                    # =================================================
                    # PNG + JSON
                    # =================================================

                    renderer = ResultRenderer(
                        report_id=task_id,
                    )

                    image_path = (
                        renderer.render(
                            table
                        )
                    )

                    json_path = (
                        renderer.save_json(
                            table
                        )
                    )

                    # =================================================
                    # 完成消息
                    # =================================================

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

                            # 对前端开放的图片地址
                            "image":
                                f"/api/speedtest/"
                                f"{task_id}/image",

                            # 保留本地路径
                            "image_path":
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

            # =================================================
            # 执行 MiaoSpeed
            # =================================================

            await self.client.run(
                nodes=nodes,
                items=items,
                on_message=on_message,
            )

            # =================================================
            # MiaoSpeed 没有发送 Result 时
            # 使用 Progress 中已经收集的结果
            # =================================================

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
                    report_id=task_id,
                )

                image_path = (
                    renderer.render(
                        table
                    )
                )

                json_path = (
                    renderer.save_json(
                        table
                    )
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
                            f"/api/speedtest/"
                            f"{task_id}/image",

                        "image_path":
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