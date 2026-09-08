"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Play } from "lucide-react";

import { TestSelector } from "@/components/test-selector";
import { SortSelector } from "@/components/sort-selector";

import type { SpeedTestRequest, SortByValue } from "@/types/speedtest";
import {
  DEFAULT_REVERSE,
  DEFAULT_SELECTED_TEST_IDS,
  DEFAULT_SORT_BY,
  buildTestsFromIds,
} from "@/lib/test-config";

interface SpeedTestFormProps {
  onStart: (request: SpeedTestRequest) => void;
  /** 任务是否正在创建 / 运行中 */
  running: boolean;
}

function isValidHttpUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export function SpeedTestForm({
  onStart,
  running,
}: SpeedTestFormProps) {
  const [subscription, setSubscription] = useState("");
  const [proxy, setProxy] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>(
    DEFAULT_SELECTED_TEST_IDS,
  );
  const [sortBy, setSortBy] = useState<SortByValue>(DEFAULT_SORT_BY);
  const [reverse, setReverse] = useState<boolean>(DEFAULT_REVERSE);

  const [errors, setErrors] = useState<{
    subscription?: string;
    proxy?: string;
    tests?: string;
  }>({});

  const tests = useMemo(() => buildTestsFromIds(selectedIds), [selectedIds]);

  function toggleTest(id: string) {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    );
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    const nextErrors: typeof errors = {};

    const subscriptionTrimmed = subscription.trim();
    if (!subscriptionTrimmed) {
      nextErrors.subscription = "订阅地址不能为空";
    } else if (!isValidHttpUrl(subscriptionTrimmed)) {
      nextErrors.subscription = "订阅地址必须是 http 或 https URL";
    }

    const proxyTrimmed = proxy.trim();
    if (proxyTrimmed && !isValidHttpUrl(proxyTrimmed)) {
      nextErrors.proxy = "订阅代理必须是 http 或 https URL";
    }

    if (tests.length === 0) {
      nextErrors.tests = "至少选择一个测试项目";
    }

    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    onStart({
      subscription: subscriptionTrimmed,
      proxy: proxyTrimmed || null,
      tests,
      sort_by: sortBy,
      reverse,
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>测速配置</CardTitle>
      </CardHeader>
      <CardContent>
        <form
          onSubmit={handleSubmit}
          className="flex flex-col gap-5"
          noValidate
        >
          {/* 订阅地址 */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="subscription">订阅地址</Label>
            <Input
              id="subscription"
              value={subscription}
              onChange={(event) => setSubscription(event.target.value)}
              placeholder="https://example.com/subscribe"
              disabled={running}
              aria-invalid={Boolean(errors.subscription)}
            />
            {errors.subscription ? (
              <p className="text-xs text-destructive">{errors.subscription}</p>
            ) : (
              <p className="text-xs text-muted-foreground">
                支持 Clash / Mihomo 订阅链接
              </p>
            )}
          </div>

          {/* 订阅代理 */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="proxy">
              订阅代理
              <span className="text-xs font-normal text-muted-foreground">
                （可选）
              </span>
            </Label>
            <Input
              id="proxy"
              value={proxy}
              onChange={(event) => setProxy(event.target.value)}
              placeholder="http://127.0.0.1:7890"
              disabled={running}
              aria-invalid={Boolean(errors.proxy)}
            />
            {errors.proxy ? (
              <p className="text-xs text-destructive">{errors.proxy}</p>
            ) : (
              <p className="text-xs text-muted-foreground">
                仅用于下载订阅配置，不影响节点测速
              </p>
            )}
          </div>

          {/* 排序 */}
          <SortSelector
            sortBy={sortBy}
            onSortByChange={setSortBy}
            reverse={reverse}
            onReverseChange={setReverse}
            disabled={running}
          />

          {/* 测试项目 */}
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <Label>测试项目</Label>
              <span className="text-xs text-muted-foreground">
                已选 {tests.length} 项
              </span>
            </div>
            {errors.tests ? (
              <Alert variant="destructive" className="py-2">
                <AlertDescription>{errors.tests}</AlertDescription>
              </Alert>
            ) : null}
            <TestSelector
              selectedIds={selectedIds}
              onToggle={toggleTest}
              disabled={running}
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            size="lg"
            disabled={running}
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
        </form>
      </CardContent>
    </Card>
  );
}
