import { permanentRedirect } from "next/navigation";

/**
 * 旧路由 /dashboard/admin/users/[id]/edit → 新路由 /dashboard/users/[id]/edit
 */
export default async function OldEditUserPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  permanentRedirect(`/dashboard/users/${id}/edit`);
}