from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    index: int
    name: str
    type: str
    server: str
    port: int | None
    raw: dict[str, Any]

    @property
    def address(self) -> str:
        if self.port is None:
            return self.server

        return f"{self.server}:{self.port}"


@dataclass
class TestItem:
    """
    一个测试项目。

    kind:
        matrix
        script
    """

    name: str
    title: str

    kind: str = "matrix"

    params: str = ""

    script_name: str | None = None


@dataclass
class Cell:
    """
    raw:
        原始值，用于排序、统计。

    display:
        展示值。
    """

    raw: Any = None

    display: Any = "-"


@dataclass
class TestResult:
    node: Node

    values: dict[str, Cell] = field(
        default_factory=dict
    )

    available: bool = False

    error: str | None = None

    invoke_duration: int | None = None


@dataclass
class TableResult:
    columns: list[str]

    rows: list[dict[str, Any]]

    results: list[TestResult]

    statistics: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class SpeedTestTask:
    task_id: str

    status: str = "created"

    total: int = 0

    completed: int = 0

    results: list[TestResult] = field(
        default_factory=list
    )

    error: str | None = None

    report_file: str | None = None