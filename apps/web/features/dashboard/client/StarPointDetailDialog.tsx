"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
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
 * 支持：时间筛选（起止日期）、类型筛选（全部/增加/扣减）
 * 表格：时间、任务、规则、T报、T实、完成比例、星点变化、说明
 * 底部汇总：本月增加、本月扣减、净变化、当前排名
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
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

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
    if (typeFilter === "increase" && r.change_amount <= 0) return false;
    if (typeFilter === "decrease" && r.change_amount >= 0) return false;
    if (startDate) {
      const d = new Date(r.created_at);
      const s = new Date(startDate);
      if (d < s) return false;
    }
    if (endDate) {
      const d = new Date(r.created_at);
      const e = new Date(endDate + "T23:59:59");
      if (d > e) return false;
    }
    return true;
  });

  // 本月扣减和净变化从 records 计算
  const monthIncrease = records?.filter((r) => r.change_amount > 0).reduce((s, r) => s + r.change_amount, 0) ?? 0;
  const monthDecrease = records?.filter((r) => r.change_amount < 0).reduce((s, r) => s + Math.abs(r.change_amount), 0) ?? 0;
  const netChange = monthIncrease - monthDecrease;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>星点明细</DialogTitle>
          <DialogDescription>查看星点变化记录和汇总信息</DialogDescription>
        </DialogHeader>

        {/* 筛选栏 */}
        <div className="flex items-center gap-4 mb-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">时间</label>
            <Input
              type="date"
              className="w-[140px]"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
            <span className="text-muted-foreground">至</span>
            <Input
              type="date"
              className="w-[140px]"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
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
                +{monthIncrease}
              </div>
            </div>
            <div className="p-3 bg-muted/30 rounded-md text-center">
              <div className="text-sm text-muted-foreground">本月扣减</div>
              <div className="text-lg font-bold text-red-600">
                -{monthDecrease}
              </div>
            </div>
            <div className="p-3 bg-muted/30 rounded-md text-center">
              <div className="text-sm text-muted-foreground">净变化</div>
              <div className="text-lg font-bold">
                {netChange >= 0 ? `+${netChange}` : netChange}
              </div>
            </div>
            <div className="p-3 bg-muted/30 rounded-md text-center">
              <div className="text-sm text-muted-foreground">当前排名</div>
              <div className="text-lg font-bold">
                {summary.rank != null ? `第${summary.rank}名` : "-"}
              </div>
            </div>
          </div>
        )}

        {/* 明细表格 */}
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : filteredRecords && filteredRecords.length > 0 ? (
          <div className="rounded-md border overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground bg-muted/50">
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">时间</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">任务</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">规则</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">T报</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">T实</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">完成比例</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">星点变化</th>
                  <th className="text-left px-3 py-2 font-medium whitespace-nowrap">说明</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((r: any, i: number) => {
                  const ratio =
                    r.T_reported && r.T_reported > 0
                      ? `${Math.round((r.T_actual ?? 0) / r.T_reported * 100)}%`
                      : "-";
                  return (
                    <tr key={r.id ?? i} className="border-b last:border-0">
                      <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">
                        {formatDateTime(r.created_at)}
                      </td>
                      <td className="px-3 py-2 max-w-[150px] truncate">
                        {r.task_name ?? "-"}
                      </td>
                      <td className="px-3 py-2">{r.judgment_type ?? "-"}</td>
                      <td className="px-3 py-2">
                        {r.T_reported != null ? `${r.T_reported}h` : "-"}
                      </td>
                      <td className="px-3 py-2">
                        {r.T_actual != null ? `${r.T_actual}h` : "-"}
                      </td>
                      <td className="px-3 py-2">{ratio}</td>
                      <td
                        className={`px-3 py-2 font-medium ${
                          r.change_amount > 0 ? "text-green-600" : "text-red-600"
                        }`}
                      >
                        {r.change_amount > 0
                          ? `+${r.change_amount}`
                          : r.change_amount}
                      </td>
                      <td className="px-3 py-2 text-muted-foreground max-w-[150px] truncate">
                        {r.reason ?? "-"}
                      </td>
                    </tr>
                  );
                })}
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