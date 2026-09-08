"use client";

import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Server } from "lucide-react";

import type { SpeedTestState } from "@/types/speedtest";

interface SpeedTestProgressProps {
  state: SpeedTestState;
}

export function SpeedTestProgress({ state }: SpeedTestProgressProps) {
  const { total, completed, currentNode } = state;

  const percent =
    total > 0
      ? Math.min(100, Math.round((completed / total) * 100))
      : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Loader2 className="size-4 animate-spin" />
          测速中
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex items-end justify-between">
          <span className="text-2xl font-semibold tabular-nums">
            {completed}
            <span className="text-base font-normal text-muted-foreground">
              {" "}
              / {total}
            </span>
          </span>
          <span className="text-sm text-muted-foreground tabular-nums">
            {percent}%
          </span>
        </div>

        <Progress value={percent} className="w-full" />

        <div className="flex items-start gap-2 rounded-lg bg-muted/50 px-3 py-2">
          <Server className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <div className="min-w-0 flex-1">
            <p className="text-xs text-muted-foreground">当前节点</p>
            <p className="truncate text-sm font-medium">
              {currentNode ?? "等待首个节点结果…"}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
