import type { SortByValue, TestItem, TestKind } from "@/types/speedtest";

// ============================================================
// 测试项目配置
//
// 前端负责把用户勾选的项目转换成后端需要的 `tests` 数组。
// 这里集中维护所有可用的矩阵测试与脚本测试。
// ============================================================

export interface TestOption {
  /** 用于前端选择状态的唯一 key（不会发送给后端） */
  id: string;
  /** 展示标题 */
  title: string;
  /** 分组：矩阵 / 脚本 */
  kind: TestKind;
  /** 最终发送给后端的测试项 */
  item: TestItem;
}

/**
 * 矩阵测试（kind = "matrix"）。
 *
 * `name` 必须与后端 tests.py 的 MATRIX_REGISTRY 一致。
 */
const MATRIX_TESTS: TestOption[] = [
  {
    id: "rtt",
    title: "RTT",
    kind: "matrix",
    item: { name: "TEST_PING_RTT", title: "RTT", kind: "matrix" },
  },
  {
    id: "rtt-sd",
    title: "RTT标准差",
    kind: "matrix",
    item: { name: "TEST_PING_SD_RTT", title: "RTT标准差", kind: "matrix" },
  },
  {
    id: "rtt-max",
    title: "MAX RTT",
    kind: "matrix",
    item: { name: "TEST_PING_MAX_RTT", title: "MAX RTT", kind: "matrix" },
  },
  {
    id: "conn",
    title: "HTTPS延迟",
    kind: "matrix",
    item: { name: "TEST_PING_CONN", title: "HTTPS延迟", kind: "matrix" },
  },
  {
    id: "speed-avg",
    title: "平均速度",
    kind: "matrix",
    item: { name: "SPEED_AVERAGE", title: "平均速度", kind: "matrix" },
  },
  {
    id: "speed-max",
    title: "最大速度",
    kind: "matrix",
    item: { name: "SPEED_MAX", title: "最大速度", kind: "matrix" },
  },
  {
    id: "speed-per-second",
    title: "每秒速度",
    kind: "matrix",
    item: { name: "SPEED_PER_SECOND", title: "每秒速度", kind: "matrix" },
  },
  {
    id: "udp-type",
    title: "UDP类型",
    kind: "matrix",
    item: { name: "UDP_TYPE", title: "UDP类型", kind: "matrix" },
  },
];

/**
 * 脚本测试（kind = "script"）。
 *
 * `script_name` 作为 MiaoSpeed 的脚本参数下发，
 * 脚本可能不存在，最终以用户选择为准，前端不假设其一定存在。
 */
const SCRIPT_NAMES = [
  "Youtube",
  "Disney+",
  "OpenAI",
  "Claude",
  "Bilibili",
  "Copilot",
  "Netflix",
  "Spotify",
  "TikTok",
  "Viu",
  "Wikipedia",
] as const;

const SCRIPT_TESTS: TestOption[] = SCRIPT_NAMES.map((name) => ({
  id: `script-${name}`,
  title: name,
  kind: "script",
  item: {
    name: "TEST_SCRIPT",
    title: name,
    kind: "script",
    script_name: name,
  },
}));

/**
 * 全部测试项目。
 */
export const ALL_TEST_OPTIONS: TestOption[] = [
  ...MATRIX_TESTS,
  ...SCRIPT_TESTS,
];

/**
 * 默认勾选的测试项目（id）。
 */
export const DEFAULT_SELECTED_TEST_IDS: string[] = [
  "rtt",
  "rtt-sd",
  "rtt-max",
  "conn",
  "speed-avg",
  "speed-max",
  "speed-per-second",
  "udp-type",
  "script-Youtube",
  "script-Disney+",
  "script-OpenAI",
  "script-Claude",
];

/**
 * 根据勾选的 id 列表，生成后端需要的 `tests` 数组。
 */
export function buildTestsFromIds(ids: string[]): TestItem[] {
  const idSet = new Set(ids);
  return ALL_TEST_OPTIONS.filter((option) => idSet.has(option.id)).map(
    (option) => option.item,
  );
}

// ============================================================
// 排序配置
// ============================================================

export interface SortOption {
  label: string;
  value: SortByValue;
}

export const SORT_OPTIONS: SortOption[] = [
  { label: "RTT", value: "rtt" },
  { label: "HTTP延迟", value: "http_delay" },
  { label: "最大速度", value: "max_speed" },
  { label: "平均速度", value: "avg_speed" },
];

export const DEFAULT_SORT_BY: SortByValue = "avg_speed";
export const DEFAULT_REVERSE = true;
