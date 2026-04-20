"use server";

import {
  readItemsV1ItemsGet,
  readItemV1ItemsItemIdGet,
  type ReadItemsV1ItemsGetData,
  type ReadItemsV1ItemsGetResponse,
  type ReadItemV1ItemsItemIdGetResponse,
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
): Promise<ReadItemV1ItemsItemIdGetResponse | null> {
  try {
    const response = await readItemV1ItemsItemIdGet({
      path: { item_id: itemId },
      throwOnError: true,
    });
    return response.data;
  } catch {
    return null;
  }
}
