"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Loader2 } from "lucide-react";
import { readAuditLogsV1AuditLogsGet, type TaskPublic } from "@repo/sdk";
import { formatDateTime } from "@/lib/utils";

/**
 * 审计日志弹窗（查看日志 / 暂停记录 / 归档日志）
 *
 * 查看指定任务的操作审计记录
 */
export function AuditLogDialog({
  task,
  open,
  onOpenChange,
}: {
  task: TaskPublic;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [logs, setLogs] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && task) {
      setLoading(true);
      readAuditLogsV1AuditLogsGet({
        query: { target_type: "task", target_id: task.id, page: 1, page_size: 50 },
      })
        .then((res) => setLogs(res.data?.data ?? []))
        .catch(() => setLogs([]))
        .finally(() => setLoading(false));
    }
  }, [open, task]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>任务日志 - {task.name}</DialogTitle>
          <DialogDescription>查看该任务的操作记录</DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : logs && logs.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="text-left px-3 py-2 font-medium">时间</th>
                <th className="text-left px-3 py-2 font-medium">操作</th>
                <th className="text-left px-3 py-2 font-medium">详情</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log: any, i: number) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">{formatDateTime(log.created_at)}</td>
                  <td className="px-3 py-2">{log.action ?? "-"}</td>
                  <td className="px-3 py-2 text-muted-foreground">{log.details ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-center py-8 text-muted-foreground">暂无日志记录</p>
        )}
      </DialogContent>
    </Dialog>
  );
}