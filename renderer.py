from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from models import TableResult, TestResult


# ============================================================
# 基础配置
# ============================================================

RESULT_DIR = Path("results")

BACKGROUND = "#FFFFFF"
HEADER_BACKGROUND = "#EAEAEA"
BORDER_COLOR = "#D5D5D5"

TEXT_COLOR = "#222222"
SECONDARY_TEXT_COLOR = "#555555"

# RTT
RTT_GOOD = "#BEE47E"
RTT_NORMAL = "#FCC43C"
RTT_BAD = "#EE6B73"
RTT_UNKNOWN = "#8D8B8E"

# Speed
SPEED_LOW = "#FAE0E4"
SPEED_MEDIUM = "#FF85A1"
SPEED_HIGH = "#FF477E"


# ============================================================
# 尺寸
# ============================================================

ROW_HEIGHT = 56
HEADER_HEIGHT = 64
TITLE_HEIGHT = 70
FOOTER_HEIGHT = 70

PADDING_X = 12

# 普通字体
FONT_SIZE = 22

# 小字体
SMALL_FONT_SIZE = 14

# 最小字体
MIN_SPEED_FONT_SIZE = 8

TITLE_FONT_SIZE = 30


# ============================================================
# 列宽
# ============================================================

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

    # 整个“每秒速度”区域
    "每秒速度": 500,

    "UDP类型": 160,

    "入口GeoIP": 160,

    "出口GeoIP": 160,
}


# ============================================================
# 字体
# ============================================================

def load_font(size: int):

    candidates = [

        # Windows
        Path(
            "C:/Windows/Fonts/msyh.ttc"
        ),

        Path(
            "C:/Windows/Fonts/msyhbd.ttc"
        ),

        Path(
            "C:/Windows/Fonts/simhei.ttf"
        ),

        # Linux
        Path(
            "/usr/share/fonts/opentype/noto/"
            "NotoSansCJK-Regular.ttc"
        ),

        Path(
            "/usr/share/fonts/opentype/noto/"
            "NotoSansCJK-Regular.otf"
        ),

        Path(
            "/usr/share/fonts/truetype/wqy/"
            "wqy-zenhei.ttc"
        ),
    ]

    for path in candidates:

        if not path.exists():
            continue

        try:

            return ImageFont.truetype(
                str(path),
                size,
            )

        except OSError:

            continue

    print(
        "警告：未找到中文字体，"
        "PNG 中中文可能无法正常显示。"
    )

    return ImageFont.load_default()


# ============================================================
# 文本
# ============================================================

def value_to_text(
    value: Any,
) -> str:

    if value is None:
        return "-"

    if isinstance(
        value,
        list,
    ):

        return " ".join(
            str(x)
            for x in value
        )

    return str(value)


def text_width(
    draw: ImageDraw.ImageDraw,
    text: Any,
    font,
) -> int:

    bbox = draw.textbbox(
        (0, 0),
        str(text),
        font=font,
    )

    return (
        bbox[2]
        - bbox[0]
    )


# ============================================================
# 速度格式化
# ============================================================

def format_speed_text(
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

    if value < 0:
        return "-"

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
        "PB",
    ]

    index = 0

    while (
        value >= 1024
        and index < len(units) - 1
    ):

        value /= 1024
        index += 1

    return (
        f"{value:.2f}"
        f"{units[index]}"
    )


# ============================================================
# RTT颜色
# ============================================================

def rtt_color(
    value: Any,
) -> str:

    try:

        value = float(value)

    except (
        TypeError,
        ValueError,
    ):

        return RTT_UNKNOWN

    if value <= 0:
        return RTT_UNKNOWN

    if value <= 50:
        return RTT_GOOD

    if value <= 200:
        return RTT_NORMAL

    return RTT_BAD


# ============================================================
# Speed颜色
# ============================================================

def speed_color(
    value: Any,
    max_speed: float,
) -> str:

    try:

        value = float(value)

    except (
        TypeError,
        ValueError,
    ):

        return SPEED_LOW

    if value <= 0:
        return SPEED_LOW

    if max_speed <= 0:
        return SPEED_LOW

    ratio = value / max_speed

    if ratio >= 0.8:
        return SPEED_HIGH

    if ratio >= 0.4:
        return SPEED_MEDIUM

    return SPEED_LOW


# ============================================================
# Renderer
# ============================================================

class ResultRenderer:

    def __init__(
        self,
        table: TableResult,
        title: str = "MiaoSpeed 节点测速",
        result_dir: str | Path = RESULT_DIR,
        report_id: str | None = None,
    ):

        self.table = table

        self.title = title

        self.result_dir = Path(
            result_dir
        )

        self.result_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # 同一次报告 PNG / JSON 使用同一个 ID
        self.report_id = (
            report_id
            or datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
        )

        self.font = load_font(
            FONT_SIZE
        )

        self.small_font = load_font(
            SMALL_FONT_SIZE
        )

        self.title_font = load_font(
            TITLE_FONT_SIZE
        )

    # ========================================================
    # 统计
    # ========================================================

    def get_statistics(
        self,
    ) -> dict[str, Any]:

        results = self.table.results

        total = len(results)

        available = sum(
            1
            for result in results
            if result.available
        )

        failed = (
            total
            - available
        )

        rtts = []

        average_speeds = []

        max_speeds = []

        traffic_bytes = 0.0

        for result in results:

            # ----------------------
            # RTT
            # ----------------------

            rtt = result.values.get(
                "RTT"
            )

            if rtt is not None:

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

            # ----------------------
            # Average Speed
            # ----------------------

            average = result.values.get(
                "平均速度"
            )

            if average is not None:

                try:

                    average_speeds.append(
                        float(
                            average.raw
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    pass

            # ----------------------
            # Max Speed
            # ----------------------

            maximum = result.values.get(
                "最大速度"
            )

            if maximum is not None:

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

            # ----------------------
            # Traffic
            # ----------------------

            per_second = result.values.get(
                "每秒速度"
            )

            if per_second is not None:

                values = per_second.raw

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

        return {
            "total":
                total,

            "available":
                available,

            "failed":
                failed,

            "rtt_average": (
                sum(rtts) / len(rtts)
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
                sum(average_speeds)
                / len(average_speeds)
                if average_speeds
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

    # ========================================================
    # 列宽
    # ========================================================

    def get_column_widths(
        self,
        draw,
    ) -> list[int]:

        widths = []

        for column in self.table.columns:

            # 配置中存在的列
            if column in COLUMN_WIDTHS:

                widths.append(
                    COLUMN_WIDTHS[column]
                )

                continue

            # 动态 Script 测试项
            #
            # Youtube
            # OpenAI
            # Claude
            # Gemini
            #
            widths.append(
                160
            )

        return widths

    # ========================================================
    # 标题
    # ========================================================

    def draw_title(
        self,
        draw,
    ) -> int:

        draw.text(
            (
                PADDING_X,
                16,
            ),
            self.title,
            font=self.title_font,
            fill=TEXT_COLOR,
        )

        statistics = (
            self.table.statistics
            or self.get_statistics()
        )

        summary = (
            f"节点 {statistics.get('total', 0)}"
            f"   "
            f"成功 {statistics.get('available', 0)}"
            f"   "
            f"失败 {statistics.get('failed', 0)}"
        )

        draw.text(
            (
                430,
                25,
            ),
            summary,
            font=self.small_font,
            fill=SECONDARY_TEXT_COLOR,
        )

        return TITLE_HEIGHT

    # ========================================================
    # Header
    # ========================================================

    def draw_header(
        self,
        draw,
        y: int,
        widths: list[int],
    ):

        x = 0

        for index, column in enumerate(
            self.table.columns
        ):

            width = widths[index]

            draw.rectangle(
                (
                    x,
                    y,
                    x + width,
                    y + HEADER_HEIGHT,
                ),
                fill=HEADER_BACKGROUND,
                outline=BORDER_COLOR,
            )

            text = str(
                column
            )

            bbox = draw.textbbox(
                (
                    0,
                    0,
                ),
                text,
                font=self.font,
            )

            tw = (
                bbox[2]
                - bbox[0]
            )

            th = (
                bbox[3]
                - bbox[1]
            )

            draw.text(
                (
                    x
                    + (
                        width
                        - tw
                    )
                    / 2,

                    y
                    + (
                        HEADER_HEIGHT
                        - th
                    )
                    / 2,
                ),
                text,
                font=self.font,
                fill=TEXT_COLOR,
            )

            x += width

    # ========================================================
    # 每秒速度
    #
    # 核心：
    #
    # 整个“每秒速度”列固定 500 px
    #
    # 有 8 个秒：
    #
    # 500 / 8 = 62.5px
    #
    # 每个格子完全相同。
    # ========================================================

    def draw_speed_blocks(
        self,
        draw,
        x: int,
        y: int,
        width: int,
        height: int,
        speeds: list[Any],
    ):

        if not speeds:

            draw.rectangle(
                (
                    x,
                    y,
                    x + width,
                    y + height,
                ),
                fill=BACKGROUND,
                outline=BORDER_COLOR,
            )

            return

        # -------------------------
        # 转换数字
        # -------------------------

        numeric_speeds = []

        for value in speeds:

            try:

                numeric_speeds.append(
                    float(value)
                )

            except (
                TypeError,
                ValueError,
            ):

                numeric_speeds.append(
                    0.0
                )

        count = len(
            numeric_speeds
        )

        # -------------------------
        # 所有速度格子统一宽度
        # -------------------------

        block_width = (
            width / count
        )

        max_speed = max(
            numeric_speeds,
            default=0,
        )

        for index, speed in enumerate(
            numeric_speeds
        ):

            start_x = round(
                x
                + index
                * block_width
            )

            end_x = round(
                x
                + (index + 1)
                * block_width
            )

            actual_width = (
                end_x
                - start_x
            )

            color = speed_color(
                speed,
                max_speed,
            )

            # ---------------------
            # 小格
            # ---------------------

            draw.rectangle(
                (
                    start_x,
                    y,
                    end_x,
                    y + height,
                ),
                fill=color,
                outline=BORDER_COLOR,
            )

            # ---------------------
            # 文本
            # ---------------------

            text = (
                format_speed_text(
                    speed
                )
            )

            # 当前格子自动选择字体大小
            font = self.small_font

            for font_size in range(
                SMALL_FONT_SIZE,
                MIN_SPEED_FONT_SIZE - 1,
                -1,
            ):

                candidate = load_font(
                    font_size
                )

                bbox = draw.textbbox(
                    (
                        0,
                        0,
                    ),
                    text,
                    font=candidate,
                )

                text_width_value = (
                    bbox[2]
                    - bbox[0]
                )

                if (
                    text_width_value
                    <= actual_width - 6
                ):

                    font = candidate

                    break

            bbox = draw.textbbox(
                (
                    0,
                    0,
                ),
                text,
                font=font,
            )

            tw = (
                bbox[2]
                - bbox[0]
            )

            th = (
                bbox[3]
                - bbox[1]
            )

            # 居中
            tx = (
                start_x
                + (
                    actual_width
                    - tw
                )
                / 2
            )

            ty = (
                y
                + (
                    height
                    - th
                )
                / 2
            )

            draw.text(
                (
                    tx,
                    ty,
                ),
                text,
                font=font,
                fill=TEXT_COLOR,
            )

    # ========================================================
    # 普通行
    # ========================================================

    def draw_row(
        self,
        draw,
        y: int,
        widths: list[int],
        row: dict[str, Any],
        result: TestResult,
    ):

        x = 0

        statistics = (
            self.table.statistics
            or self.get_statistics()
        )

        global_max_speed = (
            statistics.get(
                "speed_max"
            )
            or 0
        )

        for index, column in enumerate(
            self.table.columns
        ):

            width = widths[index]

            # =================================================
            # 每秒速度
            # =================================================

            if column == "每秒速度":

                cell = result.values.get(
                    "每秒速度"
                )

                speeds = (
                    cell.raw
                    if cell is not None
                    else []
                )

                if not isinstance(
                    speeds,
                    list,
                ):

                    speeds = []

                self.draw_speed_blocks(
                    draw=draw,

                    x=x,

                    y=y,

                    width=width,

                    height=ROW_HEIGHT,

                    speeds=speeds,
                )

                x += width

                continue

            # =================================================
            # 普通数据
            # =================================================

            value = row.get(
                column,
                "-",
            )

            value_text = (
                value_to_text(
                    value
                )
            )

            background = (
                BACKGROUND
            )

            # =================================================
            # RTT
            # =================================================

            if column in {
                "RTT",
                "MAX RTT",
                "RTT标准差",
                "连接标准差",
                "HTTPS延迟",
                "HTTP(S)延迟",
                "TLS RTT",
                "总RTT",
            }:

                cell = result.values.get(
                    column
                )

                background = (
                    rtt_color(
                        cell.raw
                        if cell is not None
                        else None
                    )
                )

            # =================================================
            # SPEED
            # =================================================

            elif column in {
                "平均速度",
                "最大速度",
            }:

                cell = result.values.get(
                    column
                )

                background = (
                    speed_color(
                        cell.raw
                        if cell is not None
                        else None,
                        global_max_speed,
                    )
                )

            # =================================================
            # 绘制格子
            # =================================================

            draw.rectangle(
                (
                    x,
                    y,
                    x + width,
                    y + ROW_HEIGHT,
                ),
                fill=background,
                outline=BORDER_COLOR,
            )

            # =================================================
            # 文字
            # =================================================

            bbox = draw.textbbox(
                (
                    0,
                    0,
                ),
                value_text,
                font=self.font,
            )

            tw = (
                bbox[2]
                - bbox[0]
            )

            th = (
                bbox[3]
                - bbox[1]
            )

            tx = (
                x
                + (
                    width
                    - tw
                )
                / 2
            )

            ty = (
                y
                + (
                    ROW_HEIGHT
                    - th
                )
                / 2
            )

            draw.text(
                (
                    tx,
                    ty,
                ),
                value_text,
                font=self.font,
                fill=TEXT_COLOR,
            )

            x += width

    # ========================================================
    # Footer
    # ========================================================

    def draw_footer(
        self,
        draw,
        y: int,
    ):

        statistics = (
            self.table.statistics
            or self.get_statistics()
        )

        rtt_average = (
            statistics.get(
                "rtt_average"
            )
        )

        speed_average = (
            statistics.get(
                "speed_average"
            )
        )

        traffic_mb = (
            statistics.get(
                "traffic_mb",
                0,
            )
        )

        if rtt_average is None:

            rtt_text = "-"

        else:

            rtt_text = (
                f"{rtt_average:.1f}ms"
            )

        speed_text = (
            format_speed_text(
                speed_average
            )
            if speed_average is not None
            else "-"
        )

        text = (
            f"平均 RTT: {rtt_text}"
            f"    "
            f"平均速度: {speed_text}"
            f"    "
            f"测试流量: {traffic_mb:.2f}MB"
        )

        draw.text(
            (
                PADDING_X,
                y + 18,
            ),
            text,
            font=self.small_font,
            fill=SECONDARY_TEXT_COLOR,
        )

    # ========================================================
    # Render PNG
    # ========================================================

    def render(
        self,
        filename: str | None = None,
    ) -> Path:

        # -------------------------
        # 临时 Canvas
        # -------------------------

        temp = Image.new(
            "RGB",
            (
                1,
                1,
            ),
            BACKGROUND,
        )

        temp_draw = ImageDraw.Draw(
            temp
        )

        # -------------------------
        # 计算固定列宽
        # -------------------------

        widths = (
            self.get_column_widths(
                temp_draw
            )
        )

        total_width = sum(
            widths
        )

        total_height = (
            TITLE_HEIGHT
            + HEADER_HEIGHT
            + (
                len(
                    self.table.rows
                )
                * ROW_HEIGHT
            )
            + FOOTER_HEIGHT
        )

        # -------------------------
        # 创建画布
        # -------------------------

        image = Image.new(
            "RGB",
            (
                total_width,
                total_height,
            ),
            BACKGROUND,
        )

        draw = ImageDraw.Draw(
            image
        )

        # -------------------------
        # Title
        # -------------------------

        y = self.draw_title(
            draw
        )

        # -------------------------
        # Header
        # -------------------------

        self.draw_header(
            draw,
            y,
            widths,
        )

        y += HEADER_HEIGHT

        # -------------------------
        # Rows
        # -------------------------

        for index, row in enumerate(
            self.table.rows
        ):

            if index >= len(
                self.table.results
            ):
                break

            self.draw_row(
                draw=draw,
                y=y,
                widths=widths,
                row=row,
                result=self.table.results[
                    index
                ],
            )

            y += ROW_HEIGHT

        # -------------------------
        # Footer
        # -------------------------

        self.draw_footer(
            draw,
            y,
        )

        # -------------------------
        # 保存
        # -------------------------

        filename = (
            filename
            or f"{self.report_id}.png"
        )

        output_path = (
            self.result_dir
            / filename
        )

        image.save(
            output_path,
            format="PNG",
        )

        return output_path

    # ========================================================
    # Save JSON
    # ========================================================

    def save_json(
        self,
        filename: str | None = None,
    ) -> Path:

        filename = (
            filename
            or f"{self.report_id}.json"
        )

        output_path = (
            self.result_dir
            / filename
        )

        statistics = (
            self.table.statistics
            or self.get_statistics()
        )

        data = {
            "columns":
                self.table.columns,

            "rows":
                self.table.rows,

            "statistics":
                statistics,
        }

        import json

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )

        return output_path