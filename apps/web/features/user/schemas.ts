import { z } from 'zod';

// User form schemas using Zod
export const userCreateSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址'),
  password: z.string().min(8, '密码至少需要8个字符').max(128, '密码不能超过128个字符'),
  full_name: z.string().max(255, '姓名不能超过255个字符').optional().nullable(),
  is_active: z.boolean(),
  is_superuser: z.boolean(),
});

export const userUpdateSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址').optional().nullable(),
  password: z.string().min(8, '密码至少需要8个字符').max(128, '密码不能超过128个字符').optional().nullable(),
  full_name: z.string().max(255, '姓名不能超过255个字符').optional().nullable(),
  is_active: z.boolean().optional(),
  is_superuser: z.boolean().optional(),
});

export const userUpdateMeSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址').optional().nullable(),
  full_name: z.string().max(255, '姓名不能超过255个字符').optional().nullable(),
});

export const updatePasswordSchema = z.object({
  current_password: z.string().min(8, '当前密码至少需要8个字符'),
  new_password: z.string().min(8, '新密码至少需要8个字符').max(128, '新密码不能超过128个字符'),
}).refine((data) => data.current_password !== data.new_password, {
  message: '新密码不能与当前密码相同',
  path: ['new_password'],
});

export const userRegisterSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址'),
  password: z.string().min(8, '密码至少需要8个字符').max(128, '密码不能超过128个字符'),
  full_name: z.string().max(255, '姓名不能超过255个字符').optional().nullable(),
});

export type UserCreateFormData = z.infer<typeof userCreateSchema>;
export type UserUpdateFormData = z.infer<typeof userUpdateSchema>;
export type UserUpdateMeFormData = z.infer<typeof userUpdateMeSchema>;
export type UpdatePasswordFormData = z.infer<typeof updatePasswordSchema>;
export type UserRegisterFormData = z.infer<typeof userRegisterSchema>;
