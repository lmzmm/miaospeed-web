from pathlib import Path
from typing import Any

import yaml

from models import Node


INVALID_NAME_KEYWORDS = (
    "公告",
    "官网",
)


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


def load_clash_proxies(
    file_path: str,
) -> list[Node]:

    config = load_yaml(
        file_path
    )

    proxies = config.get(
        "proxies"
    )

    if not isinstance(
        proxies,
        list,
    ):
        raise ValueError(
            f"{file_path} 不是 Clash/Mihomo "
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


def proxy_to_yaml(
    node: Node,
) -> str:

    return yaml.safe_dump(
        node.raw,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )