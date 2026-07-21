import { permanentRedirect } from "next/navigation";

/**
 * 旧路由 /dashboard/admin/tasks → 新路由 /dashboard/tasks
 */
export default function OldAdminTasksPage() {
  permanentRedirect("/dashboard/tasks");
}