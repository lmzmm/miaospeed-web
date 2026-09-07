import json
from typing import Any

from models import (
    Node,
    TestItem,
    TestResult,
    Cell,
    TableResult,
)


def decode_payload(
    payload: Any,
) -> Any:

    if payload is None:
        return None

    if isinstance(
        payload,
        (
            dict,
            list,
            int,
            float,
            bool,
        ),
    ):
        return payload

    if not isinstance(
        payload,
        str,
    ):
        return payload

    payload = payload.strip()

    if not payload:
        return None

    try:
        return json.loads(
            payload
        )

    except json.JSONDecodeError:

        return payload


def set_value(
    result: TestResult,
    column: str,
    raw: Any,
    display: Any = None,
):

    if display is None:

        display = (
            raw
            if raw is not None
            else "-"
        )

    result.values[column] = Cell(
        raw=raw,
        display=display,
    )


def format_rtt(
    value: Any,
) -> str:

    if value is None:
        return "-"

    try:
        value = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return str(value)

    if value.is_integer():

        return f"{int(value)}ms"

    return f"{value:g}ms"


def format_speed(
    value: Any,
) -> str:

    if value is None:
        return "-"

    try:
        value = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return str(value)

    if value <= 0:
        return "0B"

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
        "PB",
    ]

    unit_index = 0

    while (
        value >= 1024
        and unit_index < len(units) - 1
    ):

        value /= 1024
        unit_index += 1

    return (
        f"{value:.2f}"
        f"{units[unit_index]}"
    )


def format_proxy_type(
    value: str,
) -> str:

    if not value:
        return "-"

    value_lower = value.lower()

    if value_lower == "ss":
        return "Shadowsocks"

    if value_lower == "ssr":
        return "ShadowsocksR"

    if value_lower == "tuic":
        return "TUIC"

    return value.capitalize()


def collect_record(
    record: dict,
    node: Node,
    index: int,
    items: list[TestItem],
) -> TestResult:

    result = TestResult(
        node=node,

        invoke_duration=record.get(
            "InvokeDuration"
        ),
    )

    matrices = (
        record.get(
            "Matrices"
        )
        or []
    )

    for matrix in matrices:

        matrix_type = matrix.get(
            "Type"
        )

        data = decode_payload(
            matrix.get(
                "Payload"
            )
        )

        # ==================================
        # RTT
        # ==================================
        if matrix_type == "TEST_PING_RTT":

            if isinstance(
                data,
                dict,
            ):

                value = data.get(
                    "Value"
                )

                set_value(
                    result,
                    "RTT",
                    value,
                    format_rtt(value),
                )

        # ==================================
        # MAX RTT
        # ==================================
        elif (
            matrix_type
            == "TEST_PING_MAX_RTT"
        ):

            if isinstance(
                data,
                dict,
            ):

                value = data.get(
                    "Value"
                )

                set_value(
                    result,
                    "MAX RTT",
                    value,
                    format_rtt(value),
                )

        # ==================================
        # RTT SD
        # ==================================
        elif (
            matrix_type
            == "TEST_PING_SD_RTT"
        ):

            if isinstance(
                data,
                dict,
            ):

                value = data.get(
                    "Value"
                )

                set_value(
                    result,
                    "RTT标准差",
                    value,
                    format_rtt(value),
                )

        # ==================================
        # Connection SD
        # ==================================
        elif (
            matrix_type
            == "TEST_PING_SD_CONN"
        ):

            if isinstance(
                data,
                dict,
            ):

                value = data.get(
                    "Value"
                )

                set_value(
                    result,
                    "连接标准差",
                    value,
                    format_rtt(value),
                )

        # ==================================
        # HTTPS
        # ==================================
        elif (
            matrix_type
            == "TEST_PING_CONN"
        ):

            if isinstance(
                data,
                dict,
            ):

                value = data.get(
                    "Value"
                )

                set_value(
                    result,
                    "HTTPS延迟",
                    value,
                    format_rtt(value),
                )

        # ==================================
        # HTTP Code
        # ==================================
        elif (
            matrix_type
            == "TEST_HTTP_CODE"
        ):

            value = (
                data.get("Value")
                if isinstance(
                    data,
                    dict,
                )
                else data
            )

            set_value(
                result,
                "HTTP状态码",
                value,
            )

        # ==================================
        # Total Conn
        # ==================================
        elif (
            matrix_type
            == "TEST_PING_TOTAL_CONN"
        ):

            value = (
                data.get("Value")
                if isinstance(
                    data,
                    dict,
                )
                else data
            )

            set_value(
                result,
                "总连接数",
                value,
            )

        # ==================================
        # Total RTT
        # ==================================
        elif (
            matrix_type
            == "TEST_PING_TOTAL_RTT"
        ):

            value = (
                data.get("Value")
                if isinstance(
                    data,
                    dict,
                )
                else data
            )

            set_value(
                result,
                "总RTT",
                value,
                format_rtt(value),
            )

        # ==================================
        # Average Speed
        # ==================================
        elif (
            matrix_type
            == "SPEED_AVERAGE"
        ):

            value = (
                data.get("Value")
                if isinstance(
                    data,
                    dict,
                )
                else data
            )

            set_value(
                result,
                "平均速度",
                value,
                format_speed(value),
            )

        # ==================================
        # Max Speed
        # ==================================
        elif (
            matrix_type
            == "SPEED_MAX"
        ):

            value = (
                data.get("Value")
                if isinstance(
                    data,
                    dict,
                )
                else data
            )

            set_value(
                result,
                "最大速度",
                value,
                format_speed(value),
            )

        # ==================================
        # Per Second Speed
        # ==================================
        elif (
            matrix_type
            == "SPEED_PER_SECOND"
        ):

            if not isinstance(
                data,
                dict,
            ):
                continue

            speeds = (
                data.get(
                    "Speeds"
                )
                or []
            )

            average = data.get(
                "Average"
            )

            maximum = data.get(
                "Max"
            )

            set_value(
                result,
                "平均速度",
                average,
                format_speed(
                    average
                ),
            )

            set_value(
                result,
                "最大速度",
                maximum,
                format_speed(
                    maximum
                ),
            )

            set_value(
                result,
                "每秒速度",
                speeds,
                [
                    format_speed(
                        value
                    )
                    for value in speeds
                ],
            )

        # ==================================
        # UDP
        # ==================================
        elif matrix_type == "UDP_TYPE":

            if isinstance(
                data,
                dict,
            ):

                value = (
                    data.get("Value")
                    or data.get("Text")
                )

            else:

                value = data

            set_value(
                result,
                "UDP类型",
                value,
            )

        # ==================================
        # GeoIP
        # ==================================
        elif (
            matrix_type
            == "GEOIP_INBOUND"
        ):

            set_value(
                result,
                "入口GeoIP",
                data,
            )

        elif (
            matrix_type
            == "GEOIP_OUTBOUND"
        ):

            set_value(
                result,
                "出口GeoIP",
                data,
            )

        # ==================================
        # Script
        # ==================================
        elif (
            matrix_type
            == "TEST_SCRIPT"
        ):

            if not isinstance(
                data,
                dict,
            ):
                continue

            key = data.get(
                "Key"
            )

            text = data.get(
                "Text"
            )

            if key:

                set_value(
                    result,
                    str(key),
                    text,
                )

    result.available = bool(
        result.values
    )

    return result


def results_to_table(
    results: list[TestResult],
) -> TableResult:

    columns = [
        "序号",
        "节点名称",
        "类型",
    ]

    dynamic_columns = []

    for result in results:

        for column in result.values:

            if column not in dynamic_columns:

                dynamic_columns.append(
                    column
                )

    columns.extend(
        dynamic_columns
    )

    rows = []

    for index, result in enumerate(
        results,
        start=1,
    ):

        row = {
            "序号": index,

            "节点名称":
                result.node.name,

            "类型":
                format_proxy_type(
                    result.node.type
                ),
        }

        for column in dynamic_columns:

            cell = result.values.get(
                column
            )

            row[column] = (
                cell.display
                if cell
                else "-"
            )

        rows.append(
            row
        )

    return TableResult(
        columns=columns,
        rows=rows,
        results=results,
    )


class ResultCleaner:

    def __init__(
        self,
        results: list[TestResult],
    ):
        self.results = results

    def sort(
        self,
        sort_by: str = "订阅原序",
        reverse: bool = False,
    ):

        if sort_by == "订阅原序":

            self.results.sort(
                key=lambda x: x.node.index
            )

            return

        def sort_key(
            result: TestResult,
        ):

            cell = result.values.get(
                sort_by
            )

            if cell is None:
                return (
                    1,
                    0,
                )

            value = cell.raw

            if value is None:
                return (
                    1,
                    0,
                )

            try:

                value = float(
                    value
                )

                if (
                    sort_by
                    in {
                        "RTT",
                        "MAX RTT",
                        "RTT标准差",
                        "连接标准差",
                        "HTTPS延迟",
                        "总RTT",
                    }
                    and value <= 0
                ):
                    return (
                        1,
                        0,
                    )

                return (
                    0,
                    value,
                )

            except (
                TypeError,
                ValueError,
            ):

                return (
                    0,
                    str(value),
                )

        self.results.sort(
            key=sort_key,
            reverse=reverse,
        )

    def calculate_statistics(
        self,
    ) -> dict[str, Any]:

        rtts = []

        avg_speeds = []

        max_speeds = []

        traffic_bytes = 0

        available = 0

        for result in self.results:

            if result.available:
                available += 1

            rtt = result.values.get(
                "RTT"
            )

            if rtt:

                try:

                    value = float(
                        rtt.raw
                    )

                    if value > 0:
                        rtts.append(
                            value
                        )

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            average = (
                result.values.get(
                    "平均速度"
                )
            )

            if average:

                try:

                    avg_speeds.append(
                        float(
                            average.raw
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            maximum = (
                result.values.get(
                    "最大速度"
                )
            )

            if maximum:

                try:

                    max_speeds.append(
                        float(
                            maximum.raw
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            every_second = (
                result.values.get(
                    "每秒速度"
                )
            )

            if every_second:

                values = every_second.raw

                if isinstance(
                    values,
                    list,
                ):

                    for value in values:

                        try:

                            traffic_bytes += float(
                                value
                            )

                        except (
                            TypeError,
                            ValueError,
                        ):
                            pass

        total = len(
            self.results
        )

        return {
            "total": total,

            "available": available,

            "failed": (
                total
                - available
            ),

            "rtt_average": (
                sum(rtts)
                / len(rtts)
                if rtts
                else None
            ),

            "rtt_min": (
                min(rtts)
                if rtts
                else None
            ),

            "rtt_max": (
                max(rtts)
                if rtts
                else None
            ),

            "speed_average": (
                sum(avg_speeds)
                / len(avg_speeds)
                if avg_speeds
                else None
            ),

            "speed_max": (
                max(max_speeds)
                if max_speeds
                else None
            ),

            "traffic_bytes":
                traffic_bytes,

            "traffic_mb":
                traffic_bytes
                / 1024
                / 1024,
        }

    def clean(
        self,
        sort_by: str = "订阅原序",
        reverse: bool = False,
    ) -> TableResult:

        self.sort(
            sort_by,
            reverse,
        )

        table = results_to_table(
            self.results
        )

        table.statistics = (
            self.calculate_statistics()
        )

        return table