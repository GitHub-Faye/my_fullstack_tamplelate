import { notFound } from "next/navigation";
import { getUserById } from "../api/server/queries";
import { UserForm } from "../client/UserForm";

interface UserDetailProps {
  userId: string;
}

/**
 * UserDetail Server Component
 * Fetches user data on the server and renders the client UserForm
 */
export async function UserDetail({ userId }: UserDetailProps) {
  // Fetch user on the server
  const user = await getUserById(userId);

  if (!user) {
    notFound();
  }

  return <UserForm user={user} mode="edit" />;
}
