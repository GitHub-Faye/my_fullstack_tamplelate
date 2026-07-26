"use client";

import { Input } from "@/components/ui/input";

/** 仅日期范围的审计日志筛选状态 */
export interface AuditLogDateFiltersState {
  start_time: string;
  end_time: string;
}

/** 默认日期筛选条件 */
export const DEFAULT_AUDIT_LOG_DATE_FILTERS: AuditLogDateFiltersState = {
  start_time: "",
  end_time: "",
};

export interface AuditLogDateFiltersProps {
  filters: AuditLogDateFiltersState;
  onChange: (filters: AuditLogDateFiltersState) => void;
}

/**
 * 审计日志日期筛选栏
 *
 * 仅包含开始时间和结束时间，无操作人选择
 * 适用于 PM、工程师等只看本人操作的页面
 */
export function AuditLogDateFilters({
  filters,
  onChange,
}: AuditLogDateFiltersProps) {
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
    </div>
  );
}