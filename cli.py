import asyncio
import sys

from result import ResultCleaner
from renderer import ResultRenderer
from service import SpeedTestService
from task.manager import TaskManager
from tests import load_test_items


async def main():

    if len(sys.argv) < 2:

        print(
            "用法:"
        )

        print(
            "python cli.py "
            "<clash.yaml>"
        )

        return

    subscription = (
        sys.argv[1]
    )

    tests_file = (
        sys.argv[2]
        if len(sys.argv) >= 3
        else "tests.yaml"
    )

    items = load_test_items(
        tests_file
    )

    print(
        "测试项目:"
    )

    for item in items:

        print(
            f"  - {item.title}"
        )

    print()

    task_manager = (
        TaskManager()
    )

    service = (
        SpeedTestService(
            task_manager
        )
    )

    task = (
        await task_manager.create_task()
    )

    await service.run_task(
        task_id=task.task_id,
        file_path=subscription,
        items=items,
        sort_by="平均速度",
        reverse=True,
    )

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

    cleaner = ResultCleaner(
        final_task.results
    )

    table = cleaner.clean(
        sort_by="平均速度",
        reverse=True,
    )

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
                for column
                in table.columns
            )
        )

    print(
        "=" * 160
    )

    print()

    renderer = ResultRenderer(
        table,
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

    print(
        f"PNG: {image_path}"
    )

    print(
        f"JSON: {json_path}"
    )

    print()

    print(
        "统计:"
    )

    for key, value in (
        table.statistics.items()
    ):

        print(
            f"  {key}: {value}"
        )


if __name__ == "__main__":

    asyncio.run(
        main()
    )