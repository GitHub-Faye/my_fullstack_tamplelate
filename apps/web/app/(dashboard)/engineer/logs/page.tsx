"use client";

import { useState } from "react";
import { useAuditLogs } from "@/features/audit-log/api";
import { AuditLogTable, type AuditLogItem } from "@/features/audit-log/client";
import { AuditLogFilters, DEFAULT_AUDIT_LOG_FILTERS, type AuditLogFiltersState } from "@/features/audit-log/client";
import { Pagination } from "@/components/ui/pagination";

/**
 * 工程师操作日志页面
 *
 * 调用 GET /v1/audit-logs 查看当前用户的操作日志
 * 支持按日期范围、操作类型筛选
 */
export default function EngineerLogsPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<AuditLogFiltersState>(DEFAULT_AUDIT_LOG_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<AuditLogFiltersState>(DEFAULT_AUDIT_LOG_FILTERS);

  const queryParams: Record<string, any> = {
    page,
    page_size: 20,
  };
  if (appliedFilters.start_time) queryParams.start_time = appliedFilters.start_time;
  if (appliedFilters.end_time) queryParams.end_time = appliedFilters.end_time;
  if (appliedFilters.action && appliedFilters.action !== "all") queryParams.action = appliedFilters.action;

  const { data, isLoading } = useAuditLogs(queryParams);

  const logs = (data?.data || []) as AuditLogItem[];
  const count = data?.count || 0;

  const handleSearch = () => {
    setAppliedFilters({ ...filters });
    setPage(1);
  };

  const handleReset = () => {
    setFilters(DEFAULT_AUDIT_LOG_FILTERS);
    setAppliedFilters(DEFAULT_AUDIT_LOG_FILTERS);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">操作日志</h1>
        <p className="text-muted-foreground">查看您的操作记录</p>
      </div>

      {/* 筛选栏 */}
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