"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { readRulesV1SystemRulesGet } from "@repo/sdk";
import { Loader2, Search, Pencil } from "lucide-react";
import type { SystemRulePublic } from "@repo/sdk";
import { RuleEditDialog } from "@/features/rules/client/RuleEditDialog";

const CATEGORY_LABELS: Record<string, string> = {
  all: "全部",
  starpoint_reward: "星点奖励",
  salary_formula: "工资公式",
  completion_judgment: "完成判定",
  system_param: "系统参数",
};

/** 尝试格式化 JSON 值，失败则返回原文本 */
function formatValue(raw: string): string {
  try {
    const parsed = JSON.parse(raw);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return raw;
  }
}

/** 判断值是否可 JSON 格式化展示 */
function isJsonValue(raw: string): boolean {
  try {
    JSON.parse(raw);
    return true;
  } catch {
    return false;
  }
}

export default function AdminRulesPage() {
  const [category, setCategory] = useState("all");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const [editRule, setEditRule] = useState<SystemRulePublic | null>(null);
  const [editOpen, setEditOpen] = useState(false);

  const queryClient = useQueryClient();

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

  const refreshRules = () => {
    queryClient.invalidateQueries({ queryKey: ["rules"] });
  };

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

      {/* 操作栏 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <label className="text-sm">分类</label>
              <Select
                value={category}
                onValueChange={(v) => {
                  setCategory(v);
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="全部" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refreshRules()}
            >
              <Search className="mr-1 h-4 w-4" />
              搜索
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 规则列表 */}
      <Card>
        <CardHeader>
          <CardTitle>规则列表</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>分类</TableHead>
                  <TableHead>规则名称</TableHead>
                  <TableHead>规则值/公式</TableHead>
                  <TableHead>适用角色</TableHead>
                  <TableHead>启用</TableHead>
                  <TableHead>公开</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rules.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center h-32">
                      暂无规则数据
                    </TableCell>
                  </TableRow>
                ) : (
                  rules.map((rule) => (
                    <TableRow key={rule.id}>
                      <TableCell>
                        {CATEGORY_LABELS[rule.category] || rule.category}
                      </TableCell>
                      <TableCell className="font-medium">
                        {rule.name}
                      </TableCell>
                      <TableCell className="text-muted-foreground max-w-[300px]">
                        {isJsonValue(rule.value) ? (
                          <pre className="text-xs whitespace-pre-wrap font-mono">
                            {formatValue(rule.value)}
                          </pre>
                        ) : (
                          <span className="text-sm">{rule.value}</span>
                        )}
                      </TableCell>
                      <TableCell>{rule.applies_to || "-"}</TableCell>
                      <TableCell>
                        {rule.is_active ? (
                          <Badge
                            variant="default"
                            className="bg-green-100 text-green-800 hover:bg-green-100"
                          >
                            启用
                          </Badge>
                        ) : (
                          <Badge variant="secondary">禁用</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        {rule.is_public ? (
                          <Badge variant="default">公开</Badge>
                        ) : (
                          <Badge variant="outline">不公开</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {rule.category === "salary_formula" ? (
                          <span className="text-xs text-muted-foreground">
                            只读
                          </span>
                        ) : (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            title="编辑"
                            onClick={() => {
                              setEditRule(rule);
                              setEditOpen(true);
                            }}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                        )}
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
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 编辑对话框（仅 system_param 可编辑） */}
      <RuleEditDialog
        rule={editRule}
        open={editOpen}
        onOpenChange={setEditOpen}
        onSuccess={refreshRules}
      />
    </div>
  );
}