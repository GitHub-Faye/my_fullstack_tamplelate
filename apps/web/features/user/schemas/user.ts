import { z } from "zod";

/**
 * User base schema (shared fields)
 * Matches backend UserBase
 */
export const userBaseSchema = z.object({
  email: z
    .string()
    .min(1, "请输入邮箱")
    .email("请输入有效的邮箱地址")
    .max(255, "邮箱不能超过255个字符"),
  isActive: z.boolean().default(true),
  isSuperuser: z.boolean().default(false),
  fullName: z
    .string()
    .max(255, "姓名不能超过255个字符")
    .optional()
    .nullable(),
});

/**
 * User create form schema (admin)
 * Matches backend UserCreate
 */
export const userCreateSchema = z.object({
  email: z
    .string()
    .min(1, "请输入邮箱")
    .email("请输入有效的邮箱地址")
    .max(255, "邮箱不能超过255个字符"),
  password: z
    .string()
    .min(1, "请输入密码")
    .min(8, "密码至少需要8个字符")
    .max(128, "密码不能超过128个字符"),
  isActive: z.boolean().default(true),
  isSuperuser: z.boolean().default(false),
  fullName: z
    .string()
    .max(255, "姓名不能超过255个字符")
    .optional()
    .or(z.literal("")),
});

export type UserCreateFormData = z.infer<typeof userCreateSchema>;

/**
 * User update form schema (admin)
 * Matches backend UserUpdate
 */
export const userUpdateSchema = z.object({
  email: z
    .string()
    .email("请输入有效的邮箱地址")
    .max(255, "邮箱不能超过255个字符")
    .optional()
    .or(z.literal("")),
  password: z
    .string()
    .min(8, "密码至少需要8个字符")
    .max(128, "密码不能超过128个字符")
    .optional()
    .or(z.literal("")),
  isActive: z.boolean().optional(),
  isSuperuser: z.boolean().optional(),
  fullName: z
    .string()
    .max(255, "姓名不能超过255个字符")
    .optional()
    .nullable(),
});

export type UserUpdateFormData = z.infer<typeof userUpdateSchema>;

/**
 * User update me form schema (self-service)
 * Matches backend UserUpdateMe
 */
export const userUpdateMeSchema = z.object({
  email: z
    .string()
    .email("请输入有效的邮箱地址")
    .max(255, "邮箱不能超过255个字符")
    .optional()
    .or(z.literal("")),
  fullName: z
    .string()
    .max(255, "姓名不能超过255个字符")
    .optional()
    .or(z.literal("")),
});

export type UserUpdateMeFormData = z.infer<typeof userUpdateMeSchema>;

/**
 * User filter/pagination schema
 */
export const userListFilterSchema = z.object({
  skip: z.number().min(0).default(0),
  limit: z.number().min(1).max(100).default(10),
  search: z.string().optional(),
});

export type UserListFilter = z.infer<typeof userListFilterSchema>;
