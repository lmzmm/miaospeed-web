"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

import type { ParsedNode } from "@/types/speedtest";

interface NodeSelectorProps {
  nodes: ParsedNode[];
  selectedIndices: number[];
  onSelectionChange: (indices: number[]) => void;
  disabled?: boolean;
}

export function NodeSelector({
  nodes,
  selectedIndices,
  onSelectionChange,
  disabled,
}: NodeSelectorProps) {
  const [query, setQuery] = useState("");

  const selectedSet = useMemo(
    () => new Set(selectedIndices),
    [selectedIndices],
  );

  const filteredNodes = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    if (!keyword) return nodes;
    return nodes.filter(
      (node) =>
        node.name.toLowerCase().includes(keyword) ||
        node.type.toLowerCase().includes(keyword) ||
        node.server.toLowerCase().includes(keyword),
    );
  }, [nodes, query]);

  const allFilteredSelected =
    filteredNodes.length > 0 &&
    filteredNodes.every((node) => selectedSet.has(node.index));

  function toggleNode(index: number) {
    if (selectedSet.has(index)) {
      onSelectionChange(selectedIndices.filter((item) => item !== index));
    } else {
      onSelectionChange([...selectedIndices, index]);
    }
  }

  function toggleAllFiltered() {
    if (allFilteredSelected) {
      const filteredSet = new Set(filteredNodes.map((node) => node.index));
      onSelectionChange(
        selectedIndices.filter((index) => !filteredSet.has(index)),
      );
    } else {
      const merged = new Set(selectedIndices);
      filteredNodes.forEach((node) => merged.add(node.index));
      onSelectionChange(Array.from(merged));
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {/* 工具栏 */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索节点名称 / 类型 / 地址"
            className="pl-8"
            disabled={disabled}
          />
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={toggleAllFiltered}
          disabled={disabled || filteredNodes.length === 0}
        >
          {allFilteredSelected ? "取消全选" : "全选"}
        </Button>
      </div>

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          已选 {selectedIndices.length} / {nodes.length} 个节点
        </span>
        {query.trim() ? <span>筛选 {filteredNodes.length} 个</span> : null}
      </div>

      {/* 节点列表 */}
      <div className="max-h-80 overflow-y-auto rounded-lg border">
        {filteredNodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-1 p-8 text-center text-sm text-muted-foreground">
            {nodes.length === 0 ? "尚未解析订阅" : "没有匹配的节点"}
          </div>
        ) : (
          <ul className="divide-y">
            {filteredNodes.map((node) => {
              const checked = selectedSet.has(node.index);
              return (
                <li key={node.index}>
                  <Label
                    className={cn(
                      "flex cursor-pointer items-center gap-2.5 px-3 py-2 text-sm font-normal transition-colors",
                      checked ? "bg-primary/5" : "hover:bg-muted/50",
                      disabled && "pointer-events-none opacity-60",
                    )}
                  >
                    <Checkbox
                      checked={checked}
                      onCheckedChange={() => toggleNode(node.index)}
                      disabled={disabled}
                      className="pointer-events-none"
                    />
                    <span className="min-w-0 flex-1 truncate font-medium">
                      {node.name}
                    </span>
                    <Badge variant="outline" className="shrink-0 uppercase">
                      {node.type}
                    </Badge>
                  </Label>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
