"use client";

import { useEffect, useRef } from "react";

import type { SpeedTestWebSocketMessage } from "@/types/speedtest";
import { createWebSocketUrl } from "@/lib/api";

interface UseSpeedTestWebSocketOptions {
  taskId: string | null;
  /** 变化时触发重新连接 */
  reconnectToken?: number;
  onMessage: (message: SpeedTestWebSocketMessage) => void;
  onError: (message: string) => void;
  onClosed: () => void;
}

/**
 * 独立的 WebSocket hook。
 *
 * 职责：
 * - 建立 / 关闭 WebSocket
 * - 解析并分发 status / progress / completed 消息
 * - 处理断线、错误
 * - 组件卸载或 taskId / reconnectToken 变化时清理连接
 *
 * 回调通过 ref 保存（在 effect 中同步最新值），
 * 避免因为回调引用变化导致重复连接。
 */
export function useSpeedTestWebSocket({
  taskId,
  reconnectToken = 0,
  onMessage,
  onError,
  onClosed,
}: UseSpeedTestWebSocketOptions): void {
  const handlersRef = useRef({ onMessage, onError, onClosed });

  useEffect(() => {
    handlersRef.current = { onMessage, onError, onClosed };
  }, [onMessage, onError, onClosed]);

  useEffect(() => {
    if (!taskId) return;

    let socket: WebSocket | null = null;
    let cancelled = false;

    try {
      socket = new WebSocket(createWebSocketUrl(taskId));
    } catch {
      handlersRef.current.onError("无法建立 WebSocket 连接");
      return;
    }

    socket.onopen = () => {
      if (cancelled) return;
    };

    socket.onmessage = (event: MessageEvent) => {
      if (cancelled) return;

      try {
        const data = JSON.parse(
          event.data as string,
        ) as SpeedTestWebSocketMessage;
        handlersRef.current.onMessage(data);
      } catch {
        // 忽略无法解析的消息
      }
    };

    socket.onerror = () => {
      if (cancelled) return;
      handlersRef.current.onError("WebSocket 连接异常");
    };

    socket.onclose = () => {
      if (cancelled) return;
      handlersRef.current.onClosed();
    };

    return () => {
      cancelled = true;
      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      socket.onclose = null;
      socket.close();
    };
  }, [taskId, reconnectToken]);
}
