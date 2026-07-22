import {
  LayoutDashboard,
  Users,
  User,
  FileCheck,
  Wrench,
  Banknote,
  Shield,
  ScrollText,
  FileText,
  ClipboardList,
  type LucideIcon,
} from "lucide-react";

/** 导航项定义 */
export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  /** 可见角色列表，空数组表示所有角色可见 */
  roles: ("pm" | "engineer" | "admin")[];
}

/** 所有导航项 */
export const NAVIGATION: NavItem[] = [
  // PM 导航
  { label: "PM工作台", href: "/pm", icon: LayoutDashboard, roles: ["pm", "admin"] },
  { label: "操作日志", href: "/pm/logs", icon: FileCheck, roles: ["pm", "admin"] },
  // 工程师导航
  { label: "工程师工作台", href: "/engineer", icon: Wrench, roles: ["engineer", "admin"] },
  { label: "工作日志", href: "/engineer/logs", icon: FileCheck, roles: ["engineer", "admin"] },
  // 管理员导航
  { label: "数据概览", href: "/admin", icon: LayoutDashboard, roles: ["admin"] },
  { label: "任务管理", href: "/admin/tasks", icon: ClipboardList, roles: ["admin"] },
  { label: "工资管理", href: "/admin/salaries", icon: Banknote, roles: ["admin"] },
  { label: "角色管理", href: "/admin/roles", icon: Shield, roles: ["admin"] },
  { label: "账号管理", href: "/admin/users", icon: Users, roles: ["admin"] },
  { label: "规则配置", href: "/admin/rules", icon: ScrollText, roles: ["admin"] },
  { label: "操作日志", href: "/admin/logs", icon: FileText, roles: ["admin"] },
  { label: "设置", href: "/dashboard/settings", icon: User, roles: ["admin"] },
];

/** 根据角色获取可见导航 */
export function getNavigationByRole(role: string | undefined): NavItem[] {
  if (!role) return [];
  return NAVIGATION.filter((item) => item.roles.includes(role as "pm" | "engineer" | "admin"));
}