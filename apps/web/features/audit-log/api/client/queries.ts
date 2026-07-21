/**
 * 审计日志模块 — API Query Hooks
 */
"use client";

import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import {
  readAuditLogsV1AuditLogsGet,
  type AuditLogList,
  type ReadAuditLogsV1AuditLogsGetData,
} from "@repo/sdk";

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