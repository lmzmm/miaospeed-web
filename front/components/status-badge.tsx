"use client";

import { Badge } from "@/components/ui/badge";

import type { SpeedTestStatus } from "@/types/speedtest";

type DisplayStatus = SpeedTestStatus | "idle";

const STATUS_META: Record<
  DisplayStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  idle: { label: "就绪", variant: "secondary" },
  created: { label: "已创建", variant: "secondary" },
  running: { label: "测速中", variant: "default" },
  completed: { label: "已完成", variant: "outline" },
  failed: { label: "失败", variant: "destructive" },
  cancelled: { label: "已取消", variant: "secondary" },
};

export function StatusBadge({ status }: { status: DisplayStatus }) {
  const meta = STATUS_META[status] ?? STATUS_META.idle;

  return <Badge variant={meta.variant}>{meta.label}</Badge>;
}
