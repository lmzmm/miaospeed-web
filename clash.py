from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp
import yaml

from models import Node


INVALID_NAME_KEYWORDS = (
    "公告",
    "官网",
)

SUBSCRIPTION_TIMEOUT = aiohttp.ClientTimeout(
    total=30
)

MAX_SUBSCRIPTION_SIZE = 20 * 1024 * 1024


def load_yaml(
    file_path: str,
) -> dict[str, Any]:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"文件不存在: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:

        data = yaml.safe_load(f)

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "YAML 根节点必须是 object"
        )

    return data


def load_yaml_text(
    content: str,
) -> dict[str, Any]:

    data = yaml.safe_load(
        content
    )

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "YAML 根节点必须是 object"
        )

    return data


def parse_clash_proxies(
    config: dict[str, Any],
) -> list[Node]:

    proxies = config.get(
        "proxies"
    )

    if not isinstance(
        proxies,
        list,
    ):
        raise ValueError(
            "不是 Clash/Mihomo "
            "配置文件，没有 proxies"
        )

    nodes: list[Node] = []

    for proxy in proxies:

        if not isinstance(
            proxy,
            dict,
        ):
            continue

        name = str(
            proxy.get("name") or ""
        ).strip()

        proxy_type = str(
            proxy.get("type") or ""
        ).strip()

        server = str(
            proxy.get("server") or ""
        ).strip()

        if not name:
            continue

        if not proxy_type:
            continue

        if not server:
            continue

        if any(
            keyword in name
            for keyword in INVALID_NAME_KEYWORDS
        ):
            continue

        port = proxy.get(
            "port"
        )

        try:

            if port is not None:
                port = int(port)

        except (
            TypeError,
            ValueError,
        ):

            port = None

        nodes.append(
            Node(
                index=len(nodes),
                name=name,
                type=proxy_type,
                server=server,
                port=port,
                raw=proxy,
            )
        )

    return nodes


def load_clash_proxies(
    file_path: str,
) -> list[Node]:

    config = load_yaml(
        file_path
    )

    return parse_clash_proxies(
        config
    )


async def download_subscription(
    url: str,
    proxy: str | None = None,
) -> str:
    """
    下载远程订阅。

    proxy:
        可选，仅用于下载订阅。
        例如：
            http://127.0.0.1:7890
            http://user:pass@127.0.0.1:7890
    """

    parsed = urlparse(
        url
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ValueError(
            "订阅 URL 必须使用 "
            "http 或 https"
        )

    if proxy:

        proxy_parsed = urlparse(
            proxy
        )

        if proxy_parsed.scheme not in {
            "http",
            "https",
        }:
            raise ValueError(
                "目前仅支持 HTTP/HTTPS "
                "订阅下载代理，"
                f"不支持: "
                f"{proxy_parsed.scheme}"
            )

    headers = {
        "User-Agent":
            "clash meta"
    }

    async with aiohttp.ClientSession(
        timeout=SUBSCRIPTION_TIMEOUT,
        headers=headers,
    ) as session:

        try:

            async with session.get(
                url,
                proxy=proxy,
                allow_redirects=True,
            ) as response:

                if response.status != 200:

                    raise RuntimeError(
                        "订阅下载失败，HTTP "
                        f"{response.status}"
                    )

                # print(await response.text())

                content_length = (
                    response.headers.get(
                        "Content-Length"
                    )
                )

                if content_length:

                    try:

                        size = int(
                            content_length
                        )

                    except ValueError:

                        size = 0

                    if (
                        size
                        > MAX_SUBSCRIPTION_SIZE
                    ):

                        raise RuntimeError(
                            "订阅文件过大，"
                            f"超过 "
                            f"{MAX_SUBSCRIPTION_SIZE // 1024 // 1024}"
                            "MB"
                        )

                chunks: list[bytes] = []
                total_size = 0

                async for chunk in response.content.iter_chunked(
                    64 * 1024
                ):

                    total_size += len(
                        chunk
                    )

                    if (
                        total_size
                        > MAX_SUBSCRIPTION_SIZE
                    ):

                        raise RuntimeError(
                            "订阅文件过大，"
                            f"超过 "
                            f"{MAX_SUBSCRIPTION_SIZE // 1024 // 1024}"
                            "MB"
                        )

                    chunks.append(
                        chunk
                    )

                raw = b"".join(
                    chunks
                )

                # 优先 UTF-8
                try:

                    return raw.decode(
                        "utf-8"
                    )

                except UnicodeDecodeError:

                    return raw.decode(
                        "utf-8",
                        errors="replace",
                    )

        except aiohttp.ClientError as e:

            raise RuntimeError(
                "订阅下载失败: "
                f"{e}"
            ) from e

        except TimeoutError as e:

            raise RuntimeError(
                "订阅下载超时"
            ) from e


def is_url(value: str) -> bool:
    """判断输入是否是 http/https 链接。"""
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


async def load_clash_proxies_source(
    source: str,
    proxy: str | None = None,
) -> list[Node]:
    """
    自动判断 source：

    http/https:
        下载订阅

    本地路径:
        读取 YAML

    其他（原始内容）:
        直接解析
    """

    if is_url(source):

        content = await download_subscription(
            source,
            proxy=proxy,
        )

        config = load_yaml_text(
            content
        )

        return parse_clash_proxies(
            config
        )

    path = Path(source)

    if path.exists():

        return load_clash_proxies(
            source
        )

    # 原始订阅内容，直接解析
    config = load_yaml_text(
        source
    )

    return parse_clash_proxies(
        config
    )


def proxy_to_yaml(
    node: Node,
) -> str:

    return yaml.safe_dump(
        node.raw,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )