# MiaoSpeed web
Clash / Mihomo 节点测速工具。输入订阅链接，解析并选择需要测试的节点，后台调用 MiaoSpeed 完成测速，最终以 PNG 图片展示结果。

## 项目结构

```
speedtest/
├── main.py                 # FastAPI 入口（含 CORS / 编码配置）
├── service.py              # 测速服务：加载节点、调用 MiaoSpeed、渲染结果
├── api/speedtest.py        # 路由：创建任务、解析订阅、查询任务、结果图片、WebSocket
├── task/manager.py         # 任务管理器（内存任务表 + 订阅发布）
├── clash.py                # Clash/Mihomo 订阅下载与节点解析
├── miaospeed_client.py     # MiaoSpeed 客户端封装
├── result.py               # 结果清洗与排序
├── renderer.py             # PNG / JSON 结果渲染
├── scripts/builtin/        # 内置脚本测试（Youtube / OpenAI / Claude 等）
├── results/                # 结果输出目录（PNG / JSON）
└── front/                  # 前端（Next.js）
    ├── app/                # 页面与布局
    ├── components/         # UI 组件
    ├── hooks/              # use-speed-test-websocket
    ├── lib/                # api / test-config / utils
    └── types/              # TypeScript 类型
```

## 技术栈

- **后端**：FastAPI + aiohttp + PyYAML + miaospeedlib
- **前端**：Next.js（App Router）+ React + TypeScript + Tailwind CSS + shadcn/ui + 原生 WebSocket

## 环境要求

- Python 3.10+
- Node.js 18+（开发时使用 Node 24）

## 后端启动

```bash
cd E:\项目\speedtest

# 安装依赖
pip install fastapi uvicorn aiohttp pyyaml miaospeedlib

# 启动（默认 http://127.0.0.1:8000）
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000
```

健康检查：`GET http://127.0.0.1:8000/health`

## 前端启动

```bash
cd E:\项目\speedtest\front

npm install
npm run dev          # http://localhost:3000
```

生产构建：

```bash
npm run build
npm run start
```

### 环境变量

前端通过环境变量指定后端地址，未配置时默认 `http://127.0.0.1:8000`：

```bash
# front/.env.local
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

参考 `front/.env.local.example`。WebSocket 地址会自动从 HTTP 地址转换（`http` → `ws`，`https` → `wss`）。

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/speedtest/parse` | 解析订阅，返回节点列表 |
| `POST` | `/api/speedtest` | 创建测速任务 |
| `GET` | `/api/speedtest/{task_id}` | 查询任务状态 |
| `GET` | `/api/speedtest/{task_id}/image` | 获取结果 PNG |
| `WS` | `/api/speedtest/ws/{task_id}` | 实时进度推送 |

### 解析订阅

```http
POST /api/speedtest/parse
Content-Type: application/json

{ "subscription": "https://example.com/subscribe", "proxy": "http://127.0.0.1:7890" }
```

### 创建测速任务

```http
POST /api/speedtest
Content-Type: application/json

{
  "subscription": "https://example.com/subscribe",
  "proxy": "http://127.0.0.1:7890",
  "node_indices": [0, 2, 5],
  "sort_by": "avg_speed",
  "reverse": true,
  "tests": [
    { "name": "TEST_PING_RTT", "title": "RTT" },
    { "name": "TEST_SCRIPT", "title": "Youtube", "kind": "script", "script_name": "Youtube" }
  ]
}
```

字段说明：

- `subscription`：Clash/Mihomo 订阅 URL（必填）
- `proxy`：仅用于下载订阅的代理（可选）
- `node_indices`：只测试指定下标的节点（下标来自 `/parse` 返回的 `index`），`null` 表示全部
- `sort_by`：`rtt` / `http_delay` / `max_speed` / `avg_speed`
- `reverse`：`true` 倒序，`false` 正序
- `tests`：测试项目数组

## 使用流程

1. 输入订阅链接，点击「解析订阅」，获取节点列表
2. 按需搜索、选择要测速的节点（默认全选）
3. 配置排序字段与测试项目
4. 点击「开始测速」，右侧实时展示进度与当前节点
5. 完成后展示结果图片，支持放大、下载、重新测速

## 注意事项

- 任务状态保存在后端内存中，重启后端会丢失未完成任务
- 结果 PNG/JSON 输出到 `results/` 目录，以 `task_id` 命名

## 打包为单个可执行文件

使用 PyInstaller 将前端、后端、MiaoSpeed 服务端打包为一个 `.exe`，双击即可运行。

### 准备工作

1. 安装 PyInstaller：

```bash
pip install pyinstaller
```

2. 编译前端静态文件：

```bash
cd front
npm run build
cd ..
```

编译完成后会在 `front/out/` 目录生成静态文件。

### 目录结构要求

打包前，项目根目录下需要有以下文件和目录：

```
miaospeed-web/
├── main.py                          # 入口文件
├── miaospeed_client.py              # MiaoSpeed 客户端
├── service.py                       # 测速服务
├── config.py                        # MiaoSpeed 配置
├── clash.py                         # 订阅解析
├── models.py                        # 数据模型
├── result.py                        # 结果处理
├── renderer.py                      # PNG 渲染
├── cli.py                           # CLI 入口
├── tests.py                         # 测试矩阵
├── api/
│   └── speedtest.py                 # API 路由
├── task/
│   └── manager.py                   # 任务管理器
├── scripts/
│   └── builtin/                     # 内置测试脚本
│       ├── youtube.js
│       ├── openai.js
│       └── ...
├── front/
│   └── out/                         # 前端编译产物（npm run build 后生成）
│       ├── index.html
│       ├── _next/
│       └── ...
└── miaospeed-windows-amd64.exe      # MiaoSpeed 服务端二进制
```

### 执行打包

```bash
pyinstaller --onefile --name miaospeed-web ^
  --add-binary "miaospeed-windows-amd64.exe;." ^
  --add-data "front/out;front/out" ^
  --add-data "scripts;scripts" ^
  --hidden-import miaospeedlib ^
  main.py
```

参数说明：

| 参数 | 作用 |
|---|---|
| `--onefile` | 打包成单个 `.exe` |
| `--add-binary` | 将 MiaoSpeed 服务端二进制一起打包 |
| `--add-data` | 将前端静态文件和内置脚本一起打包 |
| `--hidden-import` | 指定隐式依赖，避免 PyInstaller 漏掉 |

> Windows 下 `--add-data` 和 `--add-binary` 的分隔符是 `;`，Linux/Mac 下是 `:`。

### 运行

打包完成后，`dist/miaospeed-web.exe` 即为最终产物。双击运行后：

1. 自动启动内置的 MiaoSpeed 服务端（后台进程）
2. FastAPI 启动，监听 `0.0.0.0:8000`
3. 浏览器访问 `http://localhost:8000` 即可使用
4. 关闭程序时自动停止 MiaoSpeed 服务端

### 常见问题

- **端口被占用**：确保 `8000` 和 `8765` 端口未被其他程序占用，或先关闭占用进程
- **杀毒软件误报**：PyInstaller 打包的单文件 `.exe` 可能被误报，可添加白名单
- **启动慢**：`--onefile` 模式每次启动需解压到临时目录，首次启动较慢属正常现象
