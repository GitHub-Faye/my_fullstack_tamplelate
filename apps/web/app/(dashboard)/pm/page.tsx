"use client";

import { useState } from "react";
import { usePmDashboard } from "@/features/dashboard";
import { PMTaskTable } from "@/features/task";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PmSalaryDetailDialog } from "@/features/dashboard/client/PmSalaryDetail";

const colorClasses: Record<string, string> = {
  cyan: "border-l-4 border-l-cyan-500",
  blue: "border-l-4 border-l-blue-500",
  green: "border-l-4 border-l-green-500",
  orange: "border-l-4 border-l-orange-500",
};

/**
 * PM 工作台首页
 *
 * 包含：4 个指标卡（含环比数据、分状态计数）+ 任务管理表格
 */
export default function PMWorkspacePage() {
  const { data: dashboard, isLoading: dashLoading } = usePmDashboard();
  const [salaryOpen, setSalaryOpen] = useState(false);

  const taskStatusDesc = [
    dashboard?.task_count_bidding != null && `竞价中 ${dashboard.task_count_bidding}`,
    dashboard?.task_count_in_progress != null && `进行中 ${dashboard.task_count_in_progress}`,
    dashboard?.task_count_unconfirmed != null && `未确认 ${dashboard.task_count_unconfirmed}`,
    dashboard?.task_count_completed != null && `已完成 ${dashboard.task_count_completed}`,
    dashboard?.task_count_paused != null && `暂停中 ${dashboard.task_count_paused}`,
  ]
    .filter(Boolean)
    .join(" / ");

  const metrics = [
    {
      label: "收入试算",
      value: dashboard?.salary_preview != null ? `¥${dashboard.salary_preview.toLocaleString()}` : "-",
      desc: "本月预估收入",
      color: "green",
      action: (
        <Button
          variant="link"
          size="sm"
          className="h-auto p-0 text-xs"
          onClick={() => setSalaryOpen(true)}
        >
          <Eye className="h-3 w-3 mr-1" />
          查看明细
        </Button>
      ),
    },
    {
      label: "我发布的任务",
      value: dashboard?.pm_task_count != null ? `${dashboard.pm_task_count}` : "-",
      desc: taskStatusDesc || "发布的任务数量",
      color: "orange",
    },
  ];

  return (
    <div className="space-y-6">
      {/* 指标卡 */}
      <div className="grid grid-cols-2 gap-4">
        {metrics.map((metric) => (
          <Card key={metric.label} className={colorClasses[metric.color] || ""}>
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
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                {metric.desc}
                {metric.action}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 收入试算明细弹窗 */}
      <PmSalaryDetailDialog open={salaryOpen} onOpenChange={setSalaryOpen} />

      {/* 任务管理表格 */}
      <PMTaskTable />
    </div>
  );
}