"use client";

import { useState, useEffect, useMemo } from "react";
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
import { Loader2, MoreHorizontal, Eye, CheckCircle, XCircle, Send, RefreshCw, AlertTriangle, ArrowLeftRight, Play, Plus, FileText, Calendar } from "lucide-react";
import { useTasks, useTask } from "../api";
import { useUsers } from "@/features/user";
import {
  usePublishTask,
  useConvertToUrgent,
  useConvertToConvenient,
  useSettleBidding,
} from "../api/client/adminMutations";
import type { TaskPublic, TaskStatus, TaskType } from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  TASK_STATUS_COLORS,
  TASK_TYPE_COLORS,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";
import { Pagination } from "@/components/ui/pagination";
import { formatDateShort, formatDate } from "@/lib/utils";
import { toast } from "sonner";
import { BidLogDialog } from "./BidLogDialog";
import { TaskDetailDialog } from "./TaskDetailDialog";
import { WorkLogDialog } from "./WorkLogDialog";
import { AuditLogDialog } from "./AuditLogDialog";
import { AdminTaskAssignDialog } from "./AdminTaskAssignDialog";

const STATUS_LABELS: Record<TaskStatus, string> = TASK_STATUS_LABELS;
const STATUS_COLORS: Record<TaskStatus, string> = TASK_STATUS_COLORS;
const TYPE_COLORS: Record<TaskType, string> = TASK_TYPE_COLORS;
const TYPE_LABELS: Record<TaskType, string> = TASK_TYPE_LABELS;

/** 审核管理关注的状态列表 */
const REVIEW_FILTERS: { value: string; label: string }[] = [
  { value: "all", label: "全部状态" },
  { value: TaskStatusConst.UNCONFIRMED, label: "未确认" },
  { value: TaskStatusConst.BIDDING, label: "竞价中" },
  { value: TaskStatusConst.PENDING_START, label: "待启动" },
  { value: TaskStatusConst.IN_PROGRESS, label: "进行中" },
  { value: TaskStatusConst.PAUSED, label: "已暂停" },
  { value: TaskStatusConst.COMPLETED, label: "已完成" },
];

/** 报价倒计时函数（纯函数，由组件层每秒触发的 now 驱动重新渲染） */
function formatCountdown(deadline: string | null | undefined, now: number): string {
  if (!deadline) return "-";
  const end = new Date(deadline).getTime();
  const diff = end - now;
  if (diff <= 0) return "已截止";
  const h = Math.floor(diff / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  const s = Math.floor((diff % 60000) / 1000);
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

/** 根据任务状态返回管理员可执行的操作列表 */
function getAdminActions(status: TaskStatus) {
  switch (status) {
    case TaskStatusConst.UNCONFIRMED:
      return [
        { key: "publish", label: "发布到竞价池", icon: Send },
        { key: "detail", label: "详情", icon: Eye },
      ];
    case TaskStatusConst.BIDDING:
      return [
        { key: "settleBidding", label: "触发竞价结算", icon: CheckCircle },
        { key: "viewBids", label: "查看报价", icon: FileText },
        { key: "convertUrgent", label: "改为紧急", icon: AlertTriangle },
        { key: "convertConvenient", label: "改为便捷", icon: RefreshCw },
        { key: "detail", label: "详情", icon: Eye },
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
    case TaskStatusConst.PAUSED:
      return [
        { key: "detail", label: "详情", icon: Eye },
      ];
    case TaskStatusConst.COMPLETED:
      return [
        { key: "auditLogs", label: "操作日志", icon: FileText },
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
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  // 每秒递增的 ticker，用于驱动报价倒计时刷新
  const [now, setNow] = useState(Date.now());

  // 改派弹窗状态
  const [assignTask, setAssignTask] = useState<TaskPublic | null>(null);

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  const { data: tasks, isLoading } = useTasks({
    page,
    page_size: 20,
    status: status !== "all" ? (status as TaskStatus) : undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  });

  // 获取用户列表用于姓名映射
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

  // 操作弹窗状态
  const [actionDialog, setActionDialog] = useState<{ open: boolean; task: TaskPublic | null; action: string }>({
    open: false, task: null, action: "",
  });
  const [biddingDays, setBiddingDays] = useState(3);
  const [bidLogTask, setBidLogTask] = useState<TaskPublic | null>(null);
  const [detailTask, setDetailTask] = useState<TaskPublic | null>(null);
  const [workLogTask, setWorkLogTask] = useState<TaskPublic | null>(null);
  const [auditLogTask, setAuditLogTask] = useState<TaskPublic | null>(null);

  const publishTask = usePublishTask();
  const convertToUrgent = useConvertToUrgent();
  const convertToConvenient = useConvertToConvenient();
  const settleBidding = useSettleBidding();

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
      case "publish":
        setActionDialog({ open: true, task, action: "publish" });
        break;
      case "viewBids":
        setBidLogTask(task);
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
        setAssignTask(task);
        break;
      case "settleBidding":
        try {
          await settleBidding.mutateAsync(task.id);
        } catch {
          // handled by mutation
        }
        break;
      case "auditLogs":
        setAuditLogTask(task);
        break;
      case "detail":
        setDetailTask(task);
        break;
      case "workLog":
        setWorkLogTask(task);
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
          {/* 管理员不创建任务，仅审核 — 见 PRD 2.2 功能矩阵 */}
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
                <SelectItem key={id} value={id}>{userMap[id] || id.slice(0, 8)}</SelectItem>
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
                <SelectItem key={id} value={id}>{userMap[id] || id.slice(0, 8)}</SelectItem>
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
                <TableHead>T报完成时间</TableHead>
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
                        <Badge variant={TYPE_COLORS[task.task_type ?? "normal"] as never} className="text-xs">
                          {task.task_type ? TYPE_LABELS[task.task_type] : "正常"}
                        </Badge>
                      </TableCell>
                      <TableCell>{(task as any).pm_name ?? (task.pm_id?.slice(0, 8) || "-")}</TableCell>
                      <TableCell>{(task as any).engineer_name ?? (task.engineer_id?.slice(0, 8) || "-")}</TableCell>
                      <TableCell>
                        <Badge variant={STATUS_COLORS[task.status] as never}>
                          {STATUS_LABELS[task.status]}
                        </Badge>
                      </TableCell>
                      <TableCell>{task.T_reported != null ? `${task.T_reported}h` : "-"}</TableCell>
                      <TableCell>{task.T_actual != null ? `${task.T_actual}h` : "-"}</TableCell>
                      <TableCell>
                        {task.status === TaskStatusConst.BIDDING && task.bidding_deadline
                          ? <span className="font-mono text-xs text-orange-600">{formatCountdown(task.bidding_deadline, now)}</span>
                          : "-"}
                      </TableCell>
                      <TableCell>{task.progress ?? "-"}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(task.T_reported_complete_time)}
                      </TableCell>
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

      {/* 报价记录弹窗 */}
      {bidLogTask && (
        <BidLogDialog
          task={bidLogTask}
          open={!!bidLogTask}
          onOpenChange={(open) => { if (!open) setBidLogTask(null); }}
        />
      )}

      {/* 详情弹窗 */}
      {detailTask && (
        <TaskDetailDialog
          task={detailTask}
          open={!!detailTask}
          onOpenChange={(open) => { if (!open) setDetailTask(null); }}
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

      {/* 改派弹窗 */}
      {assignTask && (
        <AdminTaskAssignDialog
          taskId={assignTask.id}
          open={!!assignTask}
          onOpenChange={(open) => {
            if (!open) setAssignTask(null);
          }}
        />
      )}

      {/* 审计日志弹窗 */}
      {auditLogTask && (
        <AuditLogDialog
          task={auditLogTask}
          open={!!auditLogTask}
          onOpenChange={(open) => { if (!open) setAuditLogTask(null); }}
        />
      )}
    </Card>
  );
}