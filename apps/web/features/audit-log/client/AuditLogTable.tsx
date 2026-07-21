"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export interface AuditLogItem {
  id: string;
  created_at: string;
  action: string;
  target_type: string;
  target_id?: string | null;
  details?: string | null;
  operator_name?: string | null;
}

interface AuditLogTableProps {
  logs: AuditLogItem[] | undefined;
  isLoading?: boolean;
  title?: string;
}

function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return isNaN(d.getTime())
    ? "-"
    : `${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

const ACTION_LABELS: Record<string, string> = {
  "task.create": "发布任务",
  "task.approve": "审核通过",
  "task.reject": "驳回任务",
  "task.publish": "发布任务",
  "task.convert_type": "转换类型",
  "task.reassign": "改派任务",
  "task.pause_approve": "批准暂停",
  "task.pause_reject": "驳回暂停",
  "user.create": "创建用户",
  "user.toggle_active": "启用/禁用用户",
  "salary.update": "更新工资参数",
  "system_rule.update": "更新规则",
};

const TARGET_TYPE_LABELS: Record<string, string> = {
  task: "任务",
  user: "用户",
  salary: "工资",
  system_rule: "系统规则",
};

export function AuditLogTable({ logs, isLoading, title = "操作日志" }: AuditLogTableProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>时间</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>内容</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs?.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDateTime(log.created_at)}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {ACTION_LABELS[log.action] || log.action}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    {log.details || `${TARGET_TYPE_LABELS[log.target_type] || log.target_type} ${log.target_id?.slice(0, 8) || ""}`}
                  </TableCell>
                </TableRow>
              ))}
              {(!logs || logs.length === 0) && (
                <TableRow>
                  <TableCell colSpan={3} className="text-center py-8">
                    暂无操作日志
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}