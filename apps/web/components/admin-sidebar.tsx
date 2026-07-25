"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  ClipboardList,
  Banknote,
  Shield,
  Users,
  ScrollText,
  FileText,
  type LucideIcon,
} from "lucide-react";

const adminNavItems: { label: string; href: string; icon: LucideIcon }[] = [
  { label: "数据概览", href: "/admin", icon: LayoutDashboard },
  { label: "任务管理", href: "/admin/tasks", icon: ClipboardList },
  { label: "工资管理", href: "/admin/salaries", icon: Banknote },
  { label: "角色管理", href: "/admin/roles", icon: Shield },
  { label: "账号管理", href: "/admin/users", icon: Users },
  { label: "规则配置", href: "/admin/rules", icon: ScrollText },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0">
      <nav className="space-y-1 sticky top-20">
        {adminNavItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}