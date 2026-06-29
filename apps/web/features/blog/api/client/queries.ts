"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";
import { toast } from "sonner";
import {
  // Post SDK functions
  listPostsV1BlogPostsGet,
  getPostDetailV1BlogPostsSlugGet,
  getArchivesV1BlogPostsArchivesGet,
  adminListPostsV1BlogPostsAdminListGet,
  createPostV1BlogPostsPost,
  updatePostV1BlogPostsPostIdPatch,
  deletePostV1BlogPostsPostIdDelete,
  // Category SDK functions
  listCategoriesV1BlogCategoriesGet,
  listCategoryPostsV1BlogCategoriesSlugPostsGet,
  createCategoryV1BlogCategoriesPost,
  updateCategoryV1BlogCategoriesCategoryIdPatch,
  deleteCategoryV1BlogCategoriesCategoryIdDelete,
  // Comment SDK functions
  listCommentsV1BlogPostsSlugCommentsGet,
  createCommentV1BlogPostsSlugCommentsPost,
  getRecentCommentsV1BlogCommentsRecentGet,
  deleteCommentV1BlogCommentsCommentIdDelete,
  // Types
  type ListPostsV1BlogPostsGetData,
  type ListPostsV1BlogPostsGetResponse,
  type ListPostsV1BlogPostsGetError,
  type GetPostDetailV1BlogPostsSlugGetData,
  type GetPostDetailV1BlogPostsSlugGetResponse,
  type GetPostDetailV1BlogPostsSlugGetError,
  type GetArchivesV1BlogPostsArchivesGetResponse,
  type AdminListPostsV1BlogPostsAdminListGetData,
  type AdminListPostsV1BlogPostsAdminListGetResponse,
  type AdminListPostsV1BlogPostsAdminListGetError,
  type CreatePostV1BlogPostsPostResponse,
  type CreatePostV1BlogPostsPostError,
  type UpdatePostV1BlogPostsPostIdPatchResponse,
  type UpdatePostV1BlogPostsPostIdPatchError,
  type DeletePostV1BlogPostsPostIdDeleteResponse,
  type DeletePostV1BlogPostsPostIdDeleteError,
  type ListCategoriesV1BlogCategoriesGetData,
  type ListCategoriesV1BlogCategoriesGetResponse,
  type ListCategoriesV1BlogCategoriesGetError,
  type ListCategoryPostsV1BlogCategoriesSlugPostsGetData,
  type ListCategoryPostsV1BlogCategoriesSlugPostsGetResponse,
  type ListCategoryPostsV1BlogCategoriesSlugPostsGetError,
  type CreateCategoryV1BlogCategoriesPostResponse,
  type CreateCategoryV1BlogCategoriesPostError,
  type UpdateCategoryV1BlogCategoriesCategoryIdPatchResponse,
  type UpdateCategoryV1BlogCategoriesCategoryIdPatchError,
  type DeleteCategoryV1BlogCategoriesCategoryIdDeleteResponse,
  type ListCommentsV1BlogPostsSlugCommentsGetData,
  type ListCommentsV1BlogPostsSlugCommentsGetResponse,
  type ListCommentsV1BlogPostsSlugCommentsGetError,
  type CreateCommentV1BlogPostsSlugCommentsPostResponse,
  type CreateCommentV1BlogPostsSlugCommentsPostError,
  type GetRecentCommentsV1BlogCommentsRecentGetData,
  type GetRecentCommentsV1BlogCommentsRecentGetResponse,
  type DeleteCommentV1BlogCommentsCommentIdDeleteResponse,
  type PostCreate,
  type PostUpdate,
  type CategoryCreate,
  type CategoryUpdate,
  type CommentCreate,
} from "@repo/sdk";

// ========================= Query Keys =========================

export const blogKeys = {
  all: ["blog"] as const,

  // Posts
  posts: {
    all: ["blog", "posts"] as const,
    lists: () => [...blogKeys.posts.all, "list"] as const,
    list: (query: ListPostsV1BlogPostsGetData["query"]) =>
      [...blogKeys.posts.lists(), query] as const,
    details: () => [...blogKeys.posts.all, "detail"] as const,
    detail: (slug: string) => [...blogKeys.posts.details(), slug] as const,
    admin: {
      all: ["blog", "posts", "admin"] as const,
      list: (query: AdminListPostsV1BlogPostsAdminListGetData["query"]) =>
        [...blogKeys.posts.admin.all, "list", query] as const,
    },
    archives: () => [...blogKeys.posts.all, "archives"] as const,
  },

  // Categories
  categories: {
    all: ["blog", "categories"] as const,
    lists: () => [...blogKeys.categories.all, "list"] as const,
    list: (query?: ListCategoriesV1BlogCategoriesGetData["query"]) =>
      [...blogKeys.categories.lists(), query ?? {}] as const,
    posts: (slug: string, query?: ListCategoryPostsV1BlogCategoriesSlugPostsGetData["query"]) =>
      [...blogKeys.categories.all, "posts", slug, query ?? {}] as const,
  },

  // Comments
  comments: {
    all: ["blog", "comments"] as const,
    byPost: (slug: string, query?: ListCommentsV1BlogPostsSlugCommentsGetData["query"]) =>
      [...blogKeys.comments.all, "post", slug, query ?? {}] as const,
    recent: (query?: GetRecentCommentsV1BlogCommentsRecentGetData["query"]) =>
      [...blogKeys.comments.all, "recent", query ?? {}] as const,
  },
};

// ========================= Post Queries =========================

/**
 * 公开文章列表（分页 + 搜索 + 分类筛选）
 */
export function usePosts(
  query: ListPostsV1BlogPostsGetData["query"] = { pagination: { page: 1, page_size: 10 } },
  options?: Omit<
    UseQueryOptions<ListPostsV1BlogPostsGetResponse, ListPostsV1BlogPostsGetError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: blogKeys.posts.list(query),
    queryFn: async () => {
      const { data } = await listPostsV1BlogPostsGet({ query, throwOnError: true });
      return data;
    },
    ...options,
  });
}

/**
 * 文章详情（通过 slug）
 */
export function usePostDetail(
  slug: string,
  options?: Omit<
    UseQueryOptions<GetPostDetailV1BlogPostsSlugGetResponse, GetPostDetailV1BlogPostsSlugGetError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: blogKeys.posts.detail(slug),
    queryFn: async () => {
      const { data } = await getPostDetailV1BlogPostsSlugGet({
        path: { slug },
        throwOnError: true,
      });
      return data;
    },
    enabled: !!slug,
    ...options,
  });
}

/**
 * 归档列表
 */
export function useArchives(
  options?: Omit<
    UseQueryOptions<GetArchivesV1BlogPostsArchivesGetResponse, Error>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: blogKeys.posts.archives(),
    queryFn: async () => {
      const { data } = await getArchivesV1BlogPostsArchivesGet({ throwOnError: true });
      return data;
    },
    ...options,
  });
}

/**
 * 后台文章列表（含未发布）
 */
export function useAdminPosts(
  query: AdminListPostsV1BlogPostsAdminListGetData["query"] = {
    pagination: { page: 1, page_size: 20 },
  },
  options?: Omit<
    UseQueryOptions<AdminListPostsV1BlogPostsAdminListGetResponse, AdminListPostsV1BlogPostsAdminListGetError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: blogKeys.posts.admin.list(query),
    queryFn: async () => {
      const { data } = await adminListPostsV1BlogPostsAdminListGet({
        query,
        throwOnError: true,
      });
      return data;
    },
    ...options,
  });
}

// ========================= Post Mutations =========================

/**
 * 创建文章
 */
export function useCreatePost() {
  const queryClient = useQueryClient();

  return useMutation<CreatePostV1BlogPostsPostResponse, Error, PostCreate>({
    mutationFn: async (data) => {
      const { data: result } = await createPostV1BlogPostsPost({
        body: data,
        throwOnError: true,
      });
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: blogKeys.posts.lists() });
      queryClient.invalidateQueries({ queryKey: blogKeys.posts.admin.all });
      toast.success("文章发布成功");
    },
    onError: (error) => {
      toast.error(error.message || "发布失败");
    },
  });
}

/**
 * 更新文章
 */
export function useUpdatePost() {
  const queryClient = useQueryClient();

  return useMutation<
    UpdatePostV1BlogPostsPostIdPatchResponse,
    Error,
    { postId: string; data: PostUpdate }
  >({
    mutationFn: async ({ postId, data }) => {
      const { data: result } = await updatePostV1BlogPostsPostIdPatch({
        path: { post_id: postId },
        body: data,
        throwOnError: true,
      });
      return result;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: blogKeys.posts.detail(variables.postId) });
      queryClient.invalidateQueries({ queryKey: blogKeys.posts.lists() });
      queryClient.invalidateQueries({ queryKey: blogKeys.posts.admin.all });
      toast.success("文章更新成功");
    },
    onError: (error) => {
      toast.error(error.message || "更新失败");
    },
  });
}

/**
 * 删除文章
 */
export function useDeletePost() {
  const queryClient = useQueryClient();

  return useMutation<DeletePostV1BlogPostsPostIdDeleteResponse, Error, string>({
    mutationFn: async (postId) => {
      const { data } = await deletePostV1BlogPostsPostIdDelete({
        path: { post_id: postId },
        throwOnError: true,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: blogKeys.posts.lists() });
      queryClient.invalidateQueries({ queryKey: blogKeys.posts.admin.all });
      toast.success("文章已删除");
    },
    onError: (error) => {
      toast.error(error.message || "删除失败");
    },
  });
}

// ========================= Category Queries =========================

/**
 * 全量分类列表（含文章计数）
 */
export function useCategories(
  query?: ListCategoriesV1BlogCategoriesGetData["query"],
  options?: Omit<
    UseQueryOptions<ListCategoriesV1BlogCategoriesGetResponse, ListCategoriesV1BlogCategoriesGetError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: blogKeys.categories.list(query),
    queryFn: async () => {
      const { data } = await listCategoriesV1BlogCategoriesGet({
        query: query ?? { page: 1, page_size: 100 },
        throwOnError: true,
      });
      return data;
    },
    ...options,
  });
}

/**
 * 分类下文章列表
 */
export function useCategoryPosts(
  slug: string,
  query?: ListCategoryPostsV1BlogCategoriesSlugPostsGetData["query"],
  options?: Omit<
    UseQueryOptions<ListCategoryPostsV1BlogCategoriesSlugPostsGetResponse, ListCategoryPostsV1BlogCategoriesSlugPostsGetError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: blogKeys.categories.posts(slug, query),
    queryFn: async () => {
      const { data } = await listCategoryPostsV1BlogCategoriesSlugPostsGet({
        path: { slug },
        query: query ?? { page: 1, page_size: 20 },
        throwOnError: true,
      });
      return data;
    },
    enabled: !!slug,
    ...options,
  });
}

// ========================= Category Mutations =========================

/**
 * 创建分类
 */
export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation<CreateCategoryV1BlogCategoriesPostResponse, Error, CategoryCreate>({
    mutationFn: async (data) => {
      const { data: result } = await createCategoryV1BlogCategoriesPost({
        body: data,
        throwOnError: true,
      });
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: blogKeys.categories.lists() });
      toast.success("分类创建成功");
    },
    onError: (error) => {
      toast.error(error.message || "创建分类失败");
    },
  });
}

/**
 * 更新分类
 */
export function useUpdateCategory() {
  const queryClient = useQueryClient();

  return useMutation<
    UpdateCategoryV1BlogCategoriesCategoryIdPatchResponse,
    Error,
    { categoryId: string; data: CategoryUpdate }
  >({
    mutationFn: async ({ categoryId, data }) => {
      const { data: result } = await updateCategoryV1BlogCategoriesCategoryIdPatch({
        path: { category_id: categoryId },
        body: data,
        throwOnError: true,
      });
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: blogKeys.categories.lists() });
      toast.success("分类更新成功");
    },
    onError: (error) => {
      toast.error(error.message || "更新分类失败");
    },
  });
}

/**
 * 删除分类
 */
export function useDeleteCategory() {
  const queryClient = useQueryClient();

  return useMutation<DeleteCategoryV1BlogCategoriesCategoryIdDeleteResponse, Error, string>({
    mutationFn: async (categoryId) => {
      const { data } = await deleteCategoryV1BlogCategoriesCategoryIdDelete({
        path: { category_id: categoryId },
        throwOnError: true,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: blogKeys.categories.lists() });
      toast.success("分类已删除");
    },
    onError: (error) => {
      toast.error(error.message || "删除分类失败");
    },
  });
}

// ========================= Comment Queries =========================

/**
 * 文章评论列表
 */
export function useComments(
  slug: string,
  query?: ListCommentsV1BlogPostsSlugCommentsGetData["query"],
  options?: Omit<
    UseQueryOptions<ListCommentsV1BlogPostsSlugCommentsGetResponse, ListCommentsV1BlogPostsSlugCommentsGetError>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: blogKeys.comments.byPost(slug, query),
    queryFn: async () => {
      const { data } = await listCommentsV1BlogPostsSlugCommentsGet({
        path: { slug },
        query: query ?? { page: 1, page_size: 20 },
        throwOnError: true,
      });
      return data;
    },
    enabled: !!slug,
    ...options,
  });
}

/**
 * 最近评论（侧栏用）
 */
export function useRecentComments(
  query?: GetRecentCommentsV1BlogCommentsRecentGetData["query"],
  options?: Omit<
    UseQueryOptions<GetRecentCommentsV1BlogCommentsRecentGetResponse, Error>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: blogKeys.comments.recent(query),
    queryFn: async () => {
      const { data } = await getRecentCommentsV1BlogCommentsRecentGet({
        query: query ?? { limit: 8 },
        throwOnError: true,
      });
      return data;
    },
    ...options,
  });
}

// ========================= Comment Mutations =========================

/**
 * 提交评论
 */
export function useCreateComment() {
  const queryClient = useQueryClient();

  return useMutation<
    CreateCommentV1BlogPostsSlugCommentsPostResponse,
    Error,
    { slug: string; data: CommentCreate }
  >({
    mutationFn: async ({ slug, data }) => {
      const { data: result } = await createCommentV1BlogPostsSlugCommentsPost({
        path: { slug },
        body: data,
        throwOnError: true,
      });
      return result;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: blogKeys.comments.byPost(variables.slug) });
      queryClient.invalidateQueries({ queryKey: blogKeys.comments.recent() });
      toast.success("评论提交成功");
    },
    onError: (error) => {
      toast.error(error.message || "评论失败");
    },
  });
}

/**
 * 删除评论
 */
export function useDeleteComment() {
  const queryClient = useQueryClient();

  return useMutation<DeleteCommentV1BlogCommentsCommentIdDeleteResponse, Error, string>({
    mutationFn: async (commentId) => {
      const { data } = await deleteCommentV1BlogCommentsCommentIdDelete({
        path: { comment_id: commentId },
        throwOnError: true,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: blogKeys.comments.all });
      toast.success("评论已删除");
    },
    onError: (error) => {
      toast.error(error.message || "删除评论失败");
    },
  });
}