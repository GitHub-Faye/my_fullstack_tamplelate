"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { usePmDashboard } from "@/features/dashboard";
import { TaskTable } from "@/features/task";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Plus } from "lucide-react";

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
      value: "-",
      desc: "查看全部任务",
      color: "orange",
    },
  ];

  return (
    <div className="space-y-6">
      {/* 指标卡 */}
      <div className="grid grid-cols-4 gap-4">
        {metrics.map((metric) => (
          <Card key={metric.label}>
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
      <TaskTable />
    </div>
  );
}