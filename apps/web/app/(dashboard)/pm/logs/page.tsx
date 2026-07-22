"use client";

import { useFilteredAuditLogs } from "@/features/audit-log/api";
import {
  AuditLogTable,
  AuditLogFilters,
} from "@/features/audit-log/client";
import { Pagination } from "@/components/ui/pagination";

/**
 * PM 操作日志页面
 *
 * 调用 GET /v1/audit-logs 查看当前用户的操作日志
 * 支持日期范围筛选和操作类型筛选
 */
export default function PMLogsPage() {
  const { filters, setFilters, page, setPage, logs, count, isLoading, handleSearch, handleReset } = useFilteredAuditLogs();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">本人相关操作日志</h1>
        <p className="text-muted-foreground">查看您的操作记录</p>
      </div>

      <AuditLogFilters
        filters={filters}
        onChange={setFilters}
        onSearch={handleSearch}
        onReset={handleReset}
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