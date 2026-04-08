import { z } from 'zod';

// Item form schemas using Zod
export const itemCreateSchema = z.object({
  title: z.string().min(1, '标题不能为空').max(255, '标题不能超过255个字符'),
  description: z.string().max(255, '描述不能超过255个字符').optional().nullable(),
});

export const itemUpdateSchema = z.object({
  title: z.string().min(1, '标题不能为空').max(255, '标题不能超过255个字符').optional().nullable(),
  description: z.string().max(255, '描述不能超过255个字符').optional().nullable(),
});

export type ItemCreateFormData = z.infer<typeof itemCreateSchema>;
export type ItemUpdateFormData = z.infer<typeof itemUpdateSchema>;
