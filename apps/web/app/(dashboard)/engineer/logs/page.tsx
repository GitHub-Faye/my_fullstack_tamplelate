"use client";

import { useState } from "react";
import { useAuditLogs } from "@/features/audit-log/api";
import { AuditLogTable, type AuditLogItem } from "@/features/audit-log/client";
import { Pagination } from "@/components/ui/pagination";

/**
 * 工程师操作日志页面
 *
 * 调用 GET /v1/audit-logs 查看当前用户的操作日志
 */
export default function EngineerLogsPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading } = useAuditLogs({
    page,
    page_size: 20,
  });

  const logs = (data?.data || []) as AuditLogItem[];
  const count = data?.count || 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">操作日志</h1>
        <p className="text-muted-foreground">查看您的操作记录</p>
      </div>

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