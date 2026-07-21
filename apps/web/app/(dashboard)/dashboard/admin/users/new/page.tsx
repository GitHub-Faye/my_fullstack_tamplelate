import { permanentRedirect } from "next/navigation";

/**
 * 旧路由 /dashboard/admin/users/new → 新路由 /dashboard/users/new
 */
export default function OldNewUserPage() {
  permanentRedirect("/dashboard/users/new");
}