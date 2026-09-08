"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

import { ALL_TEST_OPTIONS } from "@/lib/test-config";

interface TestSelectorProps {
  selectedIds: string[];
  onToggle: (id: string) => void;
  disabled?: boolean;
}

export function TestSelector({
  selectedIds,
  onToggle,
  disabled,
}: TestSelectorProps) {
  const selectedSet = new Set(selectedIds);

  const matrixTests = ALL_TEST_OPTIONS.filter(
    (option) => option.kind === "matrix",
  );
  const scriptTests = ALL_TEST_OPTIONS.filter(
    (option) => option.kind === "script",
  );

  const renderGroup = (
    title: string,
    options: typeof ALL_TEST_OPTIONS,
  ) => (
    <div>
      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {title}
      </p>
      <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3 lg:grid-cols-4">
        {options.map((option) => {
          const checked = selectedSet.has(option.id);
          return (
            <Label
              key={option.id}
              className={cn(
                "group flex cursor-pointer items-center gap-2 rounded-lg border px-2.5 py-2 text-sm font-normal transition-colors",
                checked
                  ? "border-primary/40 bg-primary/5 text-foreground"
                  : "border-border text-muted-foreground hover:bg-muted/50",
                disabled && "pointer-events-none opacity-60",
              )}
            >
              <Checkbox
                checked={checked}
                onCheckedChange={() => onToggle(option.id)}
                disabled={disabled}
                className="pointer-events-none"
              />
              <span className="truncate">{option.title}</span>
            </Label>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col gap-4">
      {renderGroup("基础测试", matrixTests)}
      <Separator />
      {renderGroup("脚本测试", scriptTests)}
    </div>
  );
}
