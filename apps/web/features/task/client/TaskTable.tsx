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
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Plus, Search } from "lucide-react";
import Link from "next/link";
import { useTasks } from "../api";
import type { TaskPublic, TaskStatus, TaskType } from "@repo/sdk";

const STATUS_LABELS: Record<TaskStatus, string> = {
  unconfirmed: "未确认",
  confirmed_unpublished: "已确认未发布",
  bidding: "竞价中",
  pending_start: "待启动",
  in_progress: "进行中",
  pause_requested: "暂停待审批",
  paused: "暂停中",
  completed: "已完成",
};

const TYPE_LABELS: Record<TaskType, string> = {
  normal: "正常任务",
  urgent: "紧急任务",
  convenient: "便捷任务",
};

/**
 * 任务列表表格组件（PM 视图）
 */
export function TaskTable() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("all");
  const [search, setSearch] = useState("");

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
        <div className="flex items-center justify-between">
          <CardTitle>任务管理</CardTitle>
          <Button asChild>
            <Link href="/dashboard/pm/tasks/new">
              <Plus className="mr-2 h-4 w-4" />
              发布任务
            </Link>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-4">
          <div className="flex items-center gap-2">
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="任务状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="unconfirmed">未确认</SelectItem>
                <SelectItem value="bidding">竞价中</SelectItem>
                <SelectItem value="pending_start">待启动</SelectItem>
                <SelectItem value="in_progress">进行中</SelectItem>
                <SelectItem value="completed">已完成</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2 flex-1 max-w-sm">
            <Input
              placeholder="搜索任务名称"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <Button variant="outline" size="icon">
              <Search className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>任务名称</TableHead>
                <TableHead>任务类型</TableHead>
                <TableHead>工程师</TableHead>
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
                  <TableCell>{task.task_type ? TYPE_LABELS[task.task_type] : "正常任务"}</TableCell>
                  <TableCell>{task.engineer_id ?? "-"}</TableCell>
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
                      onClick={() => router.push(`/dashboard/pm/tasks/${task.id}`)}
                    >
                      详情
                    </Button>
                    {task.status === "unconfirmed" && (
                      <Button
                        variant="link"
                        size="sm"
                        onClick={() => router.push(`/dashboard/pm/tasks/${task.id}/edit`)}
                      >
                        编辑
                      </Button>
                    )}
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