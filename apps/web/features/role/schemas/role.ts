import { z } from "zod";
import { ALL_SCOPES } from "@repo/contracts/scopes";

/**
 * Role creation schema
 * Matches backend RoleCreate（name 必填，scopes 可选，默认空集合）
 */
export const roleCreateSchema = z.object({
  name: z.string().min(1, "角色名不能为空").max(50, "角色名最多50个字符"),
  scopes: z
    .array(z.string())
    .max(100, "scope 数量不能超过100")
    .optional()
    .default([]),
});

/**
 * Role update schema
 * Matches backend RoleUpdate（所有字段可选，部分更新）
 * scopes 为整体替换语义（非增量合并）
 */
export const roleUpdateSchema = z.object({
  name: z
    .string()
    .min(1, "角色名不能为空")
    .max(50, "角色名最多50个字符")
    .optional(),
  scopes: z
    .array(z.string())
    .max(100, "scope 数量不能超过100")
    .optional(),
});

export type RoleCreateInput = z.infer<typeof roleCreateSchema>;
export type RoleUpdateInput = z.infer<typeof roleUpdateSchema>;

/**
 * 可选 scope 列表（来自契约层 ALL_SCOPES，与后端 scopes.py 保持一致）
 */
export const AVAILABLE_SCOPES: readonly string[] = ALL_SCOPES;
