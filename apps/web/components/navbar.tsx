"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCurrentUser, useUserScopes, useAuthStore } from "@/features/user";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { LayoutDashboard, Users, Settings, LogOut, User, Shield } from "lucide-react";
import { cn } from "@/lib/utils";
import { hasScope, UserScope, RoleScope } from "@repo/contracts/scopes";

const navigation = [
  { name: "仪表盘", href: "/dashboard", icon: LayoutDashboard },
  { name: "设置", href: "/dashboard/settings", icon: Settings },
];

const adminNavigation = [
  { name: "用户管理", href: "/dashboard/admin", icon: Users },
  { name: "角色管理", href: "/dashboard/roles", icon: Shield },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = useCurrentUser();
  const userScopes = useUserScopes();
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const getInitials = (name: string | undefined | null) => {
    if (!name) return "U";
    return name.slice(0, 2).toUpperCase();
  };

  // 管理入口按 scope 判定可见性（与后端 require_scope 一致）：
  // - 用户管理: user:read
  // - 角色管理: role:read
  // 无对应 scope 时（如仅 viewer）不显示管理入口
  const visibleAdminNavigation = adminNavigation.filter((item) => {
    if (item.href === "/dashboard/admin") {
      return hasScope(userScopes, UserScope.READ);
    }
    if (item.href === "/dashboard/roles") {
      return hasScope(userScopes, RoleScope.READ);
    }
    return true;
  });

  const allNavigation = [...navigation, ...visibleAdminNavigation];

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        {/* Logo */}
        <div className="mr-4 flex">
          <Link href="/dashboard" className="flex items-center space-x-2">
            <span className="font-bold text-lg">MyApp</span>
          </Link>
        </div>

        {/* Navigation Links */}
        <nav className="flex flex-1 items-center space-x-6 text-sm font-medium">
          {allNavigation.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center space-x-1 transition-colors hover:text-primary",
                  isActive
                    ? "text-foreground"
                    : "text-muted-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* User Menu */}
        <div className="flex items-center space-x-4">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="relative h-8 w-8 rounded-full"
              >
                <Avatar className="h-8 w-8">
                  <AvatarFallback>
                    {getInitials(user?.full_name || user?.email)}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {user?.full_name || "用户"}
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/dashboard/settings" className="cursor-pointer">
                  <User className="mr-2 h-4 w-4" />
                  <span>个人设置</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="cursor-pointer text-red-600 focus:text-red-600"
                onClick={handleLogout}
              >
                <LogOut className="mr-2 h-4 w-4" />
                <span>退出登录</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
