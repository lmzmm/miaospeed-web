from miaospeedlib.backend import (
    MiaoSpeedSlave,
    MiaoSpeedOption,
)


# ============================================================
# Web 服务
# ============================================================

WEB_HOST = "0.0.0.0"
WEB_PORT = 8000


# ============================================================
# MiaoSpeed 服务端
# ============================================================

MIAOSPEED_BIND = "127.0.0.1:8765"
MIAOSPEED_TOKEN = "9876543210"


MIAOSPEED_CONFIG = MiaoSpeedSlave(
    id="local",
    comment="Local",
    hidden=False,

    token=MIAOSPEED_TOKEN,
    type="miaospeed",
    address=MIAOSPEED_BIND,

    option=MiaoSpeedOption(
        downloadDuration=8,
        downloadThreading=4,

        pingAverageOver=5,
        taskRetry=3,

        downloadURL=(
            "https://dl.google.com/dl/android/studio/install/3.4.1.0/"
            "android-studio-ide-183.5522156-windows.exe"
        ),

        pingAddress=(
            "https://cp.cloudflare.com/generate_204"
        ),

        stunURL=(
            "udp://stunserver2025.stunprotocol.org:3478"
        ),

        taskTimeout=5000,

        dnsServer=[],

        apiVersion=1,
    ),

    skipCertVerify=True,
    tls=False,
    invoker="python",

    # 修改成你的实际 buildtoken
    buildtoken=(
        "MIAOKO4|580JxAo049R|GEnERAl|1X571R930|T0kEN"
    ),

    path="/",
)