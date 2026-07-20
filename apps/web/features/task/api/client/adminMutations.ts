/**
 * Admin Task 审核模块 API Query Hooks
 *
 * 基于 @repo/sdk 自动生成的类型，提供管理员任务审核相关 React Query hooks
 */

"use client";

import {
  useMutation,
  useQueryClient,
  type UseMutationOptions,
} from "@tanstack/react-query";
import { toast } from "sonner";
import {
  // SDK functions
  approveTaskV1TasksTaskIdApprovePost,
  rejectTaskV1TasksTaskIdRejectPost,
  publishTaskV1TasksTaskIdPublishPost,
  convertToUrgentV1TasksTaskIdConvertUrgentPost,
  convertToConvenientV1TasksTaskIdConvertConvenientPost,
  // Types
  type TaskPublic,
} from "@repo/sdk";

// ==================== Mutations ====================

/**
 * 审核通过任务（管理员）
 */
export function useApproveTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      const response = await approveTaskV1TasksTaskIdApprovePost({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("任务审核通过");
    },
    onError: (error: Error) => {
      toast.error(error.message || "审核失败");
    },
  });
}

/**
 * 驳回任务（管理员）
 */
export function useRejectTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      const response = await rejectTaskV1TasksTaskIdRejectPost({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("任务已驳回");
    },
    onError: (error: Error) => {
      toast.error(error.message || "驳回失败");
    },
  });
}

/**
 * 发布任务到竞价池（管理员）
 */
export function usePublishTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      taskId,
      biddingDays = 3,
    }: {
      taskId: string;
      biddingDays?: number;
    }) => {
      const response = await publishTaskV1TasksTaskIdPublishPost({
        path: { task_id: taskId },
        query: { bidding_days: biddingDays },
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("任务已发布到竞价池");
    },
    onError: (error: Error) => {
      toast.error(error.message || "发布失败");
    },
  });
}

/**
 * 转换为紧急任务（管理员）
 */
export function useConvertToUrgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      const response = await convertToUrgentV1TasksTaskIdConvertUrgentPost({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("已转换为紧急任务");
    },
    onError: (error: Error) => {
      toast.error(error.message || "转换失败");
    },
  });
}

/**
 * 转换为便捷任务（管理员）
 */
export function useConvertToConvenient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      const response = await convertToConvenientV1TasksTaskIdConvertConvenientPost({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      toast.success("已转换为便捷任务");
    },
    onError: (error: Error) => {
      toast.error(error.message || "转换失败");
    },
  });
}
