import asyncio
import uuid
from collections import defaultdict
from typing import Any

from models import (
    SpeedTestTask,
    TestResult,
)


class TaskManager:

    def __init__(self):

        self.tasks: dict[
            str,
            SpeedTestTask,
        ] = {}

        self.subscribers: dict[
            str,
            set[asyncio.Queue],
        ] = defaultdict(set)

        self.lock = asyncio.Lock()

    async def create_task(
        self,
    ) -> SpeedTestTask:

        task_id = uuid.uuid4().hex

        task = SpeedTestTask(
            task_id=task_id
        )

        async with self.lock:

            self.tasks[
                task_id
            ] = task

        return task

    async def get_task(
        self,
        task_id: str,
    ) -> SpeedTestTask | None:

        async with self.lock:

            return self.tasks.get(
                task_id
            )

    async def update_status(
        self,
        task_id: str,
        status: str,
        error: str | None = None,
    ):

        async with self.lock:

            task = self.tasks.get(
                task_id
            )

            if task is None:
                return

            task.status = status

            if error is not None:

                task.error = error

        await self.publish(
            task_id,
            {
                "type": "status",
                "task_id": task_id,
                "status": status,
                "error": error,
            },
        )

    async def set_total(
        self,
        task_id: str,
        total: int,
    ):

        async with self.lock:

            task = self.tasks.get(
                task_id
            )

            if task:

                task.total = total

    async def set_results(
        self,
        task_id: str,
        results: list[TestResult],
    ):

        async with self.lock:

            task = self.tasks.get(
                task_id
            )

            if task is None:
                return

            task.results = results

            task.completed = len(
                results
            )

    async def subscribe(
        self,
        task_id: str,
    ) -> asyncio.Queue:

        queue = asyncio.Queue()

        self.subscribers[
            task_id
        ].add(queue)

        return queue

    async def unsubscribe(
        self,
        task_id: str,
        queue: asyncio.Queue,
    ):

        subscribers = (
            self.subscribers.get(
                task_id
            )
        )

        if not subscribers:
            return

        subscribers.discard(
            queue
        )

    async def publish(
        self,
        task_id: str,
        message: dict[str, Any],
    ):

        subscribers = (
            self.subscribers.get(
                task_id
            )
            or set()
        )

        for queue in list(
            subscribers
        ):

            await queue.put(
                message
            )


def serialize_result(
    result: TestResult,
) -> dict:

    values = {}

    for key, cell in (
        result.values.items()
    ):

        values[key] = {
            "raw": cell.raw,
            "display": cell.display,
        }

    return {
        "index":
            result.node.index,

        "name":
            result.node.name,

        "type":
            result.node.type,

        "server":
            result.node.server,

        "port":
            result.node.port,

        "address":
            result.node.address,

        "available":
            result.available,

        "invoke_duration":
            result.invoke_duration,

        "values":
            values,
    }