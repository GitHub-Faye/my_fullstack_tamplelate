"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Settings,
  Users,
  Shield,
  LogOut,
  User,
} from "lucide-react";
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
import { cn } from "@/lib/utils";
import { hasScope, UserScope, RoleScope } from "@repo/contracts/scopes";
import { Brand } from "@/components/brand";
import { ThemeToggle } from "@/components/theme-toggle";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";

const navigation = [
  { name: "仪表盘", href: "/dashboard", icon: LayoutDashboard },
  { name: "设置", href: "/dashboard/settings", icon: Settings },
];

const adminNavigation = [
  { name: "用户管理", href: "/dashboard/admin", icon: Users },
  { name: "角色管理", href: "/dashboard/roles", icon: Shield },
];

interface SidebarProps {
  /** 移动端导航点击后关闭抽屉 */
  onNavigate?: () => void;
}

/**
 * 侧边导航：品牌 + 按 scope 过滤的导航项
 * 桌面端固定展示；移动端由抽屉承载
 */
export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const userScopes = useUserScopes();

  // 管理入口按 scope 判定可见性（与后端 require_scope 一致）
  const visibleAdmin = adminNavigation.filter((item) => {
    if (item.href === "/dashboard/admin") return hasScope(userScopes, UserScope.READ);
    if (item.href === "/dashboard/roles") return hasScope(userScopes, RoleScope.READ);
    return true;
  });

  const groups = [
    { items: navigation },
    ...(visibleAdmin.length ? [{ items: visibleAdmin }] : []),
  ];

  return (
    <div className="flex h-full flex-col">
      {/* 品牌 */}
      <div className="flex h-16 items-center border-b px-5">
        <Brand onClick={onNavigate} />
      </div>

      {/* 导航 */}
      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4" aria-label="主导航">
        {groups.map((group, gi) => (
          <div key={gi} className="space-y-1">
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive =
                pathname === item.href ||
                (item.href !== "/dashboard" && pathname.startsWith(`${item.href}/`));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={onNavigate}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {item.name}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* 底部用户区 */}
      <div className="space-y-1 border-t p-3">
        <div className="flex items-center justify-between px-2 py-1">
          <span className="text-xs font-medium text-muted-foreground">外观</span>
          <ThemeToggle />
        </div>
        <SidebarUserMenu />
      </div>
    </div>
  );
}

/** 侧边栏底部用户菜单 */
function SidebarUserMenu() {
  const router = useRouter();
  const user = useCurrentUser();
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  const getInitials = (name: string | null | undefined) => {
    if (!name) return "U";
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-auto w-full justify-start gap-3 px-2 py-2">
          <Avatar className="h-8 w-8">
            <AvatarFallback>{getInitials(user?.full_name || user?.email)}</AvatarFallback>
          </Avatar>
          <span className="flex min-w-0 flex-1 flex-col items-start text-left">
            <span className="max-w-[8rem] truncate text-sm font-medium">
              {user?.full_name || "用户"}
            </span>
            <span className="max-w-[8rem] truncate text-xs text-muted-foreground">
              {user?.email}
            </span>
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="start" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">
              {user?.full_name || "用户"}
            </p>
            <p className="text-xs leading-none text-muted-foreground">{user?.email}</p>
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
          className="cursor-pointer text-destructive focus:text-destructive"
          onClick={handleLogout}
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>退出登录</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

/** 移动端抽屉（由 DashboardLayout 控制开关） */
export function MobileSidebar({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-72 p-0 sm:max-w-sm">
        <SheetTitle className="sr-only">导航菜单</SheetTitle>
        <Sidebar onNavigate={() => onOpenChange(false)} />
      </SheetContent>
    </Sheet>
  );
}