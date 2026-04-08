'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  readUsersV1UsersGet,
  readUserByIdV1UsersUserIdGet,
  readUserMeV1UsersMeGet,
  createUserV1UsersPost,
  updateUserV1UsersUserIdPatch,
  updateUserMeV1UsersMePatch,
  updatePasswordMeV1UsersMePasswordPatch,
  deleteUserV1UsersUserIdDelete,
  deleteUserMeV1UsersMeDelete,
  registerUserV1UsersSignupPost,
  type UserCreate,
  type UserUpdate,
  type UserUpdateMe,
  type UpdatePassword,
  type UserRegister,
} from '@/src/lib/api-sdk';

// Query keys
export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (skip: number, limit: number) => [...userKeys.lists(), { skip, limit }] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
  me: () => [...userKeys.all, 'me'] as const,
};

// Get all users (admin only)
export function useUsers(skip: number = 0, limit: number = 100) {
  return useQuery({
    queryKey: userKeys.list(skip, limit),
    queryFn: async () => {
      const response = await readUsersV1UsersGet({
        query: { skip, limit },
      });
      if (response.error) {
        throw new Error('获取用户列表失败');
      }
      return response.data;
    },
  });
}

// Get user by ID
export function useUser(userId: string) {
  return useQuery({
    queryKey: userKeys.detail(userId),
    queryFn: async () => {
      const response = await readUserByIdV1UsersUserIdGet({
        path: { user_id: userId },
      });
      if (response.error) {
        throw new Error('获取用户信息失败');
      }
      return response.data;
    },
    enabled: !!userId,
  });
}

// Get current user
export function useCurrentUser() {
  return useQuery({
    queryKey: userKeys.me(),
    queryFn: async () => {
      const response = await readUserMeV1UsersMeGet();
      if (response.error) {
        throw new Error('获取当前用户信息失败');
      }
      return response.data;
    },
  });
}

// Create user (admin only)
export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UserCreate) => {
      const response = await createUserV1UsersPost({
        body: data,
      });
      if (response.error) {
        throw new Error('创建用户失败');
      }
      return response.data;
    },
    onSuccess: () => {
      toast.success('用户创建成功');
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Update user (admin only)
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ userId, data }: { userId: string; data: UserUpdate }) => {
      const response = await updateUserV1UsersUserIdPatch({
        path: { user_id: userId },
        body: data,
      });
      if (response.error) {
        throw new Error('更新用户失败');
      }
      return response.data;
    },
    onSuccess: (_, variables) => {
      toast.success('用户更新成功');
      queryClient.invalidateQueries({ queryKey: userKeys.detail(variables.userId) });
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Update current user
export function useUpdateUserMe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UserUpdateMe) => {
      const response = await updateUserMeV1UsersMePatch({
        body: data,
      });
      if (response.error) {
        throw new Error('更新个人信息失败');
      }
      return response.data;
    },
    onSuccess: () => {
      toast.success('个人信息更新成功');
      queryClient.invalidateQueries({ queryKey: userKeys.me() });
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Update password
export function useUpdatePassword() {
  return useMutation({
    mutationFn: async (data: UpdatePassword) => {
      const response = await updatePasswordMeV1UsersMePasswordPatch({
        body: data,
      });
      if (response.error) {
        throw new Error('修改密码失败');
      }
      return response.data;
    },
    onSuccess: () => {
      toast.success('密码修改成功');
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Delete user (admin only)
export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userId: string) => {
      const response = await deleteUserV1UsersUserIdDelete({
        path: { user_id: userId },
      });
      if (response.error) {
        throw new Error('删除用户失败');
      }
      return response.data;
    },
    onSuccess: () => {
      toast.success('用户删除成功');
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Delete current user
export function useDeleteUserMe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await deleteUserMeV1UsersMeDelete();
      if (response.error) {
        throw new Error('删除账户失败');
      }
      return response.data;
    },
    onSuccess: () => {
      toast.success('账户已删除');
      queryClient.clear();
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}

// Register user
export function useRegisterUser() {
  return useMutation({
    mutationFn: async (data: UserRegister) => {
      const response = await registerUserV1UsersSignupPost({
        body: data,
      });
      if (response.error) {
        throw new Error('注册失败');
      }
      return response.data;
    },
    onSuccess: () => {
      toast.success('注册成功，请登录');
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });
}
