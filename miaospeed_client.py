from __future__ import annotations

import os
import sys
from pathlib import Path

import aiohttp
import miaospeedlib as m

from clash import proxy_to_yaml
from config import MIAOSPEED_CONFIG
from models import Node, TestItem
from tests import build_matrices


# ============================================================
# 路径
# ============================================================

def _resource_path(relative_path: str) -> Path:
    """获取资源文件路径，兼容 PyInstaller 打包。"""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parent / relative_path


SCRIPT_DIR = _resource_path("scripts/builtin")

# 单个脚本最大执行时间：
# 这里给 30 秒，避免某个脚本异常时无限等待。
SCRIPT_TIMEOUT_MILLIS = 30_000


class MiaoSpeedClient:

    def __init__(self):

        self.config = MIAOSPEED_CONFIG

    # ========================================================
    # Script
    # ========================================================

    def _find_script_file(
        self,
        script_name: str,
    ) -> Path:
        """
        根据脚本名称查找 scripts/builtin 下的 JS 文件。

        例如：

            Youtube  -> youtube.js
            Claude   -> Claude.js
            OpenAI   -> openai.js
            Disney+  -> disney+.js

        文件名匹配不区分大小写。
        """

        if not SCRIPT_DIR.exists():

            raise FileNotFoundError(
                "脚本目录不存在: "
                f"{SCRIPT_DIR}"
            )

        target = (
            script_name
            .strip()
            .lower()
        )

        if not target:

            raise ValueError(
                "脚本名称不能为空"
            )

        # 优先精确匹配 stem
        for path in SCRIPT_DIR.iterdir():

            if not path.is_file():
                continue

            if path.suffix.lower() != ".js":
                continue

            if (
                path.stem.lower()
                == target
            ):
                return path

        # 找不到时，再进行宽松匹配
        # 主要处理特殊字符 / 大小写问题
        normalized_target = (
            target
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
        )

        for path in SCRIPT_DIR.iterdir():

            if not path.is_file():
                continue

            if path.suffix.lower() != ".js":
                continue

            normalized_name = (
                path.stem
                .lower()
                .replace(" ", "")
                .replace("_", "")
                .replace("-", "")
            )

            if (
                normalized_name
                == normalized_target
            ):
                return path

        raise FileNotFoundError(
            "找不到脚本: "
            f"{script_name}，搜索目录: "
            f"{SCRIPT_DIR}"
        )

    def _build_scripts(
        self,
        items: list[TestItem],
    ) -> list[m.Script]:
        """
        根据 tests.yaml 中的 script 测试项目，
        自动加载 scripts/builtin 下的 JS。

        同一个脚本只加载一次。
        """

        scripts: list[m.Script] = []

        loaded_ids: set[str] = set()

        for item in items:

            if item.kind != "script":
                continue

            script_name = (
                item.script_name
                or item.title
            ).strip()

            if not script_name:
                continue

            # 避免重复加载
            if script_name in loaded_ids:
                continue

            script_path = (
                self._find_script_file(
                    script_name
                )
            )

            content = (
                script_path.read_text(
                    encoding="utf-8"
                )
            )

            script = m.Script(
                ID=script_name,
                Type=m.ScriptType.STypeMedia.value,
                Content=content,
                TimeoutMillis=(
                    SCRIPT_TIMEOUT_MILLIS
                ),
            )

            scripts.append(
                script
            )

            loaded_ids.add(
                script_name
            )

            print(
                "加载脚本: "
                f"{script_name} "
                f"<- "
                f"{script_path.name}"
            )

        return scripts

    # ========================================================
    # Request
    # ========================================================

    def build_request(
        self,
        nodes: list[Node],
        items: list[TestItem],
    ):

        request = m.SlaveRequest(
            Options=m.SlaveRequestOptions(
                Matrices=build_matrices(
                    items
                )
            )
        )

        # ----------------------------------------------------
        # 基础配置
        # ----------------------------------------------------

        request.Configs = (
            m.SlaveRequestConfigs.from_option(
                self.config.option
            )
        )

        # ----------------------------------------------------
        # 加载 JS Script
        # ----------------------------------------------------

        request.Configs.Scripts = (
            self._build_scripts(
                items
            )
        )

        # ----------------------------------------------------
        # Invoker
        # ----------------------------------------------------

        request.Basics.Invoker = (
            self.config.invoker
            or ""
        )

        # ----------------------------------------------------
        # Vendor
        # ----------------------------------------------------

        request.Vendor = (
            m.VendorType.VendorClash
        )

        # ----------------------------------------------------
        # Nodes
        # ----------------------------------------------------

        request.Nodes = [
            m.SlaveRequestNode(
                Name=node.name,
                Payload=proxy_to_yaml(node),
            )
            for node in nodes
        ]

        return request

    # ========================================================
    # Run
    # ========================================================

    async def run(
        self,
        nodes: list[Node],
        items: list[TestItem],
        on_message=None,
    ):

        request = self.build_request(
            nodes,
            items,
        )

        # ----------------------------------------------------
        # 创建 MiaoSpeed
        # ----------------------------------------------------

        ms = m.MiaoSpeed(
            slave_config=self.config,
            slave_request=request,
            proxyconfig=[],
            debug=True,
        )

        # ----------------------------------------------------
        # WebSocket
        # ----------------------------------------------------

        ws_scheme, verify_ssl = (
            ms.get_ws_opt()
        )

        ws_url = (
            f"{ws_scheme}://"
            f"{ms.host}:"
            f"{ms.port}"
            f"{ms.path}"
        )

        print(
            f"MiaoSpeed: {ws_url}"
        )

        # ----------------------------------------------------
        # Token 签名
        # ----------------------------------------------------

        ms.sign_request()

        request_json = (
            ms.SlaveRequest.to_json()
        )

        # 调试：
        # 检查实际发送的脚本数量
        scripts = (
            request.Configs.Scripts
            or []
        )

        print(
            f"MiaoSpeed Script: "
            f"{len(scripts)}"
        )

        for script in scripts:

            print(
                f"  - "
                f"{script.ID} "
                f"({script.Type})"
            )

        # ----------------------------------------------------
        # WebSocket
        # ----------------------------------------------------

        timeout = aiohttp.ClientTimeout(
            total=None
        )

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.ws_connect(
                ws_url,
                verify_ssl=verify_ssl,
            ) as ws:

                await ws.send_str(
                    request_json
                )

                while True:

                    msg = (
                        await ws.receive()
                    )

                    # ========================================
                    # 文本消息
                    # ========================================

                    if (
                        msg.type
                        == aiohttp.WSMsgType.TEXT
                    ):

                        should_stop = False

                        if on_message:

                            should_stop = (
                                await on_message(
                                    msg.data
                                )
                            )

                        if should_stop:

                            break

                    # ========================================
                    # WebSocket 错误
                    # ========================================

                    elif (
                        msg.type
                        == aiohttp.WSMsgType.ERROR
                    ):

                        raise RuntimeError(
                            "MiaoSpeed WebSocket "
                            f"error: "
                            f"{ws.exception()}"
                        )

                    # ========================================
                    # WebSocket 关闭
                    # ========================================

                    elif msg.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSE,
                    ):

                        break