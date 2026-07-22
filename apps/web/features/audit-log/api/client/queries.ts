/**
 * 审计日志模块 — API Query Hooks
 */
"use client";

import { useCallback, useState } from "react";
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
 * 通用的审计日志筛选状态管理 hook
 * 封装 filters/activeFilters 双状态、分页、handleSearch/handleReset 逻辑
 */
export function useFilteredAuditLogs(initialPageSize = 20) {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<AuditLogFiltersState>(DEFAULT_AUDIT_LOG_FILTERS);
  const [activeFilters, setActiveFilters] = useState<AuditLogFiltersState>(DEFAULT_AUDIT_LOG_FILTERS);

  const query = useAuditLogs({
    page,
    page_size: initialPageSize,
    start_time: activeFilters.start_time || undefined,
    end_time: activeFilters.end_time || undefined,
    action: activeFilters.action !== "all" ? activeFilters.action : undefined,
  });

  const logs = (query.data?.data || []) as AuditLogItem[];
  const count = query.data?.count || 0;

  const handleSearch = useCallback(() => {
    setActiveFilters(filters);
    setPage(1);
  }, [filters]);

  const handleReset = useCallback(() => {
    setFilters(DEFAULT_AUDIT_LOG_FILTERS);
    setActiveFilters(DEFAULT_AUDIT_LOG_FILTERS);
    setPage(1);
  }, []);

  return {
    filters,
    setFilters,
    page,
    setPage,
    logs,
    count,
    isLoading: query.isLoading,
    handleSearch,
    handleReset,
  };
}