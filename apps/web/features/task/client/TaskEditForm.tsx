"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";

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

import { taskUpdateSchema, type TaskUpdateFormData } from "../schemas";
import { useUpdateTask, useTask } from "../api";
import { AttachmentUpload } from "./AttachmentUpload";
import type { TaskUpdate } from "@repo/sdk";

interface TaskEditFormProps {
  taskId: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

/**
 * 任务编辑表单组件
 */
export function TaskEditForm({ taskId, onSuccess, onCancel }: TaskEditFormProps) {
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
          T_estimate: task.T_estimate ?? null,
        }
      : undefined,
  });

  if (loadingTask) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!task) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">任务不存在</p>
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
        T_estimate: data.T_estimate != null ? Number(data.T_estimate) : undefined,
      };
      await updateTask.mutateAsync({ taskId, data: payload });
      onSuccess?.();
    } catch {
      // Error is handled by mutation
    }
  }

  return (
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
          name="T_estimate"
          render={({ field }) => (
            <FormItem>
              <FormLabel>T估（预计完成工时，小时）</FormLabel>
              <FormControl>
                <Input
                  type="number"
                  min={0}
                  step="0.5"
                  placeholder="例如：8"
                  value={field.value ?? ""}
                  onChange={(e) => field.onChange(e.target.value)}
                  disabled={updateTask.isPending}
                />
              </FormControl>
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

        {/* 附件管理 */}
        <AttachmentUpload taskId={taskId} />

        <div className="flex justify-end gap-4">
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
            >
              取消
            </Button>
          )}
          <Button type="submit" disabled={updateTask.isPending}>
            {updateTask.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                保存中...
              </>
            ) : (
              "保存修改"
            )}
          </Button>
        </div>
      </form>
    </Form>
  );
}