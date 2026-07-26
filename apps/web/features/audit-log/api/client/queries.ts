/**
 * 审计日志模块 — API Query Hooks
 */
"use client";

import { useMemo, useState } from "react";
import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import {
  readAuditLogsV1AuditLogsGet,
  type AuditLogList,
  type ReadAuditLogsV1AuditLogsGetData,
} from "@repo/sdk";
import {
  type AuditLogItem,
  type AuditLogFiltersState,
  DEFAULT_AUDIT_LOG_FILTERS,
} from "../../client";

export const auditLogKeys = {
  all: ["audit-logs"] as const,
  lists: () => [...auditLogKeys.all, "list"] as const,
  list: (filters: ReadAuditLogsV1AuditLogsGetData["query"]) =>
    [...auditLogKeys.lists(), filters] as const,
};

export function useAuditLogs(
  filters: ReadAuditLogsV1AuditLogsGetData["query"] = { page: 1, page_size: 20 },
  options?: Omit<
    UseQueryOptions<AuditLogList, Error, AuditLogList>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: auditLogKeys.list(filters),
    queryFn: async () => {
      const response = await readAuditLogsV1AuditLogsGet({
        query: filters,
        throwOnError: true,
      });
      return response.data as AuditLogList;
    },
    ...options,
  });
}

/**
 * 审计日志筛选状态管理 hook（自动搜索，无按钮）
 * 筛选条件变化即自动触发查询
 */
export function useFilteredAuditLogs(initialPageSize = 20) {
  const [filters, setFilters] = useState<AuditLogFiltersState>(DEFAULT_AUDIT_LOG_FILTERS);
  const [page, setPage] = useState(1);

  const query = useAuditLogs({
    page,
    page_size: initialPageSize,
    start_time: filters.start_time || undefined,
    end_time: filters.end_time || undefined,
    user_id: filters.user_id || undefined,
  });

  const logs = (query.data?.data || []) as AuditLogItem[];
  const count = query.data?.count || 0;

  const handleFilterChange = (newFilters: AuditLogFiltersState) => {
    setFilters(newFilters);
    setPage(1);
  };

  return {
    filters,
    setFilters: handleFilterChange,
    page,
    setPage,
    logs,
    count,
    isLoading: query.isLoading,
  };
}