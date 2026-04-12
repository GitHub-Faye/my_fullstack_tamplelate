"use server";

import {
  readItemsV1ItemsGet,
  readItemV1ItemsIdGet,
  type ReadItemsV1ItemsGetData,
  type ReadItemsV1ItemsGetResponse,
  type ReadItemV1ItemsIdGetResponse,
} from "@repo/sdk";

// ==================== Server-Side Data Fetching ====================

/**
 * Get items list (server-side)
 * Use this in Server Components for initial data fetching
 */
export async function getItems(
  filters: ReadItemsV1ItemsGetData["query"] = { page: 1, page_size: 10 }
): Promise<ReadItemsV1ItemsGetResponse> {
  const response = await readItemsV1ItemsGet({
    query: filters,
    throwOnError: true,
  });
  return response.data;
}

/**
 * Get item by ID (server-side)
 * Use this in Server Components for initial data fetching
 */
export async function getItemById(
  itemId: string
): Promise<ReadItemV1ItemsIdGetResponse | null> {
  try {
    const response = await readItemV1ItemsIdGet({
      path: { id: itemId },
      throwOnError: true,
    });
    return response.data;
  } catch {
    return null;
  }
}
