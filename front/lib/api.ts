import type {
  ParseResponse,
  SpeedTestCreateResponse,
  SpeedTestRequest,
  SpeedTestTask,
} from "@/types/speedtest";

// ============================================================
// API 基础地址
//
// 统一通过环境变量 NEXT_PUBLIC_API_BASE_URL 配置，
// 未配置时默认 http://127.0.0.1:8000 。
// ============================================================

export function getApiBaseUrl(): string {
  const base =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
  return base.replace(/\/+$/, "");
}

/**
 * 自定义 API 错误，携带后端返回的 detail 信息。
 */
export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * 解析 FastAPI 的错误响应。
 *
 * FastAPI 常见两种格式：
 * - `{ "detail": "字符串错误信息" }`
 * - `{ "detail": [{ "msg": "...", "loc": [...] }] }`（校验错误）
 */
function parseErrorBody(data: unknown): string | null {
  if (!data || typeof data !== "object") return null;

  const detail = (data as { detail?: unknown }).detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return null;
      })
      .filter((m): m is string => Boolean(m));

    if (messages.length) {
      return messages.join("；");
    }
  }

  return null;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `请求失败（HTTP ${response.status}）`;

    try {
      const data: unknown = await response.json();
      const detail = parseErrorBody(data);
      if (detail) message = detail;
    } catch {
      // 响应体不是 JSON，保持默认错误信息
    }

    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

// ============================================================
// API 方法
// ============================================================

export async function createSpeedTest(
  request: SpeedTestRequest,
): Promise<SpeedTestCreateResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/speedtest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  return handleResponse<SpeedTestCreateResponse>(response);
}

/**
 * 解析订阅，返回节点列表。
 */
export async function parseSubscription(input: {
  subscription: string;
  proxy?: string | null;
}): Promise<ParseResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/speedtest/parse`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      subscription: input.subscription,
      proxy: input.proxy ?? null,
    }),
  });

  return handleResponse<ParseResponse>(response);
}

export async function getSpeedTest(
  taskId: string,
): Promise<SpeedTestTask> {
  const response = await fetch(
    `${getApiBaseUrl()}/api/speedtest/${encodeURIComponent(taskId)}`,
  );

  return handleResponse<SpeedTestTask>(response);
}

/**
 * 返回最终结果图片地址。
 *
 * @param taskId 任务 id
 * @param cacheBust 是否需要带时间戳参数避免缓存。
 *   仅在任务完成、首次拿到图片时传入一次，避免每次 render 都重新请求。
 */
export function getSpeedTestImageUrl(
  taskId: string,
  cacheBust?: string,
): string {
  const base = `${getApiBaseUrl()}/api/speedtest/${encodeURIComponent(taskId)}/image`;
  if (cacheBust) {
    return `${base}?v=${encodeURIComponent(cacheBust)}`;
  }
  return base;
}

/**
 * 根据 HTTP API 地址自动转换成 WebSocket 地址。
 *
 * http:// -> ws://
 * https:// -> wss://
 */
export function createWebSocketUrl(taskId: string): string {
  const base = getApiBaseUrl();
  const wsBase = base.replace(/^http/i, "ws");
  return `${wsBase}/api/speedtest/ws/${encodeURIComponent(taskId)}`;
}
