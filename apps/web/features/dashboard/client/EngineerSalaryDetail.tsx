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
import { useQuery } from "@tanstack/react-query";
import { readMySalaryV1SalariesMyGet } from "@repo/sdk";
import { useEngineerDashboard } from "../api/client/queries";

/**
 * 工程师收入试算弹窗
 *
 * 显示 S0、月计划工时、T月剩余、K系数、调休/调整、收入试算
 * 使用 react-query hook 替代 raw fetch
 */
export function EngineerSalaryDetail({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { data: dashboard } = useEngineerDashboard();

  const { data: salary, isLoading } = useQuery({
    queryKey: ["salary", "my"],
    queryFn: async () => {
      const res = await readMySalaryV1SalariesMyGet({ throwOnError: true });
      return res.data as any;
    },
    enabled: open,
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>收入试算</DialogTitle>
          <DialogDescription>本人收入预估数据</DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : (
          <div className="space-y-3">
            <div className="rounded-md border">
              <table className="w-full text-sm">
                <tbody>
                  <tr className="border-b">
                    <td className="px-3 py-2 text-muted-foreground">S0</td>
                    <td className="px-3 py-2 font-medium">
                      {(salary as any)?.S0 != null
                        ? `¥${(salary as any).S0.toLocaleString()}`
                        : "-"}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      工程师月度工资基数
                    </td>
                  </tr>
                  <tr className="border-b">
                    <td className="px-3 py-2 text-muted-foreground">
                      个人月计划工时
                    </td>
                    <td className="px-3 py-2 font-medium">
                      {dashboard?.T_monthly_plan != null
                        ? `${dashboard.T_monthly_plan}h`
                        : "-"}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      按当月工作日计算
                    </td>
                  </tr>
                  <tr className="border-b">
                    <td className="px-3 py-2 text-muted-foreground">T月剩余</td>
                    <td className="px-3 py-2 font-medium">
                      {dashboard?.T_remaining != null
                        ? `${dashboard.T_remaining}h`
                        : "-"}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      当前剩余可承接工时
                    </td>
                  </tr>
                  <tr className="border-b">
                    <td className="px-3 py-2 text-muted-foreground">K系数</td>
                    <td className="px-3 py-2 font-medium">
                      {(salary as any)?.K != null ? (salary as any).K : "-"}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      星点排名系数
                    </td>
                  </tr>
                  <tr className="border-b">
                    <td className="px-3 py-2 text-muted-foreground">
                      调休/调整
                    </td>
                    <td className="px-3 py-2 font-medium">
                      {(salary as any)?.adjustment_hours != null
                        ? `+${(salary as any).adjustment_hours}h`
                        : "-"}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      紧急任务超法定工时返还
                    </td>
                  </tr>
                  <tr>
                    <td className="px-3 py-2 text-muted-foreground">收入试算</td>
                    <td className="px-3 py-2 font-bold text-lg text-green-600">
                      {dashboard?.salary_preview != null
                        ? `¥${dashboard.salary_preview.toLocaleString()}`
                        : "-"}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      月度试算，最终以管理员确认为准
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}