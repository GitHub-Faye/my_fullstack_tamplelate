"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";
import { getTodayReportSummaryV1DailyReportsTodaySummaryGet } from "@repo/sdk";
import { AdminHistoryDailyDialog } from "./AdminHistoryDailyDialog";
import { formatDateTime } from "@/lib/utils";

/**
 * 今日提交日志弹窗（管理员）
 *
 * 展示所有工程师今日的日志提交情况：
 * - 已提交工程师：今日工作时长、提交时间、任务量
 * - 未提交工程师：不显示"查看今日详情"按钮
 *
 * 筛选：工程师下拉 + 日期选择
 * 点击"查看今日详情" → AdminHistoryDailyDialog（工程师当天的日报详情）
 */
export function TodayLogDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [data, setData] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [totalEngineers, setTotalEngineers] = useState(0);

  // 筛选条件
  const [filterDate, setFilterDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [filterEngineerId, setFilterEngineerId] = useState<string>("all");

  // 工程师选项（从数据中动态提取）
  const [engineerOptions, setEngineerOptions] = useState<{ id: string; name: string }[]>([]);

  // 查看详情弹窗
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [detailEngineerId, setDetailEngineerId] = useState<string>("");
  const [detailEngineerName, setDetailEngineerName] = useState("");
  const [detailDate, setDetailDate] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const query: Record<string, any> = { report_date: filterDate };
      if (filterEngineerId && filterEngineerId !== "all") {
        query.engineer_id = filterEngineerId;
      }
      const res = await getTodayReportSummaryV1DailyReportsTodaySummaryGet({
        throwOnError: true,
        query,
      });
      setData(res.data?.data ?? []);
      setTotalEngineers(res.data?.total_engineers ?? 0);
    } catch {
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [filterDate, filterEngineerId]);

  useEffect(() => {
    if (open) fetchData();
  }, [open, fetchData]);

  // 从数据中提取工程师选项
  useEffect(() => {
    if (data) {
      const options = data.map((item: any) => ({
        id: item.engineer_id,
        name: item.engineer_name,
      }));
      // 去重
      const seen = new Set<string>();
      const unique = options.filter((o) => {
        const dup = seen.has(o.id);
        seen.add(o.id);
        return !dup;
      });
      setEngineerOptions(unique);
    }
  }, [data]);

  const handleViewDetail = (engineerId: string, engineerName: string) => {
    setDetailEngineerId(engineerId);
    setDetailEngineerName(engineerName);
    setDetailDate(filterDate);
    setDetailDialogOpen(true);
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-5xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>今日提交日志详情</DialogTitle>
            <DialogDescription>
              共 {totalEngineers} 位工程师，已提交 {data?.filter((d) => d.status === "submitted").length ?? 0} 位
            </DialogDescription>
          </DialogHeader>

          {/* 筛选栏 */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground whitespace-nowrap">日期</label>
              <Input
                type="date"
                className="w-[150px]"
                value={filterDate}
                onChange={(e) => setFilterDate(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground whitespace-nowrap">工程师</label>
              <Select value={filterEngineerId} onValueChange={setFilterEngineerId}>
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="全部" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  {engineerOptions.map((opt) => (
                    <SelectItem key={opt.id} value={opt.id}>
                      {opt.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : data && data.length > 0 ? (
            <div className="rounded-md border overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground bg-muted/50">
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">工程师</th>
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">今日工作时长</th>
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">提交时间</th>
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">任务量</th>
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">状态</th>
                    <th className="text-left px-3 py-2 font-medium whitespace-nowrap">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((item: any, i: number) => (
                    <tr key={item.engineer_id ?? i} className="border-b last:border-0">
                      <td className="px-3 py-2 font-medium">{item.engineer_name ?? "-"}</td>
                      <td className="px-3 py-2">{item.today_hours != null ? `${item.today_hours}h` : "-"}</td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {item.submitted_at ? formatDateTime(item.submitted_at) : "-"}
                      </td>
                      <td className="px-3 py-2">{item.task_count ?? 0}个</td>
                      <td className="px-3 py-2">
                        {item.status === "submitted" ? (
                          <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                            已提交
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700">
                            未提交
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        {item.status === "submitted" ? (
                          <Button
                            variant="link"
                            className="h-auto p-0 text-sm"
                            onClick={() => handleViewDetail(item.engineer_id, item.engineer_name)}
                          >
                            查看今日详情
                          </Button>
                        ) : (
                          <span className="text-muted-foreground text-sm">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-center py-8 text-muted-foreground">暂无数据</p>
          )}
        </DialogContent>
      </Dialog>

      {/* 工程师日报详情弹窗 */}
      {detailDialogOpen && (
        <AdminHistoryDailyDialog
          open={detailDialogOpen}
          onOpenChange={setDetailDialogOpen}
          engineerId={detailEngineerId}
          engineerName={detailEngineerName}
          reportDate={detailDate}
        />
      )}
    </>
  );
}
