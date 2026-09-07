# renderer.py

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from models import Cell, TableResult, TestResult


RESULT_DIR = Path("results")


# ============================================================
# 颜色
# ============================================================

BACKGROUND = "#FFFFFF"
HEADER_BACKGROUND = "#EAEAEA"
BORDER_COLOR = "#D5D5D5"

TEXT_COLOR = "#222222"
SECONDARY_TEXT_COLOR = "#666666"

RTT_GOOD = "#BEE47E"
RTT_NORMAL = "#FCC43C"
RTT_BAD = "#EE6B73"
RTT_UNKNOWN = "#8D8B8E"

SPEED_LOW = "#FAE0E4"
SPEED_MEDIUM = "#FF85A1"
SPEED_HIGH = "#FF477E"

# 折线图
CHART_LINE_COLOR = "#FF477E"
CHART_POINT_COLOR = "#FF477E"
CHART_GRID_COLOR = "#E5E5E5"
CHART_AVG_COLOR = "#999999"
CHART_MAX_COLOR = "#FF85A1"


# ============================================================
# 尺寸
# ============================================================

ROW_HEIGHT = 64
HEADER_HEIGHT = 64
TITLE_HEIGHT = 72
FOOTER_HEIGHT = 72

PADDING_X = 12

SMALL_FONT_SIZE = 14
TITLE_FONT_SIZE = 30

# 每秒速度折线图
CHART_PADDING_LEFT = 30
CHART_PADDING_RIGHT = 8
CHART_PADDING_TOP = 8
CHART_PADDING_BOTTOM = 12

# 固定列宽
COLUMN_WIDTHS = {
    "序号": 70,
    "节点名称": 360,
    "类型": 140,

    "RTT": 130,
    "RTT标准差": 130,
    "MAX RTT": 130,
    "连接标准差": 130,
    "HTTPS延迟": 140,
    "HTTP(S)延迟": 140,
    "TLS RTT": 130,
    "总RTT": 130,
    "总连接数": 130,
    "HTTP状态码": 130,

    "平均速度": 150,
    "最大速度": 150,

    "每秒速度": 500,

    "UDP类型": 160,
    "入口GeoIP": 160,
    "出口GeoIP": 160,
}


# ============================================================
# 字体
# ============================================================

def load_font(
    size: int,
    bold: bool = False,
):
    candidates = []

    if bold:
        candidates.extend([
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.otf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ])
    else:
        candidates.extend([
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ])

    # Windows
    if bold:
        candidates.extend([
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ])
    else:
        candidates.extend([
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ])

    for path in candidates:
        try:
            return ImageFont.truetype(
                path,
                size=size,
            )
        except Exception:
            continue

    return ImageFont.load_default()


SMALL_FONT = load_font(
    SMALL_FONT_SIZE
)

TITLE_FONT = load_font(
    TITLE_FONT_SIZE,
    bold=True,
)


# ============================================================
# 工具
# ============================================================

def safe_str(
    value: Any,
) -> str:

    if value is None:
        return "-"

    if isinstance(value, str):
        return value

    return str(value)


def get_value(
    cell: Cell | Any,
) -> Any:

    if isinstance(cell, Cell):
        return cell.raw

    return cell


def get_display_value(
    cell: Cell | Any,
) -> Any:

    if isinstance(cell, Cell):
        return cell.display

    return cell


def numeric_value(
    value: Any,
) -> float | None:

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(
        value,
        (int, float),
    ):
        number = float(value)

        if math.isfinite(number):
            return number

        return None

    try:

        text = str(
            value
        ).strip()

        if not text:
            return None

        for suffix in (
            "MB/s",
            "MiB/s",
            "KB/s",
            "KiB/s",
            "B/s",
            "MB",
            "MiB",
            "KB",
            "KiB",
            "B",
            "ms",
        ):
            if text.endswith(suffix):
                text = text[
                    :-len(suffix)
                ].strip()
                break

        number = float(text)

        if math.isfinite(number):
            return number

    except Exception:
        pass

    return None


def human_size(
    value: float | int | None,
) -> str:

    if value is None:
        return "-"

    value = float(
        value
    )

    if value < 1024:
        return f"{value:.0f}B"

    value /= 1024

    if value < 1024:
        return f"{value:.2f}KB"

    value /= 1024

    if value < 1024:
        return f"{value:.2f}MB"

    value /= 1024

    return f"{value:.2f}GB"


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    font,
) -> str:

    text = safe_str(
        text
    )

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    if (
        bbox[2] - bbox[0]
        <= max_width
    ):
        return text

    ellipsis = "..."
    current = ""

    for char in text:

        candidate = (
            current
            + char
            + ellipsis
        )

        bbox = draw.textbbox(
            (0, 0),
            candidate,
            font=font,
        )

        if (
            bbox[2] - bbox[0]
            > max_width
        ):
            break

        current += char

    return current + ellipsis


def centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font,
    fill=TEXT_COLOR,
):

    x1, y1, x2, y2 = box

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    text_width = (
        bbox[2] - bbox[0]
    )

    text_height = (
        bbox[3] - bbox[1]
    )

    x = (
        x1
        + (
            x2 - x1 - text_width
        ) / 2
    )

    y = (
        y1
        + (
            y2 - y1 - text_height
        ) / 2
        - bbox[1]
    )

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
    )


# ============================================================
# 颜色
# ============================================================

def rtt_background(
    value: Any,
) -> str:

    number = numeric_value(
        value
    )

    if number is None:
        return RTT_UNKNOWN

    if number <= 100:
        return RTT_GOOD

    if number <= 300:
        return RTT_NORMAL

    return RTT_BAD


def speed_background(
    value: Any,
) -> str:

    number = numeric_value(
        value
    )

    if number is None:
        return BACKGROUND

    if number < 1024 * 1024:
        return SPEED_LOW

    if number < 10 * 1024 * 1024:
        return SPEED_MEDIUM

    return SPEED_HIGH


# ============================================================
# Renderer
# ============================================================

class ResultRenderer:

    def __init__(
        self,
        output_dir: str | Path = RESULT_DIR,
    ):

        self.output_dir = Path(
            output_dir
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # 输出文件名：日期命名
        self.report_id = (
            datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
        )

    # ========================================================
    # 列宽
    # ========================================================

    def get_column_widths(
        self,
        columns: list[str],
    ) -> list[int]:

        return [
            COLUMN_WIDTHS.get(
                column,
                160,
            )
            for column in columns
        ]

    # ========================================================
    # 统计
    # ========================================================

    def get_statistics(
        self,
        table: TableResult,
    ) -> dict[str, Any]:

        total = len(
            table.results
        )

        available = sum(
            1
            for result
            in table.results
            if result.available
        )

        failed = (
            total
            - available
        )

        rtts = []
        avg_speeds = []
        max_speeds = []

        for result in table.results:

            cell = result.values.get(
                "RTT"
            )

            if cell is not None:

                number = numeric_value(
                    get_value(cell)
                )

                if number is not None:
                    rtts.append(
                        number
                    )

            cell = result.values.get(
                "平均速度"
            )

            if cell is not None:

                number = numeric_value(
                    get_value(cell)
                )

                if number is not None:
                    avg_speeds.append(
                        number
                    )

            cell = result.values.get(
                "最大速度"
            )

            if cell is not None:

                number = numeric_value(
                    get_value(cell)
                )

                if number is not None:
                    max_speeds.append(
                        number
                    )

        statistics = {
            "total": total,
            "available": available,
            "failed": failed,
        }

        if rtts:

            statistics["avg_rtt"] = (
                sum(rtts)
                / len(rtts)
            )

            statistics["min_rtt"] = min(
                rtts
            )

            statistics["max_rtt"] = max(
                rtts
            )

        if avg_speeds:

            statistics["avg_speed"] = (
                sum(avg_speeds)
                / len(avg_speeds)
            )

        if max_speeds:

            statistics["max_speed"] = max(
                max_speeds
            )

        # 保留 ResultCleaner 的统计
        if table.statistics:

            for key, value in (
                table.statistics.items()
            ):

                statistics.setdefault(
                    key,
                    value,
                )

        return statistics

    # ========================================================
    # 标题
    # ========================================================

    def draw_title(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        statistics: dict[str, Any],
    ):

        draw.rectangle(
            (
                0,
                0,
                width,
                TITLE_HEIGHT,
            ),
            fill=BACKGROUND,
        )

        draw.text(
            (
                PADDING_X,
                18,
            ),
            "MiaoSpeed 节点测速",
            font=TITLE_FONT,
            fill=TEXT_COLOR,
        )

        total = statistics.get(
            "total",
            0,
        )

        available = statistics.get(
            "available",
            0,
        )

        failed = statistics.get(
            "failed",
            0,
        )

        summary = (
            f"节点 {total}    "
            f"成功 {available}    "
            f"失败 {failed}"
        )

        bbox = draw.textbbox(
            (0, 0),
            summary,
            font=SMALL_FONT,
        )

        summary_width = (
            bbox[2] - bbox[0]
        )

        draw.text(
            (
                max(
                    PADDING_X,
                    width
                    - summary_width
                    - PADDING_X,
                ),
                28,
            ),
            summary,
            font=SMALL_FONT,
            fill=SECONDARY_TEXT_COLOR,
        )

    # ========================================================
    # 表头
    # ========================================================

    def draw_header(
        self,
        draw: ImageDraw.ImageDraw,
        columns: list[str],
        widths: list[int],
        y: int,
    ):

        x = 0

        for column, width in zip(
            columns,
            widths,
        ):

            x2 = (
                x + width
            )

            draw.rectangle(
                (
                    x,
                    y,
                    x2,
                    y + HEADER_HEIGHT,
                ),
                fill=HEADER_BACKGROUND,
                outline=BORDER_COLOR,
                width=1,
            )

            centered_text(
                draw,
                (
                    x,
                    y,
                    x2,
                    y + HEADER_HEIGHT,
                ),
                column,
                font=SMALL_FONT,
            )

            x = x2

    # ========================================================
    # 普通单元格
    # ========================================================

    def draw_normal_cell(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        value: Any,
        *,
        background: str = BACKGROUND,
        font=None,
        fill=TEXT_COLOR,
    ):

        x1, y1, x2, y2 = box

        draw.rectangle(
            box,
            fill=background,
            outline=BORDER_COLOR,
            width=1,
        )

        if font is None:
            font = SMALL_FONT

        text = fit_text(
            draw,
            safe_str(value),
            max_width=max(
                10,
                x2 - x1 - 16,
            ),
            font=font,
        )

        centered_text(
            draw,
            box,
            text,
            font=font,
            fill=fill,
        )

    # ========================================================
    # RTT 单元格
    # ========================================================

    def draw_rtt_cell(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        value: Any,
    ):

        draw.rectangle(
            box,
            fill=rtt_background(
                value
            ),
            outline=BORDER_COLOR,
            width=1,
        )

        centered_text(
            draw,
            box,
            safe_str(value),
            font=SMALL_FONT,
        )

    # ========================================================
    # 提取每秒速度
    # ========================================================

    def extract_speed_values(
        self,
        result: TestResult,
    ) -> list[float]:

        cell = result.values.get(
            "每秒速度"
        )

        if cell is None:
            cell = result.values.get(
                "SPEED_PER_SECOND"
            )

        if cell is None:
            return []

        raw = get_value(
            cell
        )

        if raw is None:
            return []

        if isinstance(
            raw,
            dict,
        ):

            raw = (
                raw.get("Speeds")
                or raw.get("speeds")
                or raw.get("Speed")
                or raw.get("speed")
                or []
            )

        if not isinstance(
            raw,
            (list, tuple),
        ):
            return []

        values = []

        for item in raw:

            number = numeric_value(
                item
            )

            if number is not None:
                values.append(
                    number
                )

        return values

    # ========================================================
    # 每秒速度折线图
    # ========================================================

    def draw_speed_chart(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        result: TestResult,
    ):

        x1, y1, x2, y2 = box

        draw.rectangle(
            box,
            fill=BACKGROUND,
            outline=BORDER_COLOR,
            width=1,
        )

        values = (
            self.extract_speed_values(
                result
            )
        )

        if not values:

            centered_text(
                draw,
                box,
                "-",
                font=SMALL_FONT,
                fill=SECONDARY_TEXT_COLOR,
            )

            return

        # ====================================================
        # 图表区域
        # ====================================================

        chart_left = (
            x1
            + CHART_PADDING_LEFT
        )

        chart_right = (
            x2
            - CHART_PADDING_RIGHT
        )

        chart_top = (
            y1
            + CHART_PADDING_TOP
        )

        chart_bottom = (
            y2
            - CHART_PADDING_BOTTOM
        )

        chart_width = (
            chart_right
            - chart_left
        )

        chart_height = (
            chart_bottom
            - chart_top
        )

        if (
            chart_width <= 10
            or chart_height <= 10
        ):
            return

        # ====================================================
        # 数据范围
        # ====================================================

        data_min = min(
            values
        )

        data_max = max(
            values
        )

        if abs(
            data_max
            - data_min
        ) < 1e-9:

            margin = max(
                data_max * 0.05,
                1,
            )

            data_min -= margin
            data_max += margin

        data_range = (
            data_max
            - data_min
        )

        data_min -= (
            data_range * 0.08
        )

        data_max += (
            data_range * 0.08
        )

        # ====================================================
        # 网格
        # ====================================================

        middle_y = (
            chart_top
            + chart_height / 2
        )

        draw.line(
            (
                chart_left,
                middle_y,
                chart_right,
                middle_y,
            ),
            fill=CHART_GRID_COLOR,
            width=1,
        )

        draw.line(
            (
                chart_left,
                chart_bottom,
                chart_right,
                chart_bottom,
            ),
            fill=CHART_GRID_COLOR,
            width=1,
        )

        # ====================================================
        # 平均速度线
        # ====================================================

        average = (
            sum(values)
            / len(values)
        )

        average_ratio = (
            (average - data_min)
            / (data_max - data_min)
        )

        average_ratio = max(
            0.0,
            min(
                1.0,
                average_ratio,
            ),
        )

        average_y = (
            chart_bottom
            - average_ratio
            * chart_height
        )

        dash = 4
        gap = 4
        current_x = chart_left

        while current_x < chart_right:

            end_x = min(
                current_x + dash,
                chart_right,
            )

            draw.line(
                (
                    current_x,
                    average_y,
                    end_x,
                    average_y,
                ),
                fill=CHART_AVG_COLOR,
                width=1,
            )

            current_x += (
                dash + gap
            )

        # ====================================================
        # 最大值线
        # ====================================================

        actual_max = max(
            values
        )

        max_ratio = (
            (actual_max - data_min)
            / (data_max - data_min)
        )

        max_ratio = max(
            0.0,
            min(
                1.0,
                max_ratio,
            ),
        )

        max_y = (
            chart_bottom
            - max_ratio
            * chart_height
        )

        draw.line(
            (
                chart_left,
                max_y,
                chart_right,
                max_y,
            ),
            fill=CHART_MAX_COLOR,
            width=1,
        )

        # ====================================================
        # 折线点
        # ====================================================

        points = []

        count = len(
            values
        )

        if count == 1:

            px = (
                chart_left
                + chart_width / 2
            )

            ratio = (
                (values[0] - data_min)
                / (data_max - data_min)
            )

            ratio = max(
                0.0,
                min(
                    1.0,
                    ratio,
                ),
            )

            py = (
                chart_bottom
                - ratio
                * chart_height
            )

            points.append(
                (px, py)
            )

        else:

            for index, value in enumerate(
                values
            ):

                px = (
                    chart_left
                    + (
                        index
                        / (count - 1)
                    )
                    * chart_width
                )

                ratio = (
                    (value - data_min)
                    / (data_max - data_min)
                )

                ratio = max(
                    0.0,
                    min(
                        1.0,
                        ratio,
                    ),
                )

                py = (
                    chart_bottom
                    - ratio
                    * chart_height
                )

                points.append(
                    (px, py)
                )

        # ====================================================
        # 折线
        # ====================================================

        if len(points) >= 2:

            draw.line(
                points,
                fill=CHART_LINE_COLOR,
                width=2,
                joint="curve",
            )

        # ====================================================
        # 数据点
        # ====================================================

        radius = 2

        for px, py in points:

            draw.ellipse(
                (
                    px - radius,
                    py - radius,
                    px + radius,
                    py + radius,
                ),
                fill=CHART_POINT_COLOR,
                outline=BACKGROUND,
                width=1,
            )

        # ====================================================
        # 平均速度文字
        # ====================================================

        label_font = load_font(9)

        draw.text(
            (
                x1 + 5,
                y1 + 2,
            ),
            human_size(
                average
            ),
            font=label_font,
            fill=SECONDARY_TEXT_COLOR,
        )

        # ====================================================
        # 时间轴
        # ====================================================

        draw.text(
            (
                chart_left - 4,
                chart_bottom + 1,
            ),
            "1",
            font=label_font,
            fill=SECONDARY_TEXT_COLOR,
        )

        if count > 1:

            last_text = str(
                count
            )

            bbox = draw.textbbox(
                (0, 0),
                last_text,
                font=label_font,
            )

            text_width = (
                bbox[2]
                - bbox[0]
            )

            draw.text(
                (
                    chart_right
                    - text_width,
                    chart_bottom + 1,
                ),
                last_text,
                font=label_font,
                fill=SECONDARY_TEXT_COLOR,
            )

    # ========================================================
    # 行
    # ========================================================

    def draw_row(
        self,
        draw: ImageDraw.ImageDraw,
        result: TestResult,
        columns: list[str],
        widths: list[int],
        y: int,
    ):

        x = 0

        for column, width in zip(
            columns,
            widths,
        ):

            x2 = (
                x + width
            )

            box = (
                x,
                y,
                x2,
                y + ROW_HEIGHT,
            )

            # ------------------------------------------------
            # 序号
            # ------------------------------------------------

            if column == "序号":

                self.draw_normal_cell(
                    draw,
                    box,
                    result.node.index,
                    font=SMALL_FONT,
                )

            # ------------------------------------------------
            # 节点名称
            # ------------------------------------------------

            elif column == "节点名称":

                self.draw_normal_cell(
                    draw,
                    box,
                    result.node.name,
                    font=SMALL_FONT,
                )

            # ------------------------------------------------
            # 类型
            # ------------------------------------------------

            elif column == "类型":

                self.draw_normal_cell(
                    draw,
                    box,
                    result.node.type,
                    font=SMALL_FONT,
                )

            # ------------------------------------------------
            # 每秒速度
            # ------------------------------------------------

            elif column == "每秒速度":

                self.draw_speed_chart(
                    draw,
                    box,
                    result,
                )

            # ------------------------------------------------
            # RTT
            # ------------------------------------------------

            elif column in {
                "RTT",
                "RTT标准差",
                "MAX RTT",
                "连接标准差",
                "HTTPS延迟",
                "HTTP(S)延迟",
                "TLS RTT",
                "总RTT",
            }:

                cell = (
                    result.values.get(
                        column
                    )
                )

                if cell is None:
                    value = "-"
                else:
                    value = get_display_value(
                        cell
                    )

                self.draw_rtt_cell(
                    draw,
                    box,
                    value,
                )

            # ------------------------------------------------
            # 平均速度
            # ------------------------------------------------

            elif column == "平均速度":

                cell = (
                    result.values.get(
                        column
                    )
                )

                if cell is None:

                    display = "-"
                    raw = None

                else:

                    display = (
                        get_display_value(
                            cell
                        )
                    )

                    raw = get_value(
                        cell
                    )

                self.draw_normal_cell(
                    draw,
                    box,
                    display,
                    background=speed_background(
                        raw
                    ),
                    font=SMALL_FONT,
                )

            # ------------------------------------------------
            # 最大速度
            # ------------------------------------------------

            elif column == "最大速度":

                cell = (
                    result.values.get(
                        column
                    )
                )

                if cell is None:

                    display = "-"
                    raw = None

                else:

                    display = (
                        get_display_value(
                            cell
                        )
                    )

                    raw = get_value(
                        cell
                    )

                self.draw_normal_cell(
                    draw,
                    box,
                    display,
                    background=speed_background(
                        raw
                    ),
                    font=SMALL_FONT,
                )

            # ------------------------------------------------
            # 其他
            # ------------------------------------------------

            else:

                cell = (
                    result.values.get(
                        column
                    )
                )

                if cell is None:
                    value = "-"
                else:
                    value = get_display_value(
                        cell
                    )

                self.draw_normal_cell(
                    draw,
                    box,
                    value,
                    font=SMALL_FONT,
                )

            x = x2

    # ========================================================
    # Footer
    # ========================================================

    def draw_footer(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        statistics: dict[str, Any],
    ):

        y = (
            height
            - FOOTER_HEIGHT
        )

        draw.line(
            (
                0,
                y,
                width,
                y,
            ),
            fill=BORDER_COLOR,
            width=1,
        )

        parts = []

        total = statistics.get(
            "total"
        )

        if total is not None:
            parts.append(
                f"节点: {total}"
            )

        available = statistics.get(
            "available"
        )

        if available is not None:
            parts.append(
                f"成功: {available}"
            )

        failed = statistics.get(
            "failed"
        )

        if failed is not None:
            parts.append(
                f"失败: {failed}"
            )

        avg_rtt = statistics.get(
            "avg_rtt"
        )

        if avg_rtt is not None:
            parts.append(
                f"平均 RTT: {avg_rtt:.0f}ms"
            )

        avg_speed = statistics.get(
            "avg_speed"
        )

        if avg_speed is not None:
            parts.append(
                "平均速度: "
                f"{human_size(avg_speed)}/s"
            )

        footer_text = "    ".join(
            parts
        )

        draw.text(
            (
                PADDING_X,
                y + 25,
            ),
            footer_text,
            font=SMALL_FONT,
            fill=SECONDARY_TEXT_COLOR,
        )

    # ========================================================
    # Render
    # ========================================================

    def render(
        self,
        table: TableResult,
    ) -> Path:

        columns = table.columns

        if not columns:

            columns = [
                "序号",
                "节点名称",
                "类型",
            ]

        widths = (
            self.get_column_widths(
                columns
            )
        )

        width = sum(
            widths
        )

        statistics = (
            self.get_statistics(
                table
            )
        )

        height = (
            TITLE_HEIGHT
            + HEADER_HEIGHT
            + ROW_HEIGHT
            * len(table.results)
            + FOOTER_HEIGHT
        )

        image = Image.new(
            "RGB",
            (
                width,
                height,
            ),
            BACKGROUND,
        )

        draw = ImageDraw.Draw(
            image
        )

        # 标题
        self.draw_title(
            draw,
            width,
            statistics,
        )

        # 表头
        self.draw_header(
            draw,
            columns,
            widths,
            TITLE_HEIGHT,
        )

        # 数据行
        y = (
            TITLE_HEIGHT
            + HEADER_HEIGHT
        )

        for result in table.results:

            self.draw_row(
                draw,
                result,
                columns,
                widths,
                y,
            )

            y += ROW_HEIGHT

        # Footer
        self.draw_footer(
            draw,
            width,
            height,
            statistics,
        )

        # PNG
        output_path = (
            self.output_dir
            / f"{self.report_id}.png"
        )

        image.save(
            output_path,
            format="PNG",
        )

        return output_path

    # ========================================================
    # JSON
    # ========================================================

    def save_json(
        self,
        table: TableResult,
    ) -> Path:

        data = {
            "columns": table.columns,
            "rows": table.rows,
            "statistics": table.statistics,
            "results": [],
        }

        for result in table.results:

            result_data = {
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

                "available":
                    result.available,

                "error":
                    result.error,

                "invoke_duration":
                    result.invoke_duration,

                "values": {},
            }

            for key, cell in (
                result.values.items()
            ):

                result_data[
                    "values"
                ][key] = {
                    "raw":
                        get_value(cell),

                    "display":
                        get_display_value(cell),
                }

            data[
                "results"
            ].append(
                result_data
            )

        output_path = (
            self.output_dir
            / f"{self.report_id}.json"
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

        return output_path