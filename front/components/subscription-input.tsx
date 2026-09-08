"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, Search } from "lucide-react";

import { isValidHttpUrl } from "@/lib/utils";

interface SubscriptionInputProps {
  subscription: string;
  proxy: string;
  onSubscriptionChange: (value: string) => void;
  onProxyChange: (value: string) => void;
  onParse: (subscription: string, proxy: string) => void;
  parsing: boolean;
  disabled?: boolean;
}

export function SubscriptionInput({
  subscription,
  proxy,
  onSubscriptionChange,
  onProxyChange,
  onParse,
  parsing,
  disabled,
}: SubscriptionInputProps) {
  const [errors, setErrors] = useState<{
    subscription?: string;
    proxy?: string;
  }>({});

  function handleParse() {
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

    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    onParse(subscriptionTrimmed, proxyTrimmed || "");
  }

  return (
    <div className="flex flex-col gap-4">
      {/* 订阅地址 */}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="subscription">订阅地址</Label>
        <Input
          id="subscription"
          value={subscription}
          onChange={(event) => onSubscriptionChange(event.target.value)}
          placeholder="https://example.com/subscribe"
          disabled={disabled || parsing}
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
          onChange={(event) => onProxyChange(event.target.value)}
          placeholder="http://127.0.0.1:7890"
          disabled={disabled || parsing}
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

      <Button
        type="button"
        variant="secondary"
        onClick={handleParse}
        disabled={disabled || parsing}
        className="w-full"
      >
        {parsing ? (
          <>
            <Loader2 className="animate-spin" />
            解析中…
          </>
        ) : (
          <>
            <Search />
            解析订阅
          </>
        )}
      </Button>
    </div>
  );
}
