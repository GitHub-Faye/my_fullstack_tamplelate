"use client";

import { useState } from "react";
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { formatDate } from "@/lib/utils";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Send,
  Zap,
  Clock,
  CheckCircle,
  XCircle,
  Play,
  ArrowLeftRight,
  FileText,
} from "lucide-react";
import { useTask, useRejectTask, usePublishTask, useConvertToUrgent, useConvertToConvenient } from "../api";
import {
  usePauseApproveTask,
  usePauseRejectTask,
  useAdminRestoreTask,
} from "../api/client/adminMutations";
import { useUserMap } from "@/features/user";
import type { TaskStatus, TaskType } from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";

const STATUS_LABELS: Record<TaskStatus, string> = TASK_STATUS_LABELS;
const TYPE_LABELS: Record<TaskType, string> = TASK_TYPE_LABELS;

/** 默认竞价天数 */
const DEFAULT_BIDDING_DAYS = 3;

type ConfirmAction =
  | "reject"
  | "publish"
  | "convertUrgent"
  | "convertConvenient"
  | "pauseApprove"
  | "pauseReject"
  | "adminRestore";

interface AdminTaskDetailProps {
  taskId: string;
}

/**
 * 管理端任务详情组件
 *
 * 显示任务详情并提供审核、发布、类型转换等操作，所有关键操作均需确认弹窗
 * 支持的状态操作：
 * - pause_requested → 审批暂停 / 驳回暂停
 * - paused → 恢复任务
 * - pending_start → 改派工程师（跳转到 assign tab）
 * - completed → 操作日志
 * - unconfirmed → 发布到竞价池 / 驳回 / 类型转换
 */
export function AdminTaskDetail({ taskId }: AdminTaskDetailProps) {
  const router = useRouter();
  const { data: task, isLoading, error } = useTask(taskId);
  const userMap = useUserMap();

  const rejectTask = useRejectTask();
  const publishTask = usePublishTask();
  const convertToUrgent = useConvertToUrgent();
  const convertToConvenient = useConvertToConvenient();
  const pauseApproveTask = usePauseApproveTask();
  const pauseRejectTask = usePauseRejectTask();
  const adminRestoreTask = useAdminRestoreTask();

  // 确认弹窗状态
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null);

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

  const handleConfirm = () => {
    if (!confirmAction) return;
    switch (confirmAction) {
      case "reject":
        rejectTask.mutate(taskId);
        break;
      case "publish":
        publishTask.mutate({ taskId, biddingDays: DEFAULT_BIDDING_DAYS });
        break;
      case "convertUrgent":
        convertToUrgent.mutate(taskId);
        break;
      case "convertConvenient":
        convertToConvenient.mutate(taskId);
        break;
      case "pauseApprove":
        pauseApproveTask.mutate(taskId);
        break;
      case "pauseReject":
        pauseRejectTask.mutate(taskId);
        break;
      case "adminRestore":
        adminRestoreTask.mutate(taskId);
        break;
    }
    setConfirmAction(null);
  };

  const isPending = confirmAction
    ? ({
        reject: rejectTask.isPending,
        publish: publishTask.isPending,
        convertUrgent: convertToUrgent.isPending,
        convertConvenient: convertToConvenient.isPending,
        pauseApprove: pauseApproveTask.isPending,
        pauseReject: pauseRejectTask.isPending,
        adminRestore: adminRestoreTask.isPending,
      })[confirmAction]
    : false;

  const confirmConfig = confirmAction
    ? ({
        reject: {
          title: "驳回任务",
          description: `确认驳回此任务？驳回后任务保持"未确认"状态，PM 可重新编辑后再次提交。`,
          actionLabel: "驳回",
        },
        publish: {
          title: "发布到竞价池",
          description: `确认将此任务发布到竞价池？发布后状态变为"竞价中"，竞价截止时间为 ${DEFAULT_BIDDING_DAYS} 天后。工程师可参与竞价。`,
          actionLabel: "确认发布",
        },
        convertUrgent: {
          title: "转换为紧急任务",
          description: "确认将此任务转换为紧急任务？紧急任务将优先竞价，获得更高曝光。",
          actionLabel: "转为紧急",
        },
        convertConvenient: {
          title: "转换为便捷任务",
          description: "确认将此任务转换为便捷任务？便捷任务不参与竞价，按需执行。",
          actionLabel: "转为便捷",
        },
        pauseApprove: {
          title: "审批暂停",
          description: "确认审批通过此暂停申请？审批通过后任务状态将变为「暂停中」。",
          actionLabel: "审批暂停",
        },
        pauseReject: {
          title: "驳回暂停申请",
          description: "确认驳回此暂停申请？驳回后工程师将继续执行任务。",
          actionLabel: "驳回暂停",
        },
        adminRestore: {
          title: "恢复任务",
          description: "确认恢复此暂停任务？恢复后任务将回到「进行中」状态。",
          actionLabel: "恢复任务",
        },
      })[confirmAction]
    : null;

  return (
    <AlertDialog open={!!confirmAction} onOpenChange={(open) => !open && setConfirmAction(null)}>
      {/* 确认弹窗 */}
      {confirmConfig && (
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirmConfig.title}</AlertDialogTitle>
            <AlertDialogDescription>{confirmConfig.description}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isPending}>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirm} disabled={isPending}>
              {isPending ? "处理中..." : confirmConfig.actionLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      )}

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
              <Badge>{STATUS_LABELS[task.status]}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="flex flex-col gap-1">
                <span className="text-sm text-muted-foreground">任务类型</span>
                <span className="text-sm">{TYPE_LABELS[task.task_type ?? "normal"]}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-sm text-muted-foreground">发布人</span>
                <span className="text-sm">{userMap?.[task.pm_id] || task.pm_id?.slice(0, 8) || "-"}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-sm text-muted-foreground">任务ID</span>
                <span className="text-sm font-mono text-xs">{task.id}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-sm text-muted-foreground">工程师</span>
                <span className="text-sm">
                  {task.engineer_id
                    ? userMap?.[task.engineer_id] || task.engineer_id.slice(0, 8)
                    : "-"}
                </span>
              </div>
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
              {task.progress !== undefined && task.progress !== null && (
                <div className="flex flex-col gap-1">
                  <span className="text-sm text-muted-foreground">进度</span>
                  <span className="text-sm">{task.progress}</span>
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

            {/* 状态相关操作区 */}
            <div className="border-t pt-4 mt-4 space-y-3">
              {/* 暂停待审批 — 审批暂停 / 驳回暂停 */}
              {task.status === TaskStatusConst.PAUSE_REQUESTED && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">暂停审批操作</h3>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => setConfirmAction("pauseApprove")}
                      disabled={pauseApproveTask.isPending}
                      variant="default"
                    >
                      <CheckCircle className="mr-2 h-4 w-4" />
                      {pauseApproveTask.isPending ? "处理中..." : "审批暂停"}
                    </Button>
                    <Button
                      onClick={() => setConfirmAction("pauseReject")}
                      disabled={pauseRejectTask.isPending}
                      variant="outline"
                    >
                      <XCircle className="mr-2 h-4 w-4" />
                      {pauseRejectTask.isPending ? "处理中..." : "驳回暂停"}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    审批通过后任务暂停，工程师可稍后恢复；驳回后工程师继续执行。
                  </p>
                </div>
              )}

              {/* 暂停中 — 恢复任务 */}
              {task.status === TaskStatusConst.PAUSED && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">暂停任务操作</h3>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => setConfirmAction("adminRestore")}
                      disabled={adminRestoreTask.isPending}
                      variant="default"
                    >
                      <Play className="mr-2 h-4 w-4" />
                      {adminRestoreTask.isPending ? "处理中..." : "恢复任务"}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    恢复后任务回到"进行中"状态。
                  </p>
                </div>
              )}

              {/* 待启动 — 改派工程师 */}
              {task.status === TaskStatusConst.PENDING_START && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">任务操作</h3>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => router.push(`/admin/tasks/${task.id}?tab=assign`)}
                      variant="default"
                    >
                      <ArrowLeftRight className="mr-2 h-4 w-4" />
                      改派工程师
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    改派任务到其他工程师。
                  </p>
                </div>
              )}

              {/* 已完成 — 操作日志 */}
              {task.status === TaskStatusConst.COMPLETED && (
                <div>
                  <h3 className="text-sm font-semibold mb-2">任务操作</h3>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => router.push(`/admin/tasks/${task.id}?tab=audit-logs`)}
                      variant="default"
                    >
                      <FileText className="mr-2 h-4 w-4" />
                      操作日志
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    查看此任务的完整操作日志。
                  </p>
                </div>
              )}

              {/* 未确认 — 发布到竞价池 / 驳回 */}
              {isUnconfirmed && (
                <>
                  <div>
                    <h3 className="text-sm font-semibold mb-2">发布操作</h3>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => setConfirmAction("publish")}
                        disabled={publishTask.isPending}
                        variant="default"
                      >
                        <Send className="mr-2 h-4 w-4" />
                        {publishTask.isPending ? "发布中..." : "发布到竞价池"}
                      </Button>
                      <Button
                        onClick={() => setConfirmAction("reject")}
                        disabled={rejectTask.isPending}
                        variant="outline"
                      >
                        <AlertCircle className="mr-2 h-4 w-4" />
                        {rejectTask.isPending ? "驳回中..." : "驳回"}
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      发布后任务进入竞价池，状态变为"竞价中"；驳回后任务保持"未确认"状态供 PM 重新编辑。
                    </p>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold mb-2">类型转换</h3>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => setConfirmAction("convertUrgent")}
                        disabled={convertToUrgent.isPending || task.task_type === "urgent"}
                        variant="outline"
                        size="sm"
                      >
                        <Zap className="mr-2 h-4 w-4" />
                        转为紧急
                      </Button>
                      <Button
                        onClick={() => setConfirmAction("convertConvenient")}
                        disabled={convertToConvenient.isPending || task.task_type === "convenient"}
                        variant="outline"
                        size="sm"
                      >
                        <Clock className="mr-2 h-4 w-4" />
                        转为便捷
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      紧急任务优先竞价，便捷任务不参与竞价按需执行。
                    </p>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </AlertDialog>
  );
}