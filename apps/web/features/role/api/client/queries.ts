"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { toast } from "sonner";
import {
  // SDK functions
  readRolesV1RolesGet,
  readRoleV1RolesRoleIdGet,
  createRoleV1RolesPost,
  updateRoleV1RolesRoleIdPatch,
  deleteRoleV1RolesRoleIdDelete,
  // Types
  type ReadRolesV1RolesGetData,
  type ReadRolesV1RolesGetResponse,
  type ReadRolesV1RolesGetError,
  type ReadRoleV1RolesRoleIdGetResponse,
  type ReadRoleV1RolesRoleIdGetError,
  type RoleCreate,
  type RoleUpdate,
} from "@repo/sdk";

// Query Keys
export const roleKeys = {
  all: ["roles"] as const,
  lists: () => [...roleKeys.all, "list"] as const,
  list: (filters: ReadRolesV1RolesGetData["query"]) =>
    [...roleKeys.lists(), filters] as const,
  details: () => [...roleKeys.all, "detail"] as const,
  detail: (id: string) => [...roleKeys.details(), id] as const,
};

// ==================== Queries ====================

/**
 * Get roles list query
 */
export function useRoles(
  filters: ReadRolesV1RolesGetData["query"] = { page: 1, page_size: 10 },
  options?: Omit<
    UseQueryOptions<
      ReadRolesV1RolesGetResponse,
      ReadRolesV1RolesGetError,
      ReadRolesV1RolesGetResponse
    >,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: roleKeys.list(filters),
    queryFn: async () => {
      const response = await readRolesV1RolesGet({
        query: filters,
        throwOnError: true,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * Get role by ID query
 */
export function useRole(
  roleId: string,
  options?: Omit<
    UseQueryOptions<
      ReadRoleV1RolesRoleIdGetResponse,
      ReadRoleV1RolesRoleIdGetError,
      ReadRoleV1RolesRoleIdGetResponse
    >,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: roleKeys.detail(roleId),
    queryFn: async () => {
      const response = await readRoleV1RolesRoleIdGet({
        path: { role_id: roleId },
        throwOnError: true,
      });
      return response.data;
    },
    enabled: !!roleId,
    ...options,
  });
}

// ==================== Mutations ====================

/**
 * Create role mutation
 */
export function useCreateRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: RoleCreate) => {
      const response = await createRoleV1RolesPost({
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.lists() });
      toast.success("角色创建成功");
    },
    onError: (error: Error) => {
      toast.error(error.message || "创建角色失败");
    },
  });
}

/**
 * Update role mutation
 */
export function useUpdateRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      roleId,
      data,
    }: {
      roleId: string;
      data: RoleUpdate;
    }) => {
      const response = await updateRoleV1RolesRoleIdPatch({
        path: { role_id: roleId },
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: roleKeys.detail(variables.roleId),
      });
      queryClient.invalidateQueries({ queryKey: roleKeys.lists() });
      toast.success("角色更新成功");
    },
    onError: (error: Error) => {
      toast.error(error.message || "更新角色失败");
    },
  });
}

/**
 * Delete role mutation
 */
export function useDeleteRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (roleId: string) => {
      const response = await deleteRoleV1RolesRoleIdDelete({
        path: { role_id: roleId },
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: roleKeys.lists() });
      toast.success("角色已删除");
    },
    onError: (error: Error) => {
      toast.error(error.message || "删除角色失败");
    },
  });
}
