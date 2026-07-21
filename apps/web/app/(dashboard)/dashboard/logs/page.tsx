"use client";

import { useState, useCallback } from "react";
import { useAuditLogs } from "@/features/audit-log/api";
import {
  AuditLogTable,
  AuditLogFilters,
  type AuditLogItem,
  type AuditLogFiltersState,
  DEFAULT_AUDIT_LOG_FILTERS,
} from "@/features/audit-log/client";
import { Pagination } from "@/components/ui/pagination";

/**
 * 管理员全量操作日志页面
 *
 * 调用 GET /v1/audit-logs 查看所有用户的操作日志
 * 支持日期范围筛选和操作类型筛选
 */
export default function AdminLogsPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<AuditLogFiltersState>(DEFAULT_AUDIT_LOG_FILTERS);
  const [activeFilters, setActiveFilters] = useState<AuditLogFiltersState>(DEFAULT_AUDIT_LOG_FILTERS);

  const { data, isLoading } = useAuditLogs({
    page,
    page_size: 20,
    start_time: activeFilters.start_time || undefined,
    end_time: activeFilters.end_time || undefined,
    action: activeFilters.action !== "all" ? activeFilters.action : undefined,
  });

  const logs = (data?.data || []) as AuditLogItem[];
  const count = data?.count || 0;

  const handleSearch = useCallback(() => {
    setActiveFilters(filters);
    setPage(1);
  }, [filters]);

  const handleReset = useCallback(() => {
    setFilters(DEFAULT_AUDIT_LOG_FILTERS);
    setActiveFilters(DEFAULT_AUDIT_LOG_FILTERS);
    setPage(1);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">操作日志</h1>
        <p className="text-muted-foreground">查看全量操作记录</p>
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
        title="全量操作日志"
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