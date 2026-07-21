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
import { Loader2, Plus, Search, RotateCcw } from "lucide-react";
import Link from "next/link";
import { useTasks } from "../api";
import { useUserMap, useCurrentUser } from "@/features/user";
import type { TaskPublic, TaskStatus, TaskType } from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  PM_EDITABLE_STATUSES,
} from "@repo/contracts";
import { Pagination } from "@/components/ui/pagination";

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

/**
 * 任务列表表格组件（PM 视图）
 */
export function TaskTable() {
  const router = useRouter();
  const [page, setPage] = useState(1);

  // 当前用户信息
  const user = useCurrentUser();
  // 用户 ID → 姓名 映射
  const userMap = useUserMap();

  // 筛选条件状态
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

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

  const { data: tasks, isLoading } = useTasks(queryParams as any);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const taskList = tasks?.data as TaskPublic[] | undefined;

  return (
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
                    <Button
                      variant="link"
                      size="sm"
                      onClick={() => router.push(`/pm/tasks/${task.id}`)}
                    >
                      详情
                    </Button>
                    {PM_EDITABLE_STATUSES.includes(task.status as any) && (
                      <Button
                        variant="link"
                        size="sm"
                        onClick={() => router.push(`/pm/tasks/${task.id}/edit`)}
                      >
                        编辑
                      </Button>
                    )}
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
  );
}