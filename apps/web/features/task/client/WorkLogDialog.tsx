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
import { readDailyReportsV1DailyReportsGet, type TaskPublic } from "@repo/sdk";
import { formatDate } from "@/lib/utils";

/**
 * 工作日志弹窗（日报）
 *
 * 查看指定任务的工程师日报记录
 */
export function WorkLogDialog({
  task,
  open,
  onOpenChange,
}: {
  task: TaskPublic;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [reports, setReports] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && task) {
      setLoading(true);
      readDailyReportsV1DailyReportsGet({
        query: { task_id: task.id, page: 1, page_size: 50 },
      })
        .then((res) => setReports(res.data?.data ?? []))
        .catch(() => setReports([]))
        .finally(() => setLoading(false));
    }
  }, [open, task]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>工作日志 - {task.name}</DialogTitle>
          <DialogDescription>查看该任务的工程师日报记录</DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : reports && reports.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="text-left px-3 py-2 font-medium">日期</th>
                <th className="text-left px-3 py-2 font-medium">投入</th>
                <th className="text-left px-3 py-2 font-medium">阶段</th>
                <th className="text-left px-3 py-2 font-medium">进度</th>
                <th className="text-left px-3 py-2 font-medium">说明</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((rpt: any, i: number) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">{formatDate(rpt.report_date ?? rpt.created_at)}</td>
                  <td className="px-3 py-2">{rpt.today_hours ?? "-"}h</td>
                  <td className="px-3 py-2">{rpt.current_stage ?? "-"}</td>
                  <td className="px-3 py-2">{rpt.progress ?? "-"}</td>
                  <td className="px-3 py-2 text-muted-foreground max-w-[200px] truncate">{rpt.notes ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-center py-8 text-muted-foreground">暂无工作日志</p>
        )}
      </DialogContent>
    </Dialog>
  );
}