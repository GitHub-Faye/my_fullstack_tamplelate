'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  readItemsV1ItemsGet,
  readItemV1ItemsIdGet,
  createItemV1ItemsPost,
  updateItemV1ItemsIdPut,
  deleteItemV1ItemsIdDelete,
  type ItemCreate,
  type ItemUpdate,
} from '@/src/lib/api-sdk';

// Query keys
export const itemKeys = {
  all: ['items'] as const,
  lists: () => [...itemKeys.all, 'list'] as const,
  list: (skip: number, limit: number) => [...itemKeys.lists(), { skip, limit }] as const,
  details: () => [...itemKeys.all, 'detail'] as const,
  detail: (id: string) => [...itemKeys.details(), id] as const,
};

// Get all items
export function useItems(skip: number = 0, limit: number = 100) {
  return useQuery({
    queryKey: itemKeys.list(skip, limit),
    queryFn: async () => {
      const response = await readItemsV1ItemsGet({
        query: { skip, limit },
      });
      if (response.error) {
        throw new Error('获取物品列表失败');
      }
      return response.data;
    },
  });
}

// Get item by ID
export function useItem(itemId: string) {
  return useQuery({
    queryKey: itemKeys.detail(itemId),
    queryFn: async () => {
      const response = await readItemV1ItemsIdGet({
        path: { id: itemId },
      });
      if (response.error) {
        throw new Error('获取物品信息失败');
      }
      return response.data;
    },
    enabled: !!itemId,
  });
}

// Create item
export function useCreateItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ItemCreate) => {
      const response = await createItemV1ItemsPost({
        body: data,
      });
      if (response.error) {
        throw new Error('创建物品失败');
      }
      return response.data;
    },
    onSuccess: () => {
      toast.success('物品创建成功');
      queryClient.invalidateQueries({ queryKey: itemKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Update item
export function useUpdateItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ itemId, data }: { itemId: string; data: ItemUpdate }) => {
      const response = await updateItemV1ItemsIdPut({
        path: { id: itemId },
        body: data,
      });
      if (response.error) {
        throw new Error('更新物品失败');
      }
      return response.data;
    },
    onSuccess: (_, variables) => {
      toast.success('物品更新成功');
      queryClient.invalidateQueries({ queryKey: itemKeys.detail(variables.itemId) });
      queryClient.invalidateQueries({ queryKey: itemKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Delete item
export function useDeleteItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (itemId: string) => {
      const response = await deleteItemV1ItemsIdDelete({
        path: { id: itemId },
      });
      if (response.error) {
        throw new Error('删除物品失败');
      }
      return response.data;
    },
    onSuccess: () => {
      toast.success('物品删除成功');
      queryClient.invalidateQueries({ queryKey: itemKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}
