"use client";

import { useState } from "react";
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
import { Loader2, Search, RotateCcw } from "lucide-react";
import { useTasks } from "../api";
import { useUserMap, useCurrentUser } from "@/features/user";
import type { TaskPublic, TaskStatus, TaskType } from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";
import { Pagination } from "@/components/ui/pagination";

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

/**
 * 任务列表表格组件（工程师视图）
 *
 * 包含两个标签页：
 * - "我的任务"：展示工程师本人任务（T报、T实、进度等）
 * - "竞价任务"：展示可竞价的开放任务（报价倒计时、发布人等）
 */
export function EngineerTaskTable() {
  const [tab, setTab] = useState<TabType>("mine");
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("all");
  const [taskTypeFilter, setTaskTypeFilter] = useState("all");

  const user = useCurrentUser();
  const userMap = useUserMap();

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

  const { data: tasks, isLoading } = useTasks(queryParams as any);

  const taskList = (tasks?.data as TaskPublic[]) || [];
  const count = tasks?.count || 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  /** 格式化日期时间 */
  function formatDateTime(dateStr: string | null | undefined): string {
    if (!dateStr) return "-";
    const d = new Date(dateStr);
    return isNaN(d.getTime())
      ? "-"
      : `${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
  }

  function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return "-";
    const d = new Date(dateStr);
    return isNaN(d.getTime())
      ? "-"
      : `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")}`;
  }

  /** 计算报价倒计时 */
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

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle>任务管理</CardTitle>
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
                      <Button
                        variant="link"
                        size="sm"
                        // TODO: 详情页面
                      >
                        详情
                      </Button>
                      {task.status === TaskStatusConst.PENDING_START && (
                        <Button variant="link" size="sm">
                          启动
                        </Button>
                      )}
                      {task.status === TaskStatusConst.PAUSED && (
                        <Button variant="link" size="sm">
                          恢复
                        </Button>
                      )}
                      {(task.status === TaskStatusConst.PENDING_START || task.status === TaskStatusConst.BIDDING) && (
                        <Button variant="link" size="sm" className="text-red-600">
                          拒绝
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
                      {task.pm_id ? userMap[task.pm_id] ?? task.pm_id.slice(0, 8) : "-"}
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
                      <Button variant="link" size="sm">
                        报价
                      </Button>
                      <Button variant="link" size="sm">
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
  );
}