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
  type UseMutationResult,
} from "@tanstack/react-query";
import { toast } from "sonner";
import {
  // SDK functions
  approveTaskV1TasksTaskIdApprovePost,
  rejectTaskV1TasksTaskIdRejectPost,
  publishTaskV1TasksTaskIdPublishPost,
  convertToUrgentV1TasksTaskIdConvertUrgentPost,
  convertToConvenientV1TasksTaskIdConvertConvenientPost,
  pauseApproveTaskV1TasksTaskIdPauseApprovePost,
  pauseRejectTaskV1TasksTaskIdPauseRejectPost,
  adminRestoreTaskV1TasksTaskIdRestorePost,
  type TaskPublic,
} from "@repo/sdk";

// 管理端专用查询 key，避免与 PM 端交叉污染
export const adminTaskKeys = {
  all: ["admin-tasks"] as const,
};

// ==================== 工厂函数 ====================

type MutationFn<T> = (taskId: string) => Promise<TaskPublic | undefined>;

function makeAdminMutation<T>(
  mutationFn: MutationFn<T>,
  successMsg: string,
  errorMsg: string,
): UseMutationResult<TaskPublic | undefined, Error, string> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminTaskKeys.all });
      toast.success(successMsg);
    },
    onError: (error: Error) => {
      toast.error(error.message || errorMsg);
    },
  }) as UseMutationResult<TaskPublic | undefined, Error, string>;
}

// ==================== Mutations ====================

/**
 * 审核通过任务（管理员）
 */
export function useApproveTask() {
  return makeAdminMutation(
    async (taskId: string) => {
      const response = await approveTaskV1TasksTaskIdApprovePost({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    "任务审核通过",
    "审核失败",
  );
}

/**
 * 驳回任务（管理员）
 */
export function useRejectTask() {
  return makeAdminMutation(
    async (taskId: string) => {
      const response = await rejectTaskV1TasksTaskIdRejectPost({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    "任务已驳回",
    "驳回失败",
  );
}

/**
 * 发布任务到竞价池（管理员）
 */
export function usePublishTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      taskId,
      biddingDays,
    }: {
      taskId: string;
      biddingDays: number;
    }) => {
      const response = await publishTaskV1TasksTaskIdPublishPost({
        path: { task_id: taskId },
        query: { bidding_days: biddingDays },
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: adminTaskKeys.all });
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
  return makeAdminMutation(
    async (taskId: string) => {
      const response = await convertToUrgentV1TasksTaskIdConvertUrgentPost({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    "已转换为紧急任务",
    "转换失败",
  );
}

/**
 * 转换为便捷任务（管理员）
 */
export function useConvertToConvenient() {
  return makeAdminMutation(
    async (taskId: string) => {
      const response = await convertToConvenientV1TasksTaskIdConvertConvenientPost({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    "已转换为便捷任务",
    "转换失败",
  );
}

/**
 * 审批暂停通过（管理员）
 */
export function usePauseApproveTask() {
  return makeAdminMutation(
    async (taskId: string) => {
      const response = await pauseApproveTaskV1TasksTaskIdPauseApprovePost({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    "暂停审批通过",
    "审批失败",
  );
}

/**
 * 驳回暂停申请（管理员）
 */
export function usePauseRejectTask() {
  return makeAdminMutation(
    async (taskId: string) => {
      const response = await pauseRejectTaskV1TasksTaskIdPauseRejectPost({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    "已驳回暂停申请",
    "驳回失败",
  );
}

/**
 * 恢复暂停任务（管理员）
 */
export function useAdminRestoreTask() {
  return makeAdminMutation(
    async (taskId: string) => {
      const response = await adminRestoreTaskV1TasksTaskIdRestorePost({
        path: { task_id: taskId },
        throwOnError: true,
      });
      return response.data;
    },
    "任务已恢复",
    "恢复失败",
  );
}