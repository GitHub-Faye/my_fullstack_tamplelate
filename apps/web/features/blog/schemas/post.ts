import { z } from "zod";

/**
 * 文章创建校验（前端表单）
 */
export const postCreateSchema = z.object({
  slug: z
    .string()
    .min(1, "slug 不能为空")
    .max(255, "slug 最多 255 个字符")
    .regex(/^[a-zA-Z0-9_-]+$/, "slug 只允许字母、数字、连字符和下划线"),
  title: z.string().min(1, "标题不能为空").max(255, "标题最多 255 个字符"),
  excerpt: z.string().max(500, "摘要最多 500 个字符").optional().nullable(),
  body: z.string().min(1, "正文不能为空"),
  category_id: z.string().uuid("无效的分类 ID").optional().nullable(),
  is_published: z.boolean().default(false),
  published_at: z.string().datetime().optional().nullable(),
});

/**
 * 文章更新校验（所有字段可选）
 */
export const postUpdateSchema = z.object({
  slug: z
    .string()
    .min(1, "slug 不能为空")
    .max(255, "slug 最多 255 个字符")
    .regex(/^[a-zA-Z0-9_-]+$/, "slug 只允许字母、数字、连字符和下划线")
    .optional()
    .nullable(),
  title: z
    .string()
    .min(1, "标题不能为空")
    .max(255, "标题最多 255 个字符")
    .optional()
    .nullable(),
  excerpt: z.string().max(500, "摘要最多 500 个字符").optional().nullable(),
  body: z.string().optional().nullable(),
  category_id: z.string().uuid("无效的分类 ID").optional().nullable(),
  is_published: z.boolean().optional().nullable(),
  published_at: z.string().datetime().optional().nullable(),
});

/**
 * 文章筛选参数
 */
export const postFilterSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  page_size: z.coerce.number().int().min(1).max(100).default(20),
  q: z.string().optional(),
  category: z.string().optional(),
});

/**
 * 评论创建校验
 */
export const commentCreateSchema = z.object({
  author_name: z.string().min(1, "昵称不能为空").max(80, "昵称最多 80 个字符"),
  content: z.string().min(1, "评论内容不能为空").max(5000, "评论最多 5000 个字符"),
});

/**
 * 分类创建校验
 */
export const categoryCreateSchema = z.object({
  name: z.string().min(1, "名称不能为空").max(50, "名称最多 50 个字符"),
  slug: z
    .string()
    .min(1, "slug 不能为空")
    .max(50, "slug 最多 50 个字符")
    .regex(/^[a-zA-Z0-9_-]+$/, "slug 只允许字母、数字、连字符和下划线"),
});

/**
 * 分类更新校验
 */
export const categoryUpdateSchema = z.object({
  name: z.string().min(1, "名称不能为空").max(50, "名称最多 50 个字符").optional().nullable(),
  slug: z
    .string()
    .min(1, "slug 不能为空")
    .max(50, "slug 最多 50 个字符")
    .regex(/^[a-zA-Z0-9_-]+$/, "slug 只允许字母、数字、连字符和下划线")
    .optional()
    .nullable(),
});

// 类型导出
export type PostCreateInput = z.infer<typeof postCreateSchema>;
export type PostUpdateInput = z.infer<typeof postUpdateSchema>;
export type PostFilterInput = z.infer<typeof postFilterSchema>;
export type CommentCreateInput = z.infer<typeof commentCreateSchema>;
export type CategoryCreateInput = z.infer<typeof categoryCreateSchema>;
export type CategoryUpdateInput = z.infer<typeof categoryUpdateSchema>;