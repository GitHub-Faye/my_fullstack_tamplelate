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
import { ACTION_LABELS } from "./actionLabels";

/**
 * Mirrors the backend AuditLog schema (domains/audit/models.py).
 * TODO: Once the SDK generates proper audit-log item types, replace this with the generated type.
 */
export interface AuditLogItem {
  id: string;
  created_at: string;
  action: string;
  target_type: string;
  target_id?: string | null;
  details?: string | null;
  operator_name?: string | null;
  affected_name?: string | null;
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
                <TableHead>操作人</TableHead>
                <TableHead>操作类型</TableHead>
                <TableHead>内容</TableHead>
                <TableHead>影响人</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs?.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDateTime(log.created_at)}
                  </TableCell>
                  <TableCell>{log.operator_name || "-"}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {ACTION_LABELS[log.action] || log.action}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{log.details || "-"}</TableCell>
                  <TableCell className="text-sm">{log.affected_name || "-"}</TableCell>
                </TableRow>
              ))}
              {(!logs || logs.length === 0) && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">
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