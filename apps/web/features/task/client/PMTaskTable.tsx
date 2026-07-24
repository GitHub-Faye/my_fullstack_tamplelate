"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, Plus, Search, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useTasks } from "../api";
import { useCurrentUser } from "@/features/user";
import {
  withdrawTaskV1TasksTaskIdWithdrawPost,
  deleteTaskV1TasksTaskIdDelete,
  type TaskPublic,
  type TaskStatus,
  type TaskType,
} from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";
import { toast } from "sonner";
import { Pagination } from "@/components/ui/pagination";
import { TaskDetailDialog, getPmActions } from "./TaskDetailDialog";
import { BidLogDialog } from "./BidLogDialog";
import { AuditLogDialog } from "./AuditLogDialog";
import { WorkLogDialog } from "./WorkLogDialog";
import { formatDateTime, formatDate } from "@/lib/utils";

const STATUS_LABELS: Record<TaskStatus, string> = TASK_STATUS_LABELS;
const TYPE_LABELS: Record<TaskType, string> = TASK_TYPE_LABELS;

/** 发布人筛选选项 */
type PublisherFilter = "all" | "mine" | "other";

/** 默认筛选条件 */
const DEFAULT_FILTERS = {
  status: "all",
  publisher: "all" as PublisherFilter,
  taskType: "all",
};

/** 删除确认弹窗状态 */
interface ConfirmState {
  open: boolean;
  action: "delete" | "withdraw" | null;
  task: TaskPublic | null;
}

/**
 * PM 任务列表表格组件
 *
 * 独立组件，不继承共享 TaskTable。
 * 实现 PM 专属的筛选栏、操作列和详情弹窗。
 */
export function PMTaskTable() {
  const router = useRouter();
  const [page, setPage] = useState(1);

  // 当前用户信息
  const user = useCurrentUser();

  // 筛选条件状态
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  // 弹窗状态
  const [detailTask, setDetailTask] = useState<TaskPublic | null>(null);
  const [bidLogTask, setBidLogTask] = useState<TaskPublic | null>(null);
  const [logTask, setLogTask] = useState<TaskPublic | null>(null);
  const [workLogTask, setWorkLogTask] = useState<TaskPublic | null>(null);
  const [confirm, setConfirm] = useState<ConfirmState>({ open: false, action: null, task: null });

  // 搜索和重置
  const handleSearch = useCallback(() => {
    setPage(1);
  }, []);

  const handleReset = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    setPage(1);
  }, []);

  // 构建 API 查询参数
  const queryParams: Record<string, any> = {
    page,
    page_size: 20,
    status: filters.status !== "all" ? filters.status : undefined,
    task_type: filters.taskType !== "all" ? filters.taskType : undefined,
  };

  // 发布人筛选逻辑
  if (filters.publisher === "mine" && user?.id) {
    queryParams.pm_id = user.id;
  } else if (filters.publisher === "other" && user?.id) {
    queryParams.pm_id = user.id;
    queryParams.exclude_pm_id = true;
  }

  const { data: tasks, isLoading, refetch } = useTasks(queryParams as any);

  const handleConfirmAction = useCallback(async () => {
    if (!confirm.task || !confirm.action) return;
    try {
      if (confirm.action === "delete") {
        await deleteTaskV1TasksTaskIdDelete({ path: { task_id: confirm.task.id } });
        toast.success("任务已删除");
      } else if (confirm.action === "withdraw") {
        await withdrawTaskV1TasksTaskIdWithdrawPost({ path: { task_id: confirm.task.id } });
        toast.success("任务已撤回");
      }
      refetch();
    } catch (e: any) {
      toast.error(e.message || "操作失败");
    } finally {
      setConfirm({ open: false, action: null, task: null });
    }
  }, [confirm, refetch]);

  const handleAction = useCallback((action: string, task: TaskPublic) => {
    switch (action) {
      case "detail":
        setDetailTask(task);
        break;
      case "edit":
        router.push(`/pm/tasks/${task.id}/edit`);
        break;
      case "delete":
        setConfirm({ open: true, action: "delete", task });
        break;
      case "withdraw":
        setConfirm({ open: true, action: "withdraw", task });
        break;
      case "bidLog":
        setBidLogTask(task);
        break;
      case "viewLog":
      case "pauseLog":
      case "archiveLog":
        setLogTask(task);
        break;
      case "workLog":
        setWorkLogTask(task);
        break;
      case "changeDoc":
        router.push(`/pm/tasks/${task.id}/edit`);
        break;
    }
  }, [router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const taskList = tasks?.data as TaskPublic[] | undefined;

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>任务管理</CardTitle>
            <Button asChild>
              <Link href="/pm/tasks/new">
                <Plus className="mr-2 h-4 w-4" />
                发布任务
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* 筛选栏 */}
          <div className="flex items-center gap-4 mb-4 flex-wrap">
            <Select
              value={filters.publisher}
              onValueChange={(v: PublisherFilter) => {
                setFilters((prev) => ({ ...prev, publisher: v }));
                setPage(1);
              }}
            >
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="发布人" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                <SelectItem value="mine">我发布的</SelectItem>
                <SelectItem value="other">其他PM</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.taskType}
              onValueChange={(v) => {
                setFilters((prev) => ({ ...prev, taskType: v }));
                setPage(1);
              }}
            >
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="任务类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="normal">正常任务</SelectItem>
                <SelectItem value="urgent">紧急任务</SelectItem>
                <SelectItem value="convenient">便捷任务</SelectItem>
              </SelectContent>
            </Select>

            <Select
              value={filters.status}
              onValueChange={(v) => {
                setFilters((prev) => ({ ...prev, status: v }));
                setPage(1);
              }}
            >
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="任务状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="unconfirmed">未确认</SelectItem>
                <SelectItem value="bidding">竞价中</SelectItem>
                <SelectItem value="pending_start">待启动</SelectItem>
                <SelectItem value="in_progress">进行中</SelectItem>
                <SelectItem value="paused">暂停中</SelectItem>
                <SelectItem value="completed">已完成</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline" size="sm" onClick={handleSearch}>
              <Search className="mr-1 h-4 w-4" />
              搜索
            </Button>
            <Button variant="ghost" size="sm" onClick={handleReset}>
              <RotateCcw className="mr-1 h-4 w-4" />
              重置
            </Button>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>任务</TableHead>
                  <TableHead>发布人</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>工程师</TableHead>
                  <TableHead>预期上线</TableHead>
                  <TableHead>T报完成时间</TableHead>
                  <TableHead>当前阶段/进度</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {taskList?.map((task: TaskPublic) => (
                  <TableRow key={task.id}>
                    <TableCell className="font-medium max-w-[200px] truncate">
                      {task.name}
                    </TableCell>
                    <TableCell className="text-sm">
                      {(task as any).pm_name ?? (task.pm_id ? task.pm_id.slice(0, 8) : "-")}
                    </TableCell>
                    <TableCell>
                      {task.task_type ? (
                        <Badge
                          variant={
                            task.task_type === "urgent"
                              ? "destructive"
                              : task.task_type === "convenient"
                                ? "secondary"
                                : "default"
                          }
                        >
                          {TYPE_LABELS[task.task_type]}
                        </Badge>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                    <TableCell className="text-sm">
                      {(task as any).engineer_name ?? (task.engineer_id ? task.engineer_id.slice(0, 8) : "-")}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDateTime(task.expected_online_time)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(task.T_reported_complete_time)}
                    </TableCell>
                    <TableCell className="text-sm">
                      {task.progress ?? "-"}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          task.status === "completed"
                            ? "default"
                            : task.status === "in_progress"
                              ? "default"
                              : task.status === "bidding" || task.status === "pending_start"
                                ? "secondary"
                                : "outline"
                        }
                      >
                        {STATUS_LABELS[task.status]}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right whitespace-nowrap">
                      {getPmActions(task, user?.id).map((act) => (
                        <Button
                          key={act.action}
                          variant={act.variant || "link"}
                          size="sm"
                          onClick={() => handleAction(act.action, task)}
                          className={act.action === "detail" ? "" : "ml-1"}
                        >
                          {act.label}
                        </Button>
                      ))}
                    </TableCell>
                  </TableRow>
                ))}
                {(!taskList || taskList.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center py-8">
                      暂无任务数据
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {tasks && tasks.count > 20 && (
            <Pagination
              page={page}
              total={tasks.count}
              pageSize={20}
              onPageChange={setPage}
            />
          )}
        </CardContent>
      </Card>

      {/* 详情弹窗 */}
      {detailTask && (
        <TaskDetailDialog
          task={detailTask}
          open={!!detailTask}
          onOpenChange={(open) => { if (!open) setDetailTask(null); }}
        />
      )}

      {/* 报价记录弹窗 */}
      {bidLogTask && (
        <BidLogDialog
          task={bidLogTask}
          open={!!bidLogTask}
          onOpenChange={(open) => { if (!open) setBidLogTask(null); }}
        />
      )}

      {/* 审计日志弹窗 */}
      {logTask && (
        <AuditLogDialog
          task={logTask}
          open={!!logTask}
          onOpenChange={(open) => { if (!open) setLogTask(null); }}
        />
      )}

      {/* 工作日志弹窗 */}
      {workLogTask && (
        <WorkLogDialog
          task={workLogTask}
          open={!!workLogTask}
          onOpenChange={(open) => { if (!open) setWorkLogTask(null); }}
        />
      )}

      {/* 确认弹窗 */}
      <AlertDialog open={confirm.open} onOpenChange={(open) => { if (!open) setConfirm({ open: false, action: null, task: null }); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {confirm.action === "delete" ? "确认删除" : "确认撤回"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {confirm.action === "delete"
                ? "此操作不可撤销，任务将被永久删除。"
                : "撤回后任务将回到「未确认」状态。"}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmAction}>
              确认
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}