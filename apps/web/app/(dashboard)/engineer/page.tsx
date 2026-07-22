"use client";

import { useState } from "react";
import { useEngineerDashboard } from "@/features/dashboard";
import { EngineerTaskTable } from "@/features/task";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { StarPointDetailDialog } from "@/features/dashboard/client/StarPointDetailDialog";
import { EngineerSalaryDetail } from "@/features/dashboard/client/EngineerSalaryDetail";
import { DailyReportDialog } from "@/features/dashboard/client/DailyReportDialog";
import { HistoryDailyDialog } from "@/features/dashboard/client/HistoryDailyDialog";

/**
 * 工程师工作台首页
 *
 * 包含：5 个指标卡（当前星点、进行中、本月剩余工时、收入试算、T报准确率）
 *       + 筛选栏 + 任务列表（双标签：我的任务 / 竞价任务）
 */
export default function EngineerWorkspacePage() {
  const { data: dashboard, isLoading: dashLoading, refetch } = useEngineerDashboard();

  // 弹窗状态
  const [starPointOpen, setStarPointOpen] = useState(false);
  const [salaryOpen, setSalaryOpen] = useState(false);
  const [dailyReportOpen, setDailyReportOpen] = useState(false);
  const [historyDailyOpen, setHistoryDailyOpen] = useState(false);

  const metrics = [
    {
      label: "当前星点",
      value: dashboard?.current_starpoint != null ? `${dashboard.current_starpoint}` : "-",
      desc: "净增 + 累计",
      color: "purple",
      onClick: () => setStarPointOpen(true),
    },
    {
      label: "进行中",
      value: dashboard?.in_progress_task_count != null ? `${dashboard.in_progress_task_count}` : "-",
      desc: "当前进行中任务数",
      color: "blue",
    },
    {
      label: "本月剩余工时",
      value: dashboard?.T_remaining != null ? `${dashboard.T_remaining}h` : "-",
      desc: "接单前参考",
      color: "orange",
    },
    {
      label: "收入试算",
      value: dashboard?.salary_preview != null ? `¥${dashboard.salary_preview.toLocaleString()}` : "-",
      desc: "本人数据",
      color: "green",
      onClick: () => setSalaryOpen(true),
    },
    {
      label: "T报准确率",
      value: dashboard?.accuracy_rate != null ? `${dashboard.accuracy_rate}%` : "-",
      desc: "本月统计",
      color: "cyan",
    },
  ];

  return (
    <div className="space-y-6">
      {/* 指标卡 */}
      <div className="grid grid-cols-5 gap-4">
        {metrics.map((metric) => (
          <Card
            key={metric.label}
            className={`border-l-4 ${
              metric.color === "purple"
                ? "border-l-purple-500"
                : metric.color === "blue"
                  ? "border-l-blue-500"
                  : metric.color === "orange"
                    ? "border-l-orange-500"
                    : metric.color === "green"
                      ? "border-l-green-500"
                      : "border-l-cyan-500"
            } ${metric.onClick ? "cursor-pointer hover:shadow-md transition-shadow" : ""}`}
            onClick={metric.onClick}
          >
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {metric.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {dashLoading ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  metric.value
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {metric.desc}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 任务列表 */}
      <EngineerTaskTable
        extraActions={
          <div className="flex gap-2">
            <Button size="sm" onClick={() => setDailyReportOpen(true)}>
              工作汇报
            </Button>
            <Button variant="outline" size="sm" onClick={() => setHistoryDailyOpen(true)}>
              历史日报
            </Button>
          </div>
        }
      />

      {/* 星点明细弹窗 */}
      <StarPointDetailDialog
        open={starPointOpen}
        onOpenChange={setStarPointOpen}
      />

      {/* 收入试算弹窗 */}
      <EngineerSalaryDetail
        open={salaryOpen}
        onOpenChange={setSalaryOpen}
      />

      {/* 日报提交弹窗 */}
      <DailyReportDialog
        open={dailyReportOpen}
        onOpenChange={setDailyReportOpen}
        onSuccess={refetch}
      />

      {/* 历史日报弹窗 */}
      <HistoryDailyDialog
        open={historyDailyOpen}
        onOpenChange={setHistoryDailyOpen}
      />
    </div>
  );
}