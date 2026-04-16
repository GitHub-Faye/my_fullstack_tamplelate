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
  readUsersV1UsersGet,
  readUserMeV1UsersMeGet,
  readUserByIdV1UsersUserIdGet,
  loginAccessTokenV1LoginAccessTokenPost,
  registerUserV1UsersSignupPost,
  createUserV1UsersPost,
  updateUserMeV1UsersMePatch,
  updatePasswordMeV1UsersMePasswordPatch,
  updateUserV1UsersUserIdPatch,
  deleteUserMeV1UsersMeDelete,
  deleteUserV1UsersUserIdDelete,
  // Types
  type ReadUsersV1UsersGetData,
  type ReadUsersV1UsersGetResponse,
  type ReadUsersV1UsersGetError,
  type ReadUserMeV1UsersMeGetResponse,
  type ReadUserByIdV1UsersUserIdGetData,
  type ReadUserByIdV1UsersUserIdGetResponse,
  type ReadUserByIdV1UsersUserIdGetError,
  type LoginAccessTokenV1LoginAccessTokenPostResponse,
  type LoginAccessTokenV1LoginAccessTokenPostError,
  type RegisterUserV1UsersSignupPostResponse,
  type RegisterUserV1UsersSignupPostError,
  type CreateUserV1UsersPostResponse,
  type CreateUserV1UsersPostError,
  type UpdateUserMeV1UsersMePatchResponse,
  type UpdateUserMeV1UsersMePatchError,
  type UpdatePasswordMeV1UsersMePasswordPatchResponse,
  type UpdatePasswordMeV1UsersMePasswordPatchError,
  type UpdateUserV1UsersUserIdPatchResponse,
  type UpdateUserV1UsersUserIdPatchError,
  type DeleteUserMeV1UsersMeDeleteResponse,
  type DeleteUserV1UsersUserIdDeleteResponse,
  type DeleteUserV1UsersUserIdDeleteError,
  type BodyLoginAccessTokenV1LoginAccessTokenPost,
  type UserRegister,
  type UserCreate,
  type UserUpdateMe,
  type UpdatePassword,
  type UserUpdate,
} from "@repo/sdk";
import { useAuthStore } from "../../stores/auth";

// Query Keys
export const userKeys = {
  all: ["users"] as const,
  lists: () => [...userKeys.all, "list"] as const,
  list: (filters: ReadUsersV1UsersGetData["query"]) =>
    [...userKeys.lists(), filters] as const,
  details: () => [...userKeys.all, "detail"] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
  me: () => [...userKeys.all, "me"] as const,
};

// ==================== Queries ====================

/**
 * Get current user query
 */
export function useCurrentUser(
  options?: Omit<
    UseQueryOptions<
      ReadUserMeV1UsersMeGetResponse,
      Error,
      ReadUserMeV1UsersMeGetResponse
    >,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: userKeys.me(),
    queryFn: async () => {
      const response = await readUserMeV1UsersMeGet({ throwOnError: true });
      return response.data;
    },
    ...options,
  });
}

/**
 * Get users list query (admin only)
 */
export function useUsers(
  filters: ReadUsersV1UsersGetData["query"] = { page: 1, page_size: 10 },
  options?: Omit<
    UseQueryOptions<
      ReadUsersV1UsersGetResponse,
      ReadUsersV1UsersGetError,
      ReadUsersV1UsersGetResponse
    >,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: userKeys.list(filters),
    queryFn: async () => {
      const response = await readUsersV1UsersGet({
        query: filters,
        throwOnError: true,
      });
      return response.data;
    },
    ...options,
  });
}

/**
 * Get user by ID query
 */
export function useUser(
  userId: string,
  options?: Omit<
    UseQueryOptions<
      ReadUserByIdV1UsersUserIdGetResponse,
      ReadUserByIdV1UsersUserIdGetError,
      ReadUserByIdV1UsersUserIdGetResponse
    >,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: userKeys.detail(userId),
    queryFn: async () => {
      const response = await readUserByIdV1UsersUserIdGet({
        path: { user_id: userId },
        throwOnError: true,
      });
      return response.data;
    },
    enabled: !!userId,
    ...options,
  });
}

// ==================== Mutations ====================

/**
 * Login mutation
 */
export function useLogin() {
  const queryClient = useQueryClient();
  const { setAuth } = useAuthStore();

  return useMutation({
    mutationFn: async (data: BodyLoginAccessTokenV1LoginAccessTokenPost) => {
      const response = await loginAccessTokenV1LoginAccessTokenPost({
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: async (data) => {
      // Store token and get user info
      if (data.access_token) {
        // Set token first
        useAuthStore.getState().setToken(data.access_token);

        // Then fetch user info
        try {
          const userResponse = await readUserMeV1UsersMeGet({
            throwOnError: true,
          });
          setAuth(userResponse.data, data.access_token);
          toast.success("登录成功");
        } catch {
          toast.error("获取用户信息失败");
        }
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || "登录失败");
    },
  });
}

/**
 * Signup mutation
 */
export function useSignup() {
  return useMutation({
    mutationFn: async (data: UserRegister) => {
      const response = await registerUserV1UsersSignupPost({
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success("注册成功，请登录");
    },
    onError: (error: Error) => {
      toast.error(error.message || "注册失败");
    },
  });
}

/**
 * Create user mutation (admin only)
 */
export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UserCreate) => {
      const response = await createUserV1UsersPost({
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      toast.success("用户创建成功");
    },
    onError: (error: Error) => {
      toast.error(error.message || "创建用户失败");
    },
  });
}

/**
 * Update current user mutation
 */
export function useUpdateCurrentUser() {
  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();

  return useMutation({
    mutationFn: async (data: UserUpdateMe) => {
      const response = await updateUserMeV1UsersMePatch({
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: userKeys.me() });
      setUser(data);
      toast.success("个人信息更新成功");
    },
    onError: (error: Error) => {
      toast.error(error.message || "更新失败");
    },
  });
}

/**
 * Update password mutation
 */
export function useUpdatePassword() {
  return useMutation({
    mutationFn: async (data: UpdatePassword) => {
      const response = await updatePasswordMeV1UsersMePasswordPatch({
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success("密码修改成功");
    },
    onError: (error: Error) => {
      toast.error(error.message || "密码修改失败");
    },
  });
}

/**
 * Update user mutation (admin only)
 */
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      userId,
      data,
    }: {
      userId: string;
      data: UserUpdate;
    }) => {
      const response = await updateUserV1UsersUserIdPatch({
        path: { user_id: userId },
        body: data,
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: userKeys.detail(variables.userId),
      });
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      toast.success("用户更新成功");
    },
    onError: (error: Error) => {
      toast.error(error.message || "更新用户失败");
    },
  });
}

/**
 * Delete current user mutation
 */
export function useDeleteCurrentUser() {
  const queryClient = useQueryClient();
  const { logout } = useAuthStore();

  return useMutation({
    mutationFn: async () => {
      const response = await deleteUserMeV1UsersMeDelete({
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.clear();
      logout();
      toast.success("账户已删除");
    },
    onError: (error: Error) => {
      toast.error(error.message || "删除账户失败");
    },
  });
}

/**
 * Delete user mutation (admin only)
 */
export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userId: string) => {
      const response = await deleteUserV1UsersUserIdDelete({
        path: { user_id: userId },
        throwOnError: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      toast.success("用户已删除");
    },
    onError: (error: Error) => {
      toast.error(error.message || "删除用户失败");
    },
  });
}
