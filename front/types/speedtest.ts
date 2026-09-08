// ============================================================
// 测速相关类型定义
// ============================================================

/**
 * 测试项目类型。
 *
 * - matrix：矩阵测试（RTT / 速度 / UDP 等）
 * - script：脚本测试（Youtube / OpenAI / Claude 等）
 */
export type TestKind = "matrix" | "script";

/**
 * 一个测试项目，直接对应后端 `tests` 数组中的每一项。
 */
export interface TestItem {
  name: string;
  title: string;
  kind: TestKind;
  params?: string;
  script_name?: string | null;
}

/**
 * 排序字段，发送给后端的英文值。
 */
export type SortByValue =
  | "rtt"
  | "http_delay"
  | "max_speed"
  | "avg_speed";

/**
 * 创建测速任务的请求体。
 */
export interface SpeedTestRequest {
  subscription: string;
  proxy?: string | null;
  tests: TestItem[];
  sort_by: SortByValue;
  reverse: boolean;
  /** 只测试指定下标的节点（下标来自 /parse 返回的 index）；null 表示全部 */
  node_indices?: number[] | null;
}

/**
 * 任务状态。
 */
export type SpeedTestStatus =
  | "created"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

/**
 * POST /api/speedtest 的返回。
 */
export interface SpeedTestCreateResponse {
  task_id: string;
  status: string;
  sort_by: string;
  reverse: boolean;
  image: string;
}

/**
 * /api/speedtest/parse 返回的单个节点。
 */
export interface ParsedNode {
  index: number;
  name: string;
  type: string;
  server: string;
  port: number | null;
  address: string;
}

/**
 * /api/speedtest/parse 的返回。
 */
export interface ParseResponse {
  nodes: ParsedNode[];
}

/**
 * 单个节点的序列化结果。
 */
export interface SerializedResult {
  index: number;
  name: string;
  type: string;
  server: string;
  port: number | null;
  address: string;
  available: boolean;
  invoke_duration: number | null;
  values: Record<
    string,
    { raw: unknown; display: unknown }
  >;
}

/**
 * GET /api/speedtest/{task_id} 的返回。
 */
export interface SpeedTestTask {
  task_id: string;
  status: string;
  total: number;
  completed: number;
  error: string | null;
  image: string | null;
  results: SerializedResult[];
}

// ============================================================
// WebSocket 消息
// ============================================================

export interface SpeedTestStatusMessage {
  type: "status";
  task_id: string;
  status: string;
  total?: number;
  completed?: number;
  error?: string | null;
  image?: string | null;
}

export interface SpeedTestProgressMessage {
  type: "progress";
  task_id: string;
  completed: number;
  total: number;
  result?: SerializedResult;
}

export interface SpeedTestCompletedMessage {
  type: "completed";
  task_id: string;
  status: "completed";
  total: number;
  completed: number;
  columns: string[];
  rows: Record<string, unknown>[];
  statistics: Record<string, unknown>;
  image: string;
  image_path?: string;
  json?: string;
}

export type SpeedTestWebSocketMessage =
  | SpeedTestStatusMessage
  | SpeedTestProgressMessage
  | SpeedTestCompletedMessage;

// ============================================================
// 前端状态
// ============================================================

export interface SpeedTestState {
  taskId: string | null;
  status: SpeedTestStatus | "idle";
  total: number;
  completed: number;
  currentNode: string | null;
  error: string | null;
  imageUrl: string | null;
}
