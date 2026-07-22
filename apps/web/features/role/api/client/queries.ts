"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { toast } from "sonner";
import {
  adminReadRolesV1AdminRolesGet,
  adminCreateRoleV1AdminRolesPost,
  adminUpdateRoleV1AdminRolesRoleIdPut,
  adminDeleteRoleV1AdminRolesRoleIdDelete,
  type AdminReadRolesV1AdminRolesGetData,
  type AdminReadRolesV1AdminRolesGetResponse,
  type AdminReadRolesV1AdminRolesGetError,
  type AdminCreateRoleV1AdminRolesPostData,
  type AdminCreateRoleV1AdminRolesPostError,
  type AdminCreateRoleV1AdminRolesPostResponse,
  type AdminUpdateRoleV1AdminRolesRoleIdPutData,
  type AdminUpdateRoleV1AdminRolesRoleIdPutError,
  type AdminUpdateRoleV1AdminRolesRoleIdPutResponse,
  type AdminDeleteRoleV1AdminRolesRoleIdDeleteData,
  type AdminDeleteRoleV1AdminRolesRoleIdDeleteError,
  type AdminDeleteRoleV1AdminRolesRoleIdDeleteResponse,
} from "@repo/sdk";

export const roleKeys = {
  all: ["roles"] as const,
  lists: () => [...roleKeys.all, "list"] as const,
  list: (filters: AdminReadRolesV1AdminRolesGetData["query"]) =>
    [...roleKeys.lists(), filters] as const,
};

/**
 * 获取角色列表
 */
export function useAdminRoles(
  filters: AdminReadRolesV1AdminRolesGetData["query"] = { page: 1, page_size: 20 },
) {
  return useQuery<
    AdminReadRolesV1AdminRolesGetResponse,
    AdminReadRolesV1AdminRolesGetError
  >({
    queryKey: roleKeys.list(filters),
    queryFn: async () => {
      const response = await adminReadRolesV1AdminRolesGet({
        query: filters,
        throwOnError: true,
      });
      return response.data;
    },
  });
}

/**
 * 创建角色
 */
export function useAdminCreateRole() {
  const queryClient = useQueryClient();

  return useMutation<
    AdminCreateRoleV1AdminRolesPostResponse,
    AdminCreateRoleV1AdminRolesPostError,
    AdminCreateRoleV1AdminRolesPostData
  >({
    mutationFn: async (data) => {
      const response = await adminCreateRoleV1AdminRolesPost({
        ...data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.lists() });
      toast.success("角色创建成功");
    },
    onError: (error) => {
      toast.error((error as Error)?.message || "创建角色失败");
    },
  });
}

/**
 * 更新角色
 */
export function useAdminUpdateRole() {
  const queryClient = useQueryClient();

  return useMutation<
    AdminUpdateRoleV1AdminRolesRoleIdPutResponse,
    AdminUpdateRoleV1AdminRolesRoleIdPutError,
    AdminUpdateRoleV1AdminRolesRoleIdPutData
  >({
    mutationFn: async (data) => {
      const response = await adminUpdateRoleV1AdminRolesRoleIdPut({
        ...data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.lists() });
      toast.success("角色更新成功");
    },
    onError: (error) => {
      toast.error((error as Error)?.message || "更新角色失败");
    },
  });
}

/**
 * 删除角色
 */
export function useAdminDeleteRole() {
  const queryClient = useQueryClient();

  return useMutation<
    AdminDeleteRoleV1AdminRolesRoleIdDeleteResponse,
    AdminDeleteRoleV1AdminRolesRoleIdDeleteError,
    AdminDeleteRoleV1AdminRolesRoleIdDeleteData
  >({
    mutationFn: async (data) => {
      const response = await adminDeleteRoleV1AdminRolesRoleIdDelete({
        ...data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.lists() });
      toast.success("角色删除成功");
    },
    onError: (error) => {
      toast.error((error as Error)?.message || "删除角色失败");
    },
  });
}