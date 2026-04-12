import { z } from "zod";

/**
 * Item creation schema
 */
export const itemCreateSchema = z.object({
  title: z.string().min(1, "标题不能为空").max(255, "标题最多255个字符"),
  description: z.string().max(255, "描述最多255个字符").optional().nullable(),
});

/**
 * Item update schema
 */
export const itemUpdateSchema = z.object({
  title: z.string().min(1, "标题不能为空").max(255, "标题最多255个字符").optional().nullable(),
  description: z.string().max(255, "描述最多255个字符").optional().nullable(),
});

export type ItemCreateInput = z.infer<typeof itemCreateSchema>;
export type ItemUpdateInput = z.infer<typeof itemUpdateSchema>;
