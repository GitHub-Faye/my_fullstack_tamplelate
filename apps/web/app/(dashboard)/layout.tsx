"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useIsAuthenticated, useIsHydrated, useUserScopes } from "@/features/user";
import { Loader2 } from "lucide-react";
import { Navbar } from "@/components/navbar";
import { hasScope, UserScope, RoleScope, type ScopeType } from "@repo/contracts/scopes";

// 管理页面所需 scope（与后端 require_scope 保持一致）
const SCOPE_GUARDS: { prefix: string; scope: ScopeType }[] = [
  { prefix: "/dashboard/admin", scope: UserScope.READ },
  { prefix: "/dashboard/roles", scope: RoleScope.READ },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const isAuthenticated = useIsAuthenticated();
  const isHydrated = useIsHydrated();
  const userScopes = useUserScopes();

  useEffect(() => {
    // Only redirect after store is hydrated
    if (isHydrated && !isAuthenticated) {
      router.replace("/login");
      return;
    }
    // 已登录但访问无 scope 的管理页面 → 回到仪表盘
    if (isHydrated && isAuthenticated) {
      const denied = SCOPE_GUARDS.find(
        (guard) =>
          pathname === guard.prefix || pathname.startsWith(`${guard.prefix}/`)
      );
      if (denied && !hasScope(userScopes, denied.scope)) {
        router.replace("/dashboard");
      }
    }
  }, [isHydrated, isAuthenticated, userScopes, pathname, router]);

  // Show loading while store is not hydrated
  if (!isHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  // After hydration, if not authenticated, show loading (will redirect)
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container p-6">{children}</main>
    </div>
  );
}
