"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { readDailyReportsV1DailyReportsGet, type TaskPublic } from "@repo/sdk";
import { formatDate } from "@/lib/utils";

/**
 * 历史日报弹窗
 *
 * 查看当前工程师的历史日报记录
 */
export function HistoryDailyDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [reports, setReports] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      setLoading(true);
      readDailyReportsV1DailyReportsGet({
        throwOnError: true,
        query: { page: 1, page_size: 50 },
      })
        .then((res) => setReports(res.data?.data ?? []))
        .catch(() => setReports([]))
        .finally(() => setLoading(false));
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>历史日报</DialogTitle>
          <DialogDescription>查看历史日报记录</DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : reports && reports.length > 0 ? (
          <div className="rounded-md border overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground bg-muted/50">
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">日期</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">投入</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">阶段</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">进度</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">完成判定</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">星点变化</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">说明</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((rpt: any, i: number) => (
                  <tr key={i} className="border-b last:border-0">
                    <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">
                      {formatDate(rpt.report_date ?? rpt.created_at)}
                    </td>
                    <td className="px-3 py-2">{rpt.today_hours ?? "-"}h</td>
                    <td className="px-3 py-2">{rpt.current_stage ?? "-"}</td>
                    <td className="px-3 py-2">{rpt.progress ?? "-"}</td>
                    <td className="px-3 py-2">{rpt.completion_judgment ?? "-"}</td>
                    <td className="px-3 py-2">
                      {rpt.starpoint_change != null && rpt.starpoint_change !== 0 ? (
                        <span className={rpt.starpoint_change > 0 ? "text-green-600" : "text-red-600"}>
                          {rpt.starpoint_change > 0 ? `+${rpt.starpoint_change}` : rpt.starpoint_change}
                        </span>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground max-w-[200px] truncate">
                      {rpt.notes ?? "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center py-8 text-muted-foreground">暂无历史日报</p>
        )}
      </DialogContent>
    </Dialog>
  );
}