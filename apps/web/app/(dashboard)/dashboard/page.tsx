"use client";

import { useAdminDashboard } from "@/features/dashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

/**
 * 管理员数据概览页面
 *
 * 调用 GET /v1/dashboard/admin 获取数据
 * 展示：4 个指标卡 + 工程师负载 + 星点排行榜 + PM客资列表 + 收入统计
 */
export default function DashboardPage() {
  const { data: dashboard, isLoading } = useAdminDashboard();

  const metrics = [
    {
      label: "今日新增客资",
      value: dashboard?.today_new_clients ?? "-",
      desc: "昨日新增 38",
      color: "cyan",
    },
    {
      label: "本月新增客资",
      value: dashboard?.monthly_new_clients ?? "-",
      desc: "上月新增客资 290",
      color: "orange",
    },
    {
      label: "今日提交日志量",
      value: dashboard?.today_submitted_reports ?? "-",
      desc: "工程师提交的工作日志",
      color: "cyan",
    },
    {
      label: "进行中任务",
      value: dashboard?.ongoing_tasks ?? "-",
      desc: "当前进行中的任务总数",
      color: "blue",
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">数据概览</h1>
        <p className="text-muted-foreground">系统整体运营数据</p>
      </div>

      {/* 指标卡 */}
      <div className="grid grid-cols-4 gap-4">
        {metrics.map((metric) => (
          <Card key={metric.label} className={`border-l-4 border-l-${metric.color}-500`}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {metric.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <p className="text-xs text-muted-foreground mt-1">{metric.desc}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 工程师负载 + 星点排行榜 */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>工程师负载</CardTitle>
          </CardHeader>
          <CardContent>
            {dashboard?.engineer_loads && dashboard.engineer_loads.length > 0 ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    <th className="text-left py-2">工程师</th>
                    <th className="text-left py-2">任务数</th>
                    <th className="text-left py-2">T月剩余</th>
                    <th className="text-left py-2">T报准确率</th>
                    <th className="text-left py-2">风险</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.engineer_loads.map((eng) => (
                    <tr key={eng.user_id} className="border-b last:border-0">
                      <td className="py-2">{eng.full_name}</td>
                      <td className="py-2">{eng.current_tasks}</td>
                      <td className="py-2">{eng.T_remaining}h</td>
                      <td className="py-2">
                        {eng.accuracy_rate != null ? `${eng.accuracy_rate.toFixed(0)}%` : "-"}
                      </td>
                      <td className="py-2">
                        <span className={`pill ${eng.accuracy_rate != null && eng.accuracy_rate >= 80 ? "green" : "orange"}`}>
                          {eng.accuracy_rate != null && eng.accuracy_rate >= 80 ? "正常" : "关注"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-muted-foreground">暂无数据</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>工程师星点排行榜</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              工程师星点排名数据将在后续版本中展示
            </p>
          </CardContent>
        </Card>
      </div>

      {/* PM客资列表 + 收入统计 */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>PM客资列表</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              PM客资数据将在后续版本中展示
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>收入统计</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">月度总收入</span>
              <span className="font-medium">¥{dashboard?.total_salary?.toLocaleString() ?? "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">工程师成本</span>
              <span className="font-medium">¥{dashboard?.engineer_salary_cost?.toLocaleString() ?? "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">PM成本</span>
              <span className="font-medium">¥{dashboard?.pm_salary_cost?.toLocaleString() ?? "-"}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}