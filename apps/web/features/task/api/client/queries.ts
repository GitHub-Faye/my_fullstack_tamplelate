/**
 * Task 模块 API Query Hooks
 *
 * 基于 @repo/sdk 自动生成的类型，提供 React Query hooks
 */

"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from "@tanstack/react-query";
import { toast } from "sonner";
import {
  // SDK functions
  createTaskV1TasksPost,
  readTasksV1TasksGet,
  readTaskV1TasksTaskIdGet,
  updateTaskV1TasksTaskIdPut,
  deleteTaskV1TasksTaskIdDelete,
  // Types
  type TaskCreate,
  type TaskPublic,
  type TasksPublic,
  type TaskUpdate,
  type ReadTasksV1TasksGetData,
} from "@repo/sdk";

// Query Keys
export const taskKeys = {
  all: ["tasks"] as const,
  lists: () => [...taskKeys.all, "list"] as const,
  list: (filters: ReadTasksV1TasksGetData["query"]) =>
    [...taskKeys.lists(), filters] as const,
  details: () => [...taskKeys.all, "detail"] as const,
  detail: (id: string) => [...taskKeys.details(), id] as const,
};

// ==================== Queries ====================

/**
 * 获取任务列表（PM 视图）
 */
export function useTasks(
  filters: ReadTasksV1TasksGetData["query"] = { page: 1, page_size: 20 },
  options?: Omit<
    UseQueryOptions<TasksPublic, Error, TasksPublic>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: taskKeys.list(filters),
    queryFn: async () => {
      const response = await readTasksV1TasksGet({
        query: filters,
        throwOnError: true,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * 获取任务详情
 */
export function useTask(
  taskId: string,
  options?: Omit<
    UseQueryOptions<TaskPublic, Error, TaskPublic>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: taskKeys.detail(taskId),
    queryFn: async () => {
      const response = await readTaskV1TasksTaskIdGet({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    enabled: !!taskId,
    ...options,
  });
}

// ==================== Mutations ====================

/**
 * 创建任务（PM）
 */
export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: TaskCreate) => {
      const response = await createTaskV1TasksPost({
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
      toast.success("任务创建成功");
    },
    onError: (error: Error) => {
      toast.error(error.message || "创建任务失败");
    },
  });
}

/**
 * 更新任务（PM）
 */
export function useUpdateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      taskId,
      data,
    }: {
      taskId: string;
      data: TaskUpdate;
    }) => {
      const response = await updateTaskV1TasksTaskIdPut({
        path: { task_id: taskId },
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: taskKeys.detail(variables.taskId),
      });
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
      toast.success("任务更新成功");
    },
    onError: (error: Error) => {
      toast.error(error.message || "更新任务失败");
    },
  });
}

// 删除任务 (Spec: 工单未要求删除功能，保留备用)
