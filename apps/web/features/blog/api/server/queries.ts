"use server";

import {
  listPostsV1BlogPostsGet,
  getPostDetailV1BlogPostsSlugGet,
  getArchivesV1BlogPostsArchivesGet,
  adminListPostsV1BlogPostsAdminListGet,
  listCategoriesV1BlogCategoriesGet,
  listCategoryPostsV1BlogCategoriesSlugPostsGet,
  listCommentsV1BlogPostsSlugCommentsGet,
  getRecentCommentsV1BlogCommentsRecentGet,
  type ListPostsV1BlogPostsGetData,
  type ListPostsV1BlogPostsGetResponse,
  type GetPostDetailV1BlogPostsSlugGetResponse,
  type GetArchivesV1BlogPostsArchivesGetResponse,
  type AdminListPostsV1BlogPostsAdminListGetData,
  type AdminListPostsV1BlogPostsAdminListGetResponse,
  type ListCategoriesV1BlogCategoriesGetData,
  type ListCategoriesV1BlogCategoriesGetResponse,
  type ListCategoryPostsV1BlogCategoriesSlugPostsGetData,
  type ListCategoryPostsV1BlogCategoriesSlugPostsGetResponse,
  type ListCommentsV1BlogPostsSlugCommentsGetData,
  type ListCommentsV1BlogPostsSlugCommentsGetResponse,
  type GetRecentCommentsV1BlogCommentsRecentGetData,
  type GetRecentCommentsV1BlogCommentsRecentGetResponse,
} from "@repo/sdk";

// ==================== Server-Side Data Fetching ====================

/**
 * 获取公开文章列表
 */
export async function getPosts(
  query: ListPostsV1BlogPostsGetData["query"] = { pagination: { page: 1, page_size: 10 } }
): Promise<ListPostsV1BlogPostsGetResponse> {
  const response = await listPostsV1BlogPostsGet({ query, throwOnError: true });
  return response.data;
}

/**
 * 获取文章详情
 */
export async function getPostDetail(
  slug: string
): Promise<GetPostDetailV1BlogPostsSlugGetResponse | null> {
  try {
    const response = await getPostDetailV1BlogPostsSlugGet({
      path: { slug },
      throwOnError: true,
    });
    return response.data;
  } catch {
    return null;
  }
}

/**
 * 获取归档
 */
export async function getArchives(): Promise<GetArchivesV1BlogPostsArchivesGetResponse> {
  const response = await getArchivesV1BlogPostsArchivesGet({ throwOnError: true });
  return response.data;
}

/**
 * 获取后台文章列表
 */
export async function getAdminPosts(
  query: AdminListPostsV1BlogPostsAdminListGetData["query"] = { pagination: { page: 1, page_size: 20 } }
): Promise<AdminListPostsV1BlogPostsAdminListGetResponse> {
  const response = await adminListPostsV1BlogPostsAdminListGet({ query, throwOnError: true });
  return response.data;
}

/**
 * 获取全量分类
 */
export async function getCategories(
  query?: ListCategoriesV1BlogCategoriesGetData["query"]
): Promise<ListCategoriesV1BlogCategoriesGetResponse> {
  const response = await listCategoriesV1BlogCategoriesGet({
    query: query ?? { page: 1, page_size: 100 },
    throwOnError: true,
  });
  return response.data;
}

/**
 * 获取分类下文章
 */
export async function getCategoryPosts(
  slug: string,
  query?: ListCategoryPostsV1BlogCategoriesSlugPostsGetData["query"]
): Promise<ListCategoryPostsV1BlogCategoriesSlugPostsGetResponse> {
  const response = await listCategoryPostsV1BlogCategoriesSlugPostsGet({
    path: { slug },
    query: query ?? { page: 1, page_size: 20 },
    throwOnError: true,
  });
  return response.data;
}

/**
 * 获取文章评论
 */
export async function getComments(
  slug: string,
  query?: ListCommentsV1BlogPostsSlugCommentsGetData["query"]
): Promise<ListCommentsV1BlogPostsSlugCommentsGetResponse> {
  const response = await listCommentsV1BlogPostsSlugCommentsGet({
    path: { slug },
    query: query ?? { page: 1, page_size: 50 },
    throwOnError: true,
  });
  return response.data;
}

/**
 * 获取最近评论
 */
export async function getRecentComments(
  query?: GetRecentCommentsV1BlogCommentsRecentGetData["query"]
): Promise<GetRecentCommentsV1BlogCommentsRecentGetResponse> {
  const response = await getRecentCommentsV1BlogCommentsRecentGet({
    query: query ?? { limit: 8 },
    throwOnError: true,
  });
  return response.data;
}