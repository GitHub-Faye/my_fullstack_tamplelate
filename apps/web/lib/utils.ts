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
 * Format user role for display
 */
export function formatUserRole(isSuperuser: boolean | undefined): string {
  return isSuperuser ? "超级管理员" : "普通用户";
}

/**
 * Format user status for display
 */
export function formatUserStatus(isActive: boolean | undefined): string {
  return isActive ? "活跃" : "已禁用";
}
