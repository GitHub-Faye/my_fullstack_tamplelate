"use server";

import {
  readUsersV1UsersGet,
  readUserByIdV1UsersUserIdGet,
  readUserMeV1UsersMeGet,
  type ReadUsersV1UsersGetData,
  type ReadUsersV1UsersGetResponse,
  type ReadUserByIdV1UsersUserIdGetResponse,
  type ReadUserMeV1UsersMeGetResponse,
} from "@repo/sdk";

// ==================== Server-Side Data Fetching ====================

/**
 * Get users list (server-side)
 * Use this in Server Components for initial data fetching
 */
export async function getUsers(
  filters: ReadUsersV1UsersGetData["query"] = { page: 1, page_size: 10 }
): Promise<ReadUsersV1UsersGetResponse> {
  const response = await readUsersV1UsersGet({
    query: filters,
    throwOnError: true,
  });
  return response.data;
}

/**
 * Get user by ID (server-side)
 * Use this in Server Components for initial data fetching
 */
export async function getUserById(
  userId: string
): Promise<ReadUserByIdV1UsersUserIdGetResponse | null> {
  try {
    const response = await readUserByIdV1UsersUserIdGet({
      path: { user_id: userId },
      throwOnError: true,
    });
    return response.data;
  } catch {
    return null;
  }
}

/**
 * Get current user (server-side)
 * Use this in Server Components when you have the token
 */
export async function getCurrentUser(
  token?: string
): Promise<ReadUserMeV1UsersMeGetResponse | null> {
  try {
    // Note: For server-side calls, you may need to configure the client
    // with the token if your SDK supports it
    const response = await readUserMeV1UsersMeGet({
      throwOnError: true,
    });
    return response.data;
  } catch {
    return null;
  }
}
