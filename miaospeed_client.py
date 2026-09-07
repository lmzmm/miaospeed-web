import aiohttp
import miaospeedlib as m

from clash import proxy_to_yaml
from config import MIAOSPEED_CONFIG
from models import Node, TestItem
from tests import build_matrices


class MiaoSpeedClient:

    def __init__(self):
        self.config = MIAOSPEED_CONFIG

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

        request.Configs = (
            m.SlaveRequestConfigs.from_option(
                self.config.option
            )
        )

        request.Basics.Invoker = (
            self.config.invoker
            or ""
        )

        request.Vendor = (
            m.VendorType.VendorClash
        )

        request.Nodes = [
            m.SlaveRequestNode(
                Name=node.name,
                Payload=proxy_to_yaml(node),
            )
            for node in nodes
        ]

        return request

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

        ms = m.MiaoSpeed(
            slave_config=self.config,
            slave_request=request,
            proxyconfig=[],
            debug=True,
        )

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

        # 保留 Token 签名
        ms.sign_request()

        request_json = (
            ms.SlaveRequest.to_json()
        )

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

                    msg = await ws.receive()

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

                    elif (
                        msg.type
                        == aiohttp.WSMsgType.ERROR
                    ):

                        raise RuntimeError(
                            "MiaoSpeed WebSocket "
                            f"error: {ws.exception()}"
                        )

                    elif msg.type in (
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.CLOSE,
                    ):

                        break