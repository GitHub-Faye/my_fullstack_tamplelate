"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, RotateCcw } from "lucide-react";
import { ACTION_OPTIONS } from "./actionLabels";

/** 审计日志筛选状态 */
export interface AuditLogFiltersState {
  start_time: string;
  end_time: string;
  action: string;
}

/** 默认筛选条件 */
export const DEFAULT_AUDIT_LOG_FILTERS: AuditLogFiltersState = {
  start_time: "",
  end_time: "",
  action: "all",
};

export { ACTION_OPTIONS };

export interface AuditLogFiltersProps {
  filters: AuditLogFiltersState;
  onChange: (filters: AuditLogFiltersState) => void;
  onSearch: () => void;
  onReset: () => void;
}

/**
 * 审计日志筛选栏
 *
 * 支持：日期范围（start_time / end_time）、操作类型（action）、搜索与重置
 */
export function AuditLogFilters({
  filters,
  onChange,
  onSearch,
  onReset,
}: AuditLogFiltersProps) {
  return (
    <div className="flex items-center gap-4 mb-4 flex-wrap">
      {/* 开始时间 */}
      <Input
        type="date"
        className="w-[150px]"
        value={filters.start_time}
        onChange={(e) =>
          onChange({ ...filters, start_time: e.target.value })
        }
        placeholder="开始时间"
      />

      {/* 结束时间 */}
      <Input
        type="date"
        className="w-[150px]"
        value={filters.end_time}
        onChange={(e) =>
          onChange({ ...filters, end_time: e.target.value })
        }
        placeholder="结束时间"
      />

      {/* 操作类型 */}
      <Select
        value={filters.action}
        onValueChange={(v) =>
          onChange({ ...filters, action: v })
        }
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="操作类型" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部操作</SelectItem>
          {ACTION_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 搜索 */}
      <Button variant="outline" size="sm" onClick={onSearch}>
        <Search className="mr-1 h-4 w-4" />
        搜索
      </Button>

      {/* 重置 */}
      <Button variant="ghost" size="sm" onClick={onReset}>
        <RotateCcw className="mr-1 h-4 w-4" />
        重置
      </Button>
    </div>
  );
}
