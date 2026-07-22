import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with clsx and tailwind-merge
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format date to locale string
 */
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return "-";
  return new Date(date).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Format date as YYYY-MM-DD (used in tables)
 */
export function formatDateShort(dateStr: string | null | undefined): string {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return isNaN(d.getTime())
    ? "-"
    : `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")}`;
}

/**
 * Format date as MM-DD HH:mm (used in tables)
 */
export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return isNaN(d.getTime())
    ? "-"
    : `${(d.getMonth() + 1).toString().padStart(2, "0")}-${d.getDate().toString().padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
}

/**
 * Format user role for display
 */
export function formatUserRole(isSuperuser: boolean | undefined): string {
  return isSuperuser ? "超级管理员" : "普通用户";
}

/** 角色值 → 中文标签映射（供 Select 选项使用） */
export const ROLE_OPTIONS = [
  { value: "engineer", label: "工程师" },
  { value: "pm", label: "PM" },
  { value: "admin", label: "管理员" },
] as const;

/** 角色值 → 中文标签映射（供 Badge 显示使用） */
export const ROLE_LABELS: Record<string, string> = {
  engineer: "工程师",
  pm: "PM",
  admin: "管理员",
};

/**
 * Format user role type for display
 */
export function formatRoleType(role: string | undefined): string {
  return role ? ROLE_LABELS[role] || role : "-";
}

/** 在岗状态 → 中文标签映射（供 Select 选项使用） */
export const EMPLOYMENT_STATUS_OPTIONS = [
  { value: "on_duty", label: "在职" },
  { value: "probation", label: "试用" },
  { value: "leave", label: "休假" },
  { value: "resigned", label: "离职" },
] as const;

/** 在岗状态值 → 中文标签映射 */
export const EMPLOYMENT_STATUS_LABELS: Record<string, string> = {
  on_duty: "在职",
  probation: "试用",
  leave: "休假",
  resigned: "离职",
};

/** 在岗状态 → Badge variant 映射 */
export const EMPLOYMENT_STATUS_VARIANTS: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  on_duty: "default",
  probation: "secondary",
  leave: "outline",
  resigned: "destructive",
};

/**
 * Format user status for display
 */
export function formatUserStatus(isActive: boolean | undefined): string {
  return isActive ? "活跃" : "已禁用";
}

/**
 * Format employment status for display
 */
export function formatEmploymentStatus(status: string | undefined | null): string {
  return status ? EMPLOYMENT_STATUS_LABELS[status] || status : "-";
}
