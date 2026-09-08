"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  ImageOff,
  Maximize2,
  RotateCcw,
} from "lucide-react";

import type { SpeedTestState } from "@/types/speedtest";

interface SpeedTestResultProps {
  state: SpeedTestState;
  onReset: () => void;
}

export function SpeedTestResult({ state, onReset }: SpeedTestResultProps) {
  const [imageError, setImageError] = useState(false);
  const [open, setOpen] = useState(false);

  if (state.status === "failed" || state.status === "cancelled") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="size-4 text-destructive" />
            测速失败
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Alert variant="destructive">
            <AlertTitle>任务未能完成</AlertTitle>
            <AlertDescription className="break-words">
              {state.error ?? "发生未知错误"}
            </AlertDescription>
          </Alert>
          <Button onClick={onReset} variant="outline" className="w-full">
            <RotateCcw />
            重新测速
          </Button>
        </CardContent>
      </Card>
    );
  }

  // 完成状态
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle2 className="size-4 text-emerald-600" />
          测速完成
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {state.imageUrl && !imageError ? (
          <div className="flex flex-col gap-3">
            <div className="overflow-hidden rounded-lg border">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={state.imageUrl}
                alt="测速结果"
                className="w-full cursor-zoom-in object-contain"
                onClick={() => setOpen(true)}
                onError={() => setImageError(true)}
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setOpen(true)}
              >
                <Maximize2 />
                查看大图
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (state.imageUrl) {
                    window.open(state.imageUrl, "_blank", "noopener");
                  }
                }}
              >
                <ExternalLink />
                下载
              </Button>
            </div>
          </div>
        ) : (
          <Alert variant="destructive">
            <ImageOff className="size-4" />
            <AlertTitle>结果图片加载失败</AlertTitle>
            <AlertDescription>
              测速已完成，但无法加载结果图片。你可以稍后重试或重新测速。
            </AlertDescription>
          </Alert>
        )}

        <Button onClick={onReset} className="w-full">
          <RotateCcw />
          重新测速
        </Button>
      </CardContent>

      {state.imageUrl && !imageError ? (
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogContent className="max-w-[calc(100vw-2rem)] sm:max-w-5xl">
            <DialogHeader>
              <DialogTitle>测速结果</DialogTitle>
            </DialogHeader>
            <div className="max-h-[80vh] overflow-auto">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={state.imageUrl}
                alt="测速结果大图"
                className="w-full object-contain"
              />
            </div>
          </DialogContent>
        </Dialog>
      ) : null}
    </Card>
  );
}
