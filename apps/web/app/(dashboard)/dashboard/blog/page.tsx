"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAdminPosts, useDeletePost } from "@/features/blog/api";
import type { PostPublic } from "@repo/sdk";
import { toast } from "sonner";

export default function BlogAdminPage() {
  const router = useRouter();
  const { data, isLoading, refetch } = useAdminPosts({
    pagination: { page: 1, page_size: 50 },
  });
  const deletePost = useDeletePost();

  const posts = (data?.data ?? []) as PostPublic[];

  const handleDelete = async (postId: string) => {
    if (!confirm("确认删除这篇文章？")) return;
    try {
      await deletePost.mutateAsync(postId);
      toast.success("已删除");
      refetch();
    } catch {
      toast.error("删除失败");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">文章管理</h1>
        <Button onClick={() => router.push("/dashboard/blog/new")}>
          写新文章
        </Button>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">加载中…</p>
      ) : posts.length === 0 ? (
        <p className="text-muted-foreground">暂无文章。</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>标题</TableHead>
              <TableHead className="w-24">分类</TableHead>
              <TableHead className="w-24">状态</TableHead>
              <TableHead className="w-32">日期</TableHead>
              <TableHead className="w-32">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {posts.map((p) => (
              <TableRow key={p.id}>
                <TableCell>
                  <a
                    href={`/blog/posts/${p.slug}`}
                    className="font-medium hover:underline"
                  >
                    {p.title}
                  </a>
                  <div className="text-xs text-muted-foreground font-mono">
                    {p.slug}
                  </div>
                </TableCell>
                <TableCell>{p.category?.name ?? "-"}</TableCell>
                <TableCell>
                  {p.is_published ? (
                    <span className="text-green-600 text-xs">已发布</span>
                  ) : (
                    <span className="text-yellow-600 text-xs">草稿</span>
                  )}
                </TableCell>
                <TableCell className="text-xs">
                  {p.published_at
                    ? new Date(p.published_at).toLocaleDateString("zh-CN")
                    : "-"}
                </TableCell>
                <TableCell className="space-x-3">
                  <Button
                    variant="link"
                    size="sm"
                    onClick={() =>
                      router.push(`/dashboard/blog/${p.id}/edit`)
                    }
                  >
                    编辑
                  </Button>
                  <Button
                    variant="link"
                    size="sm"
                    className="text-destructive"
                    onClick={() => handleDelete(p.id)}
                    disabled={deletePost.isPending}
                  >
                    删除
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}