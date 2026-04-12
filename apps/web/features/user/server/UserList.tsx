import { getUsers } from "../api/server/queries";
import { UserTable } from "../client/UserTable";

interface UserListProps {
  currentUserId?: string;
}

/**
 * UserList Server Component
 * Fetches initial user data on the server and renders the client UserTable
 */
export async function UserList({ currentUserId }: UserListProps) {
  // Fetch users on the server
  const initialData = await getUsers({ page: 1, page_size: 10 });

  // Pass initial data to the client component
  // Note: The UserTable component uses React Query, so it will handle
  // client-side data fetching. For a fully server-rendered table,
  // you would need to create a separate Server Component version.
  return <UserTable currentUserId={currentUserId} />;
}
