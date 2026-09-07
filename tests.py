from dataclasses import dataclass

import yaml
import miaospeedlib as m

from models import TestItem


@dataclass(frozen=True)
class MatrixDefinition:
    name: str

    matrix_type: object

    params: str

    column: str


MATRIX_REGISTRY = {

    "TEST_PING_RTT": MatrixDefinition(
        name="TEST_PING_RTT",

        matrix_type=(
            m.SlaveRequestMatrixType.TEST_PING_RTT
        ),

        params="",

        column="RTT",
    ),

    "TEST_PING_MAX_RTT": MatrixDefinition(
        name="TEST_PING_MAX_RTT",

        matrix_type=(
            m.SlaveRequestMatrixType.TEST_PING_MAX_RTT
        ),

        params="",

        column="MAX RTT",
    ),

    "TEST_PING_SD_RTT": MatrixDefinition(
        name="TEST_PING_SD_RTT",

        matrix_type=(
            m.SlaveRequestMatrixType.TEST_PING_SD_RTT
        ),

        params="",

        column="RTT标准差",
    ),

    "TEST_PING_SD_CONN": MatrixDefinition(
        name="TEST_PING_SD_CONN",

        matrix_type=(
            m.SlaveRequestMatrixType.TEST_PING_SD_CONN
        ),

        params="",

        column="连接标准差",
    ),

    "TEST_PING_CONN": MatrixDefinition(
        name="TEST_PING_CONN",

        matrix_type=(
            m.SlaveRequestMatrixType.TEST_PING_CONN
        ),

        params="",

        column="HTTPS延迟",
    ),

    "TEST_HTTP_CODE": MatrixDefinition(
        name="TEST_HTTP_CODE",

        matrix_type=(
            m.SlaveRequestMatrixType.TEST_HTTP_CODE
        ),

        params="",

        column="HTTP状态码",
    ),

    "TEST_PING_TOTAL_CONN": MatrixDefinition(
        name="TEST_PING_TOTAL_CONN",

        matrix_type=(
            m.SlaveRequestMatrixType.TEST_PING_TOTAL_CONN
        ),

        params="",

        column="总连接数",
    ),

    "TEST_PING_TOTAL_RTT": MatrixDefinition(
        name="TEST_PING_TOTAL_RTT",

        matrix_type=(
            m.SlaveRequestMatrixType.TEST_PING_TOTAL_RTT
        ),

        params="",

        column="总RTT",
    ),

    "SPEED_AVERAGE": MatrixDefinition(
        name="SPEED_AVERAGE",

        matrix_type=(
            m.SlaveRequestMatrixType.SPEED_AVERAGE
        ),

        params="0",

        column="平均速度",
    ),

    "SPEED_MAX": MatrixDefinition(
        name="SPEED_MAX",

        matrix_type=(
            m.SlaveRequestMatrixType.SPEED_MAX
        ),

        params="0",

        column="最大速度",
    ),

    "SPEED_PER_SECOND": MatrixDefinition(
        name="SPEED_PER_SECOND",

        matrix_type=(
            m.SlaveRequestMatrixType.SPEED_PER_SECOND
        ),

        params="0",

        column="每秒速度",
    ),

    "UDP_TYPE": MatrixDefinition(
        name="UDP_TYPE",

        matrix_type=(
            m.SlaveRequestMatrixType.UDP_TYPE
        ),

        params="0",

        column="UDP类型",
    ),

    "GEOIP_INBOUND": MatrixDefinition(
        name="GEOIP_INBOUND",

        matrix_type=(
            m.SlaveRequestMatrixType.GEOIP_INBOUND
        ),

        params="",

        column="入口GeoIP",
    ),

    "GEOIP_OUTBOUND": MatrixDefinition(
        name="GEOIP_OUTBOUND",

        matrix_type=(
            m.SlaveRequestMatrixType.GEOIP_OUTBOUND
        ),

        params="",

        column="出口GeoIP",
    ),
}


def build_matrix(
    item: TestItem,
) -> m.SlaveRequestMatrixEntry:

    if item.kind == "script":

        return m.SlaveRequestMatrixEntry(
            Type=(
                m.SlaveRequestMatrixType.TEST_SCRIPT
            ),

            Params=(
                item.script_name
                or item.title
            ),
        )

    definition = MATRIX_REGISTRY.get(
        item.name
    )

    if definition is None:
        raise ValueError(
            f"未知测试项: {item.name}"
        )

    params = (
        item.params
        if item.params != ""
        else definition.params
    )

    return m.SlaveRequestMatrixEntry(
        Type=definition.matrix_type,
        Params=params,
    )


def build_matrices(
    items: list[TestItem],
) -> list[m.SlaveRequestMatrixEntry]:

    return [
        build_matrix(item)
        for item in items
    ]


def load_test_items(
    file_path: str = "tests.yaml",
) -> list[TestItem]:

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as f:

        config = yaml.safe_load(f)

    if not isinstance(
        config,
        dict,
    ):
        raise ValueError(
            "tests.yaml 格式错误"
        )

    raw_tests = config.get(
        "tests",
        [],
    )

    if not isinstance(
        raw_tests,
        list,
    ):
        raise ValueError(
            "tests 必须是数组"
        )

    items: list[TestItem] = []

    for raw in raw_tests:

        if not isinstance(
            raw,
            dict,
        ):
            continue

        name = str(
            raw.get("name") or ""
        ).strip()

        if not name:
            continue

        title = str(
            raw.get(
                "title",
                name,
            )
        )

        items.append(
            TestItem(
                name=name,

                title=title,

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