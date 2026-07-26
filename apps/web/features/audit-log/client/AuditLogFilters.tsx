"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

/** 审计日志筛选状态 */
export interface AuditLogFiltersState {
  start_time: string;
  end_time: string;
  user_id: string;
}

/** 默认筛选条件 */
export const DEFAULT_AUDIT_LOG_FILTERS: AuditLogFiltersState = {
  start_time: "",
  end_time: "",
  user_id: "",
};

export interface AuditLogFiltersProps {
  filters: AuditLogFiltersState;
  onChange: (filters: AuditLogFiltersState) => void;
  users: Array<{ id: string; full_name?: string | null }>;
}

/**
 * 审计日志筛选栏
 *
 * 支持：开始时间、结束时间、操作人 三个筛选条件，自动搜索无按钮
 */
export function AuditLogFilters({
  filters,
  onChange,
  users = [],
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

      {/* 操作人 */}
      <Select
        value={filters.user_id}
        onValueChange={(v) =>
          onChange({ ...filters, user_id: v === "all" ? "" : v })
        }
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="全部操作人" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部操作人</SelectItem>
          {users.map((u) => (
            <SelectItem key={u.id} value={u.id}>
              {u.full_name || u.id.slice(0, 8)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
