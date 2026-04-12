import { z } from "zod";

/**
 * Login form validation schema
 * Matches backend BodyLoginAccessTokenV1LoginAccessTokenPost
 */
export const loginSchema = z.object({
  email: z
    .string()
    .min(1, "请输入邮箱")
    .email("请输入有效的邮箱地址"),
  password: z
    .string()
    .min(1, "请输入密码")
    .min(8, "密码至少需要8个字符"),
  rememberMe: z.boolean().default(false),
});

export type LoginFormData = z.infer<typeof loginSchema>;

/**
 * Signup form validation schema
 * Matches backend UserRegister
 */
export const signupSchema = z.object({
  email: z
    .string()
    .min(1, "请输入邮箱")
    .email("请输入有效的邮箱地址"),
  password: z
    .string()
    .min(1, "请输入密码")
    .min(8, "密码至少需要8个字符")
    .max(128, "密码不能超过128个字符"),
  confirmPassword: z.string().min(1, "请确认密码"),
  fullName: z
    .string()
    .max(255, "姓名不能超过255个字符")
    .optional()
    .or(z.literal("")),
  acceptTerms: z.boolean().refine((val) => val === true, {
    message: "请同意服务条款",
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: "两次输入的密码不一致",
  path: ["confirmPassword"],
});

export type SignupFormData = z.infer<typeof signupSchema>;

/**
 * Password change form validation schema
 * Matches backend UpdatePassword
 */
export const passwordChangeSchema = z.object({
  currentPassword: z
    .string()
    .min(1, "请输入当前密码")
    .min(8, "密码至少需要8个字符"),
  newPassword: z
    .string()
    .min(1, "请输入新密码")
    .min(8, "密码至少需要8个字符")
    .max(128, "密码不能超过128个字符"),
  confirmNewPassword: z.string().min(1, "请确认新密码"),
}).refine((data) => data.newPassword === data.confirmNewPassword, {
  message: "两次输入的密码不一致",
  path: ["confirmNewPassword"],
}).refine((data) => data.currentPassword !== data.newPassword, {
  message: "新密码不能与当前密码相同",
  path: ["newPassword"],
});

export type PasswordChangeFormData = z.infer<typeof passwordChangeSchema>;

/**
 * Password reset request schema
 */
export const passwordResetRequestSchema = z.object({
  email: z
    .string()
    .min(1, "请输入邮箱")
    .email("请输入有效的邮箱地址"),
});

export type PasswordResetRequestFormData = z.infer<typeof passwordResetRequestSchema>;

/**
 * Password reset confirmation schema
 * Matches backend NewPassword
 */
export const passwordResetConfirmSchema = z.object({
  token: z.string().min(1, "Token不能为空"),
  newPassword: z
    .string()
    .min(1, "请输入新密码")
    .min(8, "密码至少需要8个字符")
    .max(128, "密码不能超过128个字符"),
  confirmPassword: z.string().min(1, "请确认密码"),
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: "两次输入的密码不一致",
  path: ["confirmPassword"],
});

export type PasswordResetConfirmFormData = z.infer<typeof passwordResetConfirmSchema>;
