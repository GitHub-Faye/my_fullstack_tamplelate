"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Paperclip, X } from "lucide-react";

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

import { taskCreateSchema, type TaskCreateFormData } from "../schemas";
import { useCreateTask } from "../api";
import type { TaskCreate } from "@repo/sdk";

/**
 * 任务创建表单组件
 */
export function TaskCreateForm({ onSuccess }: { onSuccess?: () => void }) {
  const createTask = useCreateTask();

  const form = useForm<TaskCreateFormData>({
    resolver: zodResolver(taskCreateSchema),
    defaultValues: {
      name: "",
      description: null,
      task_type: "normal",
      expected_online_time: null,
    },
  });

  async function onSubmit(data: TaskCreateFormData) {
    try {
      const payload: TaskCreate = {
        name: data.name,
        description: data.description ?? undefined,
        task_type: data.task_type,
        expected_online_time: data.expected_online_time ?? undefined,
      };
      await createTask.mutateAsync(payload);
      form.reset();
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
                  disabled={createTask.isPending}
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
                  disabled={createTask.isPending}
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
                defaultValue={field.value}
                disabled={createTask.isPending}
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
                  disabled={createTask.isPending}
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

        <Button type="submit" className="w-full" disabled={createTask.isPending}>
          {createTask.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              创建中...
            </>
          ) : (
            "创建任务"
          )}
        </Button>
      </form>
    </Form>
  );
}