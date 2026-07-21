"use client";

import { useEngineerDashboard } from "@/features/dashboard";
import { EngineerTaskTable } from "@/features/task";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

/**
 * 工程师工作台首页
 *
 * 包含：5 个指标卡 + 任务列表（双标签：我的任务 / 竞价任务）
 */
export default function EngineerWorkspacePage() {
  const { data: dashboard, isLoading: dashLoading } = useEngineerDashboard();

  const metrics = [
    {
      label: "当前星点",
      value: dashboard?.current_starpoint != null ? `${dashboard.current_starpoint}` : "-",
      desc: "累计星点",
      color: "purple",
    },
    {
      label: "月度计划工时",
      value: dashboard?.T_monthly_plan != null ? `${dashboard.T_monthly_plan}h` : "-",
      desc: "本月计划",
      color: "cyan",
    },
    {
      label: "剩余工时",
      value: dashboard?.T_remaining != null ? `${dashboard.T_remaining}h` : "-",
      desc: "T_remaining = T_monthly_plan - T_actual_monthly",
      color: "orange",
    },
    {
      label: "本月实际工时",
      value: dashboard?.T_actual_monthly != null ? `${dashboard.T_actual_monthly}h` : "-",
      desc: "T实累计",
      color: "blue",
    },
    {
      label: "收入试算",
      value: dashboard?.salary_preview != null ? `¥${dashboard.salary_preview.toLocaleString()}` : "-",
      desc: "本月预估收入",
      color: "green",
    },
  ];

  return (
    <div className="space-y-6">
      {/* 指标卡 */}
      <div className="grid grid-cols-5 gap-4">
        {metrics.map((metric) => (
          <Card key={metric.label} className={`border-l-4 border-l-${metric.color}-500`}>
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
      <EngineerTaskTable />
    </div>
  );
}