"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { SubscriptionInput } from "@/components/subscription-input";
import { NodeSelector } from "@/components/node-selector";
import { SortSelector } from "@/components/sort-selector";
import { TestSelector } from "@/components/test-selector";
import { SpeedTestProgress } from "@/components/speed-test-progress";
import { SpeedTestResult } from "@/components/speed-test-result";
import { StatusBadge } from "@/components/status-badge";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { AlertCircle, Gauge, Loader2, Play } from "lucide-react";

import { useSpeedTestWebSocket } from "@/hooks/use-speed-test-websocket";
import {
  ApiError,
  createSpeedTest,
  getSpeedTest,
  getSpeedTestImageUrl,
  parseSubscription,
} from "@/lib/api";

import type {
  ParsedNode,
  SortByValue,
  SpeedTestState,
  SpeedTestStatus,
  SpeedTestTask,
  SpeedTestWebSocketMessage,
} from "@/types/speedtest";
import {
  DEFAULT_REVERSE,
  DEFAULT_SELECTED_TEST_IDS,
  DEFAULT_SORT_BY,
  buildTestsFromIds,
} from "@/lib/test-config";

const STORAGE_KEY = "miaospeed.speedtest.task_id";

const INITIAL_STATE: SpeedTestState = {
  taskId: null,
  status: "idle",
  total: 0,
  completed: 0,
  currentNode: null,
  error: null,
  imageUrl: null,
};

function isTerminal(status: string): boolean {
  return (
    status === "completed" || status === "failed" || status === "cancelled"
  );
}

export default function Home() {
  // ----------------------------------------------------------
  // 配置状态
  // ----------------------------------------------------------
  const [subscription, setSubscription] = useState("");
  const [proxy, setProxy] = useState("");
  const [nodes, setNodes] = useState<ParsedNode[]>([]);
  const [selectedNodeIndices, setSelectedNodeIndices] = useState<number[]>([]);
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [selectedTestIds, setSelectedTestIds] = useState<string[]>(
    DEFAULT_SELECTED_TEST_IDS,
  );
  const [sortBy, setSortBy] = useState<SortByValue>(DEFAULT_SORT_BY);
  const [reverse, setReverse] = useState<boolean>(DEFAULT_REVERSE);

  // ----------------------------------------------------------
  // 任务状态
  // ----------------------------------------------------------
  const [state, setState] = useState<SpeedTestState>(INITIAL_STATE);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [wsError, setWsError] = useState<string | null>(null);
  const [reconnectToken, setReconnectToken] = useState(0);

  const stateRef = useRef(state);
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const running = state.status === "created" || state.status === "running";

  // ----------------------------------------------------------
  // 应用后端任务状态到前端 state
  // ----------------------------------------------------------
  const applyTask = useCallback((task: SpeedTestTask) => {
    setState((prev) => {
      const status = task.status as SpeedTestStatus;
      const imageUrl =
        status === "completed"
          ? getSpeedTestImageUrl(task.task_id, String(Date.now()))
          : prev.imageUrl;

      return {
        taskId: task.task_id,
        status,
        total: task.total ?? 0,
        completed: task.completed ?? 0,
        currentNode: prev.currentNode,
        error: task.error ?? null,
        imageUrl,
      };
    });
  }, []);

  // ----------------------------------------------------------
  // WebSocket 消息处理
  // ----------------------------------------------------------
  const handleMessage = useCallback((message: SpeedTestWebSocketMessage) => {
    switch (message.type) {
      case "status": {
        setState((prev) => {
          const status = (message.status as SpeedTestStatus) ?? prev.status;
          const imageUrl =
            status === "completed" && message.image
              ? getSpeedTestImageUrl(message.task_id, String(Date.now()))
              : prev.imageUrl;

          return {
            ...prev,
            status,
            total: message.total ?? prev.total,
            completed: message.completed ?? prev.completed,
            error: message.error ?? prev.error,
            imageUrl,
          };
        });
        break;
      }
      case "progress": {
        setState((prev) => ({
          ...prev,
          status: "running",
          total: message.total ?? prev.total,
          completed: message.completed,
          currentNode: message.result?.name ?? prev.currentNode,
        }));
        break;
      }
      case "completed": {
        setState((prev) => ({
          ...prev,
          status: "completed",
          total: message.total,
          completed: message.completed,
          currentNode: null,
          error: null,
          imageUrl: getSpeedTestImageUrl(message.task_id, String(Date.now())),
        }));
        break;
      }
    }
  }, []);

  const handleWsError = useCallback((message: string) => {
    setWsError(message);
  }, []);

  const handleWsClosed = useCallback(async () => {
    const current = stateRef.current;
    const taskId = current.taskId;

    if (!taskId || isTerminal(current.status)) return;

    try {
      const task = await getSpeedTest(taskId);
      applyTask(task);
      if (!isTerminal(task.status)) {
        setReconnectToken((token) => token + 1);
      }
    } catch {
      // 拉取失败，保持现状
    }
  }, [applyTask]);

  useSpeedTestWebSocket({
    taskId: state.taskId,
    reconnectToken,
    onMessage: handleMessage,
    onError: handleWsError,
    onClosed: handleWsClosed,
  });

  // ----------------------------------------------------------
  // 页面加载：恢复上次任务
  // ----------------------------------------------------------
  useEffect(() => {
    const storedTaskId = localStorage.getItem(STORAGE_KEY);
    if (!storedTaskId) return;

    let cancelled = false;

    getSpeedTest(storedTaskId)
      .then((task) => {
        if (!cancelled) applyTask(task);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.status === 404) {
          localStorage.removeItem(STORAGE_KEY);
          setState(INITIAL_STATE);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [applyTask]);

  // ----------------------------------------------------------
  // 解析订阅
  // ----------------------------------------------------------
  const handleSubscriptionChange = useCallback((value: string) => {
    setSubscription(value);
    // 订阅地址变化后，旧的节点列表失效
    setNodes([]);
    setSelectedNodeIndices([]);
    setParseError(null);
  }, []);

  const handleParse = useCallback(
    async (parsedSubscription: string, parsedProxy: string) => {
      setParsing(true);
      setParseError(null);
      setSubmitError(null);

      try {
        const response = await parseSubscription({
          subscription: parsedSubscription,
          proxy: parsedProxy || null,
        });
        const nodeList = response.nodes;
        setNodes(nodeList);
        setSelectedNodeIndices(nodeList.map((node) => node.index));
      } catch (error: unknown) {
        const message =
          error instanceof ApiError ? error.message : "解析订阅失败";
        setParseError(message);
        setNodes([]);
        setSelectedNodeIndices([]);
      } finally {
        setParsing(false);
      }
    },
    [],
  );

  // ----------------------------------------------------------
  // 开始测速
  // ----------------------------------------------------------
  const handleStart = useCallback(async () => {
    if (nodes.length === 0) {
      setSubmitError("请先解析订阅，获取节点列表");
      return;
    }
    if (selectedNodeIndices.length === 0) {
      setSubmitError("至少选择一个节点");
      return;
    }
    const tests = buildTestsFromIds(selectedTestIds);
    if (tests.length === 0) {
      setSubmitError("至少选择一个测试项目");
      return;
    }

    setSubmitError(null);
    setWsError(null);

    try {
      const created = await createSpeedTest({
        subscription: subscription.trim(),
        proxy: proxy.trim() || null,
        tests,
        sort_by: sortBy,
        reverse,
        node_indices: selectedNodeIndices,
      });
      localStorage.setItem(STORAGE_KEY, created.task_id);
      setState({
        taskId: created.task_id,
        status: "created",
        total: 0,
        completed: 0,
        currentNode: null,
        error: null,
        imageUrl: null,
      });
    } catch (error: unknown) {
      const message =
        error instanceof ApiError
          ? error.message
          : "创建任务失败，请检查后端服务是否可用";
      setSubmitError(message);
      setState((prev) => ({
        ...prev,
        taskId: null,
        status: "idle",
        error: message,
      }));
    }
  }, [nodes, selectedNodeIndices, selectedTestIds, subscription, proxy, sortBy, reverse]);

  // ----------------------------------------------------------
  // 重新测速
  // ----------------------------------------------------------
  const handleReset = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setSubmitError(null);
    setWsError(null);
    setReconnectToken(0);
    setState(INITIAL_STATE);
  }, []);

  const showProgress = state.status === "created" || state.status === "running";
  const showResult =
    state.status === "completed" ||
    state.status === "failed" ||
    state.status === "cancelled";

  return (
    <div className="min-h-screen bg-muted/30">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 py-6 sm:px-6">
        {/* 顶部 */}
        <header className="mb-6 flex flex-col gap-1">
          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-lg bg-foreground text-background">
              <Gauge className="size-5" />
            </div>
            <h1 className="text-xl font-semibold tracking-tight">
              MiaoSpeed SpeedTest
            </h1>
          </div>
          <p className="text-sm text-muted-foreground">
            Clash / Mihomo 节点测速
          </p>
        </header>

        <main className="grid flex-1 grid-cols-1 gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          {/* 左列：订阅 + 节点选择 */}
          <section className="flex flex-col gap-4">
            <Card>
              <CardHeader>
                <CardTitle>订阅配置</CardTitle>
              </CardHeader>
              <CardContent>
                <SubscriptionInput
                  subscription={subscription}
                  proxy={proxy}
                  onSubscriptionChange={handleSubscriptionChange}
                  onProxyChange={setProxy}
                  onParse={handleParse}
                  parsing={parsing}
                  disabled={running}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>节点选择</CardTitle>
                <p className="text-sm text-muted-foreground">
                  默认全选，可搜索筛选后手动选择
                </p>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {parseError ? (
                  <Alert variant="destructive">
                    <AlertCircle className="size-4" />
                    <AlertTitle>订阅解析失败</AlertTitle>
                    <AlertDescription className="break-words">
                      {parseError}
                    </AlertDescription>
                  </Alert>
                ) : null}
                <NodeSelector
                  nodes={nodes}
                  selectedIndices={selectedNodeIndices}
                  onSelectionChange={setSelectedNodeIndices}
                  disabled={running}
                />
              </CardContent>
            </Card>
          </section>

          {/* 右列：测速配置 + 进度/结果 */}
          <section className="flex flex-col gap-4">
            <Card>
              <CardHeader>
                <CardTitle>测速配置</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-5">
                <SortSelector
                  sortBy={sortBy}
                  onSortByChange={setSortBy}
                  reverse={reverse}
                  onReverseChange={setReverse}
                  disabled={running}
                />
                <Separator />
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium leading-none">
                      测试项目
                    </span>
                    <span className="text-xs text-muted-foreground">
                      已选 {buildTestsFromIds(selectedTestIds).length} 项
                    </span>
                  </div>
                  <TestSelector
                    selectedIds={selectedTestIds}
                    onToggle={(id) =>
                      setSelectedTestIds((prev) =>
                        prev.includes(id)
                          ? prev.filter((item) => item !== id)
                          : [...prev, id],
                      )
                    }
                    disabled={running}
                  />
                </div>

                <Button
                  type="button"
                  size="lg"
                  className="w-full"
                  disabled={running}
                  onClick={handleStart}
                >
                  {running ? (
                    <>
                      <Loader2 className="animate-spin" />
                      测速中…
                    </>
                  ) : (
                    <>
                      <Play />
                      开始测速
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {submitError ? (
              <Alert variant="destructive">
                <AlertCircle className="size-4" />
                <AlertTitle>无法开始测速</AlertTitle>
                <AlertDescription className="break-words">
                  {submitError}
                </AlertDescription>
              </Alert>
            ) : null}

            {wsError && running ? (
              <Alert variant="destructive">
                <AlertCircle className="size-4" />
                <AlertTitle>连接异常</AlertTitle>
                <AlertDescription className="break-words">
                  {wsError}
                </AlertDescription>
              </Alert>
            ) : null}

            {state.status === "idle" ? (
              <div className="flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed p-10 text-center">
                <p className="text-sm text-muted-foreground">
                  输入订阅并解析，配置好测速项后点击「开始测速」，结果将在这里显示
                </p>
              </div>
            ) : null}

            {showProgress ? <SpeedTestProgress state={state} /> : null}

            {showResult ? (
              <SpeedTestResult state={state} onReset={handleReset} />
            ) : null}

            {state.status !== "idle" ? (
              <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-2.5 text-sm">
                <span className="text-muted-foreground">任务状态</span>
                <StatusBadge status={state.status} />
              </div>
            ) : null}
          </section>
        </main>

        <footer className="mt-8 border-t pt-4 text-center text-xs text-muted-foreground">
          MiaoSpeed SpeedTest · 后端地址{" "}
          {process.env.NEXT_PUBLIC_API_BASE_URL || "同源"}
        </footer>
      </div>
    </div>
  );
}
