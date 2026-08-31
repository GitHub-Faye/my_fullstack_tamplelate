"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Menu } from "lucide-react";
import { useIsAuthenticated, useIsHydrated, useUserScopes } from "@/features/user";
import { Loader2 } from "lucide-react";
import { hasScope, UserScope, RoleScope, type ScopeType } from "@repo/contracts/scopes";
import { Sidebar, MobileSidebar } from "@/components/sidebar";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { Brand } from "@/components/brand";

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
  const [mobileOpen, setMobileOpen] = useState(false);

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

  // 路由变化时关闭移动端抽屉
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  // Show loading while store is not hydrated
  if (!isHydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // After hydration, if not authenticated, show loading (will redirect)
  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* 移动端抽屉 */}
      <MobileSidebar open={mobileOpen} onOpenChange={setMobileOpen} />

      {/* 桌面端侧边栏 */}
      <div className="hidden md:fixed md:inset-y-0 md:left-0 md:z-40 md:flex md:w-60 md:flex-col border-r bg-sidebar">
        <Sidebar />
      </div>

      {/* 主内容区 */}
      <div className="md:pl-60">
        {/* 移动端顶栏 */}
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 md:hidden">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileOpen(true)}
            aria-label="打开导航菜单"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <Brand size="sm" />
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </header>

        {/* 页面内容 */}
        <main className="mx-auto max-w-7xl p-4 sm:p-6 md:p-8">{children}</main>
      </div>
    </div>
  );
}
