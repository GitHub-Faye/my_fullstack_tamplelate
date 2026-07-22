"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useQuery } from "@tanstack/react-query";
import { readSalarySummaryV1SalariesGet, exportSalariesV1SalariesExportPost } from "@repo/sdk";
import { Loader2, Search, Download } from "lucide-react";
import { toast } from "sonner";

export default function AdminSalariesPage() {
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const [person, setPerson] = useState("all");
  const [tab, setTab] = useState<"engineer" | "pm">("engineer");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["salary-summary", { page, page_size: pageSize }],
    queryFn: async () => {
      const response = await readSalarySummaryV1SalariesGet({
        query: { page, page_size: pageSize },
        throwOnError: true,
      });
      return response.data;
    },
  });

  const salaries = (data?.data || []) as any[];
  const totalCount = data?.count || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

  const filteredSalaries = person === "all"
    ? salaries
    : salaries.filter((s) => s.role === person);

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
        <h1 className="text-3xl font-bold">工资管理</h1>
        <p className="text-muted-foreground">查看和管理员工工资</p>
      </div>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <label className="text-sm">月份</label>
              <Input
                type="month"
                className="w-[160px]"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm">人员</label>
              <Select value={person} onValueChange={setPerson}>
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="全部" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="engineer">工程师</SelectItem>
                  <SelectItem value="pm">市场产品PM</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" size="sm">
              <Search className="mr-1 h-4 w-4" />搜索
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={async () => {
                try {
                  await exportSalariesV1SalariesExportPost({
                    body: { month },
                    throwOnError: true,
                  });
                  toast.success("工资表导出请求已提交");
                } catch {
                  toast.error("导出失败");
                }
              }}
            >
              <Download className="mr-1 h-4 w-4" />导出工资表
            </Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <CardTitle>工资管理</CardTitle>
            <div className="flex gap-1 bg-muted rounded-lg p-1">
              <button
                className={`px-3 py-1 text-sm rounded-md transition-colors ${tab === "engineer" ? "bg-background shadow-sm" : "hover:bg-background/50"}`}
                onClick={() => setTab("engineer")}
              >
                工程师
              </button>
              <button
                className={`px-3 py-1 text-sm rounded-md transition-colors ${tab === "pm" ? "bg-background shadow-sm" : "hover:bg-background/50"}`}
                onClick={() => setTab("pm")}
              >
                市场产品PM
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            {tab === "engineer" ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>姓名</TableHead>
                    <TableHead>S0</TableHead>
                    <TableHead>H0</TableHead>
                    <TableHead>T月计划</TableHead>
                    <TableHead>本月实际工时</TableHead>
                    <TableHead>本月报价工时</TableHead>
                    <TableHead>P差额</TableHead>
                    <TableHead>K系数</TableHead>
                    <TableHead className="text-right">最终工资</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSalaries.filter((s) => s.role === "engineer" || !s.role).length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center h-32">
                        暂无数据
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredSalaries
                      .filter((s) => s.role === "engineer" || !s.role)
                      .map((s, i) => (
                        <TableRow key={s.user_id || i}>
                          <TableCell>{s.full_name || "-"}</TableCell>
                          <TableCell>{s.S0 ?? "-"}</TableCell>
                          <TableCell>{s.H0 ?? "-"}</TableCell>
                          <TableCell>{s.T_monthly_plan ?? "-"}</TableCell>
                          <TableCell>{s.T_actual_monthly ?? "-"}</TableCell>
                          <TableCell>{s.T_reported_monthly ?? "-"}</TableCell>
                          <TableCell>{s.P_diff ?? "-"}</TableCell>
                          <TableCell>{s.k_coefficient ?? "-"}</TableCell>
                          <TableCell className="text-right font-medium">
                            {s.salary_final != null ? `¥${s.salary_final.toLocaleString()}` : "-"}
                          </TableCell>
                        </TableRow>
                      ))
                  )}
                </TableBody>
              </Table>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>姓名</TableHead>
                    <TableHead>S底</TableHead>
                    <TableHead>S考</TableHead>
                    <TableHead>R底</TableHead>
                    <TableHead>R考</TableHead>
                    <TableHead>L实</TableHead>
                    <TableHead>L基</TableHead>
                    <TableHead className="text-right">总工资</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSalaries.filter((s) => s.role === "pm").length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center h-32">
                        暂无数据
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredSalaries
                      .filter((s) => s.role === "pm")
                      .map((s, i) => (
                        <TableRow key={s.user_id || i}>
                          <TableCell>{s.full_name || "-"}</TableCell>
                          <TableCell>{s.S_base ?? "-"}</TableCell>
                          <TableCell>{s.S_assess ?? "-"}</TableCell>
                          <TableCell>{s.R_base ?? "-"}</TableCell>
                          <TableCell>{s.R_assess ?? "-"}</TableCell>
                          <TableCell>{s.L_actual ?? "-"}</TableCell>
                          <TableCell>{s.L_base ?? "-"}</TableCell>
                          <TableCell className="text-right font-medium">
                            {s.salary_total != null ? `¥${s.salary_total.toLocaleString()}` : "-"}
                          </TableCell>
                        </TableRow>
                      ))
                  )}
                </TableBody>
              </Table>
            )}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                共 {totalCount} 条记录，第 {page} / {totalPages} 页
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>上一页</Button>
                <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>下一页</Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}