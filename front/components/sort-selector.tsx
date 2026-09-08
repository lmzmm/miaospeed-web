"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";

import type { SortByValue } from "@/types/speedtest";
import { SORT_OPTIONS } from "@/lib/test-config";

interface SortSelectorProps {
  sortBy: SortByValue;
  onSortByChange: (value: SortByValue) => void;
  reverse: boolean;
  onReverseChange: (value: boolean) => void;
  disabled?: boolean;
}

const REVERSE_OPTIONS = [
  { label: "正序", value: false },
  { label: "倒序", value: true },
];

export function SortSelector({
  sortBy,
  onSortByChange,
  reverse,
  onReverseChange,
  disabled,
}: SortSelectorProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div className="flex flex-col gap-1.5">
        <Label>排序字段</Label>
        <Select
          value={sortBy}
          onValueChange={(value) => {
            if (value) onSortByChange(value as SortByValue);
          }}
          disabled={disabled}
        >
          <SelectTrigger className="w-full">
            <SelectValue>
              {(value) =>
                SORT_OPTIONS.find((option) => option.value === value)?.label ??
                "请选择排序字段"
              }
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-col gap-1.5">
        <Label>排序方向</Label>
        <Select
          value={String(reverse)}
          onValueChange={(value) => {
            if (value !== null) onReverseChange(value === "true");
          }}
          disabled={disabled}
        >
          <SelectTrigger className="w-full">
            <SelectValue>
              {(value) =>
                REVERSE_OPTIONS.find(
                  (option) => String(option.value) === value,
                )?.label ?? "请选择排序方向"
              }
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {REVERSE_OPTIONS.map((option) => (
              <SelectItem
                key={option.label}
                value={String(option.value)}
              >
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
