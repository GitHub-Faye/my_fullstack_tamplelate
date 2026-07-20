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
import { formatDate } from "@/lib/utils";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { useTask } from "../api";
import type { TaskStatus, TaskType } from "@repo/sdk";

const STATUS_LABELS: Record<TaskStatus, string> = {
  unconfirmed: "未确认",
  confirmed_unpublished: "已确认未发布",
  bidding: "竞价中",
  pending_start: "待启动",
  in_progress: "进行中",
  pause_requested: "暂停待审批",
  paused: "暂停中",
  completed: "已完成",
};

const STATUS_COLORS: Record<TaskStatus, string> = {
  unconfirmed: "secondary",
  confirmed_unpublished: "secondary",
  bidding: "default",
  pending_start: "default",
  in_progress: "default",
  pause_requested: "default",
  paused: "default",
  completed: "default",
} as const;

const TYPE_LABELS: Record<TaskType, string> = {
  normal: "正常任务",
  urgent: "紧急任务",
  convenient: "便捷任务",
};

interface TaskDetailProps {
  taskId: string;
}

/**
 * 任务详情组件
 */
export function TaskDetail({ taskId }: TaskDetailProps) {
  const router = useRouter();
  const { data: task, isLoading, error } = useTask(taskId);

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

  const isEditable = task.status === "unconfirmed";

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
              <span className="text-sm text-muted-foreground">任务ID</span>
              <span className="text-sm font-mono text-xs">{task.id}</span>
            </div>
            {task.engineer_id && (
              <div className="flex flex-col gap-1">
                <span className="text-sm text-muted-foreground">工程师ID</span>
                <span className="text-sm font-mono text-xs">{task.engineer_id}</span>
              </div>
            )}
            {task.T_reported !== undefined && task.T_reported !== null && (
              <div className="flex flex-col gap-1">
                <span className="text-sm text-muted-foreground">T报</span>
                <span className="text-sm">{task.T_reported}h</span>
              </div>
            )}
            {task.T_actual !== undefined && task.T_actual !== null && (
              <div className="flex flex-col gap-1">
                <span className="text-sm text-muted-foreground">T实</span>
                <span className="text-sm">{task.T_actual}h</span>
              </div>
            )}
            {task.bidding_deadline && (
              <div className="flex flex-col gap-1">
                <span className="text-sm text-muted-foreground">竞价截止</span>
                <span className="text-sm">{formatDate(task.bidding_deadline)}</span>
              </div>
            )}
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">创建时间</span>
              <span className="text-sm">{formatDate(task.created_at)}</span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">更新时间</span>
              <span className="text-sm">{formatDate(task.updated_at)}</span>
            </div>
          </div>

          {task.description && (
            <div className="flex flex-col gap-1">
              <span className="text-sm text-muted-foreground">任务描述</span>
              <p className="text-sm whitespace-pre-wrap">{task.description}</p>
            </div>
          )}

          <div className="flex gap-2 pt-4">
            {isEditable && (
              <>
                <Button asChild>
                  <Link href={`/pm/tasks/${task.id}/edit`}>编辑任务</Link>
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}