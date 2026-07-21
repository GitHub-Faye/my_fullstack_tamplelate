"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCurrentUser, useIsSuperuser, useAuthStore } from "@/features/user";
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
import { LayoutDashboard, Users, Settings, LogOut, User, FileCheck, ClipboardList, Wrench, Banknote, Shield, ScrollText, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

const pmNavigation = [
  { name: "PM工作台", href: "/pm", icon: LayoutDashboard },
  { name: "操作日志", href: "/pm/logs", icon: FileCheck },
];

const engineerNavigation = [
  { name: "工程师工作台", href: "/engineer", icon: Wrench },
  { name: "操作日志", href: "/engineer/logs", icon: FileCheck },
];

const navigation = [
  { name: "数据概览", href: "/dashboard", icon: LayoutDashboard },
  { name: "设置", href: "/dashboard/settings", icon: Settings },
];

const adminNavigation = [
  { name: "任务管理", href: "/dashboard/tasks", icon: ClipboardList },
  { name: "工资管理", href: "/dashboard/salaries", icon: Banknote },
  { name: "角色管理", href: "/dashboard/roles", icon: Shield },
  { name: "账号管理", href: "/dashboard/users", icon: Users },
  { name: "规则配置", href: "/dashboard/rules", icon: ScrollText },
  { name: "操作日志", href: "/dashboard/logs", icon: FileText },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = useCurrentUser();
  const isSuperuser = useIsSuperuser();
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const getInitials = (name: string | undefined | null) => {
    if (!name) return "U";
    return name.slice(0, 2).toUpperCase();
  };

  const isPm = user?.role === "pm";
  const isEngineer = user?.role === "engineer";
  const showPmNav = isSuperuser || isPm;
  const showEngineerNav = isSuperuser || isEngineer;

  // 数据概览：仅 superuser 可见
  // 设置：仅 superuser 可见
  const showDashboardNav = isSuperuser;

  let allNavigation: typeof navigation = [];
  if (showDashboardNav) {
    allNavigation = [...allNavigation, ...navigation];
  }
  if (showPmNav) {
    allNavigation = [...allNavigation, ...pmNavigation];
  }
  if (showEngineerNav) {
    allNavigation = [...allNavigation, ...engineerNavigation];
  }
  if (isSuperuser) {
    allNavigation = [...allNavigation, ...adminNavigation];
  }

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
