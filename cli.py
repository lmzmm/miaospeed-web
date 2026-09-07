import asyncio
import sys

from result import ResultCleaner
from renderer import ResultRenderer
from service import SpeedTestService
from task.manager import TaskManager
from tests import load_test_items


async def main():

    # ========================================================
    # 参数
    # ========================================================

    if len(sys.argv) < 2:

        print("用法:")
        print(
            "python cli.py "
            "<clash.yaml> "
            "[tests.yaml]"
        )

        return

    # 第一个参数：Clash / Mihomo 配置文件
    subscription = sys.argv[1]

    # 第二个参数：测试项目配置，可选
    tests_file = (
        sys.argv[2]
        if len(sys.argv) >= 3
        else "tests.yaml"
    )

    # ========================================================
    # 加载测试项目
    # ========================================================

    items = load_test_items(
        tests_file
    )

    print("测试项目:")

    for item in items:
        print(
            f"  - {item.title}"
        )

    print()

    # ========================================================
    # 初始化任务管理器 / 服务
    # ========================================================

    task_manager = TaskManager()

    service = SpeedTestService(
        task_manager
    )

    task = (
        await task_manager.create_task()
    )

    print(
        f"任务 ID: {task.task_id}"
    )

    print()

    # ========================================================
    # 开始测速
    # ========================================================

    await service.run_task(
        task_id=task.task_id,
        file_path=subscription,
        items=items,
        sort_by="平均速度",
        reverse=True,
    )

    # ========================================================
    # 获取最终任务
    # ========================================================

    final_task = (
        await task_manager.get_task(
            task.task_id
        )
    )

    if final_task is None:
        raise RuntimeError(
            "任务不存在"
        )

    if final_task.status != "completed":
        raise RuntimeError(
            final_task.error
            or "测速失败"
        )

    # ========================================================
    # 清洗结果
    # ========================================================

    cleaner = ResultCleaner(
        final_task.results
    )

    table = cleaner.clean(
        sort_by="平均速度",
        reverse=True,
    )

    # ========================================================
    # 输出 CLI 表格
    # ========================================================

    print()

    print(
        "=" * 160
    )

    print(
        " | ".join(
            table.columns
        )
    )

    print(
        "-" * 160
    )

    for row in table.rows:

        print(
            " | ".join(
                str(
                    row.get(
                        column,
                        "-",
                    )
                )
                for column in table.columns
            )
        )

    print(
        "=" * 160
    )

    print()

    # ========================================================
    # 生成 PNG / JSON
    # ========================================================

    renderer = ResultRenderer()

    image_path = renderer.render(
        table,
    )

    json_path = renderer.save_json(
        table,
    )

    # ========================================================
    # 输出文件
    # ========================================================

    print(
        f"PNG: {image_path}"
    )

    print(
        f"JSON: {json_path}"
    )

    print()

    # ========================================================
    # 统计
    # ========================================================

    print("统计:")

    for key, value in (
        table.statistics.items()
    ):
        print(
            f"  {key}: {value}"
        )

    print()


if __name__ == "__main__":

    asyncio.run(
        main()
    )