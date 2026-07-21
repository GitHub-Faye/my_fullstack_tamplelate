/**
 * Dashboard 模块 — API Query Hooks
 */
"use client";

import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import {
  readPmDashboardV1DashboardPmGet,
  readEngineerDashboardV1DashboardEngineerGet,
  readAdminDashboardV1DashboardAdminGet,
} from "@repo/sdk";

export const dashboardKeys = {
  pm: () => ["dashboard", "pm"] as const,
  engineer: () => ["dashboard", "engineer"] as const,
  admin: () => ["dashboard", "admin"] as const,
};

export type PMDashboardData = {
  user_id: string;
  full_name: string;
  today_new_clients: number;
  monthly_new_clients: number;
  salary_preview: number;
  pm_task_count: number;
};

export type EngineerDashboardData = {
  user_id: string;
  full_name: string;
  current_starpoint: number;
  T_monthly_plan: number;
  T_remaining: number;
  T_actual_monthly: number;
  T_reported_monthly: number;
  accuracy_rate: number | null;
  salary_preview: number;
};

export type AdminDashboardData = {
  today_new_clients: number;
  monthly_new_clients: number;
  today_submitted_reports: number;
  ongoing_tasks: number;
  engineer_loads: Array<{
    engineer_id: string;
    engineer_name: string;
    ongoing_count: number;
    pending_count: number;
    T_monthly_plan: number;
    T_remaining: number;
    T_accuracy_rate: number | null;
    risk_label: string;
  }>;
  total_salary: number;
  engineer_salary_cost: number;
  pm_salary_cost: number;
};

export function usePmDashboard(
  options?: Omit<
    UseQueryOptions<PMDashboardData, Error, PMDashboardData>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: dashboardKeys.pm(),
    queryFn: async () => {
      const response = await readPmDashboardV1DashboardPmGet({
        throwOnError: true,
      });
      return response.data as PMDashboardData;
    },
    ...options,
  });
}

export function useEngineerDashboard(
  options?: Omit<
    UseQueryOptions<EngineerDashboardData, Error, EngineerDashboardData>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: dashboardKeys.engineer(),
    queryFn: async () => {
      const response = await readEngineerDashboardV1DashboardEngineerGet({
        throwOnError: true,
      });
      return response.data as EngineerDashboardData;
    },
    ...options,
  });
}

export function useAdminDashboard(
  options?: Omit<
    UseQueryOptions<AdminDashboardData, Error, AdminDashboardData>,
    "queryKey" | "queryFn"
  >
) {
  return useQuery({
    queryKey: dashboardKeys.admin(),
    queryFn: async () => {
      const response = await readAdminDashboardV1DashboardAdminGet({
        throwOnError: true,
      });
      return response.data as AdminDashboardData;
    },
    ...options,
  });
}