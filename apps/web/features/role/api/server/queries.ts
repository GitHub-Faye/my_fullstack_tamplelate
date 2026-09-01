"use server";

import {
  readRolesV1RolesGet,
  readRoleV1RolesRoleIdGet,
  type ReadRolesV1RolesGetData,
  type ReadRolesV1RolesGetResponse,
  type ReadRoleV1RolesRoleIdGetResponse,
} from "@repo/sdk";

// ==================== Server-Side Data Fetching ====================

import { DEFAULT_PAGINATION } from "@repo/contracts/pagination";

/**
 * Get roles list (server-side)
 * Use this in Server Components for initial data fetching
 */
export async function getRoles(
  filters: ReadRolesV1RolesGetData["query"] = {
    page: DEFAULT_PAGINATION.page,
    page_size: DEFAULT_PAGINATION.page_size,
  }
): Promise<ReadRolesV1RolesGetResponse> {
  const response = await readRolesV1RolesGet({
    query: filters,
    throwOnError: true,
  });
  return response.data;
}

/**
 * Get role by ID (server-side)
 * Use this in Server Components for initial data fetching
 */
export async function getRoleById(
  roleId: string
): Promise<ReadRoleV1RolesRoleIdGetResponse | null> {
  try {
    const response = await readRoleV1RolesRoleIdGet({
      path: { role_id: roleId },
      throwOnError: true,
    });
    return response.data;
  } catch {
    return null;
  }
}
