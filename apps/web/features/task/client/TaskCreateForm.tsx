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
export function TaskCreateForm() {
  const createTask = useCreateTask();

  const form = useForm<TaskCreateFormData>({
    resolver: zodResolver(taskCreateSchema),
    defaultValues: {
      name: "",
      description: null,
      task_type: "normal",
    },
  });

  async function onSubmit(data: TaskCreateFormData) {
    try {
      const payload: TaskCreate = {
        name: data.name,
        description: data.description ?? undefined,
        task_type: data.task_type,
      };
      await createTask.mutateAsync(payload);
      form.reset();
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