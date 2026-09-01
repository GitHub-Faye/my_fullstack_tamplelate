import { DEFAULT_PAGINATION } from "@repo/contracts/pagination";
import { getRoles } from "../api/server/queries";
import { RoleTable } from "../client/RoleTable";

/**
 * RoleList Server Component
 * Fetches initial role data on the server and renders the client RoleTable
 */
export async function RoleList() {
  // Fetch roles on the server
  await getRoles({
    page: DEFAULT_PAGINATION.page,
    page_size: DEFAULT_PAGINATION.page_size,
  });

  // Pass initial data to the client component
  // Note: The RoleTable component uses React Query, so it will handle
  // client-side data fetching. For a fully server-rendered table,
  // you would need to create a separate Server Component version.
  return <RoleTable />;
}
