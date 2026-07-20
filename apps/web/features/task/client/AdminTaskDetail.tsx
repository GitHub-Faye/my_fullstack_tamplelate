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
import { ArrowLeft, Loader2, AlertCircle, CheckCircle, Send, Zap, Clock } from "lucide-react";
import { useTask, useApproveTask, useRejectTask, usePublishTask, useConvertToUrgent, useConvertToConvenient } from "../api";
import type { TaskStatus, TaskType } from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";

const STATUS_LABELS: Record<TaskStatus, string> = TASK_STATUS_LABELS;
const TYPE_LABELS: Record<TaskType, string> = TASK_TYPE_LABELS;

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

interface AdminTaskDetailProps {
  taskId: string;
}

/**
 * 管理端任务详情组件
 *
 * 显示任务详情并提供审核、发布、类型转换等操作
 */
export function AdminTaskDetail({ taskId }: AdminTaskDetailProps) {
  const router = useRouter();
  const { data: task, isLoading, error } = useTask(taskId);

  const approveTask = useApproveTask();
  const rejectTask = useRejectTask();
  const publishTask = usePublishTask();
  const convertToUrgent = useConvertToUrgent();
  const convertToConvenient = useConvertToConvenient();

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
            <Link href="/admin/tasks">
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

  const isUnconfirmed = task.status === TaskStatusConst.UNCONFIRMED;
  const isConfirmedUnpublished = task.status === TaskStatusConst.CONFIRMED_UNPUBLISHED;

  const handleApprove = () => {
    approveTask.mutate(taskId);
  };

  const handleReject = () => {
    rejectTask.mutate(taskId);
  };

  const handlePublish = () => {
    publishTask.mutate({ taskId, biddingDays: 3 });
  };

  const handleConvertToUrgent = () => {
    convertToUrgent.mutate(taskId);
  };

  const handleConvertToConvenient = () => {
    convertToConvenient.mutate(taskId);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="sm" asChild>
          <Link href="/admin/tasks">
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
              <CardDescription>任务审核与管理</CardDescription>
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
              <span className="text-sm text-muted-foreground">发布人 ID</span>
              <span className="text-sm font-mono text-xs">{task.pm_id ?? "-"}</span>
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

          {/* 审核操作 */}
          {isUnconfirmed && (
            <div className="border-t pt-4 mt-4 space-y-3">
              <h3 className="text-sm font-semibold">审核操作</h3>
              <div className="flex gap-2">
                <Button
                  onClick={handleApprove}
                  disabled={approveTask.isPending}
                  variant="default"
                >
                  <CheckCircle className="mr-2 h-4 w-4" />
                  {approveTask.isPending ? "审核中..." : "审核通过"}
                </Button>
                <Button
                  onClick={handleReject}
                  disabled={rejectTask.isPending}
                  variant="outline"
                >
                  <AlertCircle className="mr-2 h-4 w-4" />
                  {rejectTask.isPending ? "驳回中..." : "驳回"}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                审核通过后状态变为"已确认未发布"，驳回后任务保持"未确认"状态供 PM 重新编辑。
              </p>
            </div>
          )}

          {/* 发布操作 */}
          {isConfirmedUnpublished && (
            <div className="border-t pt-4 mt-4 space-y-3">
              <h3 className="text-sm font-semibold">发布操作</h3>
              <div className="flex gap-2">
                <Button
                  onClick={handlePublish}
                  disabled={publishTask.isPending}
                  variant="default"
                >
                  <Send className="mr-2 h-4 w-4" />
                  {publishTask.isPending ? "发布中..." : "发布到竞价池"}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                发布后任务进入竞价池，状态变为"竞价中"，工程师可参与竞价。
              </p>
            </div>
          )}

          {/* 类型转换操作 */}
          <div className="border-t pt-4 mt-4 space-y-3">
            <h3 className="text-sm font-semibold">类型转换</h3>
            <div className="flex gap-2">
              <Button
                onClick={handleConvertToUrgent}
                disabled={convertToUrgent.isPending || task.task_type === "urgent"}
                variant="outline"
                size="sm"
              >
                <Zap className="mr-2 h-4 w-4" />
                转为紧急
              </Button>
              <Button
                onClick={handleConvertToConvenient}
                disabled={convertToConvenient.isPending || task.task_type === "convenient"}
                variant="outline"
                size="sm"
              >
                <Clock className="mr-2 h-4 w-4" />
                转为便捷
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              紧急任务优先竞价，便捷任务不参与竞价按需执行。
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}