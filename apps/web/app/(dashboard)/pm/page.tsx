"use client";

import { useState } from "react";
import { usePmDashboard } from "@/features/dashboard";
import { PMTaskTable } from "@/features/task";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

const colorClasses: Record<string, string> = {
  cyan: "border-l-4 border-l-cyan-500",
  blue: "border-l-4 border-l-blue-500",
  green: "border-l-4 border-l-green-500",
  orange: "border-l-4 border-l-orange-500",
};

/**
 * PM 工作台首页
 *
 * 包含：4 个指标卡 + 任务管理表格
 */
export default function PMWorkspacePage() {
  const { data: dashboard, isLoading: dashLoading } = usePmDashboard();

  const metrics = [
    {
      label: "本月新增客资",
      value: dashboard?.monthly_new_clients ?? "-",
      desc: "本月客资累计",
      color: "cyan",
    },
    {
      label: "今日新增客资",
      value: dashboard?.today_new_clients ?? "-",
      desc: "今日新增客户资源",
      color: "blue",
    },
    {
      label: "收入试算",
      value: dashboard?.salary_preview != null ? `¥${dashboard.salary_preview.toLocaleString()}` : "-",
      desc: "本月预估收入",
      color: "green",
    },
    {
      label: "我发布的任务",
      value: dashboard?.pm_task_count != null ? `${dashboard.pm_task_count}` : "-",
      desc: dashboard?.pm_task_count != null ? `发布的任务数量` : "查看全部任务",
      color: "orange",
    },
  ];

  return (
    <div className="space-y-6">
      {/* 指标卡 */}
      <div className="grid grid-cols-4 gap-4">
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
              <p className="text-xs text-muted-foreground mt-1">
                {metric.desc}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 任务管理表格 */}
      <PMTaskTable />
    </div>
  );
}