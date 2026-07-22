"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Plus, Search, RotateCcw, X, Eye, FileText, Edit, Trash2, History, AlertTriangle, Archive, ReceiptText, ListTodo, NotebookText } from "lucide-react";
import Link from "next/link";
import { useTasks } from "../api";
import { useUserMap, useCurrentUser } from "@/features/user";
import {
  withdrawTaskV1TasksTaskIdWithdrawPost,
  deleteTaskV1TasksTaskIdDelete,
  readBidsByTaskV1TasksTaskIdBidsGet,
  readDailyReportsV1DailyReportsGet,
  readAuditLogsV1AuditLogsGet,
  type TaskPublic,
  type TaskStatus,
  type TaskType,
  type BidPublic,
} from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  PM_EDITABLE_STATUSES,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";
import { toast } from "sonner";
import { Pagination } from "@/components/ui/pagination";

// 操作类型列表 — 用于日志展示
const LOG_ACTIONS = ["bidLog", "viewLog", "workLog", "pauseLog", "archiveLog"] as const;
type LogAction = (typeof LOG_ACTIONS)[number];

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

/**
 * 格式化日期时间
 */
function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return isNaN(d.getTime())
    ? "-"
    : `${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

/**
 * 格式化日期（不含时间）
 */
function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return isNaN(d.getTime())
    ? "-"
    : `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")}`;
}

/** 任务状态 → PM 操作按钮映射 */
function getPmActions(task: TaskPublic, currentUserId: string | undefined, onAction: (action: string, task: TaskPublic) => void) {
  const status = task.status as string;
  const isOwner = currentUserId != null && task.pm_id === currentUserId;
  const actions: { label: string; icon: React.ReactNode; action: string; variant?: "default" | "outline" | "destructive" }[] = [];

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
      actions.push({
        label: "编辑",
        icon: <Edit className="h-3.5 w-3.5" />,
        action: "edit",
        variant: "outline",
      });
      actions.push({
        label: "删除",
        icon: <Trash2 className="h-3.5 w-3.5" />,
        action: "delete",
        variant: "destructive",
      });
      break;
    case TaskStatusConst.BIDDING:
      if (PM_EDITABLE_STATUSES.includes(status as any)) {
        actions.push({
          label: "编辑",
          icon: <Edit className="h-3.5 w-3.5" />,
          action: "edit",
          variant: "outline",
        });
      }
      actions.push({
        label: "报价记录",
        icon: <FileText className="h-3.5 w-3.5" />,
        action: "bidLog",
        variant: "outline",
      });
      actions.push({
        label: "撤回",
        icon: <AlertTriangle className="h-3.5 w-3.5" />,
        action: "withdraw",
        variant: "destructive",
      });
      break;
    case TaskStatusConst.PENDING_START:
      actions.push({
        label: "查看日志",
        icon: <History className="h-3.5 w-3.5" />,
        action: "viewLog",
        variant: "outline",
      });
      break;
    case TaskStatusConst.IN_PROGRESS:
      actions.push({
        label: "资料变更",
        icon: <FileText className="h-3.5 w-3.5" />,
        action: "changeDoc",
        variant: "outline",
      });
      actions.push({
        label: "工作日志",
        icon: <History className="h-3.5 w-3.5" />,
        action: "workLog",
        variant: "outline",
      });
      break;
    case TaskStatusConst.PAUSED:
      actions.push({
        label: "暂停记录",
        icon: <History className="h-3.5 w-3.5" />,
        action: "pauseLog",
        variant: "outline",
      });
      break;
    case TaskStatusConst.COMPLETED:
      actions.push({
        label: "归档日志",
        icon: <Archive className="h-3.5 w-3.5" />,
        action: "archiveLog",
        variant: "outline",
      });
      break;
  }

  return actions;
}

/**
 * 任务详情弹窗组件
 */
function TaskDetailDialog({
  task,
  open,
  onOpenChange,
  currentUserId,
}: {
  task: TaskPublic;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentUserId?: string;
}) {
  if (!task) return null;

  const isStarted = ["pending_start", "in_progress", "paused", "completed"].includes(task.status);
  const statusText = STATUS_LABELS[task.status] || task.status;
  const typeText = task.task_type ? TYPE_LABELS[task.task_type] ?? task.task_type : "-";
  const actions = getPmActions(task, currentUserId, () => {});

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
              <Badge variant="outline">{statusText}</Badge>
            </div>
            <div className="flex gap-1">
              <span className="text-muted-foreground shrink-0">发布人</span>
              <span>PM</span>
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
              <span>{formatDate(task.T_reported_complete_time)}</span>
            </div>
            <div className="flex gap-1">
              <span className="text-muted-foreground shrink-0">资料完整度</span>
              <span>-</span>
            </div>
            {isStarted && (
              <>
                <div className="flex gap-1">
                  <span className="text-muted-foreground shrink-0">执行工程师</span>
                  <span>-</span>
                </div>
                <div className="flex gap-1">
                  <span className="text-muted-foreground shrink-0">当前进度</span>
                  <span>{task.progress ?? "-"}</span>
                </div>
                <div className="flex gap-1">
                  <span className="text-muted-foreground shrink-0">T实</span>
                  <span>{task.T_actual != null ? `${task.T_actual}h` : "-"}</span>
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

          {/* 附件表格（占位） */}
          <div className="border rounded-md">
            <div className="px-3 py-2 text-sm font-medium border-b bg-muted/50">附件/截图</div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="text-left px-3 py-2 font-medium">文件</th>
                  <th className="text-left px-3 py-2 font-medium">类型</th>
                  <th className="text-left px-3 py-2 font-medium">状态</th>
                  <th className="text-left px-3 py-2 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-muted-foreground">
                    暂无附件（后端功能尚未实现）
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* 工作日志（占位） */}
          {isStarted && (
            <div className="border rounded-md">
              <div className="px-3 py-2 text-sm font-medium border-b bg-muted/50">最近工作日志</div>
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
                  <tr>
                    <td colSpan={4} className="px-3 py-6 text-center text-muted-foreground">
                      暂无工作日志
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* 附件表格（占位） */}
          <div className="border rounded-md">
            <div className="px-3 py-2 text-sm font-medium border-b bg-muted/50">附件/截图</div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="text-left px-3 py-2 font-medium">文件</th>
                  <th className="text-left px-3 py-2 font-medium">类型</th>
                  <th className="text-left px-3 py-2 font-medium">状态</th>
                  <th className="text-left px-3 py-2 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-muted-foreground">
                    暂无附件（后端功能尚未实现）
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* 工作日志（占位） */}
          {isStarted && (
            <div className="border rounded-md">
              <div className="px-3 py-2 text-sm font-medium border-b bg-muted/50">最近工作日志</div>
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
                  <tr>
                    <td colSpan={4} className="px-3 py-6 text-center text-muted-foreground">
                      暂无工作日志
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex flex-wrap gap-2 pt-2 border-t">
            {actions.map((act) => (
              <Button
                key={act.action}
                variant={act.variant || "outline"}
                size="sm"
                onClick={() => {
                  onOpenChange(false);
                }}
              >
                {act.icon}
                <span className="ml-1">{act.label}</span>
              </Button>
            ))}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * 报价记录弹窗
 */
function BidLogDialog({
  task,
  open,
  onOpenChange,
}: {
  task: TaskPublic;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [bids, setBids] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && task) {
      setLoading(true);
      readBidsByTaskV1TasksTaskIdBidsGet({ path: { task_id: task.id } })
        .then((res) => setBids(res.data?.data ?? []))
        .catch(() => setBids([]))
        .finally(() => setLoading(false));
    }
  }, [open, task]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>报价记录 - {task.name}</DialogTitle>
          <DialogDescription>查看该任务的工程师报价列表</DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : bids && bids.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="text-left px-3 py-2 font-medium">工程师</th>
                <th className="text-left px-3 py-2 font-medium">报价工时(T报)</th>
                <th className="text-left px-3 py-2 font-medium">报价金额</th>
                <th className="text-left px-3 py-2 font-medium">报价时间</th>
              </tr>
            </thead>
            <tbody>
              {bids.map((bid: any) => (
                <tr key={bid.id} className="border-b last:border-0">
                  <td className="px-3 py-2">{bid.engineer_id?.slice(0, 8) ?? "-"}</td>
                  <td className="px-3 py-2">{bid.T_reported ?? "-"}h</td>
                  <td className="px-3 py-2">¥{bid.amount?.toLocaleString() ?? "-"}</td>
                  <td className="px-3 py-2 text-muted-foreground">{formatDateTime(bid.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-center py-8 text-muted-foreground">暂无报价记录</p>
        )}
      </DialogContent>
    </Dialog>
  );
}

/**
 * 审计日志弹窗（查看日志 / 暂停记录 / 归档日志）
 */
function AuditLogDialog({
  task,
  open,
  onOpenChange,
}: {
  task: TaskPublic;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [logs, setLogs] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && task) {
      setLoading(true);
      readAuditLogsV1AuditLogsGet({
        query: { target_type: "task", target_id: task.id, page: 1, page_size: 50 },
      })
        .then((res) => setLogs(res.data?.data ?? []))
        .catch(() => setLogs([]))
        .finally(() => setLoading(false));
    }
  }, [open, task]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>任务日志 - {task.name}</DialogTitle>
          <DialogDescription>查看该任务的操作记录</DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : logs && logs.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="text-left px-3 py-2 font-medium">时间</th>
                <th className="text-left px-3 py-2 font-medium">操作</th>
                <th className="text-left px-3 py-2 font-medium">详情</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log: any, i: number) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">{formatDateTime(log.created_at)}</td>
                  <td className="px-3 py-2">{log.action ?? "-"}</td>
                  <td className="px-3 py-2 text-muted-foreground">{log.details ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-center py-8 text-muted-foreground">暂无日志记录</p>
        )}
      </DialogContent>
    </Dialog>
  );
}

/**
 * 工作日志弹窗（日报）
 */
function WorkLogDialog({
  task,
  open,
  onOpenChange,
}: {
  task: TaskPublic;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [reports, setReports] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && task) {
      setLoading(true);
      readDailyReportsV1DailyReportsGet({
        query: { task_id: task.id, page: 1, page_size: 50 },
      })
        .then((res) => setReports(res.data?.data ?? []))
        .catch(() => setReports([]))
        .finally(() => setLoading(false));
    }
  }, [open, task]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>工作日志 - {task.name}</DialogTitle>
          <DialogDescription>查看该任务的工程师日报记录</DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : reports && reports.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="text-left px-3 py-2 font-medium">日期</th>
                <th className="text-left px-3 py-2 font-medium">投入</th>
                <th className="text-left px-3 py-2 font-medium">阶段</th>
                <th className="text-left px-3 py-2 font-medium">进度</th>
                <th className="text-left px-3 py-2 font-medium">说明</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((rpt: any, i: number) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="px-3 py-2 text-muted-foreground whitespace-nowrap">{formatDate(rpt.report_date ?? rpt.created_at)}</td>
                  <td className="px-3 py-2">{rpt.today_hours ?? "-"}h</td>
                  <td className="px-3 py-2">{rpt.current_stage ?? "-"}</td>
                  <td className="px-3 py-2">{rpt.progress ?? "-"}</td>
                  <td className="px-3 py-2 text-muted-foreground max-w-[200px] truncate">{rpt.notes ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-center py-8 text-muted-foreground">暂无工作日志</p>
        )}
      </DialogContent>
    </Dialog>
  );
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
  // 用户 ID → 姓名 映射
  const userMap = useUserMap();

  // 筛选条件状态
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  // 详情弹窗
  const [detailTask, setDetailTask] = useState<TaskPublic | null>(null);
  // 报价记录弹窗
  const [bidLogTask, setBidLogTask] = useState<TaskPublic | null>(null);
  // 审计日志弹窗（查看日志 / 暂停记录 / 归档日志）
  const [logTask, setLogTask] = useState<TaskPublic | null>(null);
  // 工作日志弹窗
  const [workLogTask, setWorkLogTask] = useState<TaskPublic | null>(null);

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

  const handleAction = useCallback(async (action: string, task: TaskPublic) => {
    switch (action) {
      case "detail":
        setDetailTask(task);
        break;
      case "edit":
        router.push(`/pm/tasks/${task.id}/edit`);
        break;
      case "delete":
        if (confirm("确认删除此任务？此操作不可撤销。")) {
          try {
            await deleteTaskV1TasksTaskIdDelete({ path: { task_id: task.id } });
            toast.success("任务已删除");
            refetch();
          } catch (e: any) {
            toast.error(e.message || "删除失败");
          }
        }
        break;
      case "withdraw":
        if (confirm("确认撤回此任务？撤回后任务将回到「未确认」状态。")) {
          try {
            await withdrawTaskV1TasksTaskIdWithdrawPost({ path: { task_id: task.id } });
            toast.success("任务已撤回");
            refetch();
          } catch (e: any) {
            toast.error(e.message || "撤回失败");
          }
        }
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
      default:
        break;
    }
  }, [router, refetch]);

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
                <SelectItem value="confirmed_unpublished">已确认未发布</SelectItem>
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
                      {task.pm_id ? userMap[task.pm_id] ?? task.pm_id.slice(0, 8) : "-"}
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
                      {task.engineer_id
                        ? userMap[task.engineer_id] ?? task.engineer_id.slice(0, 8)
                        : "-"}
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
                      {getPmActions(task, user?.id, handleAction).map((act) => (
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
          onOpenChange={(open) => {
            if (!open) setDetailTask(null);
          }}
          currentUserId={user?.id}
        />
      )}

      {/* 报价记录弹窗 */}
      {bidLogTask && (
        <BidLogDialog
          task={bidLogTask}
          open={!!bidLogTask}
          onOpenChange={(open) => {
            if (!open) setBidLogTask(null);
          }}
        />
      )}

      {/* 审计日志弹窗（查看日志 / 暂停记录 / 归档日志） */}
      {logTask && (
        <AuditLogDialog
          task={logTask}
          open={!!logTask}
          onOpenChange={(open) => {
            if (!open) setLogTask(null);
          }}
        />
      )}

      {/* 工作日志弹窗 */}
      {workLogTask && (
        <WorkLogDialog
          task={workLogTask}
          open={!!workLogTask}
          onOpenChange={(open) => {
            if (!open) setWorkLogTask(null);
          }}
        />
      )}
    </>
  );
}