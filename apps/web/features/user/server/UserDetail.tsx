import { notFound } from "next/navigation";
import { getAdminUserDetail } from "../api/server/queries";
import { UserForm } from "../client/UserForm";

interface UserDetailProps {
  userId: string;
}

/**
 * UserDetail Server Component
 * Fetches user data on the server via admin API (full fields) and renders the client UserForm
 */
export async function UserDetail({ userId }: UserDetailProps) {
  const user = await getAdminUserDetail(userId);

  if (!user) {
    notFound();
  }

  return <UserForm user={user} mode="edit" />;
}