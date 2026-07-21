import { permanentRedirect } from "next/navigation";

/**
 * 旧路由 /dashboard/admin → 新路由 /dashboard/users
 */
export default function OldAdminPage() {
  permanentRedirect("/dashboard/users");
}