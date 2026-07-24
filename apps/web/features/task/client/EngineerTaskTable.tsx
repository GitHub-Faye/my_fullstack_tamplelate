"use client";

import { useState, useCallback } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Loader2, Search, RotateCcw } from "lucide-react";
import { useTasks } from "../api";
import { useCurrentUser } from "@/features/user";
import { useEngineerDashboard } from "@/features/dashboard";
import { TaskDetailDialog } from "./TaskDetailDialog";
import type { TaskPublic, TaskStatus, TaskType } from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";
import {
  startTaskV1TasksTaskIdStartPost,
  declineTaskV1TasksTaskIdDeclinePost,
  pauseRequestTaskV1TasksTaskIdPauseRequestPost,
  resumeTaskV1TasksTaskIdResumePost,
  createBidV1TasksTaskIdBidsPost,
} from "@repo/sdk";
import { Pagination } from "@/components/ui/pagination";
import { formatDateTime } from "@/lib/utils";
import { toast } from "sonner";

const STATUS_LABELS: Record<TaskStatus, string> = TASK_STATUS_LABELS;
const TYPE_LABELS: Record<TaskType, string> = TASK_TYPE_LABELS;

/** 工程师任务状态筛选选项 */
const ENGINEER_TASK_STATUSES = [
  { value: "all", label: "全部状态" },
  { value: TaskStatusConst.BIDDING, label: "竞价中" },
  { value: TaskStatusConst.PENDING_START, label: "待启动" },
  { value: TaskStatusConst.IN_PROGRESS, label: "进行中" },
  { value: TaskStatusConst.PAUSED, label: "暂停中" },
  { value: TaskStatusConst.COMPLETED, label: "已完成" },
];

/** 竞价任务状态筛选选项 */
const BIDDING_TASK_STATUSES = [
  { value: "all", label: "全部状态" },
  { value: TaskStatusConst.BIDDING, label: "竞价中" },
];

type TabType = "mine" | "bidding";

/** 确认弹窗状态 */
interface ConfirmState {
  open: boolean;
  action: "start" | "decline" | "resume" | "pauseRequest" | "bid" | null;
  task: TaskPublic | null;
  /** 报价弹窗专用：工时输入 */
  bidHours: number;
}

/**
 * 任务列表表格组件（工程师视图）
 *
 * 包含两个标签页：
 * - "我的任务"：展示工程师本人任务（T报、T实、进度等）
 * - "竞价任务"：展示可竞价的开放任务（报价倒计时、发布人等）
 */
export function EngineerTaskTable({
  extraActions,
}: {
  extraActions?: React.ReactNode;
}) {
  const [tab, setTab] = useState<TabType>("mine");
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("all");
  const [taskTypeFilter, setTaskTypeFilter] = useState("all");

  const user = useCurrentUser();
  const { data: dashboard } = useEngineerDashboard();

  const [confirm, setConfirm] = useState<ConfirmState>({ open: false, action: null, task: null, bidHours: 0 });
  const [detailTask, setDetailTask] = useState<TaskPublic | null>(null);

  const queryParams: Record<string, any> = {
    page,
    page_size: 20,
    status: statusFilter !== "all" ? statusFilter : undefined,
    task_type: taskTypeFilter !== "all" ? taskTypeFilter : undefined,
  };

  // 我的任务：按工程师 ID 过滤
  if (tab === "mine" && user?.id) {
    queryParams.engineer_id = user.id;
  }

  const { data: tasks, isLoading, refetch } = useTasks(queryParams as any);

  const taskList = (tasks?.data as TaskPublic[]) || [];
  const count = tasks?.count || 0;

  /** 报价倒计时 */
  function countdown(deadline: string | null | undefined): string {
    if (!deadline) return "-";
    const now = new Date();
    const end = new Date(deadline);
    const diff = end.getTime() - now.getTime();
    if (diff <= 0) return "已截止";
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }

  /** 确认操作 */
  const handleConfirmAction = useCallback(async () => {
    if (!confirm.task || !confirm.action) return;
    try {
      const taskId = confirm.task.id;
      switch (confirm.action) {
        case "start":
          await startTaskV1TasksTaskIdStartPost({ path: { task_id: taskId } });
          toast.success("任务已启动");
          break;
        case "decline":
          await declineTaskV1TasksTaskIdDeclinePost({ path: { task_id: taskId } });
          toast.success("已拒绝任务");
          break;
        case "resume":
          await resumeTaskV1TasksTaskIdResumePost({ path: { task_id: taskId } });
          toast.success("任务已恢复");
          break;
        case "pauseRequest":
          await pauseRequestTaskV1TasksTaskIdPauseRequestPost({ path: { task_id: taskId } });
          toast.success("已申请暂停，等待管理员审批");
          break;
        case "bid":
          if (!confirm.bidHours || confirm.bidHours <= 0) {
            toast.error("请填写工时");
            return;
          }
          await createBidV1TasksTaskIdBidsPost({
            path: { task_id: taskId },
            body: { T_reported: confirm.bidHours },
          });
          toast.success("报价成功");
          break;
      }
      refetch();
    } catch (e: any) {
      toast.error(e.message || "操作失败");
    } finally {
      setConfirm({ open: false, action: null, task: null, bidHours: 0 });
    }
  }, [confirm, refetch]);

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
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle>任务管理</CardTitle>
            {extraActions}
          </div>
          {/* 标签栏 */}
          <div className="flex gap-4 border-b pb-2">
            <button
              className={`text-sm font-medium pb-1 border-b-2 transition-colors ${
                tab === "mine"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => { setTab("mine"); setPage(1); setStatusFilter("all"); }}
            >
              我的任务
            </button>
            <button
              className={`text-sm font-medium pb-1 border-b-2 transition-colors ${
                tab === "bidding"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => { setTab("bidding"); setPage(1); setStatusFilter("all"); }}
            >
              竞价任务
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {/* 筛选栏 */}
          <div className="flex items-center gap-4 mb-4 flex-wrap">
            <Select
              value={taskTypeFilter}
              onValueChange={(v) => { setTaskTypeFilter(v); setPage(1); }}
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
              value={statusFilter}
              onValueChange={(v) => { setStatusFilter(v); setPage(1); }}
            >
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="任务状态" />
              </SelectTrigger>
              <SelectContent>
                {(tab === "mine" ? ENGINEER_TASK_STATUSES : BIDDING_TASK_STATUSES).map((s) => (
                  <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button variant="outline" size="sm" onClick={() => setPage(1)}>
              <Search className="mr-1 h-4 w-4" />
              搜索
            </Button>
            <Button variant="ghost" size="sm" onClick={() => { setStatusFilter("all"); setTaskTypeFilter("all"); setPage(1); }}>
              <RotateCcw className="mr-1 h-4 w-4" />
              重置
            </Button>
          </div>

          {/* 我的任务表格 */}
          {tab === "mine" && (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>任务</TableHead>
                    <TableHead>类型</TableHead>
                    <TableHead>T报</TableHead>
                    <TableHead>T实</TableHead>
                    <TableHead>T报完成时间</TableHead>
                    <TableHead>当前阶段/进度</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {taskList.map((task: TaskPublic) => (
                    <TableRow key={task.id}>
                      <TableCell className="font-medium max-w-[200px] truncate">
                        {task.name}
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
                        ) : "-"}
                      </TableCell>
                      <TableCell>{task.T_reported != null ? `${task.T_reported}h` : "-"}</TableCell>
                      <TableCell>{task.T_actual != null ? `${task.T_actual}h` : "-"}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDateTime(task.T_reported_complete_time)}
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
                        <Button
                          variant="link"
                          size="sm"
                          onClick={() => setDetailTask(task)}
                        >
                          详情
                        </Button>
                        {task.status === TaskStatusConst.PENDING_START && (
                          <>
                            <Button
                              variant="link"
                              size="sm"
                              onClick={() => setConfirm({ open: true, action: "start", task, bidHours: 0 })}
                            >
                              启动
                            </Button>
                            <Button
                              variant="link"
                              size="sm"
                              className="text-red-600"
                              onClick={() => setConfirm({ open: true, action: "decline", task, bidHours: 0 })}
                            >
                              拒绝
                            </Button>
                          </>
                        )}
                        {task.status === TaskStatusConst.IN_PROGRESS && (
                          <Button
                            variant="link"
                            size="sm"
                            onClick={() => setConfirm({ open: true, action: "pauseRequest", task, bidHours: 0 })}
                          >
                            申请暂停/顺延
                          </Button>
                        )}
                        {task.status === TaskStatusConst.PAUSED && (
                          <Button
                            variant="link"
                            size="sm"
                            onClick={() => setConfirm({ open: true, action: "resume", task, bidHours: 0 })}
                          >
                            恢复
                          </Button>
                        )}
                        {task.status === TaskStatusConst.COMPLETED && (
                          <Button
                            variant="link"
                            size="sm"
                            onClick={() => setDetailTask(task)}
                          >
                            详情
                          </Button>
                        )}
                        {task.status === TaskStatusConst.BIDDING && (
                          <Button
                            variant="link"
                            size="sm"
                            onClick={() => setConfirm({ open: true, action: "bid", task, bidHours: 0 })}
                          >
                            报价
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {taskList.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-8">
                        暂无任务数据
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          )}

          {/* 竞价任务表格 */}
          {tab === "bidding" && (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>任务</TableHead>
                    <TableHead>类型</TableHead>
                    <TableHead>发布人</TableHead>
                    <TableHead>预期上线</TableHead>
                    <TableHead>报价倒计时</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {taskList.map((task: TaskPublic) => (
                    <TableRow key={task.id}>
                      <TableCell className="font-medium max-w-[200px] truncate">
                        {task.name}
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
                        ) : "-"}
                      </TableCell>
                      <TableCell className="text-sm">
                        {(task as any).pm_name ?? (task.pm_id ? task.pm_id.slice(0, 8) : "-")}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDateTime(task.expected_online_time)}
                      </TableCell>
                      <TableCell>
                        <span className="font-mono text-sm text-orange-600">
                          {countdown(task.bidding_deadline)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {STATUS_LABELS[task.status]}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right whitespace-nowrap">
                        <Button
                          variant="link"
                          size="sm"
                          onClick={() => setConfirm({ open: true, action: "bid", task, bidHours: 0 })}
                        >
                          报价
                        </Button>
                        <Button
                          variant="link"
                          size="sm"
                          onClick={() => setDetailTask(task)}
                        >
                          详情
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {taskList.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8">
                        暂无竞价任务数据
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          )}

          {/* 分页 */}
          {count > 20 && (
            <Pagination
              page={page}
              total={count}
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
          onOpenChange={(o) => { if (!o) setDetailTask(null); }}
        />
      )}

      {/* 统一确认弹窗（启动/拒绝/恢复/报价） */}
      <AlertDialog open={confirm.open} onOpenChange={(o) => { if (!o) setConfirm({ open: false, action: null, task: null, bidHours: 0 }); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {confirm.action === "start" ? "确认启动" : confirm.action === "decline" ? "确认拒绝" : confirm.action === "resume" ? "确认恢复" : confirm.action === "pauseRequest" ? "确认申请暂停" : "报价"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {confirm.action === "start" && "启动后任务将进入进行中状态。"}
              {confirm.action === "decline" && "拒绝后任务将重新进入竞价流程。"}
              {confirm.action === "resume" && "恢复后任务将继续进行中状态。"}
              {confirm.action === "pauseRequest" && "申请暂停后需等待管理员审批。"}
              {confirm.action === "bid" && (
                <div className="space-y-4 mt-2">
                  <div className="text-sm font-medium">{confirm.task?.name}</div>
                  {dashboard && (
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>基准时薪：¥{(dashboard.H0 ?? 100).toFixed(2)}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-muted-foreground">工时（小时）</label>
                    <input
                      type="number"
                      min="0.5"
                      step="0.5"
                      className="w-24 h-9 px-2 border rounded text-sm"
                      value={confirm.bidHours || ""}
                      onChange={(e) => setConfirm((prev) => ({ ...prev, bidHours: parseFloat(e.target.value) || 0 }))}
                    />
                  </div>
                  {confirm.bidHours > 0 && (
                    <div className="text-sm text-muted-foreground">
                      报价金额：<span className="font-medium text-foreground">¥{(confirm.bidHours * (dashboard?.H0 ?? 100)).toFixed(2)}</span>
                    </div>
                  )}
                </div>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmAction} disabled={confirm.action === "bid" && confirm.bidHours <= 0}>
              确认
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}