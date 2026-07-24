"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import { readRulesV1SystemRulesGet } from "@repo/sdk";
import { Loader2, Search, Plus } from "lucide-react";
import type { SystemRulePublic } from "@repo/sdk";

const CATEGORY_LABELS: Record<string, string> = {
  all: "全部",
  starpoint_reward: "星点奖励",
  salary_formula: "工资公式",
  completion_judgment: "完成判定",
  system_param: "系统参数",
};

export default function AdminRulesPage() {
  const [category, setCategory] = useState("all");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["rules", { category: category === "all" ? undefined : category, page, page_size: pageSize }],
    queryFn: async () => {
      const response = await readRulesV1SystemRulesGet({
        query: {
          category: category === "all" ? null : category,
          page,
          page_size: pageSize,
        },
        throwOnError: true,
      });
      return response.data;
    },
  });

  const rules = (data?.data || []) as SystemRulePublic[];
  const totalCount = data?.count || 0;
  const totalPages = Math.ceil(totalCount / pageSize);

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
        <h1 className="text-3xl font-bold">规则配置</h1>
        <p className="text-muted-foreground">管理系统中的业务规则</p>
      </div>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 flex-wrap">
            <Button variant="default" size="sm" disabled>
              <Plus className="mr-1 h-4 w-4" />新增规则
            </Button>
            <div className="flex items-center gap-2">
              <label className="text-sm">分类</label>
              <Select value={category} onValueChange={(v) => { setCategory(v); setPage(1); }}>
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="全部" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" size="sm" disabled>
              <Search className="mr-1 h-4 w-4" />搜索
            </Button>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>规则配置</CardTitle></CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>分类</TableHead>
                  <TableHead>规则名称</TableHead>
                  <TableHead>规则值/公式</TableHead>
                  <TableHead>适用角色</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rules.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center h-32">
                      暂无规则数据
                    </TableCell>
                  </TableRow>
                ) : (
                  rules.map((rule) => (
                    <TableRow key={rule.id}>
                      <TableCell>{CATEGORY_LABELS[rule.category] || rule.category}</TableCell>
                      <TableCell className="font-medium">{rule.name}</TableCell>
                      <TableCell className="text-muted-foreground">{rule.value}</TableCell>
                      <TableCell>{rule.applies_to || "-"}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="link" size="sm" disabled>
                          修改
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
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