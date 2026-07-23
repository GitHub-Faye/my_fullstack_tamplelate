"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
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
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Loader2, MoreHorizontal, Eye, CheckCircle, XCircle, Send, RefreshCw, AlertTriangle, ArrowLeftRight, Play, Plus } from "lucide-react";
import { useTasks, useTask } from "../api";
import { useUserMap } from "@/features/user";
import {
  useApproveTask,
  useRejectTask,
  usePublishTask,
  useConvertToUrgent,
  useConvertToConvenient,
  usePauseApproveTask,
  usePauseRejectTask,
  useAdminRestoreTask,
} from "../api/client/adminMutations";
import type { TaskPublic, TaskStatus, TaskType } from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";
import { Pagination } from "@/components/ui/pagination";
import { formatDateShort } from "@/lib/utils";
import { toast } from "sonner";

const STATUS_LABELS: Record<TaskStatus, string> = TASK_STATUS_LABELS;
const TYPE_LABELS: Record<TaskType, string> = TASK_TYPE_LABELS;

/** 审核管理关注的状态列表 */
const REVIEW_FILTERS: { value: string; label: string }[] = [
  { value: "all", label: "全部状态" },
  { value: TaskStatusConst.UNCONFIRMED, label: "未确认" },
  { value: TaskStatusConst.CONFIRMED_UNPUBLISHED, label: "已确认未发布" },
  { value: TaskStatusConst.BIDDING, label: "竞价中" },
  { value: TaskStatusConst.PENDING_START, label: "待启动" },
  { value: TaskStatusConst.IN_PROGRESS, label: "进行中" },
  { value: TaskStatusConst.PAUSE_REQUESTED, label: "暂停待审批" },
  { value: TaskStatusConst.PAUSED, label: "已暂停" },
  { value: TaskStatusConst.COMPLETED, label: "已完成" },
];

function useCountdown(deadline: string | null | undefined): string {
  const [display, setDisplay] = useState("-");

  useEffect(() => {
    if (!deadline) {
      setDisplay("-");
      return;
    }

    function tick() {
      const now = new Date();
      const end = new Date(deadline!);
      const diff = end.getTime() - now.getTime();
      if (diff <= 0) {
        setDisplay("已截止");
        return;
      }
      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setDisplay(
        `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`
      );
    }

    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [deadline]);

  return display;
}

/** 根据任务状态返回管理员可执行的操作列表 */
function getAdminActions(status: TaskStatus) {
  switch (status) {
    case TaskStatusConst.UNCONFIRMED:
      return [
        { key: "approve", label: "审核通过", icon: CheckCircle },
        { key: "reject", label: "驳回", icon: XCircle },
      ];
    case TaskStatusConst.CONFIRMED_UNPUBLISHED:
      return [
        { key: "publish", label: "发布到竞价池", icon: Send },
        { key: "reject", label: "驳回", icon: XCircle },
      ];
    case TaskStatusConst.BIDDING:
      return [
        { key: "viewBids", label: "查看报价", icon: Eye },
        { key: "convertUrgent", label: "改为紧急", icon: AlertTriangle },
        { key: "convertConvenient", label: "改为便捷", icon: RefreshCw },
      ];
    case TaskStatusConst.PENDING_START:
      return [
        { key: "reassign", label: "改派工程师", icon: ArrowLeftRight },
        { key: "detail", label: "详情", icon: Eye },
      ];
    case TaskStatusConst.IN_PROGRESS:
      return [
        { key: "detail", label: "详情", icon: Eye },
      ];
    case TaskStatusConst.PAUSE_REQUESTED:
      return [
        { key: "pauseApprove", label: "审批暂停", icon: CheckCircle },
        { key: "pauseReject", label: "驳回暂停", icon: XCircle },
        { key: "detail", label: "详情", icon: Eye },
      ];
    case TaskStatusConst.PAUSED:
      return [
        { key: "adminRestore", label: "恢复任务", icon: Play },
        { key: "detail", label: "详情", icon: Eye },
      ];
    case TaskStatusConst.COMPLETED:
      return [
        { key: "detail", label: "详情", icon: Eye },
      ];
    default:
      return [
        { key: "detail", label: "详情", icon: Eye },
      ];
  }
}

/**
 * 管理端任务列表组件
 *
 * 展示所有任务，支持状态/工程师/PM 筛选，根据任务状态展示不同操作
 */
export function AdminTaskTable() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("all");
  const [engineerFilter, setEngineerFilter] = useState("all");
  const [pmFilter, setPmFilter] = useState("all");

  const { data: tasks, isLoading } = useTasks({
    page,
    page_size: 20,
    status: status !== "all" ? (status as TaskStatus) : undefined,
  });
  const userMap = useUserMap();

  // 操作弹窗状态
  const [actionDialog, setActionDialog] = useState<{ open: boolean; task: TaskPublic | null; action: string }>({
    open: false, task: null, action: "",
  });
  const [biddingDays, setBiddingDays] = useState(3);

  const approveTask = useApproveTask();
  const rejectTask = useRejectTask();
  const publishTask = usePublishTask();
  const convertToUrgent = useConvertToUrgent();
  const convertToConvenient = useConvertToConvenient();
  const pauseApproveTask = usePauseApproveTask();
  const pauseRejectTask = usePauseRejectTask();
  const adminRestoreTask = useAdminRestoreTask();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const taskList = (tasks?.data as TaskPublic[] | undefined) ?? [];
  const totalCount = tasks?.count || 0;

  // 提取所有工程师/PM 用于筛选
  const engineerIds = [...new Set(taskList.map((t) => t.engineer_id).filter(Boolean))] as string[];
  const pmIds = [...new Set(taskList.map((t) => t.pm_id).filter(Boolean))] as string[];

  // 筛选
  let filtered = taskList;
  if (engineerFilter !== "all") {
    filtered = filtered.filter((t) => t.engineer_id === engineerFilter);
  }
  if (pmFilter !== "all") {
    filtered = filtered.filter((t) => t.pm_id === pmFilter);
  }

  async function handleAction(task: TaskPublic, action: string) {
    switch (action) {
      case "approve":
        try {
          await approveTask.mutateAsync(task.id);
        } catch {
          // handled by mutation
        }
        break;
      case "publish":
        setActionDialog({ open: true, task, action: "publish" });
        break;
      case "reject":
        try {
          await rejectTask.mutateAsync(task.id);
        } catch {
          // handled by mutation
        }
        break;
      case "viewBids":
        router.push(`/admin/tasks/${task.id}?tab=bids`);
        break;
      case "convertUrgent":
        try {
          await convertToUrgent.mutateAsync(task.id);
        } catch {
          // handled by mutation
        }
        break;
      case "convertConvenient":
        try {
          await convertToConvenient.mutateAsync(task.id);
        } catch {
          // handled by mutation
        }
        break;
      case "reassign":
        router.push(`/admin/tasks/${task.id}?tab=assign`);
        break;
      case "pauseApprove":
        try {
          await pauseApproveTask.mutateAsync(task.id);
        } catch {
          // handled by mutation
        }
        break;
      case "pauseReject":
        try {
          await pauseRejectTask.mutateAsync(task.id);
        } catch {
          // handled by mutation
        }
        break;
      case "adminRestore":
        try {
          await adminRestoreTask.mutateAsync(task.id);
        } catch {
          // handled by mutation
        }
        break;
      case "detail":
        router.push(`/admin/tasks/${task.id}`);
        break;
    }
  }

  async function handleConfirmPublish() {
    const task = actionDialog.task;
    if (!task) return;
    try {
      await publishTask.mutateAsync({ taskId: task.id, biddingDays });
      setActionDialog({ open: false, task: null, action: "" });
      setBiddingDays(3);
    } catch {
      // handled by mutation
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>任务管理</CardTitle>
          <Button asChild>
            <Link href="/admin/tasks/new">
              <Plus className="mr-2 h-4 w-4" />
              发布任务
            </Link>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* 筛选栏 */}
        <div className="flex items-center gap-4 mb-4 flex-wrap">
          <Select value={status} onValueChange={(v) => { setStatus(v); setPage(1); }}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="任务状态" />
            </SelectTrigger>
            <SelectContent>
              {REVIEW_FILTERS.map((f) => (
                <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={engineerFilter} onValueChange={(v) => { setEngineerFilter(v); setPage(1); }}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="全部工程师" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部工程师</SelectItem>
              {engineerIds.map((id) => (
                <SelectItem key={id} value={id}>{userMap?.[id] || id.slice(0, 8)}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={pmFilter} onValueChange={(v) => { setPmFilter(v); setPage(1); }}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="全部PM" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部PM</SelectItem>
              {pmIds.map((id) => (
                <SelectItem key={id} value={id}>{userMap?.[id] || id.slice(0, 8)}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>任务名称</TableHead>
                <TableHead>任务类型</TableHead>
                <TableHead>发布人</TableHead>
                <TableHead>工程师</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>T报</TableHead>
                <TableHead>T实</TableHead>
                <TableHead>报价倒计时</TableHead>
                <TableHead>进度</TableHead>
                <TableHead>预计上线时间</TableHead>
                <TableHead>创建时间</TableHead>
                <TableHead className="w-[80px]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={12} className="text-center py-8">
                    暂无任务数据
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((task: TaskPublic) => {
                  const actions = getAdminActions(task.status);
                  return (
                    <TableRow key={task.id}>
                      <TableCell className="font-medium max-w-[200px] truncate">{task.name}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-xs">
                          {task.task_type ? TYPE_LABELS[task.task_type] : "正常"}
                        </Badge>
                      </TableCell>
                      <TableCell>{userMap?.[task.pm_id] || task.pm_id?.slice(0, 8) || "-"}</TableCell>
                      <TableCell>{userMap?.[task.engineer_id ?? ""] || task.engineer_id?.slice(0, 8) || "-"}</TableCell>
                      <TableCell>
                        <Badge>{STATUS_LABELS[task.status]}</Badge>
                      </TableCell>
                      <TableCell>{task.T_reported != null ? `${task.T_reported}h` : "-"}</TableCell>
                      <TableCell>{task.T_actual != null ? `${task.T_actual}h` : "-"}</TableCell>
                      <TableCell>
                        {task.status === TaskStatusConst.BIDDING && task.bidding_deadline
                          ? <span className="font-mono text-xs text-orange-600">{useCountdown(task.bidding_deadline)}</span>
                          : "-"}
                      </TableCell>
                      <TableCell>{task.progress ?? "-"}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {task.expected_online_time ? formatDateShort(task.expected_online_time) : "-"}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {task.created_at ? formatDateShort(task.created_at) : "-"}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {actions.map((act) => (
                              <DropdownMenuItem
                                key={act.key}
                                onClick={() => handleAction(task, act.key)}
                              >
                                <act.icon className="mr-2 h-4 w-4" />
                                {act.label}
                              </DropdownMenuItem>
                            ))}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        {totalCount > 20 && (
          <Pagination
            page={page}
            total={totalCount}
            pageSize={20}
            onPageChange={setPage}
          />
        )}
      </CardContent>

      {/* 发布到竞价池弹窗 */}
      <Dialog
        open={actionDialog.open && actionDialog.action === "publish"}
        onOpenChange={(open) => { if (!open) setActionDialog({ open: false, task: null, action: "" }); }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>发布到竞价池</DialogTitle>
            <DialogDescription>
              将任务 <strong>{actionDialog.task?.name}</strong> 发布到竞价池，工程师将可以看到并进行报价。
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">竞价天数</label>
              <Input
                type="number"
                min={1}
                max={30}
                value={biddingDays}
                onChange={(e) => setBiddingDays(Number(e.target.value))}
              />
              <p className="text-xs text-muted-foreground">设置竞价截止天数，默认 3 天</p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setActionDialog({ open: false, task: null, action: "" })}
            >
              取消
            </Button>
            <Button
              onClick={handleConfirmPublish}
              disabled={publishTask.isPending}
            >
              {publishTask.isPending ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />发布中...</>
              ) : "确认发布"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}