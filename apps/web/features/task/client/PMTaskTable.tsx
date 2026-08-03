"use client";

import { useCallback, useState, useMemo } from "react";
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
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
import { Input } from "@/components/ui/input";
import { Loader2, Plus, Search, RotateCcw, Paperclip, Calendar, User } from "lucide-react";
import { useTasks } from "../api";
import { useCurrentUser, useUsers } from "@/features/user";
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
  TASK_STATUS_COLORS,
  TASK_TYPE_COLORS,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";
import { toast } from "sonner";
import { Pagination } from "@/components/ui/pagination";
import { TaskDetailDialog, getPmActions } from "./TaskDetailDialog";
import { BidLogDialog } from "./BidLogDialog";
import { AuditLogDialog } from "./AuditLogDialog";
import { WorkLogDialog } from "./WorkLogDialog";
import { StarPointReviewDialog } from "./StarPointReviewDialog";
import { formatDateTime, formatDate } from "@/lib/utils";
import { TaskCreateForm } from "./TaskCreateForm";
import { TaskEditForm } from "./TaskEditForm";

const STATUS_LABELS: Record<TaskStatus, string> = TASK_STATUS_LABELS;
const TYPE_LABELS: Record<TaskType, string> = TASK_TYPE_LABELS;
const STATUS_COLORS_MAP: Record<TaskStatus, string> = TASK_STATUS_COLORS;
const TYPE_COLORS_MAP: Record<TaskType, string> = TASK_TYPE_COLORS;

/** PM 只能看到自己发布的任务，不需要发布人筛选 */
type TaskTypeFilter = "all" | "normal" | "urgent" | "convenient";

/** 默认筛选条件 */
const DEFAULT_FILTERS = {
  status: "all",
  taskType: "all" as TaskTypeFilter,
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

  // 获取用户列表用于 PM 姓名映射
  const { data: usersData } = useUsers({ page: 1, page_size: 100 });
  const userMap = useMemo(() => {
    const map: Record<string, string> = {};
    if (usersData?.data) {
      for (const u of usersData.data as Array<{ id: string; full_name?: string | null }>) {
        map[u.id] = u.full_name ?? u.id.slice(0, 8);
      }
    }
    return map;
  }, [usersData]);

  // 筛选条件状态
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [pmFilter, setPmFilter] = useState("all");
  const [detailTask, setDetailTask] = useState<TaskPublic | null>(null);
  const [bidLogTask, setBidLogTask] = useState<TaskPublic | null>(null);
  const [logTask, setLogTask] = useState<TaskPublic | null>(null);
  const [workLogTask, setWorkLogTask] = useState<TaskPublic | null>(null);
  const [confirm, setConfirm] = useState<ConfirmState>({ open: false, action: null, task: null });
  const [createOpen, setCreateOpen] = useState(false);
  const [editTask, setEditTask] = useState<TaskPublic | null>(null);
  const [reviewTask, setReviewTask] = useState<TaskPublic | null>(null);

  // 搜索和重置
  const handleSearch = useCallback(() => {
    setPage(1);
  }, []);

  const handleReset = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    setPage(1);
  }, []);

  // 构建 API 查询参数 — 不传 pm_id 拉取全部任务，客户端筛选
  const queryParams: Record<string, any> = {
    page,
    page_size: 20,
    status: filters.status !== "all" ? filters.status : undefined,
    task_type: filters.taskType !== "all" ? filters.taskType : undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  };

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
        setEditTask(task);
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
        setLogTask(task);
        break;
      case "archiveLog":
        setWorkLogTask(task);
        break;
      case "workLog":
        setWorkLogTask(task);
        break;
      case "changeDoc":
        router.push(`/pm/tasks/${task.id}/edit`);
        break;
      case "review":
        setReviewTask(task);
        break;
    }
  }, [router]);

  // 编辑后刷新
  const handleEditSuccess = useCallback(() => {
    setEditTask(null);
    refetch();
  }, [refetch]);

  // 提取 PM ID 列表用于筛选（必须在 early return 之前）
  const taskList = tasks?.data as TaskPublic[] | undefined;
  const pmIds = useMemo(() => {
    if (!taskList) return [];
    return [...new Set(taskList.map((t) => t.pm_id).filter(Boolean))] as string[];
  }, [taskList]);

  // 客户端过滤 — 同 AdminTaskTable 方式
  const filteredTaskList = useMemo(() => {
    if (!taskList) return undefined;
    if (pmFilter === "all") return taskList;
    return taskList.filter((t) => t.pm_id === pmFilter);
  }, [taskList, pmFilter]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>任务管理</CardTitle>
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              发布任务
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* 筛选栏 */}
          <div className="flex items-center gap-4 mb-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <Input
                type="date"
                className="w-[140px]"
                value={startDate}
                onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
              />
              <span className="text-muted-foreground text-sm">至</span>
              <Input
                type="date"
                className="w-[140px]"
                value={endDate}
                onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
              />
            </div>
            <Select
              value={filters.taskType}
              onValueChange={(v) => {
                setFilters((prev) => ({ ...prev, taskType: v as TaskTypeFilter }));
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

            {/* PM 筛选 */}
            <Select value={pmFilter} onValueChange={(v) => { setPmFilter(v); setPage(1); }}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="全部PM" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部任务</SelectItem>
                <SelectItem value={user?.id ?? ""}>我的任务</SelectItem>
                {pmIds.filter((id) => id !== user?.id).map((id) => (
                  <SelectItem key={id} value={id}>{userMap[id] || id.slice(0, 8)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>任务</TableHead>
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
                {filteredTaskList?.map((task: TaskPublic) => (
                  <TableRow key={task.id}>
                    <TableCell className="font-medium max-w-[200px] truncate">
                      {task.name}
                    </TableCell>
                    <TableCell>
                      {task.task_type ? (
                        <Badge
                          variant={TYPE_COLORS_MAP[task.task_type] as never}
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
                        variant={STATUS_COLORS_MAP[task.status] as never}
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
                {(!filteredTaskList || filteredTaskList.length === 0) && (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8">
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

      {/* 发布任务弹窗 */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>发布任务</DialogTitle>
            <DialogDescription>填写任务基本信息后提交给管理员审核</DialogDescription>
          </DialogHeader>
          <TaskCreateForm onSuccess={() => { setCreateOpen(false); refetch(); }} />
        </DialogContent>
      </Dialog>

      {/* 编辑任务弹窗 */}
      <Dialog open={!!editTask} onOpenChange={(open) => { if (!open) setEditTask(null); }}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>编辑任务</DialogTitle>
            <DialogDescription>修改任务信息</DialogDescription>
          </DialogHeader>
          {editTask && (
            <TaskEditForm
              taskId={editTask.id}
              onSuccess={handleEditSuccess}
              onCancel={() => setEditTask(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* 星点评分弹窗 */}
      {reviewTask && (
        <StarPointReviewDialog
          task={reviewTask}
          open={!!reviewTask}
          onOpenChange={(open) => { if (!open) setReviewTask(null); }}
          onSuccess={refetch}
        />
      )}
    </>
  );
}