import { permanentRedirect } from "next/navigation";

/**
 * 旧路由 /dashboard/admin/tasks/[id] → 新路由 /dashboard/tasks/[id]
 */
export default async function OldAdminTaskDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  permanentRedirect(`/dashboard/tasks/${id}`);
}