"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import {
  readMyStarpointsV1StarpointsMyGet,
  readMyStarpointSummaryV1StarpointsMySummaryGet,
} from "@repo/sdk";
import { formatDateTime } from "@/lib/utils";

/**
 * 星点明细弹窗
 *
 * 查看当前工程师的星点变化记录和汇总信息
 */
export function StarPointDetailDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [records, setRecords] = useState<any[] | null>(null);
  const [summary, setSummary] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    if (open) {
      setLoading(true);
      Promise.all([
        readMyStarpointsV1StarpointsMyGet({ throwOnError: true }).then((r) =>
          setRecords(r.data?.data ?? [])
        ),
        readMyStarpointSummaryV1StarpointsMySummaryGet({ throwOnError: true }).then(
          (r) => setSummary(r.data)
        ),
      ])
        .catch(() => {
          setRecords([]);
          setSummary(null);
        })
        .finally(() => setLoading(false));
    }
  }, [open]);

  const filteredRecords = records?.filter((r) => {
    if (typeFilter === "increase") return r.change_amount > 0;
    if (typeFilter === "decrease") return r.change_amount < 0;
    return true;
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>星点明细</DialogTitle>
          <DialogDescription>查看星点变化记录和汇总信息</DialogDescription>
        </DialogHeader>

        {/* 筛选栏 */}
        <div className="flex items-center gap-4 mb-4">
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-[130px]">
              <SelectValue placeholder="类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              <SelectItem value="increase">增加</SelectItem>
              <SelectItem value="decrease">扣减</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 汇总信息 */}
        {summary && (
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div className="p-3 bg-muted/30 rounded-md text-center">
              <div className="text-sm text-muted-foreground">本月增加</div>
              <div className="text-lg font-bold text-green-600">
                +{summary.current_month_earned}
              </div>
            </div>
            <div className="p-3 bg-muted/30 rounded-md text-center">
              <div className="text-sm text-muted-foreground">当前排名</div>
              <div className="text-lg font-bold">
                {summary.rank != null ? `第${summary.rank}名` : "-"}
              </div>
            </div>
            <div className="p-3 bg-muted/30 rounded-md text-center">
              <div className="text-sm text-muted-foreground">K系数</div>
              <div className="text-lg font-bold">{summary.k_coefficient}</div>
            </div>
            <div className="p-3 bg-muted/30 rounded-md text-center">
              <div className="text-sm text-muted-foreground">星点总数</div>
              <div className="text-lg font-bold">{summary.total_starpoints}</div>
            </div>
          </div>
        )}

        {/* 明细表格 */}
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : filteredRecords && filteredRecords.length > 0 ? (
          <div className="rounded-md border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground bg-muted/50">
                  <th className="text-left px-3 py-2 font-medium">时间</th>
                  <th className="text-left px-3 py-2 font-medium">任务</th>
                  <th className="text-left px-3 py-2 font-medium">T报</th>
                  <th className="text-left px-3 py-2 font-medium">T实</th>
                  <th className="text-left px-3 py-2 font-medium">星点变化</th>
                  <th className="text-left px-3 py-2 font-medium">说明</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((r: any, i: number) => (
                  <tr key={r.id ?? i} className="border-b last:border-0">
                    <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">
                      {formatDateTime(r.created_at)}
                    </td>
                    <td className="px-3 py-2 max-w-[180px] truncate">
                      {r.reason ?? "-"}
                    </td>
                    <td className="px-3 py-2">
                      {r.T_reported != null ? `${r.T_reported}h` : "-"}
                    </td>
                    <td className="px-3 py-2">
                      {r.T_actual != null ? `${r.T_actual}h` : "-"}
                    </td>
                    <td
                      className={`px-3 py-2 font-medium ${
                        r.change_amount > 0 ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {r.change_amount > 0
                        ? `+${r.change_amount}`
                        : r.change_amount}
                    </td>
                    <td className="px-3 py-2 text-muted-foreground max-w-[200px] truncate">
                      {r.judgment_type ?? "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center py-8 text-muted-foreground">
            暂无星点记录
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}