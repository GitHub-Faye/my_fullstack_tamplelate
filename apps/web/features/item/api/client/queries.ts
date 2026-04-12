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
  readItemsV1ItemsGet,
  readItemV1ItemsIdGet,
  createItemV1ItemsPost,
  updateItemV1ItemsIdPut,
  deleteItemV1ItemsIdDelete,
  // Types
  type ReadItemsV1ItemsGetData,
  type ReadItemsV1ItemsGetResponse,
  type ReadItemsV1ItemsGetError,
  type ReadItemV1ItemsIdGetData,
  type ReadItemV1ItemsIdGetResponse,
  type ReadItemV1ItemsIdGetError,
  type CreateItemV1ItemsPostResponse,
  type CreateItemV1ItemsPostError,
  type UpdateItemV1ItemsIdPutResponse,
  type UpdateItemV1ItemsIdPutError,
  type DeleteItemV1ItemsIdDeleteResponse,
  type DeleteItemV1ItemsIdDeleteError,
  type ItemCreate,
  type ItemUpdate,
} from "@repo/sdk";

// Query Keys
export const itemKeys = {
  all: ["items"] as const,
  lists: () => [...itemKeys.all, "list"] as const,
  list: (filters: ReadItemsV1ItemsGetData["query"]) =>
    [...itemKeys.lists(), filters] as const,
  details: () => [...itemKeys.all, "detail"] as const,
  detail: (id: string) => [...itemKeys.details(), id] as const,
};

// ==================== Queries ====================

/**
 * Get items list query
 */
export function useItems(
  filters: ReadItemsV1ItemsGetData["query"] = { page: 1, page_size: 10 },
  options?: Omit<
    UseQueryOptions<
      ReadItemsV1ItemsGetResponse,
      ReadItemsV1ItemsGetError,
      ReadItemsV1ItemsGetResponse
    >,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: itemKeys.list(filters),
    queryFn: async () => {
      const response = await readItemsV1ItemsGet({
        query: filters,
        throwOnError: true,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * Get item by ID query
 */
export function useItem(
  itemId: string,
  options?: Omit<
    UseQueryOptions<
      ReadItemV1ItemsIdGetResponse,
      ReadItemV1ItemsIdGetError,
      ReadItemV1ItemsIdGetResponse
    >,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: itemKeys.detail(itemId),
    queryFn: async () => {
      const response = await readItemV1ItemsIdGet({
        path: { id: itemId },
        throwOnError: true,
      });
      return response.data;
    },
    enabled: !!itemId,
    ...options,
  });
}

// ==================== Mutations ====================

/**
 * Create item mutation
 */
export function useCreateItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ItemCreate) => {
      const response = await createItemV1ItemsPost({
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: itemKeys.lists() });
      toast.success("物品创建成功");
    },
    onError: (error: Error) => {
      toast.error(error.message || "创建物品失败");
    },
  });
}

/**
 * Update item mutation
 */
export function useUpdateItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      itemId,
      data,
    }: {
      itemId: string;
      data: ItemUpdate;
    }) => {
      const response = await updateItemV1ItemsIdPut({
        path: { id: itemId },
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: itemKeys.detail(variables.itemId),
      });
      queryClient.invalidateQueries({ queryKey: itemKeys.lists() });
      toast.success("物品更新成功");
    },
    onError: (error: Error) => {
      toast.error(error.message || "更新物品失败");
    },
  });
}

/**
 * Delete item mutation
 */
export function useDeleteItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (itemId: string) => {
      const response = await deleteItemV1ItemsIdDelete({
        path: { id: itemId },
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: itemKeys.lists() });
      toast.success("物品已删除");
    },
    onError: (error: Error) => {
      toast.error(error.message || "删除物品失败");
    },
  });
}
