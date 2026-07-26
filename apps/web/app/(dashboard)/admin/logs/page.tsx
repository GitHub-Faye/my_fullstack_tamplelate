"use client";

import { useFilteredAuditLogs } from "@/features/audit-log/api";
import { AuditLogTable, AuditLogFilters } from "@/features/audit-log/client";
import { Pagination } from "@/components/ui/pagination";
import { useUsers } from "@/features/user/api";

export default function AdminLogsPage() {
  const { filters, setFilters, page, setPage, logs, count, isLoading } = useFilteredAuditLogs();
  const { data: usersData } = useUsers({ page: 1, page_size: 100 });
  const users = (usersData?.data || []) as Array<{ id: string; full_name?: string | null }>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">操作日志</h1>
        <p className="text-muted-foreground">查看全量操作记录</p>
      </div>
      <AuditLogFilters filters={filters} onChange={setFilters} users={users} />
      <AuditLogTable logs={logs} isLoading={isLoading} title="全量操作日志" />
      {count > 20 && <Pagination page={page} total={count} pageSize={20} onPageChange={setPage} />}
    </div>
  );
}