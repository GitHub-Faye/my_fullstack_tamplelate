"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { Loader2, Paperclip } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
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
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { taskUpdateSchema, type TaskUpdateFormData } from "../schemas";
import { useUpdateTask, useTask } from "../api";
import type { TaskUpdate } from "@repo/sdk";

interface TaskEditFormProps {
  taskId: string;
}

/**
 * 任务编辑表单组件
 */
export function TaskEditForm({ taskId }: TaskEditFormProps) {
  const router = useRouter();
  const { data: task, isLoading: loadingTask } = useTask(taskId);
  const updateTask = useUpdateTask();

  const form = useForm<TaskUpdateFormData>({
    resolver: zodResolver(taskUpdateSchema),
    values: task
      ? {
          name: task.name ?? null,
          description: task.description ?? null,
          task_type: task.task_type ?? null,
          expected_online_time: task.expected_online_time ?? null,
        }
      : undefined,
  });

  if (loadingTask) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!task) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold">任务不存在</h2>
      </div>
    );
  }

  async function onSubmit(data: TaskUpdateFormData) {
    try {
      const payload: TaskUpdate = {
        name: data.name ?? undefined,
        description: data.description ?? undefined,
        task_type: data.task_type ?? undefined,
        expected_online_time: data.expected_online_time ?? undefined,
      };
      await updateTask.mutateAsync({ taskId, data: payload });
      router.push(`/pm/tasks/${taskId}`);
    } catch {
      // Error is handled by mutation
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>编辑任务</CardTitle>
        <CardDescription>修改任务信息</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>任务名称 *</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="请输入任务名称"
                      {...field}
                      value={field.value ?? ""}
                      disabled={updateTask.isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>任务描述</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="请输入任务描述"
                      rows={4}
                      {...field}
                      value={field.value ?? ""}
                      disabled={updateTask.isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="task_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>任务类型</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    value={field.value ?? undefined}
                    disabled={updateTask.isPending}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="请选择任务类型" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="normal">正常任务</SelectItem>
                      <SelectItem value="urgent">紧急任务</SelectItem>
                      <SelectItem value="convenient">便捷任务</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="expected_online_time"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>预期上线时间</FormLabel>
                  <FormControl>
                    <Input
                      type="date"
                      {...field}
                      value={field.value ?? ""}
                      disabled={updateTask.isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* 附件上传骨架 — 后端上传路由就绪后对接 */}
            <div className="space-y-2">
              <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">附件</label>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled
                >
                  <Paperclip className="mr-1 h-4 w-4" />
                  选择文件
                </Button>
                <span className="text-xs text-muted-foreground">暂未开放，后续版本支持</span>
              </div>
              <p className="text-xs text-muted-foreground">
                支持上传任务相关文档（PRD、设计稿等）
              </p>
            </div>

            <div className="flex gap-4">
              <Button
                type="submit"
                disabled={updateTask.isPending}
              >
                {updateTask.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    保存中...
                  </>
                ) : (
                  "保存修改"
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
              >
                取消
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}