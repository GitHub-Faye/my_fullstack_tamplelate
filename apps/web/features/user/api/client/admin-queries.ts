"use client";

import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { toast } from "sonner";
import {
  adminToggleUserActiveV1AdminUsersUserIdToggleActivePost,
  adminResetPasswordV1AdminUsersUserIdResetPasswordPost,
  adminCreateUserV1AdminUsersPost,
  adminUpdateUserV1AdminUsersUserIdPatch,
  adminReadUserV1AdminUsersUserIdGet,
  type AdminToggleUserActiveV1AdminUsersUserIdToggleActivePostData,
  type AdminToggleUserActiveV1AdminUsersUserIdToggleActivePostError,
  type AdminToggleUserActiveV1AdminUsersUserIdToggleActivePostResponse,
  type AdminResetPasswordV1AdminUsersUserIdResetPasswordPostData,
  type AdminResetPasswordV1AdminUsersUserIdResetPasswordPostError,
  type AdminResetPasswordV1AdminUsersUserIdResetPasswordPostResponse,
  type AdminCreateUserV1AdminUsersPostData,
  type AdminCreateUserV1AdminUsersPostError,
  type AdminCreateUserV1AdminUsersPostResponse,
  type AdminUpdateUserV1AdminUsersUserIdPatchData,
  type AdminUpdateUserV1AdminUsersUserIdPatchError,
  type AdminUpdateUserV1AdminUsersUserIdPatchResponse,
  type AdminReadUserV1AdminUsersUserIdGetData,
  type AdminReadUserV1AdminUsersUserIdGetResponse,
  type AdminReadUserV1AdminUsersUserIdGetError,
} from "@repo/sdk";
import { userKeys } from "./queries";

/**
 * 管理员创建用户 mutation
 */
export function useAdminCreateUser() {
  const queryClient = useQueryClient();

  return useMutation<
    AdminCreateUserV1AdminUsersPostResponse,
    AdminCreateUserV1AdminUsersPostError,
    AdminCreateUserV1AdminUsersPostData
  >({
    mutationFn: async (data) => {
      const response = await adminCreateUserV1AdminUsersPost({
        ...data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      toast.success("用户创建成功");
    },
    onError: (error) => {
      toast.error((error as Error)?.message || "创建用户失败");
    },
  });
}

/**
 * 管理员更新用户 mutation
 */
export function useAdminUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation<
    AdminUpdateUserV1AdminUsersUserIdPatchResponse,
    AdminUpdateUserV1AdminUsersUserIdPatchError,
    AdminUpdateUserV1AdminUsersUserIdPatchData
  >({
    mutationFn: async (data) => {
      const response = await adminUpdateUserV1AdminUsersUserIdPatch({
        ...data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: userKeys.detail(variables.path.user_id),
      });
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      toast.success("用户更新成功");
    },
    onError: (error) => {
      toast.error((error as Error)?.message || "更新用户失败");
    },
  });
}

/**
 * 管理员启用/禁用用户 mutation
 */
export function useAdminToggleUserActive() {
  const queryClient = useQueryClient();

  return useMutation<
    AdminToggleUserActiveV1AdminUsersUserIdToggleActivePostResponse,
    AdminToggleUserActiveV1AdminUsersUserIdToggleActivePostError,
    AdminToggleUserActiveV1AdminUsersUserIdToggleActivePostData
  >({
    mutationFn: async (data) => {
      const response = await adminToggleUserActiveV1AdminUsersUserIdToggleActivePost({
        ...data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      toast.success("用户状态已更新");
    },
    onError: (error) => {
      toast.error((error as Error)?.message || "操作失败");
    },
  });
}

/**
 * 管理员重置密码 mutation
 */
export function useAdminResetPassword() {
  return useMutation<
    AdminResetPasswordV1AdminUsersUserIdResetPasswordPostResponse,
    AdminResetPasswordV1AdminUsersUserIdResetPasswordPostError,
    AdminResetPasswordV1AdminUsersUserIdResetPasswordPostData
  >({
    mutationFn: async (data) => {
      const response = await adminResetPasswordV1AdminUsersUserIdResetPasswordPost({
        ...data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success("密码重置成功");
    },
    onError: (error) => {
      toast.error((error as Error)?.message || "重置密码失败");
    },
  });
}