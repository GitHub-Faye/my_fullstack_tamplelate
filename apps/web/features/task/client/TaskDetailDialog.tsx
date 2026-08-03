"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Eye, Edit, Trash2, FileText, AlertTriangle, History, Archive, Loader2, Download, Paperclip, Star } from "lucide-react";
import type { TaskPublic, TaskStatus, TaskType } from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  TASK_STATUS_COLORS,
  TASK_TYPE_COLORS,
  PM_EDITABLE_STATUSES,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";
import { formatDateTime, formatDate } from "@/lib/utils";
import { readDailyReportsV1DailyReportsGet, listAttachmentsV1TasksTaskIdAttachmentsGet, client } from "@repo/sdk";
import { getAuthToken } from "@/lib/api-sdk";

const STATUS_LABELS: Record<TaskStatus, string> = TASK_STATUS_LABELS;
const TYPE_LABELS: Record<TaskType, string> = TASK_TYPE_LABELS;
const STATUS_COLORS: Record<TaskStatus, string> = TASK_STATUS_COLORS;
const TYPE_COLORS: Record<TaskType, string> = TASK_TYPE_COLORS;

export interface PmAction {
  label: string;
  icon: React.ReactNode;
  action: string;
  variant?: "default" | "outline" | "destructive";
}

/**
 * 任务状态 → PM 操作按钮映射
 */
export function getPmActions(task: TaskPublic, currentUserId: string | undefined): PmAction[] {
  const status = task.status as string;
  const isOwner = currentUserId != null && task.pm_id === currentUserId;
  const actions: PmAction[] = [];

  // 详情 — 所有任务都有
  actions.push({
    label: "详情",
    icon: <Eye className="h-3.5 w-3.5" />,
    action: "detail",
    variant: "outline",
  });

  // 非自己发布的任务，只有详情按钮
  if (!isOwner) return actions;

  switch (status) {
    case TaskStatusConst.UNCONFIRMED:
      actions.push({ label: "编辑", icon: <Edit className="h-3.5 w-3.5" />, action: "edit", variant: "outline" });
      actions.push({ label: "删除", icon: <Trash2 className="h-3.5 w-3.5" />, action: "delete", variant: "destructive" });
      break;
    case TaskStatusConst.BIDDING:
      if (PM_EDITABLE_STATUSES.includes(status as any)) {
        actions.push({ label: "编辑", icon: <Edit className="h-3.5 w-3.5" />, action: "edit", variant: "outline" });
      }
      actions.push({ label: "报价记录", icon: <FileText className="h-3.5 w-3.5" />, action: "bidLog", variant: "outline" });
      actions.push({ label: "撤回", icon: <AlertTriangle className="h-3.5 w-3.5" />, action: "withdraw", variant: "destructive" });
      break;
    case TaskStatusConst.PENDING_START:
      // 待启动任务没有操作按钮
      break;
    case TaskStatusConst.IN_PROGRESS:
      actions.push({ label: "资料变更", icon: <FileText className="h-3.5 w-3.5" />, action: "changeDoc", variant: "outline" });
      actions.push({ label: "工作日志", icon: <History className="h-3.5 w-3.5" />, action: "workLog", variant: "outline" });
      break;
    case TaskStatusConst.PAUSED:
      actions.push({ label: "暂停记录", icon: <History className="h-3.5 w-3.5" />, action: "pauseLog", variant: "outline" });
      break;
    case TaskStatusConst.COMPLETED:
      actions.push({ label: "评价", icon: <Star className="h-3.5 w-3.5" />, action: "review", variant: "default" });
      actions.push({ label: "归档日志", icon: <Archive className="h-3.5 w-3.5" />, action: "archiveLog", variant: "outline" });
      break;
  }

  return actions;
}

/**
 * 任务详情弹窗组件
 */
export function TaskDetailDialog({
  task,
  open,
  onOpenChange,
}: {
  task: TaskPublic;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  if (!task) return null;

  const isStarted = ["pending_start", "in_progress", "paused", "completed"].includes(task.status);
  const statusText = STATUS_LABELS[task.status] || task.status;
  const typeText = task.task_type ? TYPE_LABELS[task.task_type] ?? task.task_type : "-";

  // 最近工作日志
  const [recentReports, setRecentReports] = useState<any[] | null>(null);
  const [reportsLoading, setReportsLoading] = useState(false);

  // 附件列表
  const [attachments, setAttachments] = useState<any[]>([]);
  const [attachmentsLoading, setAttachmentsLoading] = useState(false);

  useEffect(() => {
    if (open && task) {
      // 加载工作日志
      if (isStarted) {
        setReportsLoading(true);
        readDailyReportsV1DailyReportsGet({
          query: { task_id: task.id, page: 1, page_size: 5 },
        })
          .then((res) => setRecentReports(res.data?.data ?? []))
          .catch(() => setRecentReports([]))
          .finally(() => setReportsLoading(false));
      }
      // 加载附件列表
      setAttachmentsLoading(true);
      listAttachmentsV1TasksTaskIdAttachmentsGet({
        path: { task_id: task.id },
      })
        .then((res) => setAttachments((res.data as any[]) ?? []))
        .catch(() => setAttachments([]))
        .finally(() => setAttachmentsLoading(false));
    } else if (!open) {
      setRecentReports(null);
      setAttachments([]);
    }
  }, [open, task]);

  // 下载附件（使用 SDK 的 auth token）
  const handleDownload = useCallback(async (attachmentId: string, fileName: string) => {
    const token = getAuthToken();
    if (!token) return;
    const baseUrl = client.getConfig().baseUrl;
    const url = `${baseUrl}/v1/tasks/attachments/${attachmentId}/download`;

    try {
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error(`下载失败 (${response.status})`);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = fileName;
      a.click();
      URL.revokeObjectURL(blobUrl);
    } catch (err: any) {
      // 静默处理
    }
  }, []);

  // 格式化文件大小
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl">{task.name}</DialogTitle>
          <DialogDescription>任务详情</DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* 任务基本信息 */}
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <div className="flex gap-1">
              <span className="text-muted-foreground shrink-0">任务类型</span>
              <span>{typeText}</span>
            </div>
            <div className="flex gap-1">
              <span className="text-muted-foreground shrink-0">状态</span>
              <Badge variant={STATUS_COLORS[task.status] as never}>{statusText}</Badge>
            </div>
            <div className="flex gap-1">
              <span className="text-muted-foreground shrink-0">发布人</span>
              <span>{(task as any).pm_name ?? task.pm_id.slice(0, 8)}</span>
            </div>
            <div className="flex gap-1">
              <span className="text-muted-foreground shrink-0">发布时间</span>
              <span>{formatDateTime(task.created_at)}</span>
            </div>
            <div className="flex gap-1">
              <span className="text-muted-foreground shrink-0">预期上线</span>
              <span>{formatDateTime(task.expected_online_time)}</span>
            </div>
            <div className="flex gap-1">
              <span className="text-muted-foreground shrink-0">T报</span>
              <span>{task.T_reported != null ? `${task.T_reported}h` : "-"}</span>
            </div>
            <div className="flex gap-1">
              <span className="text-muted-foreground shrink-0">T报完成时间</span>
              <span>{formatDateTime(task.T_reported_complete_time)}</span>
            </div>
            {isStarted && (
              <>
                <div className="flex gap-1">
                  <span className="text-muted-foreground shrink-0">执行工程师</span>
                  <span>{task.engineer_id ? ((task as any).engineer_name ?? task.engineer_id.slice(0, 8)) : "-"}</span>
                </div>
                <div className="flex gap-1">
                  <span className="text-muted-foreground shrink-0">T实</span>
                  <span>{task.T_actual != null ? `${task.T_actual}h` : "-"}</span>
                </div>
                <div className="flex gap-1">
                  <span className="text-muted-foreground shrink-0">当前进度</span>
                  <span>{task.progress ?? "-"}</span>
                </div>
              </>
            )}
          </div>

          {/* 任务说明 */}
          {task.description && (
            <div className="flex flex-col gap-1 text-sm">
              <span className="text-muted-foreground">任务说明</span>
              <p className="whitespace-pre-wrap">{task.description}</p>
            </div>
          )}

          {/* 附件列表 */}
          <div className="border rounded-md">
            <div className="px-3 py-2 text-sm font-medium border-b bg-muted/50">附件/截图</div>
            {attachmentsLoading ? (
              <div className="flex justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
            ) : attachments.length > 0 ? (
              <div className="divide-y">
                {attachments.map((att: any) => (
                  <div key={att.id} className="flex items-center justify-between px-3 py-2 text-sm">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <Paperclip className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <span className="truncate">{att.file_name}</span>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {formatSize(att.file_size)}
                      </span>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="shrink-0"
                      onClick={() => handleDownload(att.id, att.file_name)}
                    >
                      <Download className="h-3.5 w-3.5 mr-1" />
                      下载
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center py-4 text-sm text-muted-foreground">暂无附件</p>
            )}
          </div>

          {/* 最近工作日志 */}
          {isStarted && (
            <div className="border rounded-md">
              <div className="px-3 py-2 text-sm font-medium border-b bg-muted/50">最近工作日志</div>
              {reportsLoading ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
              ) : recentReports && recentReports.length > 0 ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-muted-foreground">
                      <th className="text-left px-3 py-2 font-medium">日期</th>
                      <th className="text-left px-3 py-2 font-medium">投入</th>
                      <th className="text-left px-3 py-2 font-medium">阶段/进度</th>
                      <th className="text-left px-3 py-2 font-medium">说明</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentReports.map((rpt: any, i: number) => (
                      <tr key={i} className="border-b last:border-0">
                        <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">
                          {formatDate(rpt.report_date ?? rpt.created_at)}
                        </td>
                        <td className="px-3 py-2">{rpt.today_hours ?? "-"}h</td>
                        <td className="px-3 py-2">
                          {rpt.current_stage ?? "-"}
                          {rpt.progress ? ` / ${rpt.progress}` : ""}
                        </td>
                        <td className="px-3 py-2 text-muted-foreground max-w-[200px] truncate">
                          {rpt.notes ?? "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-center py-4 text-sm text-muted-foreground">暂无工作日志</p>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}