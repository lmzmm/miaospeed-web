"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { SpeedTestForm } from "@/components/speed-test-form";
import { SpeedTestProgress } from "@/components/speed-test-progress";
import { SpeedTestResult } from "@/components/speed-test-result";
import { StatusBadge } from "@/components/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Gauge } from "lucide-react";

import { useSpeedTestWebSocket } from "@/hooks/use-speed-test-websocket";
import {
  ApiError,
  createSpeedTest,
  getSpeedTest,
  getSpeedTestImageUrl,
} from "@/lib/api";

import type {
  SpeedTestRequest,
  SpeedTestState,
  SpeedTestStatus,
  SpeedTestTask,
  SpeedTestWebSocketMessage,
} from "@/types/speedtest";

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
  const [state, setState] = useState<SpeedTestState>(INITIAL_STATE);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [wsError, setWsError] = useState<string | null>(null);
  const [reconnectToken, setReconnectToken] = useState(0);

  // 用 ref 保存最新状态，供异步回调读取
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

  // ----------------------------------------------------------
  // WebSocket 连接状态
  // ----------------------------------------------------------
  const handleWsError = useCallback((message: string) => {
    setWsError(message);
  }, []);

  const handleWsClosed = useCallback(async () => {
    const current = stateRef.current;
    const taskId = current.taskId;

    if (!taskId || isTerminal(current.status)) return;

    // 运行中连接意外断开，尝试重新拉取状态并重连
    try {
      const task = await getSpeedTest(taskId);
      applyTask(task);
      if (!isTerminal(task.status)) {
        setReconnectToken((token) => token + 1);
      }
    } catch {
      // 拉取失败，保持现状，交由用户手动重试
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
  // 开始测速
  // ----------------------------------------------------------
  const handleStart = useCallback(async (request: SpeedTestRequest) => {
    setSubmitError(null);
    setWsError(null);

    try {
      const created = await createSpeedTest(request);
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
  }, []);

  // ----------------------------------------------------------
  // 重新测速：清空结果，保留表单配置
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

        <main className="grid flex-1 grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          {/* 左侧：配置 */}
          <section>
            <SpeedTestForm onStart={handleStart} running={running} />
          </section>

          {/* 右侧：状态 / 结果 */}
          <section className="flex flex-col gap-4">
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
                  填写左侧配置并点击「开始测速」，结果将在这里显示
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
          {process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"}
        </footer>
      </div>
    </div>
  );
}
