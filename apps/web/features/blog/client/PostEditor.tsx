"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useCreatePost, useUpdatePost, useCategories } from "../api";
import type { PostPublic, CategoryPublic } from "@repo/sdk";
import { toast } from "sonner";

interface PostEditorProps {
  initial?: Partial<PostPublic & { body: string }>;
  submitLabel?: string;
  onSuccess?: () => void;
  postId?: string; // for editing
}

export function PostEditor({
  initial,
  submitLabel = "发布",
  onSuccess,
  postId,
}: PostEditorProps) {
  const router = useRouter();
  const { data: categoriesData } = useCategories({ page: 1, page_size: 100 });
  const categories = (categoriesData?.data ?? []) as CategoryPublic[];

  const [slug, setSlug] = useState(initial?.slug ?? "");
  const [title, setTitle] = useState(initial?.title ?? "");
  const [excerpt, setExcerpt] = useState(initial?.excerpt ?? "");
  const [body, setBody] = useState(initial?.body ?? "");
  const [categoryId, setCategoryId] = useState(initial?.category_id ?? "");
  const [isPublished, setIsPublished] = useState(initial?.is_published ?? false);
  const [publishedAt, setPublishedAt] = useState(
    initial?.published_at
      ? new Date(initial.published_at).toISOString().slice(0, 16)
      : ""
  );

  const createPost = useCreatePost();
  const updatePost = useUpdatePost();

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      try {
        const data = {
          slug,
          title,
          excerpt: excerpt || null,
          body,
          category_id: categoryId || null,
          is_published: isPublished,
          published_at: publishedAt
            ? new Date(publishedAt).toISOString()
            : null,
        };

        if (postId) {
          await updatePost.mutateAsync({ postId, data });
        } else {
          await createPost.mutateAsync(data);
        }

        toast.success(postId ? "文章更新成功" : "文章发布成功");
        onSuccess?.();
        router.push("/dashboard/blog");
      } catch (err) {
        toast.error((err as Error).message || "操作失败");
      }
    },
    [
      slug, title, excerpt, body, categoryId, isPublished, publishedAt,
      postId, createPost, updatePost, onSuccess, router,
    ]
  );

  return (
    <form onSubmit={handleSubmit}>
      <Card>
        <CardHeader>
          <CardTitle>{postId ? "编辑文章" : "发布新文章"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="slug">Slug</Label>
              <Input
                id="slug"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="weekly-001"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="category">分类</Label>
              <Select value={categoryId} onValueChange={setCategoryId}>
                <SelectTrigger>
                  <SelectValue placeholder="选择分类（可选）" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">无分类</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>
                      {cat.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="title">标题</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="文章标题"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="excerpt">摘要</Label>
            <Textarea
              id="excerpt"
              value={excerpt}
              onChange={(e) => setExcerpt(e.target.value)}
              placeholder="文章摘要（可选，最多 500 字）"
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="body">正文（Markdown）</Label>
            <Textarea
              id="body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="支持 Markdown 格式..."
              rows={12}
              required
            />
          </div>

          <div className="flex items-center gap-6 pt-2">
            <div className="flex items-center gap-2">
              <Switch
                checked={isPublished}
                onCheckedChange={setIsPublished}
                id="published"
              />
              <Label htmlFor="published">发布</Label>
            </div>
            <div className="space-y-1">
              <Label htmlFor="publishedAt" className="text-xs">
                发布日期
              </Label>
              <Input
                id="publishedAt"
                type="datetime-local"
                value={publishedAt}
                onChange={(e) => setPublishedAt(e.target.value)}
                className="w-56"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
            >
              取消
            </Button>
            <Button type="submit" disabled={createPost.isPending || updatePost.isPending}>
              {createPost.isPending || updatePost.isPending
                ? "保存中..."
                : submitLabel}
            </Button>
          </div>
        </CardContent>
      </Card>
    </form>
  );
}