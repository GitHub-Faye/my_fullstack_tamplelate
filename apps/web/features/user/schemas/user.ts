import { z } from "zod";

/**
 * 在岗状态枚举
 */
export const employmentStatusEnum = z.enum(["on_duty", "probation", "leave", "resigned"]);

/**
 * 用户角色枚举
 */
export const userRoleEnum = z.enum(["engineer", "pm", "admin"]);

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
 * 对应后端 UserAdminCreate
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
  // 人事管理字段
  phone: z.string().max(20, "手机号不能超过20个字符").optional().or(z.literal("")),
  department: z.string().max(100, "部门不能超过100个字符").optional().or(z.literal("")),
  hireDate: z.string().optional().or(z.literal("")),
  employmentStatus: employmentStatusEnum.optional(),
  role: userRoleEnum.optional(),
  // 工程师工资字段
  S0: z.number().min(0).optional(),
  H0: z.number().min(0).optional(),
  TMonthlyPlan: z.number().min(0).optional(),
  // PM 工资字段
  SBase: z.number().min(0).optional(),
  SAssess: z.number().min(0).optional(),
  RBase: z.number().min(0).max(1).optional(),
  RAssess: z.number().min(0).max(1).optional(),
  baselineClientCount: z.number().min(0).optional(),
});

export type UserCreateFormData = z.infer<typeof userCreateSchema>;

/**
 * User update form schema (admin)
 * 对应后端 UserAdminUpdate
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
  // 人事管理字段
  phone: z.string().max(20, "手机号不能超过20个字符").optional().or(z.literal("")),
  department: z.string().max(100, "部门不能超过100个字符").optional().or(z.literal("")),
  hireDate: z.string().optional().or(z.literal("")),
  employmentStatus: employmentStatusEnum.optional(),
  role: userRoleEnum.optional(),
  // 工程师工资字段
  S0: z.number().min(0).optional(),
  H0: z.number().min(0).optional(),
  TMonthlyPlan: z.number().min(0).optional(),
  // PM 工资字段
  SBase: z.number().min(0).optional(),
  SAssess: z.number().min(0).optional(),
  RBase: z.number().min(0).max(1).optional(),
  RAssess: z.number().min(0).max(1).optional(),
  baselineClientCount: z.number().min(0).optional(),
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
