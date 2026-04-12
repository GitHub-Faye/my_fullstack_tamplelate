import { getItems } from "../api/server/queries";
import { ItemTable } from "../client/ItemTable";

interface ItemListProps {
  currentUserId?: string;
}

/**
 * ItemList Server Component
 * Fetches initial item data on the server and renders the client ItemTable
 */
export async function ItemList({ currentUserId }: ItemListProps) {
  // Fetch items on the server
  const initialData = await getItems({ page: 1, page_size: 10 });

  // Pass initial data to the client component
  // Note: The ItemTable component uses React Query, so it will handle
  // client-side data fetching. For a fully server-rendered table,
  // you would need to create a separate Server Component version.
  return <ItemTable currentUserId={currentUserId} />;
}
