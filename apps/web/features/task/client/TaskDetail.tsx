"use client";

import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDateTime, formatDate } from "@/lib/utils";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { useTask } from "../api";
import { useUserMap } from "@/features/user";
import type { TaskStatus, TaskType } from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  PM_EDITABLE_STATUSES,
} from "@repo/contracts";

const STATUS_LABELS: Record<TaskStatus, string> = TASK_STATUS_LABELS;

const STATUS_COLORS: Record<TaskStatus, string> = {
  unconfirmed: "secondary",
  bidding: "default",
  pending_start: "default",
  in_progress: "default",
  pause_requested: "default",
  paused: "default",
  completed: "default",
} as const;

const TYPE_LABELS: Record<TaskType, string> = TASK_TYPE_LABELS;

interface TaskDetailProps {
  taskId: string;
}

/**
 * 任务详情组件
 */
export function TaskDetail({ taskId }: TaskDetailProps) {
  const router = useRouter();
  const { data: task, isLoading, error } = useTask(taskId);
  const userMap = useUserMap();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" asChild>
            <Link href="/pm/tasks">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回列表
            </Link>
          </Button>
        </div>
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold">任务不存在</h2>
          <p className="text-muted-foreground">该任务可能已被删除或您没有访问权限</p>
        </div>
      </div>
    );
  }

  const isEditable = PM_EDITABLE_STATUSES.includes(task.status as any);
  const isStarted = ["pending_start", "in_progress", "paused", "completed"].includes(task.status);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" asChild>
          <Link href="/pm/tasks">
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回列表
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-xl">{task.name}</CardTitle>
              <CardDescription>任务详情</CardDescription>
            </div>
            <Badge variant={STATUS_COLORS[task.status] as "default" | "secondary"}>
              {STATUS_LABELS[task.status]}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">任务类型</span>
              <span className="text-sm">{TYPE_LABELS[task.task_type ?? "normal"]}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">状态</span>
              <span className="text-sm">{STATUS_LABELS[task.status]}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">发布人</span>
              <span className="text-sm">{(task as any).pm_name ?? userMap[task.pm_id] ?? task.pm_id.slice(0, 8)}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">发布时间</span>
              <span className="text-sm">{formatDateTime(task.created_at)}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">预期上线</span>
              <span className="text-sm">{formatDateTime(task.expected_online_time)}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">T报</span>
              <span className="text-sm">{task.T_reported != null ? `${task.T_reported}h` : "-"}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">T报完成时间</span>
              <span className="text-sm">{formatDateTime(task.T_reported_complete_time)}</span>
            </div>
            {isStarted && (
              <>
                <div className="flex flex-col gap-1">
                  <span className="text-sm text-muted-foreground">执行工程师</span>
                  <span className="text-sm">{task.engineer_id ? ((task as any).engineer_name ?? userMap[task.engineer_id] ?? task.engineer_id.slice(0, 8)) : "-"}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-sm text-muted-foreground">T实</span>
                  <span className="text-sm">{task.T_actual != null ? `${task.T_actual}h` : "-"}</span>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-sm text-muted-foreground">当前进度</span>
                  <span className="text-sm">{task.progress ?? "-"}</span>
                </div>
              </>
            )}
          </div>

          {task.description && (
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">任务说明</span>
              <p className="text-sm whitespace-pre-wrap">{task.description}</p>
            </div>
          )}

          <div className="flex gap-2 pt-4">
            {isEditable && (
              <Button asChild>
                <Link href={`/pm/tasks/${task.id}/edit`}>编辑任务</Link>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}