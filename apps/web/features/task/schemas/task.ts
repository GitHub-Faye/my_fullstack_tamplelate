/**
 * Task 模块 - 任务表单验证 Schema
 */

import { z } from "zod";

/**
 * 任务创建表单验证
 * 使用 z.input 获取宽松输入类型（允许 description 传入 string）
 */
export const taskCreateSchema = z.object({
  name: z
    .string()
    .min(1, "任务名称不能为空")
    .max(255, "任务名称不能超过255个字符"),
  description: z
    .string()
    .max(2000, "任务描述不能超过2000个字符")
    .nullable()
    .default(null),
  task_type: z.enum(["normal", "urgent", "convenient"]).default("normal"),
  expected_online_time: z
    .string()
    .nullable()
    .default(null),
});

export type TaskCreateFormData = z.input<typeof taskCreateSchema>;

/**
 * 任务更新表单验证
 */
export const taskUpdateSchema = z.object({
  name: z
    .string()
    .min(1, "任务名称不能为空")
    .max(255, "任务名称不能超过255个字符")
    .nullable()
    .default(null),
  description: z
    .string()
    .max(2000, "任务描述不能超过2000个字符")
    .nullable()
    .default(null),
  task_type: z.enum(["normal", "urgent", "convenient"]).nullable().default(null),
  expected_online_time: z
    .string()
    .nullable()
    .default(null),
});

export type TaskUpdateFormData = z.input<typeof taskUpdateSchema>;