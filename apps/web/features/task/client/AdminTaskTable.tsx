"use client";

import { useState } from "react";
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
import { Loader2, MoreHorizontal, Eye } from "lucide-react";
import { useTasks } from "../api";
import { useUserMap } from "@/features/user";
import type { TaskPublic, TaskStatus, TaskType } from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";
import { Pagination } from "@/components/ui/pagination";
import { formatDateShort } from "@/lib/utils";

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
  { value: TaskStatusConst.COMPLETED, label: "已完成" },
  { value: TaskStatusConst.PAUSED, label: "已暂停" },
];

/**
 * 管理端任务列表组件
 *
 * 展示所有任务，支持状态/工程师/PM 筛选和操作入口
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>任务管理</CardTitle>
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
                <TableHead>进度</TableHead>
                <TableHead>预计上线时间</TableHead>
                <TableHead>创建时间</TableHead>
                <TableHead className="w-[80px]">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={11} className="text-center py-8">
                    暂无任务数据
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((task: TaskPublic) => (
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
                          <DropdownMenuItem onClick={() => router.push(`/admin/tasks/${task.id}`)}>
                            <Eye className="mr-2 h-4 w-4" />
                            审核
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
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
    </Card>
  );
}