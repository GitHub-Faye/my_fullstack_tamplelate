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
import { Loader2 } from "lucide-react";
import { useTasks } from "../api";
import type { TaskPublic, TaskStatus, TaskType } from "@repo/sdk";
import {
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
  TaskStatus as TaskStatusConst,
} from "@repo/contracts";

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
];

/**
 * 管理端任务列表组件
 *
 * 展示所有任务，支持状态筛选和审核操作入口
 */
export function AdminTaskTable() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("all");

  const { data: tasks, isLoading } = useTasks({
    page,
    page_size: 20,
    status: status !== "all" ? (status as TaskStatus) : undefined,
  });

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
        <CardTitle>任务审核</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-4">
          <Select value={status} onValueChange={(v) => { setStatus(v); setPage(1); }}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="任务状态" />
            </SelectTrigger>
            <SelectContent>
              {REVIEW_FILTERS.map((f) => (
                <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>任务名称</TableHead>
                <TableHead>发布人</TableHead>
                <TableHead>任务类型</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>T报</TableHead>
                <TableHead>T实</TableHead>
                <TableHead>创建时间</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {taskList?.map((task: TaskPublic) => (
                <TableRow key={task.id}>
                  <TableCell className="font-medium">{task.name}</TableCell>
                  <TableCell>{task.pm_id ?? "-"}</TableCell>
                  <TableCell>{task.task_type ? TYPE_LABELS[task.task_type] : "正常任务"}</TableCell>
                  <TableCell>
                    <Badge>{STATUS_LABELS[task.status]}</Badge>
                  </TableCell>
                  <TableCell>{task.T_reported ? `${task.T_reported}h` : "-"}</TableCell>
                  <TableCell>{task.T_actual ? `${task.T_actual}h` : "-"}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(task.created_at ?? "").toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="link"
                      size="sm"
                      onClick={() => router.push(`/dashboard/admin/tasks/${task.id}`)}
                    >
                      审核
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {(!taskList || taskList.length === 0) && (
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
          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-muted-foreground">
              共 {tasks.count} 条记录
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                上一页
              </Button>
              <span className="text-sm">第 {page} 页</span>
              <Button
                variant="outline"
                size="sm"
                disabled={tasks.count !== undefined && page * 20 >= tasks.count}
                onClick={() => setPage(page + 1)}
              >
                下一页
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}