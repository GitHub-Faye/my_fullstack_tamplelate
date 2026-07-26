"use client";

import { useFilteredAuditLogs } from "@/features/audit-log/api";
import {
  AuditLogTable,
  AuditLogDateFilters,
  type AuditLogDateFiltersState,
} from "@/features/audit-log/client";
import { Pagination } from "@/components/ui/pagination";

/**
 * PM 操作日志页面
 *
 * 调用 GET /v1/audit-logs 查看当前用户的操作日志
 * PM 只能看见自己的操作，所以没有操作人筛选，仅日期范围筛选
 */
export default function PMLogsPage() {
  const { filters, setFilters, page, setPage, logs, count, isLoading } = useFilteredAuditLogs();

  const handleDateFilterChange = (dateFilters: AuditLogDateFiltersState) => {
    setFilters({ start_time: dateFilters.start_time, end_time: dateFilters.end_time, user_id: "" });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">本人相关操作日志</h1>
        <p className="text-muted-foreground">查看您的操作记录</p>
      </div>

      <AuditLogDateFilters
        filters={{ start_time: filters.start_time, end_time: filters.end_time }}
        onChange={handleDateFilterChange}
      />

      <AuditLogTable
        logs={logs}
        isLoading={isLoading}
        title="本人相关操作日志"
      />

      {count > 20 && (
        <Pagination
          page={page}
          total={count}
          pageSize={20}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}